"""`services/rbac_service.py` — coordinación de resolución de permisos (`plan.md
§2`). Implementa **RF-006, RF-007**.

Solo importa de `core/ports/` (`UserRepositoryPort`, `CachePort`) y
`core/errors.py` — nunca de `adapters/` ni de FastAPI (`SRV-ADR-017`).

Ampliado en T-034/T-035 (`plan.md §10`, resolución de RNF-001 — Directiva de
Pausa: el round-trip real a Redis por request en *cache-hit* costaba ~27-30ms
a 100 concurrentes, aditivo al piso de `BaseHTTPMiddleware`, T-038): añade
`LocalPermissionsCache`, una caché en memoria del proceso (sin I/O, `dict` +
TTL) delante de Redis — es la ruta caliente que resuelve RNF-001. **No es un
puerto** (Registro de decisiones de `plan.md`): no habla con ningún sistema
externo, es una estructura de datos interna. La invalidación cruzada entre
procesos/réplicas se propaga por pub/sub de `CachePort` (*best-effort*, RF-006)
con la TTL local (30s) como cota máxima de obsolescencia si un mensaje se pierde.
"""
import json
import time as time_module
from collections.abc import Callable
from dataclasses import dataclass

from core.errors import ProblemDetailError
from core.ports.cache_port import CachePort
from core.ports.user_repository_port import UserRepositoryPort

RBAC_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 días — mismo TTL que el refresh token
LOCAL_CACHE_TTL_SECONDS = 30  # red de seguridad — no es el mecanismo principal
INVALIDATION_CHANNEL = "rbac:invalidations"

_ERRORS_BASE_URL = "https://hira.dev/errors"


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identidad + permisos resueltos de un usuario autenticado (RF-006, RF-007)."""

    user_id: str
    rol: str
    scope: str
    project_id: str | None
    activo: bool


class LocalPermissionsCache:
    """Caché en memoria del proceso, delante de Redis (RNF-001, `plan.md §10`).

    `dict[str, tuple[AuthenticatedUser, float]]` (valor + timestamp de
    expiración) con TTL por entrada (`LOCAL_CACHE_TTL_SECONDS` por defecto).
    Reloj inyectable (`clock`, por defecto `time.monotonic`) — permite a los
    tests simular el paso del tiempo sin `sleep` real. **No es un puerto**: sin
    I/O, no es una frontera de salida.
    """

    def __init__(self, clock: Callable[[], float] = time_module.monotonic) -> None:
        self._clock = clock
        self._store: dict[str, tuple[AuthenticatedUser, float]] = {}

    def get(self, user_id: str) -> AuthenticatedUser | None:
        """`None` si no existe o si ya expiró (y la purga en ese caso)."""
        entry = self._store.get(user_id)
        if entry is None:
            return None
        user, expires_at = entry
        if self._clock() >= expires_at:
            del self._store[user_id]
            return None
        return user

    def set(
        self,
        user_id: str,
        user: AuthenticatedUser,
        ttl_seconds: int = LOCAL_CACHE_TTL_SECONDS,
    ) -> None:
        self._store[user_id] = (user, self._clock() + ttl_seconds)

    def invalidate(self, user_id: str) -> None:
        """Idempotente — no falla si `user_id` no está en la caché."""
        self._store.pop(user_id, None)


# Singleton de módulo para el uso real en producción (`adapters/factory.py` no
# instancia esto — no es un puerto). `resolve_permissions`/etc. resuelven la
# referencia dinámicamente (sentinel `None`) para que los tests puedan
# monkeypatchear este nombre y simular 2+ "procesos" en el mismo test (`plan.md
# §5`) sin que el valor por defecto quede fijado al importar el módulo.
_default_local_cache = LocalPermissionsCache()


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
    user_id: str,
    users_repo: UserRepositoryPort,
    cache: CachePort,
    local_cache: LocalPermissionsCache | None = None,
) -> AuthenticatedUser:
    """RF-006, RF-007, RNF-001 — resuelve `rol`/`scope`/`project_id` vigentes de
    `user_id`.

    1) *Hit* en `local_cache` (memoria del proceso): retorna **sin ningún I/O**
       — es la ruta caliente que resuelve RNF-001.
    2) *Miss* local + *hit* en `cache` (Redis, `rbac:{user_id}`): deserializa,
       repuebla `local_cache`, retorna — sin tocar `users_repo` (RF-007: "no
       consulta BD salvo cache-miss", el nivel local es una capa adicional, no
       sustituye esa semántica).
    3) *Miss* en ambos niveles: consulta `users_repo.get_by_id`, repuebla
       **ambos** niveles, retorna.

    Usuario no encontrado o `activo=False` → `ProblemDetailError(401,
    "token-invalid")` (sin cachear en ningún nivel).
    """
    if local_cache is None:
        local_cache = _default_local_cache

    local_hit = local_cache.get(user_id)
    if local_hit is not None:
        return local_hit

    cache_key = _rbac_cache_key(user_id)
    cached_raw = await cache.get(cache_key)
    if cached_raw is not None:
        cached = json.loads(cached_raw)
        authenticated_user = AuthenticatedUser(
            user_id=user_id,
            rol=cached["rol"],
            scope=cached["scope"],
            project_id=cached["project_id"],
            activo=cached["activo"],
        )
        local_cache.set(user_id, authenticated_user)
        return authenticated_user

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
    local_cache.set(user_id, authenticated_user)
    return authenticated_user


async def invalidate_permissions_cache(
    user_id: str, cache: CachePort, local_cache: LocalPermissionsCache | None = None
) -> None:
    """RF-006 — `DEL rbac:{user_id}` + invalida la caché local **de este
    proceso** + publica en `INVALIDATION_CHANNEL` para que otros
    procesos/réplicas converjan vía `run_invalidation_subscriber` (*best-effort*,
    cota máxima de obsolescencia = `LOCAL_CACHE_TTL_SECONDS` si el mensaje se
    pierde)."""
    if local_cache is None:
        local_cache = _default_local_cache

    await cache.delete(_rbac_cache_key(user_id))
    local_cache.invalidate(user_id)
    await cache.publish(INVALIDATION_CHANNEL, user_id)


async def update_user_role(
    user_id: str,
    new_role: str,
    users_repo: UserRepositoryPort,
    cache: CachePort,
    local_cache: LocalPermissionsCache | None = None,
) -> None:
    """RF-006 — actualiza el rol en `users_repo` y **luego** invalida el cache de
    permisos (Redis + local + publica), en ese orden fijo. Si `update_role`
    lanza, la caché no se toca — no hay confirmación de una modificación que no
    ocurrió.

    **Matiz de semántica (RNF-001, `plan.md §10`/`spec.md` RF-006):** lo que
    ocurre "antes de confirmar la modificación" —invalidación de Redis + del
    `LocalPermissionsCache` del proceso que ejecuta la llamada— sigue siendo
    síncrono y atómico dentro de esta función. La convergencia de la caché en
    memoria de **otros** procesos/réplicas es *best-effort* vía pub/sub (typ.
    sub-segundo), sin garantía atómica cruzada — acotada por
    `LOCAL_CACHE_TTL_SECONDS` como cota máxima de obsolescencia.
    """
    if local_cache is None:
        local_cache = _default_local_cache

    await users_repo.update_role(user_id, new_role)
    await invalidate_permissions_cache(user_id, cache, local_cache=local_cache)


async def run_invalidation_subscriber(
    cache: CachePort, local_cache: LocalPermissionsCache | None = None
) -> None:
    """RNF-001 — consume `cache.subscribe(INVALIDATION_CHANNEL)` y propaga cada
    invalidación al `LocalPermissionsCache` de este proceso. Pensada para correr
    como tarea de fondo (`asyncio.create_task`) desde `main.py::lifespan`, uno
    por proceso backend (T-036/T-037).

    Bucle infinito — sale únicamente por `asyncio.CancelledError`, que **no se
    captura aquí a propósito**: debe propagarse para que quien la lanzó como
    tarea (`lifespan`) pueda cancelarla limpio en el *shutdown* sin que quede
    una tarea huérfana.
    """
    if local_cache is None:
        local_cache = _default_local_cache

    async for user_id in cache.subscribe(INVALIDATION_CHANNEL):
        local_cache.invalidate(user_id)
