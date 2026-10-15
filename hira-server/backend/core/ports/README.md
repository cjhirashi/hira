# core/ports

Interfaces abstractas (`typing.Protocol`) del patrón Hexagonal (`SRV-ADR-017`).
`services/` importa únicamente de aquí — nunca de `adapters/` directamente.

Puertos del Walking Skeleton (`AC-SRV-01`):

- `database_port.py` — `DatabasePort.ping()`.
- `cache_port.py` — `CachePort.ping()` (*liveness*) + `get`/`set`/`incr`/`expire`/
  `delete` (ampliado en `SRV-002-auth-rbac`, T-010/T-011 — cache real, no solo
  *liveness*; `RF-006, RF-007, RF-010, RF-011, RF-013, RF-014`).
- `notification_port.py` — `NotificationPort.ping()` / `.connect()`. `send()` queda
  explícitamente fuera de alcance de este sprint (`plan.md §7`) — sin consumidor real
  todavía.

Puertos de `SRV-002-auth-rbac`:

- `user_repository_port.py` — `UserRepositoryPort` (`get_by_email`, `get_by_id`,
  `update_role`) + `UserRecord` (dataclass). Repositorio de dominio de usuarios,
  distinto de `DatabasePort` (*liveness*-only, sin tocar su contrato) — decisión
  registrada en `plan.md §2`/Registro de decisiones (T-009). Sin test propio,
  igual que `database_port.py`.

Implementaciones concretas (`adapters/db/postgresql_adapter.py`,
`adapters/cache/redis_adapter.py`, `adapters/mqtt/mosquitto_adapter.py`,
`adapters/db/user_repository_adapter.py`) pendientes de batches posteriores de
`tasks.md` (T-019/T-020, T-022 para el Walking Skeleton; T-024/T-025 para
`UserRepositoryPort`).

Puertos de `SRV-003-bacnet-adapter`:

- `bacnet_transport_port.py` — `BacnetTransportPort` (`who_is`,
  `read_device_objects`) + `BacnetDeviceAnnouncement`/`BacnetObjectReading`
  (dataclasses) + `BacnetReadTimeoutError`. Transporte BACnet/IP — ningún tipo
  de `BAC0`/`bacpypes3` cruza a `services/` (`plan.md §2`, Registro de
  decisiones). Sin test propio.
- `device_repository_port.py` — `DeviceRepositoryPort` (`upsert_device`,
  `list_devices`, `get_device`, `upsert_candidate`,
  `list_candidates_for_device`) + `DeviceRecord`/`DeviceCandidateRecord`
  (dataclasses). Repositorio de dominio de dispositivos/candidatos, distinto de
  `DatabasePort` y de `UserRepositoryPort` — mismo criterio ya registrado en
  `SRV-002-auth-rbac/plan.md`. Sin test propio.

Implementaciones concretas de `SRV-003-bacnet-adapter`
(`adapters/bacnet/bac0_adapter.py::BAC0Adapter`, `adapters/db/
device_repository_adapter.py::PostgreSQLDeviceRepository`) fuera de alcance de
este batch (T-013..T-016 de `tasks.md`).

Puerto de `SRV-005-mqtt-scanning`:

- `mqtt_scan_transport_port.py` — `MqttScanTransportPort` (un único método,
  `listen(topic_pattern, window_seconds) -> list[MqttTopicMessage]` — MQTT es
  push-based, sin operación de "leer" análoga a BACnet/Modbus) +
  `MqttTopicMessage` (dataclass) + `MqttInvalidTopicPatternError` (excepción
  de dominio, RF-004, mismo criterio que `BacnetReadTimeoutError` — a
  diferencia de `ModbusReadFailure`, que es un valor de retorno). Sin test
  propio, igual que `bacnet_transport_port.py`/`device_repository_port.py`.
  Implementación concreta: `adapters/mqtt/mqtt_scan_adapter.py::
  MqttScanAdapter` (`paho-mqtt` real, T-009/T-010) — archivo **separado** de
  `adapters/mqtt/mosquitto_adapter.py` (`NotificationPort`, ciclo de vida de
  conexión distinto, ver `SRV-005-mqtt-scanning/plan.md §1` Registro de
  decisiones).

Puertos de `SRV-006-simuladores` — 3 puertos **nuevos** (no son ampliaciones
de los puertos de transporte existentes — ciclos de vida y roles incompatibles,
`plan.md §2` Registro de decisiones: cliente efímero de solo-lectura vs.
servidor/publicador persistente hasta `DELETE`):

- `bacnet_simulator_port.py` — `BacnetSimulatorPort` (2 métodos:
  `start(device_instance, objects) -> str` arranca una instancia BACnet/IP
  real que responde a Who-Is; `stop(token)` la detiene liberando el socket
  UDP) + `BacnetSimulatedObjectSpec` (dataclass — `object_type`, `object_instance`,
  `present_value: str`). El token opaco retornado por `start()` es la única
  referencia a la instancia en ejecución que cruza a `services/` (el tipo
  concreto de `BAC0.lite()` no cruza nunca — `SRV-ADR-017`). Sin test
  propio. Implementación real: `adapters/bacnet/bacnet_simulator_adapter.py::
  BacnetSimulatorAdapter` (T-021).

- `modbus_simulator_port.py` — `ModbusSimulatorPort` (2 métodos:
  `start(host, port, unit_id, registers) -> str` arranca un servidor Modbus
  TCP real; `stop(token)` lo detiene) + `ModbusSimulatedRegisterSpec`
  (dataclass — reutiliza `ModbusRegisterType` de `modbus_transport_port.py`,
  `SRV-004`, sin duplicarlo). Sin test propio. Implementación real:
  `adapters/modbus/modbus_simulator_adapter.py::ModbusSimulatorAdapter` (T-023).

- `mqtt_publisher_port.py` — `MqttPublisherPort` (2 métodos:
  `start(topic, payload, interval_seconds) -> str` arranca un publicador
  periódico; `stop(token)` lo detiene) + `MqttInvalidPublishError` (excepción
  de dominio, RF-014 — mismo criterio que `MqttInvalidTopicPatternError`,
  `SRV-005`: envuelve el `ValueError` síncrono de `paho-mqtt`, sin exponer
  la excepción cruda). Sin test propio. Implementación real:
  `adapters/mqtt/mqtt_publisher_adapter.py::MqttPublisherAdapter` (T-025).

`device_repository_port.py` **ampliado** en `SRV-006-simuladores` (T-006):
- Método nuevo: `get_device_by_address(protocol, address) -> DeviceRecord | None`
  — lectura puntual por el índice único `(protocol, address)` ya existente
  (`SRV-003`); usado como "find-or-reject" antes de cualquier `upsert_device`
  para rechazar con 409 sin escribir nada (RF-006/RF-007).
- `upsert_device` — contrato sin cambio de firma; docstring ampliado con la
  garantía RF-008: "una vez que una fila tiene `is_simulator=true`, ninguna
  llamada posterior con `is_simulator=false` la revierte".
  Implementación en `adapters/db/device_repository_adapter.py::
  PostgreSQLDeviceRepository` (T-019): `ON CONFLICT DO UPDATE` ahora fija
  `is_simulator = devices.is_simulator OR excluded.is_simulator`.
