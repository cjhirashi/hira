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

`get_user_repository_port()` (`SRV-002-auth-rbac`): nació en T-017/T-018 con un
placeholder in-memory (`_InMemoryUserRepository`, mismo patrón exacto que las 3
funciones de arriba en T-015) porque `PostgreSQLUserRepository` no existía
todavía. T-024/T-025 reemplaza el **cuerpo** de esta función para instanciar el
adaptador real (`adapters/db/user_repository_adapter.py::PostgreSQLUserRepository`)
— la **firma no cambia**, así que `routers/auth.py`/`core/middleware.py` no se
tocan en este batch. El placeholder in-memory se retira de este archivo (dead
code tras el reemplazo — `tests/test_auth_router.py` nunca lo importó, usa su
propio `_FakeUserRepository` local vía `app.dependency_overrides`/`monkeypatch`).
"""
from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.postgresql_adapter import PostgreSQLAdapter
from adapters.db.user_repository_adapter import PostgreSQLUserRepository
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.config import Settings
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.notification_port import NotificationPort
from core.ports.user_repository_port import UserRepositoryPort

_database_port: DatabasePort | None = None
_cache_port: CachePort | None = None
_notification_port: NotificationPort | None = None
_user_repository_port: UserRepositoryPort | None = None


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
        _user_repository_port = PostgreSQLUserRepository(Settings().database_url)
    return _user_repository_port
