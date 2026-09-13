"""`adapters/factory.py` — único punto de selección de implementaciones concretas
de `core/ports/` (`SRV-ADR-017`, regla de oro: `services/` y `routers/` nunca
instancian un adaptador directamente).

Estado de este sprint (`tasks.md` T-015, antes de T-019/T-020): los adaptadores
reales de PostgreSQL/Redis/Mosquitto todavía no existen — requieren contenedores
levantados (T-016..T-018) y llegan en T-020. Este factory devuelve implementaciones
**in-memory** mínimas, coherentes con los `Protocol` de `core/ports/`, que siempre
responden `ok` — permiten que `GET /health` sea extremo-a-extremo testeable por HTTP
sin infraestructura real todavía.

T-020 reemplaza el **cuerpo** de `get_database_port`/`get_cache_port`/
`get_notification_port` para instanciar `PostgreSQLAdapter`/`RedisAdapter`/
`MosquittoAdapter` reales — la firma no cambia, así que `routers/monitor.py` no se
toca en ese batch. Ver nota de decisión en `tasks.md` T-015.
"""
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.notification_port import NotificationPort


class _InMemoryDatabasePort:
    """Placeholder coherente con `DatabasePort` — reemplazado por T-020."""

    async def ping(self) -> bool:
        return True


class _InMemoryCachePort:
    """Placeholder coherente con `CachePort` — reemplazado por T-020."""

    async def ping(self) -> bool:
        return True


class _InMemoryNotificationPort:
    """Placeholder coherente con `NotificationPort` — reemplazado por T-020."""

    async def ping(self) -> bool:
        return True

    async def connect(self) -> None:
        return None


def get_database_port() -> DatabasePort:
    """Único punto de selección de la implementación de `DatabasePort` (RF-002)."""
    return _InMemoryDatabasePort()


def get_cache_port() -> CachePort:
    """Único punto de selección de la implementación de `CachePort` (RF-002)."""
    return _InMemoryCachePort()


def get_notification_port() -> NotificationPort:
    """Único punto de selección de la implementación de `NotificationPort` (RF-002)."""
    return _InMemoryNotificationPort()
