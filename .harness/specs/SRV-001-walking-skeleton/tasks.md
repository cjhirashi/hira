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
      con el payload del contrato (debe fallar) (cubre RF-002) [zona: test-adaptador-entrada].
      **Nota (2026-09-13, hallazgo del `revisor` sobre el batch T-019..T-023):** al
      quedar `main.py::lifespan` invocando `MosquittoAdapter.connect()` de verdad
      (T-022 ampliada), la fixture `client` (que dispara el `lifespan` real vía
      `TestClient(app)`) pasó a pagar el backoff completo (~7s x 2 tests) intentando
      resolver el host `mosquitto` fuera de la red de docker. Corregido con el mismo
      patrón de `test_main_lifespan.py` (`monkeypatch.setattr(MosquittoAdapter,
      "connect", AsyncMock(return_value=None))` en la fixture `client`) — esta zona
      es contrato HTTP del router, no depende de red real ni del backoff de
      Mosquitto. 2/2 subsegundo de nuevo (0.73s los 2 juntos).
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
- [x] T-019 — Test `tests/integration/test_adapters.py` (requiere T-016..T-018 arriba):
      `DatabasePort.ping()` y `CachePort.ping()` contra Postgres/Redis reales (debe
      fallar) (cubre RF-002) [zona: test-adaptadores]. Confirmado en rojo: con los
      adaptadores movidos fuera del árbol y sin contenedores arriba, las 4 pruebas
      de esta suite + `test_mqtt_security.py` fallaban (`ConnectionRefusedError`) —
      evidencia pegada en el reporte de la sesión (`pytest -m integration`, 4 failed).
- [x] T-020 — Implementar `backend/adapters/db/postgresql_adapter.py` (`SELECT 1`,
      SQLAlchemy 2.x async + `asyncpg`, coherente con el formato
      `postgresql+asyncpg://` ya fijado en `.env.example`) + `backend/adapters/
      cache/redis_adapter.py` (`PING`, `redis.asyncio`) + reemplazado el **cuerpo**
      (no la firma) de `get_database_port`/`get_cache_port` en `backend/adapters/
      factory.py` — instancian los adaptadores reales como singleton perezoso por
      proceso (evita crear un `engine`/cliente nuevo por request) (cubre RF-002)
      [zona: adaptadores]. Verificado real: `docker compose -f docker-compose.yml
      -f docker-compose.dev.yml up -d postgres redis mosquitto` (los 3 `healthy`
      en segundos) → `pytest -m integration` → `test_postgresql_adapter_ping_
      against_real_container` y `test_redis_adapter_ping_against_real_container`
      en verde contra los contenedores reales. Sanity adicional (no sustituye
      T-024): `TestClient` sobre `main.py` con env vars apuntando a `localhost` →
      `GET /health` → `200 {"status":"ok","services":{"postgres":"ok","redis":
      "ok","mosquitto":"ok"},...}`.
- [x] T-021 — Test de integración: conexión a Mosquitto con credencial inválida no
      reintenta indefinidamente (backoff 1s/2s/4s, 3 intentos) (debe fallar) (cubre
      RF-008) [zona: test-adaptadores]. Mismo rojo que T-019 (adaptador no existía).
- [x] T-022 — Implementar `backend/adapters/mqtt/mosquitto_adapter.py::connect()`
      (credencial `MQTT_USER`/`MQTT_PASSWORD`, log `level: error` + backoff fijo en
      fallo) (cubre RF-006, RF-008) [zona: adaptadores]. **Decisión de interpretación
      de "3 intentos"** (spec/plan usan la frase sin desambiguar si cuenta el
      intento inicial): implementado como 1 intento inicial + 3 reintentos con
      backoff 1s/2s/4s = 4 intentos de conexión en total, luego se rinde sin lanzar
      excepción (`is_connected = False`). `ping()` (usado por `/health` en cada
      chequeo, RF-007) hace un único intento sin el backoff de `connect()` — es el
      "lazy retry en cada chequeo" que ya describía `plan.md §2`. Reemplazado el
      cuerpo de `get_notification_port` en `factory.py` (mismo patrón singleton).
      Verificado real contra Mosquitto real con credencial inválida: `connect()`
      tardó ~7s (backoff acumulado), registró 4 logs `level: error`, terminó sin
      lanzar excepción; verificado también con credencial **válida** (`connect()`
      → `is_connected=True`, `ping()` → `True`) — ambos casos contra el contenedor
      real, no solo el caso de rechazo TCP sin broker.

      **Directiva de Pausa (2026-09-13, #2 — ver `plan.md §7`, aprobada por el
      usuario):** el `revisor` encontró que este backoff no se invocaba en
      ningún camino real de la aplicación (`main.py` nunca llamaba
      `connect()`, solo `ping()` vía `/health`) — RF-008 no era demostrable a
      nivel de sistema. **Ampliación de esta misma tarea, cerrada:** el
      `lifespan` de `backend/main.py` ahora invoca `get_notification_port().
      connect()` (mismo punto de inyección que ya usa `routers/monitor.py` vía
      `Depends`) justo después de validar `Settings()`, envuelto en
      `try/except` que **no** aborta el arranque si falla (a diferencia del
      error de `Settings()`, que sí hace `sys.exit(1)`) — logueado y dejado
      para que `/health` lo refleje vía `ping()` (RF-007). Test de sistema
      ampliado en `backend/tests/test_main_lifespan.py`
      (`test_lifespan_invokes_mosquitto_connect_and_does_not_abort_on_failure`,
      `test_lifespan_invokes_mosquitto_connect_and_reflects_success`) con
      dobles (`AsyncMock`) de `MosquittoAdapter.connect` — verifica que el
      `lifespan` invoca `connect()` y tolera ambos resultados sin `sys.exit`.
      Verificado además contra el broker real (`docker compose up -d postgres
      redis mosquitto`): con credencial inválida, `connect()` corrió su
      backoff completo (~7s, 4 logs `level: error`, CONNACK rc=5) dentro del
      `lifespan` real y el proceso siguió (sin `sys.exit`), `is_connected=
      False`; con credencial válida, mismo camino, `is_connected=True`.
      Contenedores y `.env`/`password_file` de prueba limpiados al terminar.

### Seguridad — Mosquitto sin auth (`VUL-SRV-001`)
- [x] T-023 — Test de seguridad de integración (`tests/integration/
      test_mqtt_security.py`): cliente MQTT externo (`paho-mqtt` directo, sin pasar
      por el adaptador) sin credenciales, es rechazado por el broker real (CONNACK
      `rc != 0`) — falló antes de tener contenedores arriba (`ConnectionRefusedError`,
      mismo rojo que T-019), pasa después (cubre RF-006) [zona: test-seguridad].
      Formaliza automatizado lo que el revisor ya verificó manualmente con
      `mosquitto_pub` en T-016/T-017.

### Sistema — verificación e2e
- [x] T-024 — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` →
      todos los contenedores `healthy` en < 60s; `curl :8000/health` → 200 con los tres
      servicios `ok`; logs del backend en JSON — evidencia de terminal pegada (cubre
      RF-001, RNF-001, RNF-002, RF-004) [zona: sistema-e2e]. Verificado real
      (2026-09-13, `.env`/`password_file` de prueba generados desde `.env.example`,
      limpiados al terminar): `up -d` (imagen ya construida) → `postgres`/`redis`/
      `mosquitto` `healthy` ~16s después de arrancar, `backend` `healthy` ~22s
      después — los 4 muy por debajo de 60s (RNF-001). `nginx` volvió a chocar con el
      puerto 80 de esta máquina compartida (mismo hallazgo que T-016, no es un fallo
      del compose) — verificado aparte con un contenedor `nginx:1.27-alpine` +
      `nginx.conf` real en un puerto libre (`18080`) contra la red del compose:
      `curl :18080/health` → 200 con el proxy `location / { proxy_pass http://
      backend:8000; }` funcionando end-to-end. `curl :8000/health` (directo) → 200
      `{"status":"ok","services":{"postgres":"ok","redis":"ok","mosquitto":"ok"},
      "version":"0.1.0","trace_id":"..."}`. Logs del backend: revisados con `docker
      compose logs backend` — en el camino feliz solo hay logs de `uvicorn` (texto
      plano, librería de terceros, fuera del alcance de RF-004 que aplica al código
      propio vía `core/logger.py`); para demostrar RF-004 con evidencia real de
      terminal se detuvo `mosquitto` un momento (`docker compose stop mosquitto`):
      `GET /health` devolvió `200 {"status":"degraded",...,"mosquitto":"error"}` y
      `docker compose logs backend` mostró una línea JSON válida con los 6 campos
      exigidos (`timestamp, level, service, module, trace_id, message`) —
      verificado además parseando esa línea con `json.loads` (campos completos);
      `mosquitto` reiniciado y `/health` volvió a `ok`. Contenedores, imagen,
      `.env`, `password_file` y override temporal de puerto limpiados al cerrar.

### Arnés
- [x] T-025 — Declarar `hira-server/backend:python` en `.harness/gate/services.txt`
      para activar el bloque 5 (tests del servicio) (cubre RF-001) [zona: arnés].
      Declarado; `check.sh` (modo rápido) pasó de "vacío — declara los servicios" a
      "hira-server/backend · sin cambios — SKIP" (activado). `.venv` local
      (gitignored) creado con `requirements.txt` + `pytest`/`pytest-asyncio`/`httpx`.

      **Hallazgo del `revisor` (2026-09-13) y corrección de raíz — arnés, no
      producto:** `check.sh --full` corría `pytest` sin excluir el marker
      `integration`, así que sin contenedores arriba daba `3 failed` y **cerraba
      la compuerta** (no un warning cosmético — `⛔ COMPUERTA CERRADA` real). Es un
      gap genérico del bloque 5 (afecta a cualquier futuro servicio Python con
      tests de integración, no solo a este), y calificó como corrección trivial
      por la rúbrica de `method.md §2` (sin lógica de negocio, revertir cuesta
      segundos): `.harness/gate/check.sh` línea del bloque 5 ahora corre
      `pytest -m "not integration"` por defecto — la suite de integración se
      verifica aparte, explícitamente, con contenedores reales arriba (mismo
      patrón que ya usaron `hira-infra`/`revisor` durante todo T-019..T-024).
      Re-verificado: `check.sh --full` sin contenedores → **40 passed, 0 failed**,
      compuerta abierta. Con contenedores arriba → **43/43** (incluye los 3 de
      integración).
- [x] T-026 — Corregir `docs/hira-server/spec/implementation-guide/estructura-de-
      repositorio.md`: retirar `HIRA_DEPLOY_MODE`, perfil `studio`, `docker-compose.
      studio.yml`, referencias a SQLite [doc]
- [x] T-027 — Corregir `docs/hira-server/spec/implementation-guide/guia-backend.md`:
      retirar `adapters/db/sqlite_adapter.py` y `HIRA_DEPLOY_MODE` en `factory.py`
      (no tocar la nota "Nginx → Caddy") [doc]
- [x] T-028 — Añadir banner "superseded por `.harness/specs/SRV-001-walking-skeleton/`"
      al inicio de `docs/planning/SPRINT.md`, sin reescribir su contenido histórico
      [doc]
- [x] T-029 — Corregir enlaces rotos en `hira-server/README.md` (apuntar a
      `.harness/specs/SRV-001-walking-skeleton/`, `docs/hira-server/decisions/`,
      `docs/hira-server/spec/`, `docs/planning/SPRINT.md` con su banner) [doc].
      Hallazgo: los enlaces ya estaban correctos (corregidos por `ADR-004`,
      2026-09-13, commit `26d4795`) — solo faltaba el enlace a
      `docs/planning/SPRINT.md`, añadido.
- [x] T-030 — Actualizar `docs/hira-server/spec/validation/vulnerabilities.md`:
      `VUL-SRV-001` de 🟡 En Proceso a 🟢 Resuelto — **tarea de cierre**, solo después
      de que T-021/T-022/T-023 estén verificados con evidencia real [doc]. Hecho tras
      confirmar T-024; cita T-016/T-017/T-021/T-022/T-023 y añadida fila en
      "Historial de Resoluciones".

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-001, T-016, T-018, T-024, T-025 | `test_health_router.py` (contrato), verificación e2e (T-024) | Pass — T-001/T-016/T-018 (compose real) + T-024 (2026-09-13, e2e formal con evidencia pegada: `postgres`/`redis`/`mosquitto`/`backend` `healthy` bien por debajo de 60s; `nginx` verificado aparte por colisión de puerto 80 en esta máquina compartida, mismo hallazgo no-bloqueante de T-016, proxy real confirmado en puerto alterno) + T-025 (`hira-server/backend:python` declarado en `services.txt`, bloque 5 del gate activado) |
| RF-002 | T-002, T-003, T-008, T-009, T-010, T-013, T-014, T-015, T-019, T-020 | `test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py` | Pass — `test_health_policy.py` (8/8), `test_health_service.py` (6/6), `test_health_router.py` (2/2, con `factory.py` in-memory hasta T-020) y `tests/integration/test_adapters.py::test_postgresql_adapter_ping_against_real_container`/`test_redis_adapter_ping_against_real_container` (2/2, 2026-09-13, contra `postgres`/`redis` reales de `docker compose up`); `factory.py` ya instancia los adaptadores reales — sanity adicional de `GET /health` end-to-end con `TestClient` + contenedores reales en verde |
| RF-003 | T-004, T-005, T-012 | `test_config.py`, `test_main_lifespan.py` (T-012) | Pass — `test_config.py` (10/10) y `test_main_lifespan.py` (3/3, 2026-09-13, wiring del `lifespan` verificado: `ValidationError` → log JSON `level: error` + `sys.exit(1)`, sin arranque parcial) |
| RF-004 | T-006, T-007 | `test_logger.py`, evidencia de T-024 | Pass — `test_logger.py` (4/4); bug de binding de `sys.stdout` corregido en T-012 (`_DynamicStdoutHandler`), tests en verde; evidencia e2e de T-024 (2026-09-13) confirma en `docker compose logs backend` una línea JSON real con los 6 campos exigidos (`timestamp, level, service, module, trace_id, message`), parseada y validada con `json.loads` |
| RF-005 | T-008, T-010, T-011, T-012 | `test_health_service.py`, `test_correlation_id.py` | Pass — `test_health_service.py` (trace_id agregado, 2/2 casos) y `test_correlation_id.py` (4/4, 2026-09-13): propaga `X-Trace-ID` o genera `uuid4()`, fija/resetea el `ContextVar` de `core/logger.py` por request |
| RF-006 | T-017, T-021, T-022, T-023 | `tests/integration/test_adapters.py`, `tests/integration/test_mqtt_security.py` (T-023) | Pass — `test_mqtt_security.py::test_anonymous_mqtt_client_is_rejected_by_real_broker` (1/1, 2026-09-13, cliente `paho-mqtt` externo sin credenciales contra el Mosquitto real del compose, CONNACK `rc != 0`); `mosquitto_adapter.py` conecta con `MQTT_USER`/`MQTT_PASSWORD` (verificado con credencial válida contra el contenedor real, `is_connected=True`) |
| RF-007 | T-008, T-010 | `test_health_service.py` | Pass — timeout de 2s por servicio no cuelga la respuesta (2.03s para 3 chequeos, uno de ellos simulando 5s), excepción no propaga (2026-09-13) |
| RF-008 | T-021, T-022 | `tests/integration/test_adapters.py`, `test_main_lifespan.py` | Pass — el backoff (`MosquittoAdapter.connect()`) sigue probado de forma aislada contra el broker real (1/1: 1s/2s/4s, 4 intentos, 4 logs `level: error`, sin excepción); **wiring cerrado** (Directiva de Pausa #2, `plan.md §7`): `backend/main.py::lifespan` invoca `get_notification_port().connect()` tras validar `Settings()`, sin abortar el arranque si falla (`sys.exit(1)` solo aplica al error de `Settings()`) — `test_main_lifespan.py` (5/5, 2026-09-13) cubre ambos casos con dobles, y se verificó además en vivo contra Mosquitto real: credencial inválida → backoff completo (~7s, 4 logs `error`, CONNACK rc=5) dentro del `lifespan` real sin `sys.exit`, `is_connected=False`; credencial válida → mismo camino, `is_connected=True` |
| RNF-001 | T-016, T-024 | verificación e2e (T-024) | Pass — medición formal con evidencia de terminal pegada (2026-09-13, `date`/`docker inspect`): `postgres`/`redis`/`mosquitto` `healthy` ~16s tras arrancar, `backend` `healthy` ~22s tras arrancar — ambos muy por debajo de 60s |
| RNF-002 | T-008, T-010 | `test_health_service.py` | Pass — `asyncio.wait_for(timeout=2)` por puerto verificado con doble que duerme 5s (2026-09-13) |
| doc: estructura-de-repositorio | T-026 | — | Pass — `HIRA_DEPLOY_MODE`/perfil `studio`/`docker-compose.studio.yml`/SQLite retirados, árbol alineado a la estructura real |
| doc: guia-backend | T-027 | — | Pass — `sqlite_adapter.py` y `HIRA_DEPLOY_MODE` retirados de `factory.py`; nota "Nginx → Caddy" intacta |
| doc: SPRINT.md banner | T-028 | — | Pass — banner de superseded añadido al inicio, contenido histórico intacto |
| doc: hira-server/README.md | T-029 | — | Pass — enlaces ya corregidos por `ADR-004`; añadido el enlace faltante a `docs/planning/SPRINT.md` |
| doc: vulnerabilities.md (VUL-SRV-001) | T-030 | — | Pass — `VUL-SRV-001` 🟢 Resuelto, cita evidencia real de T-016/T-017/T-021/T-022/T-023, fila añadida en "Historial de Resoluciones" |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
