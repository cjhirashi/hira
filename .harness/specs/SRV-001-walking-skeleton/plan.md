---
id: PLAN-SRV-001
tipo: plan
feature: SRV-001-walking-skeleton
estado: draft
aprobaciones:
  fase_2: pendiente
actualizado: 2026-09-13
---

# PLAN-SRV-001 · Walking Skeleton de Hira Server

> El *cómo*. Traduce cada `RF-` de `spec.md` al patrón **Hexagonal** fijado en la
> Génesis para `hira-server` (Constitución Art. 1–2, `SRV-ADR-017`). Perfil único:
> PostgreSQL+TimescaleDB (`E-ADR-001` retira `HIRA_DEPLOY_MODE`/SQLite — sin perfil
> `studio` en este producto).

## 0. Gates de simplicidad
- [x] **Simplicity** — un solo perfil de despliegue, sin esquema de datos de negocio,
      3 puertos mínimos (`DatabasePort`, `CachePort`, `NotificationPort`), un único
      router (`/health`). Nada más de lo que `RF-001..RF-008` exigen.
- [x] **Anti-Abstraction** — sin capas especulativas, con una excepción declarada y
      justificada en §7 (`adapters/factory.py` sin *branching* real todavía).
- [x] **Integration-First** — `docs/openapi.yaml` se escribe **antes** que
      `routers/monitor.py` (Contract-First, ya decidido en `spec.md §2`); los puertos
      (`Protocol`) se definen antes que sus adaptadores concretos.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/` (casos de uso) solo importa de `core/ports/`; `adapters/factory.py` inyecta las implementaciones concretas de Postgres/Redis/Mosquitto. Ningún router importa un adaptador directamente. |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo sin mocks, coordinación con dobles de puertos, adaptadores contra contenedores reales, sistema e2e con evidencia de terminal pegada. |
| Art. 4 (persistencia) | Un `StoragePort`/`DatabasePort` por backend — en este sprint solo PostgreSQL+TimescaleDB (imagen del compose); sin SQLite (retirado por `E-ADR-001`, ver §8). |
| Art. 5 (seguridad) | `VUL-SRV-001` resuelto en este sprint: Mosquitto con `allow_anonymous false` + `password_file`; credencial propia del backend vía `MQTT_USER`/`MQTT_PASSWORD` (§2, §5, RF-006/RF-008). Secretos en `.env`, nunca en el repo (`.env.example` sin valores reales). |
| Art. 6 (contratos/errores) | `GET /health` no usa el sobre RFC 9457 (decisión ya cerrada en `spec.md §3`: es monitoreo, no negocio). `docs/openapi.yaml` es el contrato Contract-First de esta frontera. |
| Art. 10 (regla de raíz) | Sin `HIRA_DEPLOY_MODE` ni ramas condicionales por perfil — la causa raíz del conflicto con la doc legacy se corrige en la doc (§8), no con un parche que mantenga dos perfiles a medias. |
| Art. 11 (documentación) | §8 de este plan — 5 filas, cada una se convierte en tarea `[doc]` en `tasks.md`. |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio
- Este sprint **no introduce entidades de negocio** (puntos, dispositivos, alarmas —
  explícitamente fuera de alcance en `spec.md §2`). El único artefacto de dominio es la
  **regla de agregación de salud**: `status = "ok"` si los tres servicios están `ok`,
  `"degraded"` si al menos uno falla (RF-002). Es lógica pura, sin I/O ni mocks:
  `backend/services/health_service.py::aggregate_status(results: dict[str, bool]) -> Literal["ok","degraded"]`.
  Vive junto a la coordinación porque no hay más código de dominio todavía, pero se
  testea como núcleo (unit puro).

### Coordinación (casos de uso / fronteras de entrada)
- **`get_health()`** — `backend/services/health_service.py` ← implementa **RF-002,
  RF-005, RF-007**. Llama en paralelo a `DatabasePort.ping()`, `CachePort.ping()`,
  `NotificationPort.ping()`, cada una envuelta en `asyncio.wait_for(timeout=2)`
  (RNF-002); una excepción o timeout se captura y marca ese servicio como `error` sin
  propagar (RF-007); agrega el `trace_id` vigente en el `contextvar` de la request y
  arma el payload exacto de `spec.md §3`.
- **`CorrelationIdMiddleware`** — `backend/core/middleware.py`, registrado en
  `backend/main.py` ← implementa **RF-005**: lee `X-Trace-ID`, genera `uuid4()` si no
  viene, lo fija en un `contextvars.ContextVar` que `core/logger.py` lee automáticamente
  y lo devuelve en la respuesta.
- **Arranque validado** — `backend/core/config.py` (`Settings(BaseSettings)`, Pydantic
  v2) ← implementa **RF-003**: `pydantic.ValidationError` se captura en el `lifespan` de
  `main.py`, se loguea en JSON (`level: error`) nombrando el/los campo(s) faltante(s) y
  se aborta el arranque (`sys.exit(1)`) — nunca arranque parcial.
- **Conexión de arranque a Mosquitto** — `backend/adapters/mqtt/mosquitto_adapter.py::connect()`,
  invocado en el `lifespan` ← implementa **RF-006, RF-008**: credencial `MQTT_USER`/
  `MQTT_PASSWORD`; si falla, log `level: error` + **un único ciclo de reintento con
  backoff fijo** (p. ej. 1s/2s/4s, 3 intentos) — nunca un loop ciego — y el estado queda
  `error` hasta que `/health` lo reevalúe (lazy retry en cada chequeo, RF-007).

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| PostgreSQL (TimescaleDB, contenedor del propio compose) | Persistencia futura de series/negocio; en este sprint solo *liveness* | `backend/adapters/db/postgresql_adapter.py` implementa `DatabasePort.ping()` — engine async (SQLAlchemy 2.x + `asyncpg`), `SELECT 1`, respeta el timeout de 2s de quien lo llama (RNF-002) |
| Redis | Cache / pub-sub futuro (`SRV-ADR-003`); en este sprint solo *liveness* | `backend/adapters/cache/redis_adapter.py` implementa `CachePort.ping()` — `redis.asyncio`, comando `PING` |
| Mosquitto | Notificaciones MQTT futuras; en este sprint conexión autenticada + *liveness* | `backend/adapters/mqtt/mosquitto_adapter.py` implementa `NotificationPort.ping()`/`.connect()` — `paho-mqtt` (cliente async o hilo dedicado), credencial `MQTT_USER`/`MQTT_PASSWORD`, backoff fijo sin loop infinito (RF-008) |

### Adaptadores de entrada
- `backend/routers/monitor.py::GET /health` (FastAPI) — único router de este sprint;
  contrato = `hira-server/docs/openapi.yaml#/paths/~1health`.
- El CLI de administración (declarado como adaptador de entrada del producto en
  Constitución Art. 2) **no se instancia en este sprint** — el walking skeleton no tiene
  todavía comandos administrativos que exponer; queda fuera de alcance explícito.

### `adapters/factory.py`
- Instancia explícitamente Postgres/Redis/Mosquitto — **sin** `HIRA_DEPLOY_MODE` (un
  solo perfil, decisión ya cerrada en `spec.md §6` y `E-ADR-001`). Se conserva el
  archivo como punto de extensión único (regla de oro `SRV-ADR-017`), aunque hoy no
  tenga una rama condicional real — justificado en §7.

### Infraestructura de contenedores *(fuera de las zonas del patrón, pero exigida por RF-001)*
- `hira-server/docker-compose.yml` (perfil producción) + `docker-compose.dev.yml`
  (override hot-reload): servicios `backend`, `postgres` (imagen TimescaleDB),
  `redis`, `mosquitto`, `nginx`. `HEALTHCHECK` propio en cada servicio (Postgres:
  `pg_isready`; Redis: `redis-cli ping`; Mosquitto: `mosquitto_pub` de prueba o socket
  check; backend: `curl -f /health` con criterio propio de "healthy" — el compose no
  depende de que `/health` diga `ok`, solo de que el proceso responda) + `depends_on`
  con `condition: service_healthy` — implementa **RF-001**, **RNF-001**.
- `hira-server/mosquitto/mosquitto.conf` (`allow_anonymous false`, `password_file
  /mosquitto/config/password_file`) + script de generación del `password_file`
  (`mosquitto_passwd`, credencial desde `MQTT_USER`/`MQTT_PASSWORD` de `.env`, nunca
  committeado en claro) — implementa **RF-006**.

## 3. Modelo de datos
- **Ninguno en este sprint.** Explícitamente fuera de alcance (`spec.md §2`: "pgvector
  / esquema de datos de negocio llega con `SRV-Sprint-2+`"). Sin migraciones Alembic
  todavía. `backend/models/` y `backend/schemas/` quedan creados (estructura de
  `SRV-ADR-017`/`guia-backend.md`) con un único archivo real:
  `backend/schemas/health.py` (Pydantic response model del payload de `/health`).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-001-walking-skeleton/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** que consume el backend es `hira-server/docs/openapi.yaml` | `GET /health` | `gate/check.sh` bloque 5: se activa automáticamente en cuanto exista un `*openapi.yaml` committeado (`git ls-files`) → Spectral lint. **Hoy el gate marca warn** (`spectral no instalado`) — no bloquea (`exit 0`); ver nota de Gate 2 más abajo. |

> **Nota para Gate 2:** instalar `spectral` es mantenimiento del arnés (tooling), no de
> esta feature de producto. Propuesta: aceptar el warn como deuda conocida y no
> bloquear este plan por eso; si el Tech Lead prefiere resolverlo ya, es una tarea de
> `.harness/`, no de `hira-server/`, y no debería llevar prefijo `RF-`.

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`aggregate_status`) | Las 8 combinaciones de 3 booleanos → `ok`/`degraded` correcto | unit puro (pytest, **sin mocks**) — RF-002 |
| Coordinación (`health_service.get_health`) | Timeout a 2s por servicio (RNF-002); no cuelga si uno falla (RF-007); agrega `trace_id` (RF-005); Mosquitto con credencial inválida no reintenta indefinidamente (RF-008) | unit + dobles (`Protocol` fakes que duermen o lanzan excepción) de `DatabasePort`/`CachePort`/`NotificationPort` |
| `core/config.py` | Variable de entorno faltante → error nombrando la variable, sin arranque parcial | unit, `monkeypatch` de env vars — RF-003 |
| `core/logger.py` + middleware | Cada log es JSON válido con `timestamp, level, service, module, trace_id, message`; `trace_id` propagado del header o generado | unit, captura de stdout — RF-004, RF-005 |
| Adaptadores (Postgres/Redis/Mosquitto) | `ping()`/`connect()` contra los **contenedores reales** del compose, no contra dobles | integración — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` + pytest marcado `@pytest.mark.integration` |
| Adaptador Mosquitto — credencial inválida | RF-008 contra broker real que rechaza auth | integración, segundo `password_file` de prueba con credencial deliberadamente mala |
| Seguridad — Mosquitto anónimo | Cliente MQTT externo sin credenciales es rechazado | integración de seguridad — cubre RF-006, `VUL-SRV-001`, `AC-SRV-12.1` |
| Sistema (e2e) | `docker compose up` → todos `healthy` en < 60s (RF-001/RNF-001) → `curl :8000/health` → 200 con los tres `ok` (RF-002) | e2e, script documentado en `tasks.md`; evidencia = **salida de terminal pegada** (Constitución Art. 3) |

## 6. Secuenciación de archivos (tests antes que código)
1. `backend/tests/test_health_policy.py` (falla) → `backend/services/health_service.py::aggregate_status` — RF-002.
2. `backend/tests/test_config.py` (falla) → `backend/core/config.py` — RF-003.
3. `backend/tests/test_logger.py` (falla) → `backend/core/logger.py` — RF-004.
4. `backend/tests/test_health_service.py` (dobles de puertos, falla) → `backend/core/ports/{database_port.py,cache_port.py,notification_port.py}` (`Protocol`) + `backend/services/health_service.py::get_health` — RF-002, RF-005, RF-007.
5. `backend/tests/test_correlation_id.py` (falla) → `backend/core/middleware.py` + registro en `backend/main.py` — RF-005.
6. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) — congela el contrato de `/health`.
7. `backend/tests/test_health_router.py` (TestClient, falla) → `backend/routers/monitor.py` + `backend/schemas/health.py` — expone RF-002 vía HTTP.
8. `hira-server/docker-compose.yml` + `docker-compose.dev.yml` + `hira-server/mosquitto/mosquitto.conf` + script de `password_file` + `hira-server/.env.example` + `hira-server/nginx/nginx.conf` — RF-001, RF-006.
9. `backend/tests/integration/test_adapters.py` (falla, requiere contenedores del paso 8 arriba) → `backend/adapters/db/postgresql_adapter.py`, `backend/adapters/cache/redis_adapter.py`, `backend/adapters/mqtt/mosquitto_adapter.py`, `backend/adapters/factory.py` — RF-002 (real), RF-006, RF-008.
10. Verificación e2e (`docker compose up` + `curl /health`, evidencia pegada) — RF-001, RNF-001, RNF-002.
11. `.harness/gate/services.txt`: añadir `hira-server/backend:python` — activa el bloque 5 del gate para esta suite.
12. Tareas `[doc]` de §8 — pueden ejecutarse en paralelo desde el paso 1; no bloquean código.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `adapters/factory.py` sin *branching* real (un solo perfil, instancia directa de los 3 adaptadores) | El patrón elegido en la Génesis (`SRV-ADR-017`) ya exige el archivo como punto único de selección de adaptadores para *todos* los sprints futuros (BACnet, Modbus, un segundo backend de storage). No es abstracción especulativa de este plan: la interfaz (`Protocol`) la impone la Constitución Art. 1–2, no la inventamos aquí. Evita una reescritura de `services/` cuando aparezca variabilidad real. |
| `NotificationPort.ping()`/`.connect()` sin `send()` implementado todavía | No hay ningún consumidor real de notificaciones en este sprint (regla de oro Art. 10: no anticipar). `send()` se añade cuando exista un caso de uso concreto que lo necesite. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/implementation-guide/estructura-de-repositorio.md` | Documenta `HIRA_DEPLOY_MODE=server\|studio`, `docker-compose.studio.yml` y perfil SQLite — **choca directamente** con la decisión ya cerrada en `spec.md §6` ("un solo perfil, sin `HIRA_DEPLOY_MODE`", `E-ADR-001`) que este sprint implementa en código real | `[doc]` corregir: retirar `HIRA_DEPLOY_MODE`, el perfil `studio`, `docker-compose.studio.yml` y las referencias a SQLite del árbol de carpetas y de las variables de entorno; dejar un único perfil (server, PostgreSQL+TimescaleDB) |
| `docs/hira-server/spec/implementation-guide/guia-backend.md` | `adapters/db/sqlite_adapter.py` y `adapters/factory.py "según HIRA_DEPLOY_MODE"` — mismo choque con `E-ADR-001` | `[doc]` corregir: retirar `sqlite_adapter.py` y las referencias a `HIRA_DEPLOY_MODE` en `factory.py`; **no tocar** la nota ya existente "Nginx → Caddy" (queda como deuda explícita ya documentada — RF-001 de este sprint sigue exigiendo `nginx` en el compose) |
| `docs/hira-server/spec/validation/vulnerabilities.md` | `VUL-SRV-001` pasa de 🟡 En Proceso a 🟢 Resuelto una vez RF-006/RF-008 estén verificados con evidencia real | `[doc]` actualizar estado a 🟢 Resuelto (tarea de **cierre**, en Fase 4, no antes) |
| `docs/planning/SPRINT.md` | Documento legacy pre-reestructuración del arnés (`SRV-Sprint-1`, tareas `T-1..T-7`) — queda **reemplazado** por `spec.md`/`plan.md`/`tasks.md` de esta feature; riesgo de que alguien lo siga usando como fuente viva | `[doc]` añadir banner "superseded por `.harness/specs/SRV-001-walking-skeleton/`" al inicio del archivo, sin reescribir su contenido histórico |
| `hira-server/README.md` | Enlaces a rutas que ya no existen en el arnés simplificado (`.harness/spec/hira-server/`, `.harness/adr/hira-server/`, `.harness/coordination/SPRINT.md`, `.harness/contracts/`) — quedarán rotos en cuanto esta feature toque el repo | `[doc]` corregir enlaces: apuntar a `.harness/specs/SRV-001-walking-skeleton/`, `docs/hira-server/decisions/`, `docs/hira-server/spec/`, `docs/planning/SPRINT.md` (con su banner) |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es un contrato de
producto, ya cubierto en §4.

## 9. Implementación por requisito

### Implementación de RF-001
- `hira-server/docker-compose.yml`, `hira-server/docker-compose.dev.yml`.
- `HEALTHCHECK` por servicio + `depends_on: condition: service_healthy`.
- Test: verificación e2e (paso 10 de §6), evidencia de terminal pegada en el cierre.
- `covers`: `hira-server/docker-compose*.yml`.

### Implementación de RF-002
- `backend/services/health_service.py` (`aggregate_status`, `get_health`).
- `backend/core/ports/{database_port.py,cache_port.py,notification_port.py}`.
- `backend/adapters/{db/postgresql_adapter.py,cache/redis_adapter.py,mqtt/mosquitto_adapter.py}`.
- `backend/routers/monitor.py`, `backend/schemas/health.py`.
- `hira-server/docs/openapi.yaml#/paths/~1health`.
- Tests: `backend/tests/test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py`.

### Implementación de RF-003
- `backend/core/config.py` (`Settings(BaseSettings)`).
- Manejo del error en el `lifespan` de `backend/main.py`.
- `hira-server/.env.example` (variables completas, sin `HIRA_DEPLOY_MODE`).
- Test: `backend/tests/test_config.py`.

### Implementación de RF-004
- `backend/core/logger.py` (`get_logger(module)`).
- `backend/core/middleware.py` (fija `trace_id` en `contextvars` para que el logger lo use).
- Test: `backend/tests/test_logger.py`.

### Implementación de RF-005
- `backend/core/middleware.py::CorrelationIdMiddleware`, registrado en `backend/main.py`.
- `backend/services/health_service.py::get_health` (incluye `trace_id` en el payload).
- Test: `backend/tests/test_correlation_id.py`.

### Implementación de RF-006
- `hira-server/mosquitto/mosquitto.conf` (`allow_anonymous false`, `password_file`).
- Script de generación del `password_file` (credencial desde `.env`, nunca en claro en el repo).
- `backend/adapters/mqtt/mosquitto_adapter.py` (conexión con `MQTT_USER`/`MQTT_PASSWORD`).
- Test: integración de seguridad (cliente MQTT externo sin credenciales rechazado) — cubre también `VUL-SRV-001`/`AC-SRV-12.1`.

### Implementación de RF-007
- `backend/services/health_service.py::get_health` — `asyncio.wait_for(timeout=2)` por servicio, captura de excepción/timeout sin colgar la respuesta.
- Test: `backend/tests/test_health_service.py` (dobles que duermen > 2s o lanzan excepción).

### Implementación de RF-008
- `backend/adapters/mqtt/mosquitto_adapter.py::connect()` — log `level: error` en fallo de auth, backoff fijo (1s/2s/4s, 3 intentos), sin loop ciego.
- `backend/services/health_service.py` refleja `mosquitto: error` en `/health` tras el fallo.
- Test: `backend/tests/integration/test_adapters.py` (credencial inválida contra broker real) + `backend/tests/test_health_service.py` (doble que simula fallo de conexión).
