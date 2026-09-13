"""`services/rbac_service.py` — coordinación de resolución de permisos (`plan.md
§2`). Implementa **RF-006, RF-007**.

Solo importa de `core/ports/` (`UserRepositoryPort`, `CachePort`) y
`core/errors.py` — nunca de `adapters/` ni de FastAPI (`SRV-ADR-017`).
"""
import json
from dataclasses import dataclass

from core.errors import ProblemDetailError
from core.ports.cache_port import CachePort
from core.ports.user_repository_port import UserRepositoryPort

RBAC_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 días — mismo TTL que el refresh token

_ERRORS_BASE_URL = "https://hira.dev/errors"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identidad + permisos resueltos de un usuario autenticado (RF-006, RF-007)."""

    user_id: str
    rol: str
    scope: str
    project_id: str | None
    activo: bool


def _rbac_cache_key(user_id: str) -> str:
    return f"rbac:{user_id}"


def _token_invalid_error() -> ProblemDetailError:
    """RF-007 — usuario no encontrado o desactivado: revocación efectiva."""
    return ProblemDetailError(
        status=401,
        type_=f"{_ERRORS_BASE_URL}/token-invalid",
        title="Token inválido",
        detail="El usuario asociado a este token no existe o está desactivado.",
    )


async def resolve_permissions(
    user_id: str, users_repo: UserRepositoryPort, cache: CachePort
) -> AuthenticatedUser:
    """RF-006, RF-007 — resuelve `rol`/`scope`/`project_id` vigentes de `user_id`.

    *Cache-hit* (`rbac:{user_id}` en `cache`): deserializa y retorna **sin tocar**
    `users_repo` — es exactamente lo que RF-007 exige ("no consulta BD salvo
    cache-miss"). *Cache-miss*: consulta `users_repo.get_by_id`, construye
    `AuthenticatedUser` y repuebla el cache con TTL de 7 días. Usuario no
    encontrado o `activo=False` → `ProblemDetailError(401, "token-invalid")`.
    """
    cache_key = _rbac_cache_key(user_id)
    cached_raw = await cache.get(cache_key)
    if cached_raw is not None:
        cached = json.loads(cached_raw)
        return AuthenticatedUser(
            user_id=user_id,
            rol=cached["rol"],
            scope=cached["scope"],
            project_id=cached["project_id"],
            activo=cached["activo"],
        )

    user = await users_repo.get_by_id(user_id)
    if user is None or not user.activo:
        raise _token_invalid_error()

    authenticated_user = AuthenticatedUser(
        user_id=user.id,
        rol=user.rol,
        scope=user.scope,
        project_id=user.project_id,
        activo=user.activo,
    )
    await cache.set(
        cache_key,
        json.dumps(
            {
                "rol": authenticated_user.rol,
                "scope": authenticated_user.scope,
                "project_id": authenticated_user.project_id,
                "activo": authenticated_user.activo,
            }
        ),
        ttl_seconds=RBAC_CACHE_TTL_SECONDS,
    )
    return authenticated_user


async def invalidate_permissions_cache(user_id: str, cache: CachePort) -> None:
    """RF-006 — `DEL rbac:{user_id}`."""
    await cache.delete(_rbac_cache_key(user_id))


async def update_user_role(
    user_id: str, new_role: str, users_repo: UserRepositoryPort, cache: CachePort
) -> None:
    """RF-006 — actualiza el rol en `users_repo` y **luego** invalida el cache de
    permisos, en ese orden fijo. Si `update_role` lanza, la caché no se toca —
    no hay confirmación de una modificación que no ocurrió."""
    await users_repo.update_role(user_id, new_role)
    await invalidate_permissions_cache(user_id, cache)
