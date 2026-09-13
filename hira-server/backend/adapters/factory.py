"""`adapters/factory.py` — único punto de selección de implementaciones concretas
de `core/ports/` (`SRV-ADR-017`, regla de oro: `services/` y `routers/` nunca
instancian un adaptador directamente).

Historial: nació en T-015 (router `/health`) con 3 placeholders in-memory,
porque los adaptadores reales de PostgreSQL/Redis/Mosquitto no existían todavía
(ver Directiva de Pausa 2026-09-13 en `plan.md §7`/`tasks.md` T-015). T-019/T-020
reemplaza el **cuerpo** de las 3 funciones para instanciar los adaptadores reales
(`PostgreSQLAdapter`/`RedisAdapter`/`MosquittoAdapter`) — la **firma no cambia**,
así que `routers/monitor.py` no se toca en este batch.

Cada puerto se cachea a nivel de módulo (patrón *singleton* perezoso): las 3
funciones se resuelven vía `fastapi.Depends` en cada request, y crear un `engine`
de SQLAlchemy o un cliente de Redis nuevo por request sería un desperdicio de
conexiones — se instancian una sola vez por proceso, igual que haría un `lifespan`
de FastAPI con un pool real.

`get_user_repository_port()` (`SRV-002-auth-rbac`, T-017/T-018, `plan.md §2`):
nace aquí con un placeholder **in-memory** (`_InMemoryUserRepository`), mismo
patrón exacto que las 3 funciones de arriba nacieron en T-015 — `routers/auth.py`
necesita el punto de inyección desde que existe, aunque no hay CRUD de usuarios
en este sprint (`spec.md §2`: la única vía de creación es el seed de T-026, fuera
de este alcance) — por eso el placeholder nace **vacío** (sin usuarios
precargados), a diferencia de los 3 placeholders de T-015 que sí "siempre
responden ok". `adapters/db/user_repository_adapter.py::PostgreSQLUserRepository`
(T-024/T-025, fuera de alcance) reemplaza el **cuerpo** de esta función — la
firma no cambia.
"""
from dataclasses import replace

from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.postgresql_adapter import PostgreSQLAdapter
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.config import Settings
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.notification_port import NotificationPort
from core.ports.user_repository_port import UserRecord, UserRepositoryPort

_database_port: DatabasePort | None = None
_cache_port: CachePort | None = None
_notification_port: NotificationPort | None = None
_user_repository_port: UserRepositoryPort | None = None


class _InMemoryUserRepository:
    """Placeholder coherente con `UserRepositoryPort` — vacío por diseño (sin
    CRUD de usuarios en este sprint, `spec.md §2`). Reemplazado por
    `PostgreSQLUserRepository` en T-024/T-025."""

    def __init__(self) -> None:
        self._by_id: dict[str, UserRecord] = {}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return next((u for u in self._by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        user = self._by_id.get(user_id)
        if user is not None:
            self._by_id[user_id] = replace(user, rol=new_role)


def get_database_port() -> DatabasePort:
    """Único punto de selección de la implementación de `DatabasePort` (RF-002)."""
    global _database_port
    if _database_port is None:
        _database_port = PostgreSQLAdapter(Settings().database_url)
    return _database_port


def get_cache_port() -> CachePort:
    """Único punto de selección de la implementación de `CachePort` (RF-002)."""
    global _cache_port
    if _cache_port is None:
        _cache_port = RedisAdapter(Settings().redis_url)
    return _cache_port


def get_notification_port() -> NotificationPort:
    """Único punto de selección de la implementación de `NotificationPort`
    (RF-002, RF-006, RF-008)."""
    global _notification_port
    if _notification_port is None:
        settings = Settings()
        _notification_port = MosquittoAdapter(
            host=settings.mqtt_broker_host,
            port=1883,
            user=settings.mqtt_user,
            password=settings.mqtt_password,
        )
    return _notification_port


def get_user_repository_port() -> UserRepositoryPort:
    """Único punto de selección de la implementación de `UserRepositoryPort`
    (`SRV-002-auth-rbac`, RF-001, RF-002, RF-006, RF-007, RF-012)."""
    global _user_repository_port
    if _user_repository_port is None:
        _user_repository_port = _InMemoryUserRepository()
    return _user_repository_port
