"""`services/auth_service.py` — coordinación de autenticación (`plan.md §2`).

Implementa **RF-001, RF-002, RF-010, RF-011, RF-013, RF-014**. Solo importa de
`core/ports/` (`UserRepositoryPort`, `CachePort`), `core/security/*` y
`core/errors.py` — nunca de `adapters/` ni de FastAPI (`SRV-ADR-017`).

Recibe `secret_key: str` explícito en cada función (misma convención que
`core/security/jwt.py`: nunca lee `Settings()` internamente) — el futuro router
(T-017/T-018) lo inyecta desde `core/config.py::Settings`.
"""
import uuid
from dataclasses import dataclass

from core.errors import ProblemDetailError
from core.ports.cache_port import CachePort
from core.ports.user_repository_port import UserRepositoryPort
from core.security import jwt as jwt_module
from core.security.jwt import TokenExpiredError, TokenInvalidError
from core.security.passwords import verify_password
from services import rbac_service

MAX_LOGIN_ATTEMPTS = 5
LOGIN_ATTEMPTS_WINDOW_SECONDS = 900

_ERRORS_BASE_URL = "https://hira.dev/errors"


@dataclass(frozen=True)
class TokenPair:
    """Par de tokens emitido por `login` (RF-001)."""

    access_token: str
    refresh_token: str


def _invalid_credentials_error() -> ProblemDetailError:
    """RF-002 — 401 genérico, idéntico para email inexistente, password
    incorrecto y usuario desactivado (evita enumeración de usuarios)."""
    return ProblemDetailError(
        status=401,
        type_=f"{_ERRORS_BASE_URL}/invalid-credentials",
        title="Credenciales inválidas",
        detail="El email o el password no coinciden con ningún usuario activo.",
    )


def _rate_limited_error() -> ProblemDetailError:
    """RF-014 — 429 al exceder `MAX_LOGIN_ATTEMPTS` en `LOGIN_ATTEMPTS_WINDOW_SECONDS`."""
    return ProblemDetailError(
        status=429,
        type_=f"{_ERRORS_BASE_URL}/rate-limited",
        title="Demasiados intentos",
        detail=(
            f"Se excedieron los {MAX_LOGIN_ATTEMPTS} intentos permitidos en "
            f"{LOGIN_ATTEMPTS_WINDOW_SECONDS} segundos para esta combinación."
        ),
    )


def _refresh_token_key(jti: str) -> str:
    return f"refresh:{jti}"


def _login_attempts_key(email: str, ip: str) -> str:
    return f"login_attempts:{email}:{ip}"


async def _register_failed_attempt(email: str, ip: str, cache: CachePort) -> None:
    """Incrementa el contador de intentos fallidos; fija el TTL de la ventana en
    el primer intento de la ventana (RF-014)."""
    key = _login_attempts_key(email, ip)
    attempts = await cache.incr(key)
    if attempts == 1:
        await cache.expire(key, LOGIN_ATTEMPTS_WINDOW_SECONDS)


async def login(
    email: str,
    password: str,
    ip: str,
    users_repo: UserRepositoryPort,
    cache: CachePort,
    secret_key: str,
) -> TokenPair:
    """RF-001, RF-002, RF-014 — valida credenciales y emite `TokenPair`.

    Antes de tocar credenciales: si la combinación `email`+`ip` ya excedió
    `MAX_LOGIN_ATTEMPTS` en la ventana vigente, rechaza con 429 sin consultar
    `users_repo` (RF-014). Cualquier fallo de credenciales (email inexistente,
    password incorrecto, usuario desactivado) incrementa el contador y responde
    con el mismo 401 genérico (RF-002). Éxito → resetea el contador, emite
    access+refresh (`core/security/jwt.py`) y guarda `refresh:{jti}` en `cache`
    con TTL de 7 días.
    """
    attempts_key = _login_attempts_key(email, ip)
    current_attempts = await cache.get(attempts_key)
    if current_attempts is not None and int(current_attempts) >= MAX_LOGIN_ATTEMPTS:
        raise _rate_limited_error()

    user = await users_repo.get_by_email(email)
    if user is None or not user.activo or not verify_password(
        password, user.password_hash
    ):
        await _register_failed_attempt(email, ip, cache)
        raise _invalid_credentials_error()

    await cache.delete(attempts_key)

    access_token = jwt_module.create_access_token(
        user_id=user.id,
        rol=user.rol,
        scope=user.scope,
        project_id=user.project_id,
        secret_key=secret_key,
    )
    jti = uuid.uuid4().hex
    refresh_token = jwt_module.create_refresh_token(
        user_id=user.id, jti=jti, secret_key=secret_key
    )
    await cache.set(
        _refresh_token_key(jti),
        user.id,
        ttl_seconds=jwt_module.REFRESH_TOKEN_TTL_DAYS * 24 * 60 * 60,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def refresh(
    refresh_token: str,
    cache: CachePort,
    users_repo: UserRepositoryPort,
    secret_key: str,
) -> str:
    """RF-011, RF-013 — emite un nuevo access token a partir de un refresh vigente.

    El `rol`/`scope`/`project_id` del nuevo access se releen vía
    `rbac_service.resolve_permissions` (vigentes), no los capturados en el
    refresh en el momento del login — un cambio de rol aplica también aquí.
    """
    try:
        claims = jwt_module.decode_token(
            refresh_token, expected_type="refresh", secret_key=secret_key
        )
    except TokenExpiredError as exc:
        raise ProblemDetailError(
            status=401,
            type_=f"{_ERRORS_BASE_URL}/token-expired",
            title="Token expirado",
            detail="El refresh token expiró; inicie sesión de nuevo.",
        ) from exc
    except TokenInvalidError as exc:
        raise ProblemDetailError(
            status=401,
            type_=f"{_ERRORS_BASE_URL}/token-invalid",
            title="Token inválido",
            detail="El refresh token es inválido.",
        ) from exc

    stored_user_id = await cache.get(_refresh_token_key(claims.jti))
    if stored_user_id is None:
        raise ProblemDetailError(
            status=401,
            type_=f"{_ERRORS_BASE_URL}/token-revoked",
            title="Refresh token revocado",
            detail="Este refresh token ya fue revocado (logout o expiración de cache).",
        )

    authenticated_user = await rbac_service.resolve_permissions(
        claims.sub, users_repo, cache
    )

    return jwt_module.create_access_token(
        user_id=authenticated_user.user_id,
        rol=authenticated_user.rol,
        scope=authenticated_user.scope,
        project_id=authenticated_user.project_id,
        secret_key=secret_key,
    )


async def logout(refresh_token: str, cache: CachePort, secret_key: str) -> None:
    """RF-010 — revoca el refresh token (`DEL refresh:{jti}`). Idempotente: un
    refresh ya revocado, expirado o malformado no lanza error — no hay nada que
    revocar."""
    try:
        claims = jwt_module.decode_token(
            refresh_token, expected_type="refresh", secret_key=secret_key
        )
    except (TokenExpiredError, TokenInvalidError):
        return

    await cache.delete(_refresh_token_key(claims.jti))
