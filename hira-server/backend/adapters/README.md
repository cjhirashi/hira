# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `SRV-ADR-017`).
`factory.py` es el **único** punto de selección de la implementación concreta —
`services/` y `routers/` nunca instancian un adaptador directamente. Un solo perfil
de despliegue, sin `HIRA_DEPLOY_MODE` (`E-ADR-001`).

- `factory.py` — nació en T-015 con placeholders **in-memory** (siempre `ok`),
  coherentes con los `Protocol` de `core/ports/`. T-019/T-020 reemplazó el
  **cuerpo** de sus 3 funciones para instanciar los adaptadores reales de abajo
  (singleton perezoso por proceso); la firma no cambió, `routers/monitor.py` no
  se tocó en ese batch. `get_user_repository_port()` (`SRV-002-auth-rbac`,
  T-017/T-018) es una 4ª función, con el mismo patrón: nace con
  `_InMemoryUserRepository` (vacío por diseño, sin CRUD de usuarios en este
  sprint) — `adapters/db/user_repository_adapter.py::PostgreSQLUserRepository`
  (T-024/T-025, fuera de alcance) reemplaza su cuerpo sin cambiar la firma.
- `db/` — `postgresql_adapter.py` implementa `DatabasePort` (PostgreSQL/TimescaleDB,
  SQLAlchemy 2.x async + `asyncpg`, `SELECT 1`).
- `cache/` — `redis_adapter.py` implementa `CachePort` (`redis.asyncio`, `PING`).
- `mqtt/` — `mosquitto_adapter.py` implementa `NotificationPort` (`paho-mqtt`,
  backoff fijo 1s/2s/4s sin loop ciego en `connect()` — RF-008).

Los tres adaptadores concretos de arriba están verificados con
`tests/integration/test_adapters.py` y `tests/integration/test_mqtt_security.py`
contra los contenedores reales del compose (`tasks.md` T-019..T-023).

- `bacnet/` — `bac0_adapter.py::BAC0Adapter` implementa `BacnetTransportPort`
  (`BAC0`/`bacpypes3` real, ver su propio README).

`get_bacnet_transport_port()`/`get_device_repository_port()`
(`SRV-003-bacnet-adapter`) son una 5ª y 6ª función de `factory.py`, mismo
patrón: nacieron (T-008/T-009) con `_PlaceholderBacnetTransport` (`who_is`
siempre `[]`, sin BAC0 real) y `_InMemoryDeviceRepository` (CRUD in-memory
completo del contrato de `DeviceRepositoryPort`, único por `(protocol,
address)`/`(device_id, object_type, object_instance)`). T-013/T-014 reemplazó
el cuerpo de `get_bacnet_transport_port()` con `adapters/bacnet/
bac0_adapter.py::BAC0Adapter` real (`_PlaceholderBacnetTransport` retirado).
`adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository`
(T-015/T-016, fuera de alcance de este batch) reemplaza el cuerpo de
`get_device_repository_port()` — ninguna firma cambia.
