---
id: TASKS-SRV-004
tipo: tasks
feature: SRV-004-modbus-adapter
estado: implemented
actualizado: 2026-09-14
---

# TASKS-SRV-004 · Adaptador Modbus — escaneo y candidatos

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-protocolos` (`.claude/agents/hira-protocolos.md`).

## Tareas

### Núcleo — dirección Modbus
- [x] T-001 — Test `test_modbus_address.py`: parseo/validación de dirección
      Modbus (`"<host>:<port>:<unit_id>"`) (debe fallar) (cubre RF-002)
      [zona: test-núcleo]
- [x] T-002 — Implementar `core/modbus_address.py` (cubre RF-002) [zona: núcleo]

### Puerto
- [x] T-003 — Implementar `core/ports/modbus_transport_port.py`
      (`ModbusTransportPort`, `ModbusRegisterType`, `ModbusRegisterReading`,
      `ModbusReadFailure` — `Protocol`, sin test propio) [zona: puertos]

### Coordinación — servicio de escaneo (amplía `device_scan_service.py`)
- [x] T-004 — Ampliar `test_device_scan_service.py` con los casos de
      `scan_modbus`: límite de 125 direcciones por tipo rechaza con
      `ModbusRangeTooLargeError` antes de leer nada; direcciones que fallan no
      abortan el resto; dispositivo se crea solo si al menos una dirección
      respondió; sin ninguna respuesta → candidatos vacíos (debe fallar)
      (cubre RF-001, RF-002, RF-004, RF-005, RF-006, RF-007, RNF-001)
      [zona: test-coordinación]

      > **Desviación de nombre (no de comportamiento), reportada al
      > orquestador — no requirió Directiva de Pausa:** `plan.md §2`/§9
      > (Gate 2, aprobado) ya había decidido explícitamente que RF-004 se
      > implementa lanzando `ProblemDetailError(400, .../modbus-range-too-
      > large, ...)` **directamente** desde `scan_modbus` — el Registro de
      > decisiones de `plan.md` descarta explícitamente un módulo/excepción
      > dedicados ("`core/modbus_range.py` para una sola comparación —
      > over-engineering"). Se implementó tal cual `plan.md` (autoridad de
      > Fase 2 ya aprobada por Carlos), no una clase `ModbusRangeTooLargeError`
      > nueva; el test verifica `pytest.raises(ProblemDetailError)` con
      > `status == 400` y `type_ == ".../modbus-range-too-large"`.
- [x] T-005 — Implementar `services/device_scan_service.py::scan_modbus` (+
      `MODBUS_MAX_RANGE_ADDRESSES=125`, `MODBUS_READ_TIMEOUT_SECONDS=1`)
      (cubre RF-001, RF-002, RF-004, RF-005, RF-006, RF-007, RNF-001)
      [zona: coordinación]

### Contrato — Contract-First
- [x] T-006 — Ampliar `hira-server/docs/openapi.yaml` con `POST /devices/scan/
      modbus` (`ScanModbusRequest`, `ModbusRegisterRange`) — sin tocar los 5
      endpoints existentes (cubre RF-001, RF-003, RF-004, RF-007) [zona: contrato]

### Adaptador de entrada — router
- [x] T-007 — Ampliar `test_devices_router.py` (`TestClient`): contrato del
      nuevo endpoint, 403 para Visor, 400 con slug `modbus-range-too-large` si
      el rango excede 125 (debe fallar) (cubre RF-001, RF-003, RF-004, RF-007)
      [zona: test-adaptador-entrada]
- [x] T-008 — Implementar el nuevo endpoint en `routers/devices.py` +
      `schemas/devices.py` (`ScanModbusRequest`, `ModbusRangeIn`) +
      `adapters/factory.py::get_modbus_transport_port()` (nace aquí con
      placeholder in-memory, mismo patrón que `get_bacnet_transport_port()`)
      (cubre RF-001, RF-003, RF-004, RF-007) [zona: adaptador-entrada]

      > **Nota de implementación (root-cause, no parche), reportada al
      > orquestador:** `ModbusRangeIn.count` se implementó **sin**
      > `Field(le=125)` a propósito, aunque `plan.md §2`/§9 lo menciona como
      > "defensa en profundidad de forma". Verificado con ejecución real: no
      > hay ningún exception handler de `RequestValidationError` registrado
      > en `main.py` (solo `ProblemDetailError`) — si el schema Pydantic
      > rechazara `count > 125`, FastAPI devolvería un 422 genérico (sin
      > sobre RFC 9457) **antes** de que `scan_modbus` pudiera ejecutarse,
      > haciendo inalcanzable por HTTP la validación de negocio que RF-004
      > exige explícitamente ("DEBE rechazar la solicitud con 400"). El
      > propio `plan.md §9` ya lo anticipaba: "no se depende únicamente del
      > schema". `openapi.yaml#/ModbusRegisterRange` sí documenta
      > `maximum: 125` (contrato para clientes/tooling); la única fuente de
      > verdad en runtime es `scan_modbus`. Test
      > `test_scan_modbus_rango_mayor_a_125_400_rfc9457` verifica 400 (no
      > 422) con el sobre RFC 9457 exacto.

### Adaptador Modbus real — integración sin hardware
- [x] T-009 — Test `tests/integration/test_pymodbus_adapter.py` (requiere un
      servidor `pymodbus` TCP real en el propio test, con registros de
      prueba cargados) (debe fallar) (cubre RF-001, RF-002, RF-005, RF-008)
      [zona: test-adaptadores]

      > Verificado con ejecución real que `pymodbus==3.15.0` (última en
      > PyPI al momento de esta tarea) sigue exigiendo la API nueva
      > (`pymodbus.simulator.simdata.SimData`/`simdevice.SimDevice`) — la
      > API "clásica" (`ModbusServerContext`/`ModbusDeviceContext`) sigue
      > rota en esta versión (confirma `plan.md §5`). `retries=0` medido de
      > nuevo: timeout real ≈1.002s (spike aislado) / ≈1.103s (evidencia de
      > terminal del test real, incluye overhead de logging/asserts).
- [x] T-010 — Implementar `adapters/modbus/pymodbus_adapter.py::
      PymodbusAdapter` + `pymodbus==3.15.0` en `requirements.txt` — reemplaza
      el **cuerpo** (no la firma) de `adapters/factory.py::
      get_modbus_transport_port()` (cubre RF-001, RF-002, RF-005, RF-008)
      [zona: adaptadores]

### Sistema — verificación e2e
- [x] T-011 — Ampliar `tests/integration/test_devices_scan_e2e.py`
      (contenedores reales + servidor `pymodbus` real): recorrido completo
      `POST /devices/scan/modbus` → `GET /devices` → `GET /devices/{id}/
      candidates`, RNF-001 medido con evidencia real (debe fallar antes de
      T-010, pasa después) (cubre RF-001, RF-002, RF-003, RF-004, RF-005,
      RF-007, RNF-001) [zona: sistema-e2e]

      > Evidencia real de tiempo (RNF-001): escaneo completo vía HTTP (3
      > holding registers reales, Postgres real) tardó 0.193s.

### Documentación (`plan.md §8`) — puede correr en paralelo desde T-001
- [x] T-012 — Actualizar `docs/hira-server/spec/modules/dispositivos-
      protocolos-puntos.md`: ampliar la nota de estado de implementación ya
      existente de `SRV-003` para incluir Modbus TCP (sondeo de rangos +
      candidatos) [doc]

### Higiene de repo
- [x] T-013 — `hira-server/backend/adapters/modbus/README.md` (nuevo) +
      ampliar `adapters/README.md` (añade la función nueva de `factory.py`
      a su historial) [zona: infra]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-004, T-005, T-007, T-008, T-009, T-010, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_pymodbus_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-002 | T-001, T-002, T-004, T-005, T-009, T-010, T-011 | `test_modbus_address.py`, `test_device_scan_service.py`, `test_pymodbus_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-003 | T-007, T-008, T-011 | `test_devices_router.py`, `test_devices_scan_e2e.py` | Pass |
| RF-004 | T-004, T-005, T-006, T-007, T-008, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_devices_scan_e2e.py` | Pass |
| RF-005 | T-004, T-005, T-009, T-010, T-011 | `test_device_scan_service.py`, `test_pymodbus_adapter.py`, `test_devices_scan_e2e.py` | Pass |
| RF-006 | T-004, T-005 | `test_device_scan_service.py` (ausencia de escritura a tabla de puntos operables) | Pass |
| RF-007 | T-004, T-005, T-006, T-007, T-008, T-011 | `test_device_scan_service.py`, `test_devices_router.py`, `test_devices_scan_e2e.py` | Pass |
| RF-008 | T-009, T-010 | `test_pymodbus_adapter.py` | Pass |
| RNF-001 | T-004, T-005, T-011 | `test_device_scan_service.py`, `test_devices_scan_e2e.py` | Pass |
| doc: dispositivos-protocolos-puntos.md | T-012 | — | Hecho |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
