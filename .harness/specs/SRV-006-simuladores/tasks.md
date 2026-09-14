---
id: TASKS-SRV-006
tipo: tasks
feature: SRV-006-simuladores
estado: draft
actualizado: 2026-09-14
---

# TASKS-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT)

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-protocolos` (`.claude/agents/hira-protocolos.md`).

## Tareas

### Núcleo — identidad restart-safe del simulador BACnet
- [ ] T-001 — Ampliar `tests/test_bacnet_address.py`: `format_simulator_device_address`
      determinista (`str(device_instance)` exacto), rechaza `< 0` y
      `> 4194303` (debe fallar) (cubre RF-001, RF-007) [zona: test-núcleo]
- [ ] T-002 — Implementar `core/bacnet_address.py::format_simulator_device_address`
      (cubre RF-001, RF-007) [zona: núcleo]

### Estado en memoria — registro de simuladores en ejecución
- [ ] T-003 — Test `tests/test_simulator_registry_service.py`:
      `register`/`get`/`is_running`/`unregister`/`list_running` sobre el
      `dict`; el `Lock` serializa 2 corutinas reales con `asyncio.gather`
      (sin mocks); una instancia nueva siempre nace vacía (equivalente
      verificable de RF-013) (debe fallar) (cubre RF-010, RF-013)
      [zona: test-coordinación]
- [ ] T-004 — Implementar `services/simulator_registry_service.py`
      (`RunningSimulator`, `SimulatorRegistryService`,
      `get_simulator_registry`) (cubre RF-010, RF-013) [zona: coordinación]

### Puertos
- [ ] T-005 — Implementar `core/ports/bacnet_simulator_port.py`
      (`BacnetSimulatorPort`, `BacnetSimulatedObjectSpec`),
      `core/ports/modbus_simulator_port.py` (`ModbusSimulatorPort`,
      `ModbusSimulatedRegisterSpec`), `core/ports/mqtt_publisher_port.py`
      (`MqttPublisherPort`, `MqttInvalidPublishError`) — `Protocol`, sin
      test propio [zona: puertos]
- [ ] T-006 — Ampliar `core/ports/device_repository_port.py`:
      `get_device_by_address(protocol, address) -> DeviceRecord | None`
      añadido al `Protocol`; docstring de `upsert_device` ampliado con la
      garantía de RF-008 — sin test propio, es una interfaz (cubre RF-006,
      RF-007, RF-008) [zona: puertos]

### Coordinación — servicio de simuladores (arranque BACnet)
- [ ] T-007 — Test `tests/test_simulator_service.py` (camino BACnet):
      arranca, persiste device+candidatos, registra; RF-006 (dispositivo
      real → 409 antes de `transport.start`; ya corriendo → 409 antes de
      `transport.start`); RF-007 (reanudación: `existing.id` reutilizado,
      sin segundo `upsert_device` con `is_simulator` distinto); limpieza
      defensiva (`upsert_device` lanza → `transport.stop(token)` invocado
      antes de propagar) (debe fallar) (cubre RF-001, RF-006, RF-007,
      RNF-001) [zona: test-coordinación]
- [ ] T-008 — Implementar `services/simulator_service.py::start_bacnet_simulator`
      (cubre RF-001, RF-006, RF-007, RNF-001) [zona: coordinación]

### Coordinación — servicio de simuladores (arranque Modbus)
- [ ] T-009 — Ampliar `tests/test_simulator_service.py` (camino Modbus):
      mismos casos que T-007 sobre `start_modbus_simulator` (debe fallar)
      (cubre RF-002, RF-006, RF-007, RNF-001) [zona: test-coordinación]
- [ ] T-010 — Implementar `services/simulator_service.py::start_modbus_simulator`
      (cubre RF-002, RF-006, RF-007, RNF-001) [zona: coordinación]

### Coordinación — servicio de simuladores (arranque MQTT + validaciones)
- [ ] T-011 — Ampliar `tests/test_simulator_service.py` (camino MQTT):
      mismos casos que T-007/T-009 sobre `start_mqtt_simulator`; RF-014
      (doble de `transport.start` lanza `MqttInvalidPublishError` → 400,
      sin `upsert_device` invocado); RF-015 (`interval_seconds<=0` → 400,
      sin invocar `transport`/`device_repo`) (debe fallar) (cubre RF-003,
      RF-006, RF-007, RF-014, RF-015, RNF-001) [zona: test-coordinación]
- [ ] T-012 — Implementar `services/simulator_service.py::start_mqtt_simulator`
      (cubre RF-003, RF-006, RF-007, RF-014, RF-015, RNF-001)
      [zona: coordinación]

### Coordinación — detener simulador
- [ ] T-013 — Ampliar `tests/test_simulator_service.py` (`stop_simulator`):
      `device_id` en el registro → despacha al puerto correcto y
      desregistra, sin tocar `devices`/candidatos (inspección: no importa
      ningún método de borrado); `device_id` ausente → 404 (debe fallar)
      (cubre RF-009, RF-011, RF-012) [zona: test-coordinación]
- [ ] T-014 — Implementar `services/simulator_service.py::stop_simulator`
      (cubre RF-009, RF-011, RF-012) [zona: coordinación]

### Contrato — Contract-First
- [ ] T-015 — Ampliar `hira-server/docs/openapi.yaml` con los 5 paths
      (`POST /simulators/{bacnet,modbus,mqtt}`, `GET /simulators`,
      `DELETE /simulators/{device_id}`) y los 6 schemas nuevos
      (`BacnetSimulatedObjectIn`, `StartBacnetSimulatorRequest`,
      `ModbusRegisterValueIn`, `StartModbusSimulatorRequest`,
      `StartMqttSimulatorRequest`, `SimulatorOut`) — sin tocar los 13
      endpoints existentes (cubre RF-001, RF-002, RF-003, RF-004, RF-005,
      RF-006, RF-012, RF-014, RF-015) [zona: contrato]

### Adaptador de entrada — router
- [ ] T-016 — Test `tests/test_simulators_router.py` (`TestClient`,
      dobles vía `app.dependency_overrides`): contrato exacto de
      `openapi.yaml`, 201 con `SimulatorOut` (los 3 protocolos), 403 con
      Operador/Visor en `POST`/`DELETE`, 403 con Visor y 200 con
      Admin/Operador en `GET`, 409 (RF-006, ambas variantes), 404
      (RF-012), 400 (RF-014/RF-015, *shape* RFC 9457 exacto), 204 sin
      cuerpo en `DELETE` exitoso (debe fallar) (cubre RF-001, RF-002,
      RF-003, RF-004, RF-005, RF-006, RF-009, RF-010, RF-012, RF-014,
      RF-015) [zona: test-adaptador-entrada]
- [ ] T-017 — Implementar `routers/simulators.py` + `schemas/simulators.py`
      + `adapters/factory.py::get_bacnet_simulator_port()/
      get_modbus_simulator_port()/get_mqtt_publisher_port()` (nacen aquí
      con placeholders in-memory, mismo patrón ya aplicado 8 veces);
      `main.py` registra el router (cubre RF-001, RF-002, RF-003, RF-004,
      RF-005, RF-006, RF-009, RF-010, RF-012, RF-014, RF-015)
      [zona: adaptador-entrada]

### Adaptador de repositorio — Postgres real
- [ ] T-018 — Ampliar `tests/integration/test_device_repository_adapter.py`:
      `get_device_by_address` (existente vs. inexistente, distingue por
      `protocol`); `upsert_device` preserva `is_simulator=true` (fila ya
      simulador → segundo `upsert_device(..., is_simulator=False)` →
      sigue `true`) — contra Postgres real (debe fallar) (cubre RF-006,
      RF-007, RF-008) [zona: test-adaptadores]
- [ ] T-019 — Implementar `adapters/db/device_repository_adapter.py::
      PostgreSQLDeviceRepository.get_device_by_address` +
      `upsert_device` corregido (`OR` booleano en `ON CONFLICT DO
      UPDATE`) (cubre RF-006, RF-007, RF-008) [zona: adaptadores]

### Adaptador BACnet real — integración contra un cliente BACnet real
- [ ] T-020 — Test `tests/integration/test_bacnet_simulator_adapter.py`
      (requiere `BAC0` real, sin `BAC0Adapter`/mocks): `start(...)` → un
      cliente BACnet real recibe I-Am con el `device_instance` correcto y
      lee `presentValue` del objeto inicial; `stop(token)` libera el
      puerto UDP; 2 simuladores concurrentes conviven sin colisión de
      puerto (debe fallar) (cubre RF-001, RNF-001) [zona: test-adaptadores]
- [ ] T-021 — Implementar `adapters/bacnet/bacnet_simulator_adapter.py::
      BacnetSimulatorAdapter` (`BAC0.lite(deviceId=...)`) — reemplaza el
      **cuerpo** (no la firma) de `get_bacnet_simulator_port()`; añade
      `Settings.bacnet_simulator_port_range_start` (opcional, default
      `47900`) (cubre RF-001, RNF-001) [zona: adaptadores]

### Adaptador Modbus real — integración contra un cliente Modbus real
- [ ] T-022 — Test `tests/integration/test_modbus_simulator_adapter.py`
      (requiere `pymodbus` real, sin `PymodbusAdapter`/mocks): `start(...)`
      → un cliente Modbus real lee los registros cargados
      (holding/input → int, coil/discrete → bool); `stop(token)` cierra el
      servidor (debe fallar) (cubre RF-002, RNF-001) [zona: test-adaptadores]
- [ ] T-023 — Implementar `adapters/modbus/modbus_simulator_adapter.py::
      ModbusSimulatorAdapter` (`ModbusTcpServer` + `SimData`/`SimDevice`)
      — reemplaza el cuerpo de `get_modbus_simulator_port()` (cubre
      RF-002, RNF-001) [zona: adaptadores]

### Adaptador MQTT real — integración contra el Mosquitto real
- [ ] T-024 — Test `tests/integration/test_mqtt_publisher_adapter.py`
      (Mosquitto real del compose, un segundo cliente `paho-mqtt` como
      suscriptor): `start(...)` → el suscriptor recibe ≥ 3 mensajes en
      3.5s con `interval_seconds=1.0`; RF-014: topic con wildcard o vacío
      → `MqttInvalidPublishError` inmediato (< 1s); `stop(token)` detiene
      el bucle (debe fallar) (cubre RF-003, RF-014, RNF-001)
      [zona: test-adaptadores]
- [ ] T-025 — Implementar `adapters/mqtt/mqtt_publisher_adapter.py::
      MqttPublisherAdapter` (`paho-mqtt`, `CallbackAPIVersion.VERSION2`,
      archivo nuevo separado de `mosquitto_adapter.py`/
      `mqtt_scan_adapter.py`) — reemplaza el cuerpo de
      `get_mqtt_publisher_port()` (cubre RF-003, RF-014, RNF-001)
      [zona: adaptadores]

### Sistema — verificación e2e
- [ ] T-026 — Nuevo `tests/integration/test_simulators_e2e.py`
      (contenedores reales + clientes reales de cada protocolo):
      `POST /simulators/bacnet` → I-Am real confirmado → `GET /simulators`
      lo lista → `GET /devices` también (`is_simulator=true`) →
      `DELETE /simulators/{id}` → `GET /simulators` ya no lo lista,
      `GET /devices` sigue listándolo (RF-009); flujo abreviado para
      Modbus y MQTT; `POST /devices/scan/modbus` sobre la dirección de un
      simulador Modbus en ejecución confirma que `is_simulator` sigue
      `true` tras el escaneo (RF-008, evidencia e2e); RNF-001 medido con
      `GET /health`/`GET /devices` respondiendo con normalidad mientras
      hay simuladores en ejecución (cubre RF-001, RF-002, RF-003, RF-004,
      RF-005, RF-006, RF-007, RF-008, RF-009, RF-010, RF-012, RF-013,
      RF-014, RF-015, RNF-001) [zona: sistema-e2e]

### Documentación (`plan.md §8`) — puede correr en paralelo desde T-001
- [ ] T-027 — Actualizar `docs/hira-server/spec/modules/dispositivos-
      protocolos-puntos.md`: cerrar la nota de estado de implementación
      ya dejada por `SRV-003`/`004`/`005` para incluir simuladores de los
      3 protocolos [doc]

### Higiene de repo
- [ ] T-028 — Ampliar `adapters/bacnet/README.md` (añade
      `bacnet_simulator_adapter.py`), `adapters/modbus/README.md` (añade
      `modbus_simulator_adapter.py`), `adapters/mqtt/README.md` (añade
      `mqtt_publisher_adapter.py`), `adapters/README.md` (3 funciones
      nuevas de `factory.py`, 11 en total), `core/ports/README.md` (3
      puertos nuevos + ampliación de `device_repository_port.py`),
      `services/README.md` (`simulator_registry_service.py`,
      `simulator_service.py`), `routers/README.md` (`simulators.py`),
      `schemas/README.md` (`simulators.py`) [zona: infra]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-002, T-007, T-008, T-015, T-016, T-017, T-020, T-021, T-026 | `test_bacnet_address.py`, `test_simulator_service.py`, `test_simulators_router.py`, `test_bacnet_simulator_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-002 | T-009, T-010, T-015, T-016, T-017, T-022, T-023, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_modbus_simulator_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-003 | T-011, T-012, T-015, T-016, T-017, T-024, T-025, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_mqtt_publisher_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-004 | T-015, T-016, T-017, T-026 | `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RF-005 | T-015, T-016, T-017, T-026 | `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RF-006 | T-006, T-007, T-009, T-011, T-015, T-016, T-017, T-018, T-019, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_device_repository_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-007 | T-001, T-002, T-006, T-007, T-009, T-011, T-018, T-019, T-026 | `test_bacnet_address.py`, `test_simulator_service.py`, `test_device_repository_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-008 | T-006, T-018, T-019, T-026 | `test_device_repository_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-009 | T-013, T-014, T-016, T-017, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RF-010 | T-003, T-004, T-016, T-017, T-026 | `test_simulator_registry_service.py`, `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RF-011 | T-013, T-014 | `test_simulator_service.py` (ausencia de escritura `is_simulator=False`) | Pendiente |
| RF-012 | T-013, T-014, T-015, T-016, T-017, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RF-013 | T-003, T-004, T-026 | `test_simulator_registry_service.py`, `test_simulators_e2e.py` | Pendiente |
| RF-014 | T-011, T-012, T-015, T-016, T-017, T-024, T-025, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_mqtt_publisher_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| RF-015 | T-011, T-012, T-015, T-016, T-017, T-026 | `test_simulator_service.py`, `test_simulators_router.py`, `test_simulators_e2e.py` | Pendiente |
| RNF-001 | T-007, T-008, T-009, T-010, T-011, T-012, T-020, T-021, T-022, T-023, T-024, T-025, T-026 | `test_simulator_service.py`, `test_bacnet_simulator_adapter.py`, `test_modbus_simulator_adapter.py`, `test_mqtt_publisher_adapter.py`, `test_simulators_e2e.py` | Pendiente |
| doc: dispositivos-protocolos-puntos.md | T-027 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
