---
id: TASKS-SRV-003
tipo: tasks
feature: SRV-003-bacnet-adapter
estado: draft
actualizado: 2026-09-14
---

# TASKS-SRV-003 · Adaptador BACnet — escaneo y candidatos

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-protocolos` (`.claude/agents/hira-protocolos.md`) —
  refrescar sus anclas contra este plan antes de invocarlo.

## Tareas

### Núcleo — dirección BACnet
- [x] T-001 — Test `test_bacnet_address.py`: parseo/validación de dirección
      BACnet (instance number + IP:puerto) (debe fallar) (cubre RF-002)
      [zona: test-núcleo]
      **Evidencia:** 10 tests, `ModuleNotFoundError: No module named
      'core.bacnet_address'` antes de T-002 → 10 passed tras T-002
      (`python -m pytest tests/test_bacnet_address.py -v`).
- [x] T-002 — Implementar `core/bacnet_address.py` (cubre RF-002) [zona: núcleo]
      **Nota de diseño:** el contrato exacto ya estaba fijado letra por letra
      en `plan.md §2` (2 funciones puras: `format_device_address(instance_number,
      network_address) -> str` / `parse_device_address(address) -> tuple[int,
      str]`, formato `"<instance_number>@<network_address>"`) — no era una
      decisión abierta de este batch, se implementó tal cual el plan (no un
      dataclass; el plan ya descartó explícitamente 2 columnas separadas y
      formatear ad-hoc en el servicio, ver Registro de decisiones de `plan.md`).
      Único detalle no fijado letra por letra: los mensajes de `ValueError` y
      el separador validado como constante interna `_SEPARATOR = "@"`.

### Puertos
- [x] T-003 — Implementar `core/ports/bacnet_transport_port.py`
      (`BacnetTransportPort`, `BacnetDeviceAnnouncement`, `BacnetObjectReading`,
      `BacnetReadTimeoutError` — `Protocol`, sin test propio) [zona: puertos]
- [x] T-004 — Implementar `core/ports/device_repository_port.py`
      (`DeviceRepositoryPort`, `DeviceRecord`, `DeviceCandidateRecord` —
      `Protocol`, sin test propio) [zona: puertos]

### Coordinación — servicio de escaneo
- [x] T-005 — Test `test_device_scan_service.py` con dobles de
      `BacnetTransportPort`/`DeviceRepositoryPort`: Who-Is → I-Am → lectura de
      objetos (timeout 2s no cuelga) → persiste device+candidatos; sin I-Am →
      lista vacía; dispositivo que no responde a la lectura no aborta el resto
      (debe fallar) (cubre RF-001, RF-002, RF-006, RF-007, RF-008, RNF-001)
      [zona: test-coordinación]
      **Evidencia:** 7 tests, `ModuleNotFoundError: No module named
      'services.device_scan_service'` antes de T-006 → 7 passed tras T-006
      (`python -m pytest tests/test_device_scan_service.py -v`, 3.23s —
      incluye un caso con `asyncio.sleep(3.0)` real para probar que el timeout
      no cuelga la respuesta total).
- [x] T-006 — Implementar `services/device_scan_service.py::scan_bacnet`
      (cubre RF-001, RF-002, RF-006, RF-007, RF-008, RNF-001)
      [zona: coordinación]

### Contrato — Contract-First
- [x] T-007 — Ampliar `hira-server/docs/openapi.yaml` con `POST /devices/scan/
      bacnet`, `GET /devices`, `GET /devices/{id}/candidates` — antes del
      router, sin tocar `/health`/`/auth/*` (cubre RF-001, RF-003, RF-004,
      RF-005, RF-008, RF-009) [zona: contrato]
      **Evidencia:** YAML válido (`yaml.safe_load`), 7 paths (los 4 previos +
      3 nuevos), 9 schemas (los 7 previos + `DeviceOut`/`DeviceCandidateOut`),
      `/health`/`/auth/*` sin cambios de contenido.

### Adaptador de entrada — router
- [x] T-008 — Test `test_devices_router.py` (`TestClient`): contrato exacto,
      403 para Visor, 404 en candidato de device inexistente (debe fallar)
      (cubre RF-001, RF-003, RF-004, RF-005, RF-008, RF-009)
      [zona: test-adaptador-entrada]
      **Evidencia:** 8 tests, `ImportError: cannot import name
      'get_bacnet_transport_port' from 'adapters.factory'` antes de T-009 → 8
      passed tras T-009 (`python -m pytest tests/test_devices_router.py -v`).
- [x] T-009 — Implementar `routers/devices.py` + `schemas/devices.py`
      (`DeviceOut`, `DeviceCandidateOut`) + `adapters/factory.py::
      get_bacnet_transport_port()`/`get_device_repository_port()` (nacen aquí
      con dobles in-memory — mismo patrón ya aplicado en `SRV-001`/`SRV-002`:
      el router necesita el punto de inyección desde que existe) + `require_role
      ("admin","operador")` (reusa `core/security/dependencies.py` de
      `SRV-002`) + registro en `main.py` (cubre RF-001, RF-003, RF-004,
      RF-005, RF-008, RF-009) [zona: adaptador-entrada]
      **Evidencia:** placeholders in-memory triviales
      (`_PlaceholderBacnetTransport`, `_InMemoryDeviceRepository`), sin BAC0/
      SQLAlchemy importados. Suite completa del backend (`pytest -m "not
      integration"`): 157 passed, 19 deselected (integración fuera de alcance
      de este batch), sin regresiones en `SRV-001`/`SRV-002`.

### Modelo de datos
- [ ] T-010 — `hira-server/backend/models/base.py` (nuevo, `metadata`
      compartida) + editar `models/user_model.py` (importa `metadata` de
      `models/base.py` en vez de declarar la suya — sin cambio de
      comportamiento; confirmar que la suite de `SRV-002` sigue en verde sin
      modificar sus aserciones) (cubre RF-002) [zona: modelo-de-datos]
- [ ] T-011 — `models/device_model.py` (`devices_table` con `UNIQUE(protocol,
      address)`, `device_points_candidates_table` con `UNIQUE(device_id,
      object_type, object_instance)` — Core `Table`) (cubre RF-002)
      [zona: modelo-de-datos]
- [ ] T-012 — Ampliar `alembic/env.py` (importar `models.device_model`) +
      `alembic/versions/0002_create_devices_tables.py`
      (`down_revision="0001"`) (cubre RF-002) [zona: modelo-de-datos]

### Adaptador BACnet real — integración sin hardware
- [ ] T-013 — Test `tests/integration/test_bac0_adapter.py` (requiere 2
      instancias reales de `BAC0.lite()` en `127.0.0.1`, una con objetos
      BACnet reales de prueba, otra escaneando — Who-Is/I-Am real por UDP,
      unicast) (debe fallar) (cubre RF-001, RF-002, RF-006, RF-010)
      [zona: test-adaptadores]
- [ ] T-014 — Implementar `adapters/bacnet/bac0_adapter.py::BAC0Adapter` +
      `BAC0==2026.7.25` en `requirements.txt` — reemplaza el **cuerpo** (no la
      firma) de `adapters/factory.py::get_bacnet_transport_port()` (cubre
      RF-001, RF-002, RF-006, RF-010) [zona: adaptadores]

### Adaptador de repositorio real — integración contra Postgres
- [ ] T-015 — Test `tests/integration/test_device_repository_adapter.py`
      (requiere Postgres real + `alembic upgrade head` con la migración
      `0002` aplicada) (debe fallar) (cubre RF-002, RF-004, RF-005, RF-009)
      [zona: test-adaptadores]
- [ ] T-016 — Implementar `adapters/db/device_repository_adapter.py::
      PostgreSQLDeviceRepository` — reemplaza el **cuerpo** de
      `adapters/factory.py::get_device_repository_port()` (cubre RF-002,
      RF-004, RF-005, RF-009) [zona: adaptadores]

### Sistema — verificación e2e
- [ ] T-017 — `tests/integration/test_devices_scan_e2e.py` (contenedores
      reales + 2 instancias BAC0 reales): recorrido completo `POST /devices/
      scan/bacnet` → `GET /devices` → `GET /devices/{id}/candidates`,
      RNF-001 medido con evidencia real (debe fallar antes de T-014/T-016,
      pasa después) (cubre RF-001, RF-002, RF-004, RF-005, RF-008, RF-009,
      RNF-001) [zona: sistema-e2e]

### Documentación (`plan.md §8`) — puede correr en paralelo desde T-001
- [ ] T-018 — Corregir `docs/hira-server/spec/modules/dispositivos-
      protocolos-puntos.md`: nota aclarando que esta feature añade el
      escaneo/candidatos (Who-Is/I-Am + `device_points_candidates`) que
      alimentan la futura asociación explícita — el Motor de Protocolos
      completo (lectura/escritura/polling de puntos *asociados*) sigue sin
      existir todavía [doc]

### Higiene de repo
- [ ] T-019 — `hira-server/backend/adapters/bacnet/README.md` (nuevo) +
      `adapters/db/README.md` (ampliar, ya existe de `SRV-001`/`SRV-002`) —
      documentan las carpetas nuevas/ampliadas [zona: infra]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-005, T-006, T-008, T-009, T-013, T-014, T-017 | `test_device_scan_service.py`, `test_devices_router.py`, `test_bac0_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-002 | T-001, T-002, T-005, T-006, T-008, T-009, T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-017 | `test_bacnet_address.py`, `test_device_scan_service.py`, `test_devices_router.py`, `test_bac0_adapter.py`, `test_device_repository_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-003 | T-008, T-009 | `test_devices_router.py` | Pass |
| RF-004 | T-008, T-009, T-015, T-016, T-017 | `test_devices_router.py`, `test_device_repository_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-005 | T-008, T-009, T-015, T-016, T-017 | `test_devices_router.py`, `test_device_repository_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-006 | T-005, T-006, T-013, T-014, T-017 | `test_device_scan_service.py`, `test_bac0_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-007 | T-006 | `test_device_scan_service.py` (ausencia de escritura a tabla de puntos operables) | Pass |
| RF-008 | T-005, T-006, T-008, T-009, T-017 | `test_device_scan_service.py`, `test_devices_router.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-009 | T-008, T-009, T-015, T-016, T-017 | `test_devices_router.py`, `test_device_repository_adapter.py`, `test_devices_scan_e2e.py` | Pendiente |
| RF-010 | T-013, T-014 | `test_bac0_adapter.py` | Pendiente |
| RNF-001 | T-005, T-006, T-017 | `test_device_scan_service.py`, `test_devices_scan_e2e.py` | Pendiente |
| doc: dispositivos-protocolos-puntos.md | T-018 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
