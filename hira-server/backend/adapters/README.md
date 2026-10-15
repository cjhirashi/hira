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

- `modbus/` — `pymodbus_adapter.py::PymodbusAdapter` implementa
  `ModbusTransportPort` (`pymodbus` real, ver su propio README).

`get_modbus_transport_port()` (`SRV-004-modbus-adapter`) es una 7ª función de
`factory.py`, mismo patrón: nació (T-008) con `_PlaceholderModbusTransport`
(`read_range` siempre retorna `count` `ModbusReadFailure`, sin `pymodbus`
real). T-009/T-010 reemplazó el cuerpo con `adapters/modbus/
pymodbus_adapter.py::PymodbusAdapter` real (`_PlaceholderModbusTransport`
retirado, dead code tras el reemplazo — ningún test la importaba
directamente) — ninguna firma cambia, `routers/devices.py` no se tocó en
este batch.

- `mqtt/mqtt_scan_adapter.py::MqttScanAdapter` implementa
  `MqttScanTransportPort` (`paho-mqtt` real, archivo **separado** de
  `mosquitto_adapter.py` — ver su propio README).

`get_mqtt_scan_transport_port()` (`SRV-005-mqtt-scanning`) es una 8ª función
de `factory.py`, mismo patrón: nació (T-008) con `_PlaceholderMqttScanTransport`
(`listen()` siempre retorna `[]`, sin `paho-mqtt` real). T-010 reemplazó el
cuerpo con `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter` real
(`_PlaceholderMqttScanTransport` retirado, dead code tras el reemplazo —
ningún test lo importaba directamente) — ninguna firma cambia,
`routers/devices.py` no se tocó en este batch. Función **independiente** de
`get_notification_port()` (`MosquittoAdapter`): mismo broker físico, puertos
de dominio distintos con ciclos de vida de conexión incompatibles
(`SRV-005-mqtt-scanning/plan.md §1`, Registro de decisiones).

`get_bacnet_simulator_port()`/`get_modbus_simulator_port()`/
`get_mqtt_publisher_port()` (`SRV-006-simuladores`, T-017/T-021/T-023/T-025)
son la 9ª, 10ª y 11ª función de `factory.py` — **total 11 funciones** —, mismo
patrón de placeholder → reemplazo:
- `get_bacnet_simulator_port()` — nació (T-017) con
  `_PlaceholderBacnetSimulator`; T-021 reemplazó el cuerpo con
  `adapters/bacnet/bacnet_simulator_adapter.py::BacnetSimulatorAdapter`
  (`ip=settings.bacnet_ip`, `port_range_start=settings.bacnet_simulator_port_range_start`
  — rango de puertos propio para no colisionar con el cliente de escaneo).
- `get_modbus_simulator_port()` — nació (T-017) con
  `_PlaceholderModbusSimulator`; T-023 reemplazó el cuerpo con
  `adapters/modbus/modbus_simulator_adapter.py::ModbusSimulatorAdapter`
  (sin estado de `Settings`: `host`/`port` llegan por parámetro en cada
  `start()`).
- `get_mqtt_publisher_port()` — nació (T-017) con `_PlaceholderMqttPublisher`;
  T-025 reemplazó el cuerpo con `adapters/mqtt/mqtt_publisher_adapter.py::
  MqttPublisherAdapter` (mismas credenciales `mqtt_user`/`mqtt_password` que
  `get_notification_port()` y `get_mqtt_scan_transport_port()`, función
  **independiente** de ambas — ciclo de vida de conexión distinto: uno por
  simulador, hasta `DELETE`). Los 3 placeholders retirados (dead code tras el
  reemplazo), la **firma no cambió**, `routers/simulators.py` no se tocó en
  esos batches.
