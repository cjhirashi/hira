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

`get_bacnet_transport_port()`/`get_device_repository_port()`
(`SRV-003-bacnet-adapter`, `tasks.md` T-008/T-009, `plan.md §2`/§6 paso 6):
nacen aquí con placeholders in-memory triviales (`_PlaceholderBacnetTransport`,
sin BAC0 real; `_InMemoryDeviceRepository`, sin Postgres real) — mismo patrón
exacto de las funciones de arriba. `_PlaceholderBacnetTransport.who_is` siempre
retorna `[]` (sin hardware BACnet real en este entorno, el escaneo responde 200
con lista vacía, RF-008); `read_device_objects` no se invoca nunca en la
práctica mientras `who_is` no anuncie nada, pero retorna `[]` por completitud
del contrato. `adapters/bacnet/bac0_adapter.py::BAC0Adapter` (T-013/T-014,
fuera de alcance de este batch) reemplaza el **cuerpo** de
`get_bacnet_transport_port()`; `adapters/db/device_repository_adapter.py::
PostgreSQLDeviceRepository` (T-015/T-016, fuera de alcance) reemplaza el
**cuerpo** de `get_device_repository_port()` — ninguna firma cambia,
`routers/devices.py` no se toca en esos batches.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.postgresql_adapter import PostgreSQLAdapter
from adapters.db.user_repository_adapter import PostgreSQLUserRepository
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.config import Settings
from core.ports.bacnet_transport_port import (
    BacnetDeviceAnnouncement,
    BacnetObjectReading,
    BacnetTransportPort,
)
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.device_repository_port import (
    DeviceCandidateRecord,
    DeviceRecord,
    DeviceRepositoryPort,
)
from core.ports.notification_port import NotificationPort
from core.ports.user_repository_port import UserRepositoryPort

_database_port: DatabasePort | None = None
_cache_port: CachePort | None = None
_notification_port: NotificationPort | None = None
_user_repository_port: UserRepositoryPort | None = None
_bacnet_transport_port: BacnetTransportPort | None = None
_device_repository_port: DeviceRepositoryPort | None = None


class _PlaceholderBacnetTransport:
    """`BacnetTransportPort` in-memory — sin hardware/BAC0 real todavía
    (`SRV-003-bacnet-adapter`, T-008/T-009). Reemplazada por
    `adapters/bacnet/bac0_adapter.py::BAC0Adapter` en T-013/T-014."""

    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        return []

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        return []


@dataclass
class _InMemoryDeviceRepository:
    """`DeviceRepositoryPort` in-memory — sin Postgres real todavía
    (`SRV-003-bacnet-adapter`, T-008/T-009). Reemplazada por
    `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository` en
    T-015/T-016. Único por `(protocol, address)` (devices) y por
    `(device_id, object_type, object_instance)` (candidatos), mismo criterio
    del modelo de datos real (`plan.md §3`)."""

    _devices_by_key: dict[tuple[str, str], DeviceRecord] = field(default_factory=dict)
    _candidates_by_key: dict[tuple[str, str, int], DeviceCandidateRecord] = field(
        default_factory=dict
    )

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        key = (protocol, address)
        now = datetime.now(timezone.utc)
        existing = self._devices_by_key.get(key)
        record = DeviceRecord(
            id=existing.id if existing else str(uuid4()),
            name=name,
            protocol=protocol,
            address=address,
            is_simulator=is_simulator,
            last_seen_at=now,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._devices_by_key[key] = record
        return record

    async def list_devices(self) -> list[DeviceRecord]:
        return list(self._devices_by_key.values())

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        for record in self._devices_by_key.values():
            if record.id == device_id:
                return record
        return None

    async def upsert_candidate(
        self,
        *,
        device_id: str,
        object_type: str,
        object_instance: int,
        object_name: str | None,
        present_value: str | None,
        units: str | None,
    ) -> DeviceCandidateRecord:
        key = (device_id, object_type, object_instance)
        now = datetime.now(timezone.utc)
        existing = self._candidates_by_key.get(key)
        record = DeviceCandidateRecord(
            id=existing.id if existing else str(uuid4()),
            device_id=device_id,
            object_type=object_type,
            object_instance=object_instance,
            object_name=object_name,
            present_value=present_value,
            units=units,
            discovered_at=existing.discovered_at if existing else now,
            updated_at=now,
        )
        self._candidates_by_key[key] = record
        return record

    async def list_candidates_for_device(
        self, device_id: str
    ) -> list[DeviceCandidateRecord]:
        return [
            record
            for record in self._candidates_by_key.values()
            if record.device_id == device_id
        ]


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


def get_bacnet_transport_port() -> BacnetTransportPort:
    """Único punto de selección de la implementación de `BacnetTransportPort`
    (`SRV-003-bacnet-adapter`, RF-001, RF-002, RF-006, RF-010)."""
    global _bacnet_transport_port
    if _bacnet_transport_port is None:
        _bacnet_transport_port = _PlaceholderBacnetTransport()
    return _bacnet_transport_port


def get_device_repository_port() -> DeviceRepositoryPort:
    """Único punto de selección de la implementación de `DeviceRepositoryPort`
    (`SRV-003-bacnet-adapter`, RF-002, RF-004, RF-005, RF-009)."""
    global _device_repository_port
    if _device_repository_port is None:
        _device_repository_port = _InMemoryDeviceRepository()
    return _device_repository_port
