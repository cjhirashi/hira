---
id: TASKS-SRV-005
tipo: tasks
feature: SRV-005-mqtt-scanning
estado: verified
actualizado: 2026-09-14
---

# TASKS-SRV-005 · Escaneo MQTT — suscripción wildcard y candidatos

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-protocolos` (`.claude/agents/hira-protocolos.md`).

## Tareas

### Núcleo — clave de topic
- [x] T-001 — Test `test_mqtt_topic_key.py`: hash determinista del topic
      (`crc32`, mismo topic → misma clave, topics distintos → claves
      distintas en el caso normal) (debe fallar) (cubre RF-002)
      [zona: test-núcleo]
- [x] T-002 — Implementar `core/mqtt_topic_key.py` (cubre RF-002) [zona: núcleo]

### Puerto
- [x] T-003 — Implementar `core/ports/mqtt_scan_transport_port.py`
      (`MqttScanTransportPort`, `MqttTopicMessage`,
      `MqttInvalidTopicPatternError` — `Protocol`, sin test propio)
      [zona: puertos]

### Coordinación — servicio de escaneo (amplía `device_scan_service.py`)
- [x] T-004 — Ampliar `test_device_scan_service.py` con los casos de
      `scan_mqtt`: patrón inválido propaga `MqttInvalidTopicPatternError` como
      400; varios mensajes en topics distintos se persisten como candidatos
      separados (misma clave `crc32` = actualiza, no duplica); sin ningún
      mensaje → candidatos vacíos, sin crear `device` (debe fallar) (cubre
      RF-001, RF-002, RF-004, RF-005, RF-006, RNF-001) [zona: test-coordinación]
- [x] T-005 — Implementar `services/device_scan_service.py::scan_mqtt` (+
      `MQTT_SCAN_WINDOW_SECONDS=3`) (cubre RF-001, RF-002, RF-004, RF-005,
      RF-006, RNF-001) [zona: coordinación]

### Contrato — Contract-First
- [x] T-006 — Ampliar `hira-server/docs/openapi.yaml` con `POST /devices/scan/
      mqtt` (`ScanMqttRequest`) — sin tocar los 8 endpoints existentes (cubre
      RF-001, RF-003, RF-004, RF-006) [zona: contrato]

### Adaptador de entrada — router
- [x] T-007 — Ampliar `test_devices_router.py` (`TestClient`): contrato del
      nuevo endpoint, 403 para Visor, 400 con sobre RFC 9457 si el patrón es
      inválido (debe fallar) (cubre RF-001, RF-003, RF-004, RF-006)
      [zona: test-adaptador-entrada]
- [x] T-008 — Implementar el nuevo endpoint en `routers/devices.py` +
      `schemas/devices.py` (`ScanMqttRequest`) + `adapters/factory.py::
      get_mqtt_scan_transport_port()` (nace aquí con placeholder in-memory,
      mismo patrón ya aplicado 5 veces) (cubre RF-001, RF-003, RF-004, RF-006)
      [zona: adaptador-entrada]

### Adaptador MQTT real — integración contra Mosquitto real
- [x] T-009 — Test `tests/integration/test_mqtt_scan_adapter.py` (requiere el
      Mosquitto real del compose, credenciales de `Settings`, un segundo
      cliente `paho-mqtt` como publisher dentro/fuera de la ventana) (debe
      fallar) (cubre RF-001, RF-002, RF-004, RNF-001) [zona: test-adaptadores]
- [x] T-010 — Implementar `adapters/mqtt/mqtt_scan_adapter.py::
      MqttScanAdapter` (`paho-mqtt`, `CallbackAPIVersion.VERSION2`, archivo
      nuevo separado de `mosquitto_adapter.py`) — reemplaza el **cuerpo** (no
      la firma) de `adapters/factory.py::get_mqtt_scan_transport_port()`
      (cubre RF-001, RF-002, RF-004, RNF-001) [zona: adaptadores]

### Sistema — verificación e2e
- [x] T-011 — Ampliar `tests/integration/test_devices_scan_e2e.py`
      (contenedores reales + publisher `paho-mqtt` real): recorrido completo
      `POST /devices/scan/mqtt` → `GET /devices` → `GET /devices/{id}/
      candidates`, RNF-001 medido con evidencia real (debe fallar antes de
      T-010, pasa después) (cubre RF-001, RF-002, RF-003, RF-004, RF-006,
      RNF-001) [zona: sistema-e2e]

### Documentación (`plan.md §8`) — puede correr en paralelo desde T-001
- [x] T-012 — Actualizar `docs/hira-server/spec/modules/dispositivos-
      protocolos-puntos.md`: ampliar la nota de estado de implementación ya
      existente de `SRV-003`/`SRV-004` para incluir MQTT scanning [doc]

### Higiene de repo
- [x] T-013 — Ampliar `adapters/mqtt/README.md` (añade `mqtt_scan_adapter.py`
      junto a `mosquitto_adapter.py`), `adapters/README.md` (8ª función de
      `factory.py`), `core/README.md` (`mqtt_topic_key.py`), `core/ports/
      README.md` (`mqtt_scan_transport_port.py`) [zona: infra]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-004, T-005, T-007, T-008, T-009, T-010, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_mqtt_scan_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-002 | T-001, T-002, T-004, T-005, T-009, T-010, T-011 | `test_mqtt_topic_key.py`, `test_device_scan_service.py`, `test_mqtt_scan_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-003 | T-007, T-008, T-011 | `test_devices_router.py`, `test_devices_scan_e2e.py` | Pass |
| RF-004 | T-004, T-005, T-006, T-007, T-008, T-009, T-010, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_mqtt_scan_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-005 | T-004, T-005 | `test_device_scan_service.py` (ausencia de escritura a tabla de puntos operables) | Pass |
| RF-006 | T-004, T-005, T-006, T-007, T-008, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_devices_scan_e2e.py` | Pass |
| RNF-001 | T-004, T-005, T-009, T-010, T-011 | `test_device_scan_service.py`, `test_mqtt_scan_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| doc: dispositivos-protocolos-puntos.md | T-012 | — | Hecho |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
