---
id: TASKS-SRV-001
tipo: tasks
feature: SRV-001-walking-skeleton
estado: draft
actualizado: 2026-09-13
---

# TASKS-SRV-001 · Walking Skeleton de Hira Server

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-infra` (`.claude/agents/hira-infra.md`) — anclas exactas de este
  sprint (`SRV-ADR-001/002/003/004/017`, `AC-SRV-01`).

## Tareas

### Estructura
- [x] T-001 — Crear árbol `hira-server/backend/{core/ports,adapters/{db,cache,mqtt},
      routers,models,schemas,services,workers,websocket,tests/integration}`,
      `frontend/` (stub), `nginx/`, `mosquitto/`, `docs/`; cada carpeta con su
      `README.md` (sin `MODULE.md`, retirado por `ADR-004`) (cubre RF-001) [zona: infra]

### Núcleo — regla de agregación de salud
- [x] T-002 — Test `test_health_policy.py`: 8 combinaciones de 3 booleanos →
      `aggregate_status` retorna `ok`/`degraded` correcto (debe fallar) (cubre RF-002)
      [zona: test-núcleo]
- [x] T-003 — Implementar `backend/services/health_service.py::aggregate_status`
      (cubre RF-002) [zona: núcleo]

### Config — arranque validado
- [x] T-004 — Test `test_config.py`: variable de entorno faltante → error nombrando la
      variable, sin arranque parcial (debe fallar) (cubre RF-003) [zona: test-servicio]
- [x] T-005 — Implementar `backend/core/config.py` (`Settings(BaseSettings)`, Pydantic
      v2) (cubre RF-003) [zona: servicio]. **Nota de alcance:** el manejo del error en
      el `lifespan` de `backend/main.py` queda pendiente para cuando exista `main.py`
      (batch posterior, T-012+) — fuera del alcance de este batch (T-001..T-007, sin
      contenedores/FastAPI todavía).

### Logger — observabilidad
- [x] T-006 — Test `test_logger.py`: cada log es JSON válido con `timestamp, level,
      service, module, trace_id, message`; cero `print()` (debe fallar) (cubre RF-004)
      [zona: test-servicio]
- [x] T-007 — Implementar `backend/core/logger.py::get_logger(module)` (cubre RF-004)
      [zona: servicio]

### Puertos + coordinación — `get_health()`
- [x] T-008 — Test `test_health_service.py` con dobles (`Protocol` fakes) de
      `DatabasePort`/`CachePort`/`NotificationPort`: timeout de 2s por servicio no
      cuelga la respuesta, agrega `trace_id` (debe fallar) (cubre RF-002, RF-005,
      RF-007) [zona: test-coordinación]
- [x] T-009 — Implementar `backend/core/ports/{database_port.py,cache_port.py,
      notification_port.py}` (`Protocol`) (cubre RF-002) [zona: puertos]
- [x] T-010 — Implementar `backend/services/health_service.py::get_health` —
      `asyncio.wait_for(timeout=2)` por puerto, agrega `status`/`services`/`trace_id`
      (cubre RF-002, RF-005, RF-007) [zona: coordinación]

### Correlation ID
- [x] T-011 — Test `test_correlation_id.py`: `X-Trace-ID` propagado o generado si el
      cliente no lo envía (debe fallar) (cubre RF-005) [zona: test-coordinación]
- [x] T-012 — Implementar `backend/core/middleware.py::CorrelationIdMiddleware` +
      registro en `backend/main.py` (cubre RF-005) [zona: coordinación]. **Incluye**
      el wiring de `Settings` en el `lifespan` de `main.py` (RF-003: `ValidationError`
      capturado, log JSON `level: error` nombrando el/los campo(s) faltante(s),
      `sys.exit(1)` sin arranque parcial) — es el primer punto donde `main.py` existe;
      test en `backend/tests/test_main_lifespan.py` (cubre RF-003, RF-005). **Nota de
      implementación:** al escribir `test_main_lifespan.py` se detectó un bug real en
      `core/logger.py` (batch anterior) — `logging.StreamHandler(stream=sys.stdout)`
      fija la referencia a `sys.stdout` en el momento de crear el logger; un logger
      creado a nivel de módulo (`main.py::_logger`, en tiempo de import) queda atado
      al `sys.stdout` real del proceso y `capsys` no puede capturar su salida en
      tests. Corregido con `_DynamicStdoutHandler` (resuelve `sys.stdout` en cada
      `emit`, no al crearse) — sin cambiar el formato JSON ni el comportamiento en
      producción; los tests de `test_logger.py` del batch anterior siguen en verde.

### Contrato — Contract-First
- [x] T-013 — Escribir `hira-server/docs/openapi.yaml` (`GET /health`, payload de
      `spec.md §3`) — antes del router (cubre RF-002) [zona: contrato]

### Adaptador de entrada — router
- [x] T-014 — Test `test_health_router.py` (`TestClient`): `GET /health` responde 200
      con el payload del contrato (debe fallar) (cubre RF-002) [zona: test-adaptador-entrada]
- [x] T-015 — Implementar `backend/routers/monitor.py` + `backend/schemas/health.py`
      (cubre RF-002) [zona: adaptador-entrada]. **Directiva de Pausa (2026-09-13,
      revisada y aprobada por Carlos — ver `plan.md §7`):** el router necesita
      inyectar los 3 puertos en
      `health_service.get_health()`. `SRV-ADR-017` prohíbe que `routers/` instancie
      un adaptador concreto directamente — esa decisión es de `adapters/factory.py`
      en exclusiva, y `plan.md §2`/§7 ya describe ese archivo como el punto único de
      selección de implementación para *todos* los sprints futuros (no es invención
      de esta sesión). Como los adaptadores reales de Postgres/Redis/Mosquitto no
      existen todavía (llegan en T-020, requieren contenedores de T-016..T-018), se
      optó por la opción (a) del encargo: crear ya `backend/adapters/factory.py`
      mínimo, con 3 funciones (`get_database_port`/`get_cache_port`/
      `get_notification_port`) que hoy devuelven placeholders in-memory (siempre
      `ok`) coherentes con los `Protocol` de `core/ports/`, inyectadas al router vía
      `fastapi.Depends`. T-020 reemplaza solo el **cuerpo** de esas 3 funciones para
      instanciar los adaptadores reales — la firma no cambia, `routers/monitor.py`
      no se toca en ese batch. El `revisor` rebotó esto en primera instancia porque
      el plan **aprobado** ataba la creación de `factory.py` al paso 9, no al 7 —
      aunque el resultado técnico era inocuo, reordenar un paso de un plan ya
      aprobado es cambiar una decisión de plan, no solo el síntoma (`method.md §2`).
      Se procesó como Directiva de Pausa real: `plan.md §6`/§7 actualizado con la
      restricción real y la solución de raíz, revisado por *git diff* y aprobado
      explícitamente por Carlos (2026-09-13) antes de dar T-013..T-015 por
      verificadas. Ver el commit `docs(SRV-001): Directiva de Pausa...`.

### Infraestructura de contenedores
- [x] T-016 — `hira-server/docker-compose.yml` + `docker-compose.dev.yml`: servicios
      `backend`/`postgres`/`redis`/`mosquitto`/`nginx` con `HEALTHCHECK` propio y
      `depends_on: condition: service_healthy` (cubre RF-001) [zona: infra]. Incluye
      `backend/Dockerfile` (Python 3.12-slim, `curl` para el `HEALTHCHECK`,
      `uvicorn main:app`) y `backend/requirements.txt` (versiones exactas, solo lo
      que `backend/` importa hoy: `fastapi`, `uvicorn[standard]`, `pydantic`,
      `pydantic-settings` — sin adelantar `asyncpg`/`redis`/`paho-mqtt` de T-020).
      Verificado con `docker compose config` (sintaxis válida) y `up -d` real:
      `postgres`/`redis`/`mosquitto`/`backend` alcanzan `healthy`; `nginx` no pudo
      publicar el puerto 80 en esta máquina compartida (`caddy_proxy` de otro
      proyecto ya lo ocupa — colisión de host, no del compose) — verificado aparte
      con `nginx:1.27-alpine` + `nginx.conf` en un puerto libre (`18080`):
      `curl :18080/health` → `200 {"status":"ok","services":{"postgres":"ok",
      "redis":"ok","mosquitto":"ok"},...,"trace_id":"..."}`, confirmando el proxy
      `location / { proxy_pass http://backend:8000; }` end-to-end.
- [x] T-017 — `hira-server/mosquitto/mosquitto.conf` (`allow_anonymous false`,
      `password_file`) + script de generación del `password_file` desde
      `MQTT_USER`/`MQTT_PASSWORD` (nunca en claro en el repo) (cubre RF-006)
      [zona: infra-seguridad]. `generate_password_file.sh` usa un contenedor
      descartable de `eclipse-mosquitto:2` (no requiere `mosquitto_passwd` en el
      host) y fija `chown 1883:1883` (uid/gid del proceso `mosquitto` dentro del
      contenedor, confirmado en `docker logs`) + `chmod 600` — sin esto Mosquitto
      rechaza el arranque (`Unable to open pwfile`, detectado y corregido durante
      la verificación real de este batch). Verificado real: `mosquitto` alcanza
      `healthy` en `docker compose up -d` con el `HEALTHCHECK` de
      `mosquitto_pub`/credencial válida.
- [x] T-018 — `hira-server/.env.example` completo (sin `HIRA_DEPLOY_MODE`) +
      `hira-server/nginx/nginx.conf` (cubre RF-001) [zona: infra]. `.env.example`
      cubre exactamente las variables de `core/config.py::Settings` (requeridas:
      `DATABASE_URL`, `REDIS_URL`, `MQTT_BROKER_HOST`, `MQTT_USER`,
      `MQTT_PASSWORD`, `SECRET_KEY`, `CORS_ORIGINS`; opcionales:
      `ENVIRONMENT`, `LOG_LEVEL`) + las de compose (`POSTGRES_USER`,
      `POSTGRES_PASSWORD`, `POSTGRES_DB`) — sin valores reales, solo placeholders.

### Adaptadores concretos — integración contra contenedores reales
- [ ] T-019 — Test `tests/integration/test_adapters.py` (requiere T-016..T-018 arriba):
      `DatabasePort.ping()` y `CachePort.ping()` contra Postgres/Redis reales (debe
      fallar) (cubre RF-002) [zona: test-adaptadores]
- [ ] T-020 — Implementar `backend/adapters/db/postgresql_adapter.py` (`SELECT 1`) +
      `backend/adapters/cache/redis_adapter.py` (`PING`) + `backend/adapters/
      factory.py` (cubre RF-002) [zona: adaptadores]
- [ ] T-021 — Test de integración: conexión a Mosquitto con credencial inválida no
      reintenta indefinidamente (backoff 1s/2s/4s, 3 intentos) (debe fallar) (cubre
      RF-008) [zona: test-adaptadores]
- [ ] T-022 — Implementar `backend/adapters/mqtt/mosquitto_adapter.py::connect()`
      (credencial `MQTT_USER`/`MQTT_PASSWORD`, log `level: error` + backoff fijo en
      fallo) (cubre RF-006, RF-008) [zona: adaptadores]

### Seguridad — Mosquitto sin auth (`VUL-SRV-001`)
- [ ] T-023 — Test de seguridad de integración: cliente MQTT externo sin credenciales
      es rechazado por el broker (debe fallar antes de T-017, pasa después) (cubre
      RF-006) [zona: test-seguridad]

### Sistema — verificación e2e
- [ ] T-024 — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` →
      todos los contenedores `healthy` en < 60s; `curl :8000/health` → 200 con los tres
      servicios `ok`; logs del backend en JSON — evidencia de terminal pegada (cubre
      RF-001, RNF-001, RNF-002, RF-004) [zona: sistema-e2e]

### Arnés
- [ ] T-025 — Declarar `hira-server/backend:python` en `.harness/gate/services.txt`
      para activar el bloque 5 (tests del servicio) (cubre RF-001) [zona: arnés]

### Documentación (`plan.md §8`) — pueden correr en paralelo desde T-002
- [ ] T-026 — Corregir `docs/hira-server/spec/implementation-guide/estructura-de-
      repositorio.md`: retirar `HIRA_DEPLOY_MODE`, perfil `studio`, `docker-compose.
      studio.yml`, referencias a SQLite [doc]
- [ ] T-027 — Corregir `docs/hira-server/spec/implementation-guide/guia-backend.md`:
      retirar `adapters/db/sqlite_adapter.py` y `HIRA_DEPLOY_MODE` en `factory.py`
      (no tocar la nota "Nginx → Caddy") [doc]
- [ ] T-028 — Añadir banner "superseded por `.harness/specs/SRV-001-walking-skeleton/`"
      al inicio de `docs/planning/SPRINT.md`, sin reescribir su contenido histórico
      [doc]
- [ ] T-029 — Corregir enlaces rotos en `hira-server/README.md` (apuntar a
      `.harness/specs/SRV-001-walking-skeleton/`, `docs/hira-server/decisions/`,
      `docs/hira-server/spec/`, `docs/planning/SPRINT.md` con su banner) [doc]
- [ ] T-030 — Actualizar `docs/hira-server/spec/validation/vulnerabilities.md`:
      `VUL-SRV-001` de 🟡 En Proceso a 🟢 Resuelto — **tarea de cierre**, solo después
      de que T-021/T-022/T-023 estén verificados con evidencia real [doc]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-016, T-018, T-024, T-025 | `test_health_router.py` (contrato), verificación e2e (T-024) | Parcial — T-001, T-016, T-018 hechas (compose real: `postgres`/`redis`/`mosquitto`/`backend` `healthy`; `nginx` verificado aparte por colisión de puerto 80 en esta máquina compartida, ver nota T-016); T-024 (e2e formal con evidencia pegada) y T-025 (gate services.txt) pendientes |
| RF-002 | T-002, T-003, T-008, T-009, T-010, T-013, T-014, T-015, T-019, T-020 | `test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py` | Parcial — `test_health_policy.py` Pass (8/8), `test_health_service.py` Pass (6/6) y `test_health_router.py` Pass (2/2, 2026-09-13: `GET /health` vía `TestClient` sobre la app real de `main.py`, shape exacto del contrato, siempre HTTP 200); router HTTP expuesto con `adapters/factory.py` in-memory (nota de decisión en T-015) — adaptadores reales contra contenedores (T-019/T-020) pendientes |
| RF-003 | T-004, T-005, T-012 | `test_config.py`, `test_main_lifespan.py` (T-012) | Pass — `test_config.py` (10/10) y `test_main_lifespan.py` (3/3, 2026-09-13, wiring del `lifespan` verificado: `ValidationError` → log JSON `level: error` + `sys.exit(1)`, sin arranque parcial) |
| RF-004 | T-006, T-007 | `test_logger.py`, evidencia de T-024 | Parcial — `test_logger.py` Pass (4/4); además corregido un bug de binding de `sys.stdout` detectado al implementar T-012 (`_DynamicStdoutHandler`), tests siguen en verde (2026-09-13); evidencia e2e de T-024 pendiente |
| RF-005 | T-008, T-010, T-011, T-012 | `test_health_service.py`, `test_correlation_id.py` | Pass — `test_health_service.py` (trace_id agregado, 2/2 casos) y `test_correlation_id.py` (4/4, 2026-09-13): propaga `X-Trace-ID` o genera `uuid4()`, fija/resetea el `ContextVar` de `core/logger.py` por request |
| RF-006 | T-017, T-021, T-022, T-023 | `tests/integration/test_adapters.py`, test de seguridad (T-023) | Pendiente |
| RF-007 | T-008, T-010 | `test_health_service.py` | Pass — timeout de 2s por servicio no cuelga la respuesta (2.03s para 3 chequeos, uno de ellos simulando 5s), excepción no propaga (2026-09-13) |
| RF-008 | T-021, T-022 | `tests/integration/test_adapters.py` | Pendiente |
| RNF-001 | T-016, T-024 | verificación e2e (T-024) | Parcial — `docker compose up -d` real (T-016) alcanzó `postgres`/`redis`/`mosquitto`/`backend` `healthy` en pocos segundos; medición formal de "< 60s" con evidencia de terminal pegada es T-024 (fuera de este batch) |
| RNF-002 | T-008, T-010 | `test_health_service.py` | Pass — `asyncio.wait_for(timeout=2)` por puerto verificado con doble que duerme 5s (2026-09-13) |
| doc: estructura-de-repositorio | T-026 | — | Pendiente |
| doc: guia-backend | T-027 | — | Pendiente |
| doc: SPRINT.md banner | T-028 | — | Pendiente |
| doc: hira-server/README.md | T-029 | — | Pendiente |
| doc: vulnerabilities.md (VUL-SRV-001) | T-030 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
