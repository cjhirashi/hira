"""`adapters/factory.py` — único punto de selección de implementaciones concretas
de `core/ports/` (`E-ADR-002`, regla de oro: `services/` y `routers/` nunca
instancian un adaptador directamente).

Historial: nació en T-015 (router `/health`) con 2 placeholders in-memory,
porque los adaptadores reales de PostgreSQL/Redis no existían todavía —
aplicando de forma **proactiva** la lección de la Directiva de Pausa de
`SRV-001` (`plan.md §7`): el router necesitaba el punto de inyección desde el
momento en que existió, sin esperar a los adaptadores reales. T-018/T-019
reemplaza el **cuerpo** de las 2 funciones para instanciar los adaptadores
reales (`PostgresAdapter`/`RedisAdapter`) — la **firma no cambia**, así que
`routers/monitor.py` no se toca en este batch.

Cada puerto se cachea a nivel de módulo (patrón *singleton* perezoso): las 2
funciones se resuelven vía `fastapi.Depends` en cada request, y crear un
`engine` de SQLAlchemy o un cliente de Redis nuevo por request sería un
desperdicio de conexiones — se instancian una sola vez por proceso.

A diferencia de `hira-server`: solo 2 funciones — sin
`get_notification_port()` (sin Mosquitto, `HUB-ADR-01`).

**Corrección post-revisión:** `get_cache_port()` pasaba solo `redis_url` a
`RedisAdapter` — el Redis del compose exige password (`--requirepass`) y
`Settings().redis_password` nunca se leía, dejando ese campo sin consumidor
real y produciendo `redis: error` en `/health` contra un Redis real y sano.
Ahora se combinan ambos campos de `Settings` explícitamente.
"""
from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.postgres_adapter import PostgresAdapter
from core.config import Settings
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort

_database_port: DatabasePort | None = None
_cache_port: CachePort | None = None


def get_database_port() -> DatabasePort:
    """Único punto de selección de la implementación de `DatabasePort` (RF-002)."""
    global _database_port
    if _database_port is None:
        _database_port = PostgresAdapter(Settings().database_url)
    return _database_port


def get_cache_port() -> CachePort:
    """Único punto de selección de la implementación de `CachePort` (RF-002)."""
    global _cache_port
    if _cache_port is None:
        settings = Settings()
        _cache_port = RedisAdapter(settings.redis_url, settings.redis_password)
    return _cache_port
