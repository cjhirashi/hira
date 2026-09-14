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
nacieron con placeholders in-memory triviales (`_PlaceholderBacnetTransport`,
sin BAC0 real; `_InMemoryDeviceRepository`, sin Postgres real) — mismo patrón
exacto de las funciones de arriba. T-013/T-014 reemplazó el **cuerpo** de
`get_bacnet_transport_port()` con `adapters/bacnet/bac0_adapter.py::
BAC0Adapter` real; T-015/T-016 reemplaza el **cuerpo** de
`get_device_repository_port()` con `adapters/db/device_repository_adapter.py::
PostgreSQLDeviceRepository` real — ambos placeholders retirados (dead code tras
el reemplazo, ningún test los importaba directamente). Ninguna firma cambió,
`routers/devices.py` no se toca en estos batches.

`get_modbus_transport_port()` (`SRV-004-modbus-adapter`, `tasks.md` T-008,
`plan.md §2`/§6 paso 5): nació con un placeholder in-memory trivial
(`_PlaceholderModbusTransport`, `read_range` siempre retorna `count`
`ModbusReadFailure` — sin `pymodbus` real, sin importarlo) — mismo patrón
exacto que `get_bacnet_transport_port()` en su batch de nacimiento. T-010
reemplaza el **cuerpo** con `adapters/modbus/pymodbus_adapter.py::
PymodbusAdapter` real (`_PlaceholderModbusTransport` retirado, dead code tras
el reemplazo — ningún test la importaba directamente) — la **firma no
cambia**, `routers/devices.py` no se toca en este batch.
"""
from adapters.bacnet.bac0_adapter import BAC0Adapter
from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.device_repository_adapter import PostgreSQLDeviceRepository
from adapters.db.postgresql_adapter import PostgreSQLAdapter
from adapters.db.user_repository_adapter import PostgreSQLUserRepository
from adapters.modbus.pymodbus_adapter import PymodbusAdapter
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.config import Settings
from core.ports.bacnet_transport_port import BacnetTransportPort
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.device_repository_port import DeviceRepositoryPort
from core.ports.modbus_transport_port import ModbusTransportPort
from core.ports.notification_port import NotificationPort
from core.ports.user_repository_port import UserRepositoryPort

_database_port: DatabasePort | None = None
_cache_port: CachePort | None = None
_notification_port: NotificationPort | None = None
_user_repository_port: UserRepositoryPort | None = None
_bacnet_transport_port: BacnetTransportPort | None = None
_device_repository_port: DeviceRepositoryPort | None = None
_modbus_transport_port: ModbusTransportPort | None = None


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
    (`SRV-003-bacnet-adapter`, RF-001, RF-002, RF-006, RF-010). `ip`/`port`
    de `Settings` opcionales — `None` deja que `BAC0.lite()` autodetecte la
    interfaz local (`plan.md §1`, Registro de decisiones)."""
    global _bacnet_transport_port
    if _bacnet_transport_port is None:
        settings = Settings()
        _bacnet_transport_port = BAC0Adapter(
            ip=settings.bacnet_ip, port=settings.bacnet_port
        )
    return _bacnet_transport_port


def get_device_repository_port() -> DeviceRepositoryPort:
    """Único punto de selección de la implementación de `DeviceRepositoryPort`
    (`SRV-003-bacnet-adapter`, RF-002, RF-004, RF-005, RF-009)."""
    global _device_repository_port
    if _device_repository_port is None:
        _device_repository_port = PostgreSQLDeviceRepository(Settings().database_url)
    return _device_repository_port


def get_modbus_transport_port() -> ModbusTransportPort:
    """Único punto de selección de la implementación de `ModbusTransportPort`
    (`SRV-004-modbus-adapter`, RF-001, RF-002, RF-005, RF-008). Nació con
    `_PlaceholderModbusTransport` (sin `pymodbus` real, T-008); T-010
    reemplaza el cuerpo con `adapters/modbus/pymodbus_adapter.py::
    PymodbusAdapter` real — sin estado de conexión persistente entre
    llamadas (cada `read_range` abre su propia conexión TCP, `plan.md §1`),
    por lo que no requiere `Settings` para construirse."""
    global _modbus_transport_port
    if _modbus_transport_port is None:
        _modbus_transport_port = PymodbusAdapter()
    return _modbus_transport_port
