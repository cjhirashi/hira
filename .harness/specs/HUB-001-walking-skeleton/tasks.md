---
id: TASKS-HUB-001
tipo: tasks
feature: HUB-001-walking-skeleton
estado: draft
actualizado: 2026-09-14
---

# TASKS-HUB-001 · Walking Skeleton de Hira Hub

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hub-infra` (`.claude/agents/hub-infra.md`) — refrescar sus anclas
  contra `HUB-ADR-01`/`E-ADR-002` y este plan antes de invocarlo (nota de
  `memory/state.md` sobre los 16 especialistas de dominio).

## Tareas

### Estructura
- [ ] T-001 — Crear árbol `hira-hub/backend/{core/ports,adapters/{db,cache},
      routers,models,schemas,services,tests/integration}`, `hira-hub/nginx/`,
      `hira-hub/docs/`; cada carpeta con su `README.md` (sin `MODULE.md`,
      retirado por `ADR-004`) (cubre RF-001) [zona: infra]

### Núcleo — regla de agregación de salud
- [ ] T-002 — Test `test_health_policy.py`: 4 combinaciones de 2 booleanos →
      `aggregate_status` retorna `ok`/`degraded` correcto (debe fallar) (cubre
      RF-002) [zona: test-núcleo]
- [ ] T-003 — Implementar `backend/services/health_service.py::aggregate_status`
      (cubre RF-002) [zona: núcleo]

### Config — arranque validado
- [ ] T-004 — Test `test_config.py`: variable de entorno faltante → error
      nombrando la variable, sin arranque parcial; confirma que `SECRET_KEY`/
      `ADMIN_PASSWORD_HASH` NO se exigen en este sprint (`VUL-HUB-03`, Panel
      Admin es H1) (debe fallar) (cubre RF-003) [zona: test-servicio]
- [ ] T-005 — Implementar `backend/core/config.py` (`Settings(BaseSettings)`,
      Pydantic v2 — `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`,
      `REDIS_PASSWORD`, `ENVIRONMENT`, `LOG_LEVEL`) (cubre RF-003)
      [zona: servicio]. **Nota de alcance:** el manejo del error en el
      `lifespan` de `backend/main.py` queda pendiente para cuando exista
      `main.py` (T-011).

### Logger — observabilidad
- [ ] T-006 — Test `test_logger.py`: cada log es JSON válido con `timestamp,
      level, service, module, trace_id, message`; cero `print()` (debe
      fallar) (cubre RF-004) [zona: test-servicio]
- [ ] T-007 — Implementar `backend/core/logger.py::get_logger(module)` (cubre
      RF-004) [zona: servicio]

### Puertos + coordinación — `get_health()`
- [ ] T-008 — Test `test_health_service.py` con dobles (`Protocol` fakes) de
      `DatabasePort`/`CachePort`: timeout de 2s por servicio no cuelga la
      respuesta, agrega `trace_id` (debe fallar) (cubre RF-002, RF-005,
      RF-007) [zona: test-coordinación]
- [ ] T-009 — Implementar `backend/core/ports/{database_port.py,cache_port.py}`
      (`Protocol`) (cubre RF-002) [zona: puertos]
- [ ] T-010 — Implementar `backend/services/health_service.py::get_health` —
      `asyncio.wait_for(timeout=2)` por puerto, agrega `status`/`services`/
      `trace_id` (cubre RF-002, RF-005, RF-007) [zona: coordinación]

### Correlation ID
- [ ] T-011 — Test `test_correlation_id.py`: `X-Trace-ID` propagado o
      generado si el cliente no lo envía (debe fallar) (cubre RF-005)
      [zona: test-coordinación]. **Incluye** el wiring de `Settings` en el
      `lifespan` de `main.py` (RF-003: `ValidationError` capturado, log JSON
      `level: error` nombrando el/los campo(s) faltante(s), `sys.exit(1)` sin
      arranque parcial) — es el primer punto donde `main.py` existe.
- [ ] T-012 — Implementar `backend/core/middleware.py::CorrelationIdMiddleware`
      + registro en `backend/main.py` (incluye el `lifespan` con la
      validación de `Settings()`) (cubre RF-003, RF-005) [zona: coordinación]

### Contrato — Contract-First
- [ ] T-013 — Escribir `hira-hub/docs/openapi.yaml` (`GET /health`, payload de
      `spec.md §3`) — antes del router (cubre RF-002) [zona: contrato]

### Adaptador de entrada — router
- [ ] T-014 — Test `test_health_router.py` (`TestClient`): `GET /health`
      responde 200 con el payload del contrato (debe fallar) (cubre RF-002)
      [zona: test-adaptador-entrada]
- [ ] T-015 — Implementar `backend/routers/monitor.py` + `backend/schemas/
      health.py` + `backend/adapters/factory.py` (nace aquí con 2 funciones
      placeholder in-memory — aplica de forma proactiva la lección de la
      Directiva de Pausa de `SRV-001`: el router necesita el punto de
      inyección desde que existe) + registro en `main.py` (cubre RF-002)
      [zona: adaptador-entrada]

### Infraestructura de contenedores
- [ ] T-016 — `hira-hub/docker-compose.yml` + `docker-compose.dev.yml`:
      servicios `backend`/`postgres`/`redis`/`nginx` (sin Mosquitto) con
      `HEALTHCHECK` propio y `depends_on: condition: service_healthy` (cubre
      RF-001) [zona: infra]
- [ ] T-017 — `hira-hub/nginx/nginx.conf` (proxy reverso genérico, sin
      dominio/TLS real) + `hira-hub/.env.example` (cubre RF-001, RF-006)
      [zona: infra]

### Adaptadores concretos — integración contra contenedores reales
- [ ] T-018 — Test `tests/integration/test_adapters.py` (requiere T-016/T-017
      arriba): `DatabasePort.ping()` y `CachePort.ping()` contra Postgres/
      Redis reales (debe fallar) (cubre RF-002) [zona: test-adaptadores]
- [ ] T-019 — Implementar `backend/adapters/db/postgres_adapter.py`
      (`SELECT 1`) + `backend/adapters/cache/redis_adapter.py` (`PING`) —
      reemplazan el **cuerpo** (no la firma) de `adapters/factory.py` (cubre
      RF-002) [zona: adaptadores]

### Sistema — verificación e2e
- [ ] T-020 — `docker compose -f docker-compose.yml -f docker-compose.dev.yml
      up` → todos los contenedores `healthy` en < 60s; `curl :8000/health` (o
      vía nginx) → 200 con los dos servicios `ok`; logs del backend en JSON —
      evidencia de terminal pegada (cubre RF-001, RF-006, RNF-001, RNF-002,
      RF-004) [zona: sistema-e2e]

### Arnés
- [ ] T-021 — Declarar `hira-hub/backend:python` en `.harness/gate/
      services.txt` para activar el bloque 5 del gate (cubre RF-001)
      [zona: arnés]

### Documentación (`plan.md §8`) — pueden correr en paralelo desde T-002
- [ ] T-022 — Corregir `docs/hira-hub/spec/conceptual-design.md`: añadir la
      nota de *superseded por `E-ADR-002`* a la sección embebida "ADR-5 —
      Arquitectura directa", sin reescribir el resto del contenido histórico
      [doc]
- [ ] T-023 — Corregir `docs/hira-hub/spec/detailed-design.md`: árbol de
      carpetas — agregar `core/ports/{database_port.py,cache_port.py}` y
      `adapters/{db/postgres_adapter.py,cache/redis_adapter.py,factory.py}`;
      retirar `core/database.py` monolítico [doc]
- [ ] T-024 — Corregir `docs/hira-hub/spec/dev-guide.md`: tabla del Sprint H0
      con los archivos reales de puertos/adaptadores/`factory.py`; aclarar
      que el `nginx.conf` de H0 es genérico/local (dominio real en el sprint
      de despliegue) [doc]
- [ ] T-025 — Corregir `docs/hira-hub/spec/validation.md`: checklist H0 —
      "Nginx sirve correctamente como proxy reverso local (dominio real fuera
      de alcance)"; añadir `trace_id` a los campos de log obligatorios [doc]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-016, T-017, T-020, T-021 | `test_health_router.py` (contrato), verificación e2e (T-020) | Pendiente |
| RF-002 | T-002, T-003, T-008, T-009, T-010, T-013, T-014, T-015, T-018, T-019 | `test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py` | Pendiente |
| RF-003 | T-004, T-005, T-012 | `test_config.py`, `test_correlation_id.py` (T-012) | Pendiente |
| RF-004 | T-006, T-007 | `test_logger.py`, evidencia de T-020 | Pendiente |
| RF-005 | T-008, T-010, T-011, T-012 | `test_health_service.py`, `test_correlation_id.py` | Pendiente |
| RF-006 | T-017, T-020 | verificación e2e (T-020) | Pendiente |
| RF-007 | T-008, T-010 | `test_health_service.py` | Pendiente |
| RNF-001 | T-016, T-020 | verificación e2e (T-020) | Pendiente |
| RNF-002 | T-008, T-010 | `test_health_service.py` | Pendiente |
| doc: conceptual-design.md | T-022 | — | Pendiente |
| doc: detailed-design.md | T-023 | — | Pendiente |
| doc: dev-guide.md | T-024 | — | Pendiente |
| doc: validation.md | T-025 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
