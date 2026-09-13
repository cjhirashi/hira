"""`services/auth_service.py::login/refresh/logout` — coordinación (`plan.md §2`,
RF-001, RF-002, RF-010, RF-011, RF-013, RF-014).

Dobles (`Protocol` fakes) de `UserRepositoryPort`/`CachePort` definidos aquí mismo
(in-memory) — no son adaptadores reales (esos llegan en T-024/T-025, fuera de
alcance). `core/security/{passwords,jwt}.py` se usan **reales** (bcrypt/PyJWT),
sin mockear — son núcleo puro ya verificado en T-001..T-004.

Nota de diseño (fuera de lo literal de `plan.md §2`, decisión de implementación
de este batch — no reabre el diseño aprobado): `login`/`refresh`/`logout` reciben
`secret_key: str` explícito, igual convención que `core/security/jwt.py`
(`plan.md §2`: "Recibe `SECRET_KEY` como parámetro explícito... mantiene el
módulo sin I/O") — `services/` tampoco lee `Settings()` (regla `SRV-ADR-017`:
`services/` no hace I/O propio de configuración), así que el `secret_key` fluye
desde quien invoque (el futuro router, T-017/T-018) como cualquier otro
parámetro de coordinación.
"""
from dataclasses import replace

import pytest

from core.errors import ProblemDetailError
from core.ports.user_repository_port import UserRecord
from core.security import jwt as jwt_module
from core.security.passwords import hash_password
from services.auth_service import (
    LOGIN_ATTEMPTS_WINDOW_SECONDS,
    MAX_LOGIN_ATTEMPTS,
    login,
    logout,
    refresh,
)

SECRET_KEY = "test-secret-key"


class _FakeCache:
    """`CachePort` in-memory — sin Redis real."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._store[key] = value
        if ttl_seconds is not None:
            self.ttls[key] = ttl_seconds

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def expire(self, key: str, ttl_seconds: int) -> None:
        self.ttls[key] = ttl_seconds

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self.ttls.pop(key, None)


class _FakeUserRepository:
    """`UserRepositoryPort` in-memory — sin Postgres real."""

    def __init__(self, users: list[UserRecord]) -> None:
        self._by_email = {u.email: u for u in users}
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        user = self._by_id[user_id]
        updated = replace(user, rol=new_role)
        self._by_id[user_id] = updated
        self._by_email[user.email] = updated


def _make_user(**overrides) -> UserRecord:
    defaults = dict(
        id="user-1",
        email="admin@hira.dev",
        password_hash=hash_password("Correcto123!"),
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    defaults.update(overrides)
    return UserRecord(**defaults)


@pytest.mark.asyncio
async def test_login_credenciales_validas_retorna_token_pair():
    """RF-001 — access + refresh emitidos, refresh guardado en cache."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )

    assert token_pair.access_token
    assert token_pair.refresh_token
    claims = jwt_module.decode_token(token_pair.access_token, "access", SECRET_KEY)
    assert claims.sub == user.id
    assert claims.rol == "admin"
    refresh_claims = jwt_module.decode_token(
        token_pair.refresh_token, "refresh", SECRET_KEY
    )
    assert await cache.get(f"refresh:{refresh_claims.jti}") == user.id


@pytest.mark.asyncio
async def test_login_password_incorrecto_401_invalid_credentials():
    """RF-002 — 401 genérico, incrementa el contador de intentos."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await login(user.email, "incorrecto", "10.0.0.1", repo, cache, SECRET_KEY)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/invalid-credentials"
    assert await cache.get(f"login_attempts:{user.email}:10.0.0.1") == "1"


@pytest.mark.asyncio
async def test_login_email_inexistente_mismo_401_que_password_incorrecto():
    """RF-002 — evita enumeración: mismo `type`/`title`/`status` que password incorrecto."""
    repo = _FakeUserRepository([])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await login(
            "no-existe@hira.dev", "cualquiera", "10.0.0.1", repo, cache, SECRET_KEY
        )

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/invalid-credentials"


@pytest.mark.asyncio
async def test_login_usuario_desactivado_mismo_401():
    """RF-002 — usuario desactivado no distingue causa (no enumeración)."""
    user = _make_user(activo=False)
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await login(user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/invalid-credentials"


@pytest.mark.asyncio
async def test_login_sexto_intento_fallido_429_rate_limited():
    """RF-014 — 5 intentos/15min; el 6º se rechaza con 429 sin tocar credenciales."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    assert MAX_LOGIN_ATTEMPTS == 5
    assert LOGIN_ATTEMPTS_WINDOW_SECONDS == 900

    for _ in range(MAX_LOGIN_ATTEMPTS):
        with pytest.raises(ProblemDetailError):
            await login(user.email, "incorrecto", "10.0.0.1", repo, cache, SECRET_KEY)

    with pytest.raises(ProblemDetailError) as exc_info:
        await login(user.email, "incorrecto", "10.0.0.1", repo, cache, SECRET_KEY)

    assert exc_info.value.status == 429
    assert exc_info.value.type_ == "https://hira.dev/errors/rate-limited"


@pytest.mark.asyncio
async def test_login_exito_resetea_contador_de_intentos():
    """RF-014 — un login exitoso resetea el contador de fuerza bruta."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError):
        await login(user.email, "incorrecto", "10.0.0.1", repo, cache, SECRET_KEY)
    await login(user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY)

    assert await cache.get(f"login_attempts:{user.email}:10.0.0.1") is None


@pytest.mark.asyncio
async def test_refresh_token_valido_emite_nuevo_access():
    """RF-011 — refresh válido y no revocado emite un nuevo access token."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )

    new_access = await refresh(token_pair.refresh_token, cache, repo, SECRET_KEY)

    claims = jwt_module.decode_token(new_access, "access", SECRET_KEY)
    assert claims.sub == user.id
    assert claims.rol == "admin"


@pytest.mark.asyncio
async def test_refresh_refleja_rol_vigente_no_el_del_jwt_viejo():
    """RF-011 — el nuevo access lleva el rol **vigente**, no el capturado al login."""
    user = _make_user(rol="visor")
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )
    await repo.update_role(user.id, "admin")

    new_access = await refresh(token_pair.refresh_token, cache, repo, SECRET_KEY)

    claims = jwt_module.decode_token(new_access, "access", SECRET_KEY)
    assert claims.rol == "admin"


@pytest.mark.asyncio
async def test_refresh_token_revocado_401_token_revoked():
    """RF-013 — refresh revocado (logout) no emite un nuevo access."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )
    await logout(token_pair.refresh_token, cache, SECRET_KEY)

    with pytest.raises(ProblemDetailError) as exc_info:
        await refresh(token_pair.refresh_token, cache, repo, SECRET_KEY)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-revoked"


@pytest.mark.asyncio
async def test_refresh_token_expirado_401_token_expired():
    """RF-013 — refresh con `exp` vencido → 401 `token-expired`.

    `exp` fijado manualmente en el pasado (mismo patrón que
    `test_jwt_tokens.py::test_decode_token_expirado_lanza_token_expired_error`) —
    sin `time.sleep`, sin mockear `datetime`.
    """
    import jwt as pyjwt
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-1",
        "jti": "jti-x",
        "type": "refresh",
        "iat": now - timedelta(days=10),
        "exp": now - timedelta(days=3),
    }
    expired_refresh = pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")
    cache = _FakeCache()
    repo = _FakeUserRepository([_make_user()])

    with pytest.raises(ProblemDetailError) as exc_info:
        await refresh(expired_refresh, cache, repo, SECRET_KEY)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-expired"


@pytest.mark.asyncio
async def test_logout_revoca_el_refresh_token():
    """RF-010 — logout revoca el refresh, ya no sirve para `/auth/refresh`."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )
    claims = jwt_module.decode_token(token_pair.refresh_token, "refresh", SECRET_KEY)

    await logout(token_pair.refresh_token, cache, SECRET_KEY)

    assert await cache.get(f"refresh:{claims.jti}") is None


@pytest.mark.asyncio
async def test_logout_es_idempotente():
    """RF-010 — invocar logout dos veces con el mismo refresh no falla."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    token_pair = await login(
        user.email, "Correcto123!", "10.0.0.1", repo, cache, SECRET_KEY
    )

    await logout(token_pair.refresh_token, cache, SECRET_KEY)
    await logout(token_pair.refresh_token, cache, SECRET_KEY)  # no debe lanzar


@pytest.mark.asyncio
async def test_logout_con_token_invalido_no_lanza():
    """Idempotencia también ante un refresh ya inválido/malformado — no hay nada
    que revocar, no es un error del llamador."""
    cache = _FakeCache()

    await logout("token-basura-no-es-jwt", cache, SECRET_KEY)  # no debe lanzar
