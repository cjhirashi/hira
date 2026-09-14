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
- [x] T-001 — Crear árbol `hira-hub/backend/{core/ports,adapters/{db,cache},
      routers,models,schemas,services,tests/integration}`, `hira-hub/nginx/`,
      `hira-hub/docs/`; cada carpeta con su `README.md` (sin `MODULE.md`,
      retirado por `ADR-004`) (cubre RF-001) [zona: infra]. **Evidencia:**
      árbol creado con `mkdir -p`, 14 `README.md` (uno por carpeta, incluida
      `backend/` raíz), `pytest.ini` + `requirements.txt` añadidos para poder
      correr la suite de este batch.

### Núcleo — regla de agregación de salud
- [x] T-002 — Test `test_health_policy.py`: 4 combinaciones de 2 booleanos →
      `aggregate_status` retorna `ok`/`degraded` correcto (debe fallar) (cubre
      RF-002) [zona: test-núcleo]. **Evidencia:** falló con
      `ModuleNotFoundError: No module named 'services.health_service'` antes
      de T-003.
- [x] T-003 — Implementar `backend/services/health_service.py::aggregate_status`
      (cubre RF-002) [zona: núcleo]. **Evidencia:** 4/4 tests pasan tras la
      implementación.

### Config — arranque validado
- [x] T-004 — Test `test_config.py`: variable de entorno faltante → error
      nombrando la variable, sin arranque parcial; confirma que `SECRET_KEY`/
      `ADMIN_PASSWORD_HASH` NO se exigen en este sprint (`VUL-HUB-03`, Panel
      Admin es H1) (debe fallar) (cubre RF-003) [zona: test-servicio].
      **Evidencia:** falló con `ModuleNotFoundError: No module named
      'core.config'` antes de T-005.
- [x] T-005 — Implementar `backend/core/config.py` (`Settings(BaseSettings)`,
      Pydantic v2 — `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`,
      `REDIS_PASSWORD`, `ENVIRONMENT`, `LOG_LEVEL`) (cubre RF-003)
      [zona: servicio]. **Nota de alcance:** el manejo del error en el
      `lifespan` de `backend/main.py` queda pendiente para cuando exista
      `main.py` (T-011). **Evidencia:** 11/11 tests pasan (incluye las 8
      variables requeridas nombradas individualmente + confirmación de que
      `secret_key`/`admin_password_hash` no son campos del modelo).

### Logger — observabilidad
- [x] T-006 — Test `test_logger.py`: cada log es JSON válido con `timestamp,
      level, service, module, trace_id, message`; cero `print()` (debe
      fallar) (cubre RF-004) [zona: test-servicio]. **Evidencia:** falló con
      `ModuleNotFoundError: No module named 'core.logger'` antes de T-007.
- [x] T-007 — Implementar `backend/core/logger.py::get_logger(module)` (cubre
      RF-004) [zona: servicio]. **Evidencia:** 4/4 tests pasan.

### Puertos + coordinación — `get_health()`
- [x] T-008 — Test `test_health_service.py` con dobles (`Protocol` fakes) de
      `DatabasePort`/`CachePort`: timeout de 2s por servicio no cuelga la
      respuesta, agrega `trace_id` (debe fallar) (cubre RF-002, RF-005,
      RF-007) [zona: test-coordinación]. **Evidencia:** falló con
      `ImportError: cannot import name 'get_health'` antes de T-009/T-010.
- [x] T-009 — Implementar `backend/core/ports/{database_port.py,cache_port.py}`
      (`Protocol`) (cubre RF-002) [zona: puertos].
- [x] T-010 — Implementar `backend/services/health_service.py::get_health` —
      `asyncio.wait_for(timeout=2)` por puerto, agrega `status`/`services`/
      `trace_id` (cubre RF-002, RF-005, RF-007) [zona: coordinación].
      **Evidencia:** 6/6 tests de `test_health_service.py` pasan (incluye
      timeout de 2s con doble que duerme 5s, resuelto en <3s).

### Correlation ID
- [x] T-011 — Test `test_correlation_id.py`: `X-Trace-ID` propagado o
      generado si el cliente no lo envía (debe fallar) (cubre RF-005)
      [zona: test-coordinación]. **Incluye** el wiring de `Settings` en el
      `lifespan` de `main.py` (RF-003: `ValidationError` capturado, log JSON
      `level: error` nombrando el/los campo(s) faltante(s), `sys.exit(1)` sin
      arranque parcial) — es el primer punto donde `main.py` existe.
      **Evidencia:** falló con `ModuleNotFoundError: No module named
      'core.middleware'` antes de T-012.
- [x] T-012 — Implementar `backend/core/middleware.py::CorrelationIdMiddleware`
      + registro en `backend/main.py` (incluye el `lifespan` con la
      validación de `Settings()`) (cubre RF-003, RF-005) [zona: coordinación].
      **Evidencia:** 7/7 tests de `test_correlation_id.py` pasan (propagación/
      generación de `trace_id` + `lifespan` aborta con `sys.exit(1)` y log
      JSON `level: error` nombrando la(s) variable(s) faltante(s)). Suite
      completa del batch: 32/32 tests pasan (`pytest -v`).

### Contrato — Contract-First
- [x] T-013 — Escribir `hira-hub/docs/openapi.yaml` (`GET /health`, payload de
      `spec.md §3`) — antes del router (cubre RF-002) [zona: contrato].
      **Evidencia:** `hira-hub/docs/openapi.yaml` creado, `/health` con
      `HealthResponse` (`status`, `services.{postgres,redis}`, `version`,
      `trace_id`), sin sobre RFC 9457.

### Adaptador de entrada — router
- [x] T-014 — Test `test_health_router.py` (`TestClient`): `GET /health`
      responde 200 con el payload del contrato (debe fallar) (cubre RF-002)
      [zona: test-adaptador-entrada]. **Evidencia:** falló con `404 Not
      Found` (sin `routers/monitor.py` registrado) antes de T-015.
- [x] T-015 — Implementar `backend/routers/monitor.py` + `backend/schemas/
      health.py` + `backend/adapters/factory.py` (nace aquí con 2 funciones
      placeholder in-memory — aplica de forma proactiva la lección de la
      Directiva de Pausa de `SRV-001`: el router necesita el punto de
      inyección desde que existe) + registro en `main.py` (cubre RF-002)
      [zona: adaptador-entrada]. **Evidencia:** 34/34 tests pasan (`pytest -v`).

### Infraestructura de contenedores
- [x] T-016 — `hira-hub/docker-compose.yml` + `docker-compose.dev.yml`:
      servicios `backend`/`postgres`/`redis`/`nginx` (sin Mosquitto) con
      `HEALTHCHECK` propio y `depends_on: condition: service_healthy` (cubre
      RF-001) [zona: infra]. **Evidencia:** `backend/Dockerfile` creado
      (Python 3.12-slim, puerto interno :8001 — `docs/hira-hub/spec/
      deployment.md` — distinto del :8000 de `hira-server`); `docker compose
      config` valida sin error; `postgres`+`redis` levantados con `docker
      compose up -d postgres redis` → ambos `healthy` en <15s (`docker compose
      ps`).
- [x] T-017 — `hira-hub/nginx/nginx.conf` (proxy reverso genérico, sin
      dominio/TLS real) + `hira-hub/.env.example` (cubre RF-001, RF-006)
      [zona: infra]. **Evidencia:** archivos creados, `docker compose config`
      los resuelve sin error.

### Adaptadores concretos — integración contra contenedores reales
- [x] T-018 — Test `tests/integration/test_adapters.py` (requiere T-016/T-017
      arriba): `DatabasePort.ping()` y `CachePort.ping()` contra Postgres/
      Redis reales (debe fallar) (cubre RF-002) [zona: test-adaptadores].
      **Evidencia:** falló con `ModuleNotFoundError: No module named
      'adapters.db.postgres_adapter'` / `'adapters.cache.redis_adapter'`
      (contenedores `postgres`+`redis` ya levantados vía `docker compose up -d
      postgres redis`, ambos `healthy`) antes de T-019.
- [x] T-019 — Implementar `backend/adapters/db/postgres_adapter.py`
      (`SELECT 1`) + `backend/adapters/cache/redis_adapter.py` (`PING`) —
      reemplazan el **cuerpo** (no la firma) de `adapters/factory.py` (cubre
      RF-002) [zona: adaptadores]. **Evidencia:** 2/2 tests de integración
      pasan contra los contenedores reales (`pytest -m integration`); suite
      completa del batch (unit + integración): 36/36 tests pasan.
      **Corrección post-revisión (misma tarea, sin abrir T-nuevo):** el
      `revisor` encontró, con evidencia real (compose levantado desde
      `.env.example` documentado), que `redis` del compose exige password
      (`--requirepass ${REDIS_PASSWORD}`) pero `RedisAdapter`/
      `adapters/factory.py::get_cache_port()` construían el cliente solo con
      `Settings().redis_url` — `Settings().redis_password` existía validado
      pero sin consumidor real, produciendo `AuthenticationError` en cada
      `PING` y `redis: error` en `/health` contra un Redis sano (falso
      negativo, viola RF-002). Además, `tests/integration/test_adapters.py`
      hardcodeaba `TEST_REDIS_URL` **con** password embebida
      (`redis://:changeme@localhost:6379/0`), distinta de `REDIS_URL` real
      (sin credenciales) — por eso pasaba en verde sin detectar el bug.
      **Fix de raíz:** `RedisAdapter.__init__(redis_url, redis_password)`
      combina ambos campos (`redis.from_url(url, password=password)`);
      `get_cache_port()` pasa `Settings().redis_url` +
      `Settings().redis_password`; el test de integración ahora arma
      `TEST_REDIS_URL`/`TEST_REDIS_PASSWORD` con la misma forma que
      `.env.example`/`factory.py` reales. Se añadió
      `tests/test_cache_adapter_wiring.py` (unit, mockeado, sin contenedor)
      para que una regresión de este wiring se detecte sin Docker.
      **Re-verificación e2e:** `docker compose -f docker-compose.yml -f
      docker-compose.dev.yml up -d --build` con `.env` copiado tal cual de
      `.env.example` (sin editar credenciales a mano) → `postgres`, `redis`,
      `backend` los 3 `healthy`; `curl :8001/health` →
      `{"status":"ok","services":{"postgres":"ok","redis":"ok"},"version":
      "0.1.0","trace_id":"…"}`. Reproducido también el bug original de forma
      aislada (código previo a este fix + credenciales reales) para
      confirmar causa raíz: `AuthenticationError: Authentication required.`
      Suite completa tras el fix: 36/36 unit (`pytest -m "not integration"`)
      + 2/2 integración (`pytest -m integration`) = 38/38. `nginx` no pudo
      levantar en este host por el puerto 80 ya ocupado por un servicio
      **no relacionado** (`caddy_proxy`, otro proyecto) — irrelevante para
      este fix (`/health` no depende de nginx) y fuera de alcance de esta
      corrección puntual (pertenece a T-020, no tocado).

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
| RF-002 | T-002, T-003, T-008, T-009, T-010, T-013, T-014, T-015, T-018, T-019 | `test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py`, `tests/test_cache_adapter_wiring.py` | Pass |
| RF-003 | T-004, T-005, T-012 | `test_config.py`, `test_correlation_id.py` (T-012) | Pass |
| RF-004 | T-006, T-007 | `test_logger.py`, evidencia de T-020 | Pendiente |
| RF-005 | T-008, T-010, T-011, T-012 | `test_health_service.py`, `test_correlation_id.py` | Pass |
| RF-006 | T-017, T-020 | verificación e2e (T-020) | Pendiente |
| RF-007 | T-008, T-010 | `test_health_service.py` | Pass |
| RNF-001 | T-016, T-020 | verificación e2e (T-020) | Pendiente |
| RNF-002 | T-008, T-010 | `test_health_service.py` | Pass |
| doc: conceptual-design.md | T-022 | — | Pendiente |
| doc: detailed-design.md | T-023 | — | Pendiente |
| doc: dev-guide.md | T-024 | — | Pendiente |
| doc: validation.md | T-025 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
