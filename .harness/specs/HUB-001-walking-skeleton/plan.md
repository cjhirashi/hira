---
id: PLAN-HUB-001
tipo: plan
feature: HUB-001-walking-skeleton
estado: implemented
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# PLAN-HUB-001 · Walking Skeleton de Hira Hub

> El *cómo*. Traduce cada `RF-` de `spec.md` al patrón **Hexagonal** fijado en la
> Génesis para `hira-hub` (Constitución Art. 1–2, `E-ADR-002`, supersede `HUB-ADR-05`).
> Perfil único: cloud single-tenant, VPS de cjhirashi. Stack `HUB-ADR-01`
> (FastAPI + PostgreSQL + Redis + Nginx) — **sin Mosquitto** (Hub no habla protocolos
> de campo). `hira-hub/` está vacío: todo se crea desde cero en este sprint, sin código
> compartido con `hira-server` todavía.

## 0. Gates de simplicidad
- [x] **Simplicity** — un solo perfil de despliegue, sin esquema de datos de negocio
      (licencias/crash-reports/versiones son H1/H2/H3), 2 puertos mínimos
      (`DatabasePort`, `CachePort`), un único router (`/health`).
- [x] **Anti-Abstraction** — sin capas especulativas, con una excepción declarada y
      justificada en §7 (`adapters/factory.py` sin *branching* real todavía — mismo
      criterio que `SRV-001`). Sin `NotificationPort`/`LicenseStoragePort`/
      `CrashReportPort`/`UpdateDistributionPort` todavía: la Constitución Art. 2 los
      registra como puertos de negocio futuros de Hub, pero **ningún caso de uso de
      este sprint los necesita** (Art. 10, no anticipar) — llegan con H1/H2/H3.
- [x] **Integration-First** — `hira-hub/docs/openapi.yaml` se escribe **antes** que
      `routers/monitor.py` (Contract-First, `spec.md §2`); los puertos (`Protocol`) se
      definen antes que sus adaptadores concretos.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `backend/services/` (casos de uso) solo importa de `backend/core/ports/`; `backend/adapters/factory.py` inyecta las implementaciones concretas de Postgres/Redis. Ningún router importa un adaptador directamente. `DatabasePort`/`CachePort` son puertos de infraestructura transversales que sostendrán a los puertos de negocio ya registrados en Art. 2 (`LicenseStoragePort` se apoyará en `DatabasePort`, por ejemplo) — no los reemplazan, simplemente este sprint no tiene todavía entidades de negocio sobre las que definirlos. |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo sin mocks, coordinación con dobles de puertos, adaptadores contra contenedores reales (Postgres+Redis, sin Mosquitto), sistema e2e con evidencia de terminal pegada. |
| Art. 4 (persistencia) | PostgreSQL propia de Hub (sin TimescaleDB — Hub no maneja series de tiempo) + Redis propia, bases separadas de `hira-server`/`hira-studio` (ninguna comparte esquema). En este sprint, `DatabasePort`/`CachePort` son *liveness*-only; el esquema de negocio (licencias, crash reports) llega en H1/H2. |
| Art. 5 (seguridad) | Sin `VUL-HUB-*` en alcance de este sprint (todos son de H1+: license keys, Panel Admin, JWT — `VUL-HUB-01..06` en `docs/hira-hub/spec/validation/vulnerabilities.md`). Alcance de este plan: secretos solo en `.env` (`hira-hub/.env.example` sin valores reales), sin SQL por concatenación (SQLAlchemy async parametrizado desde que `postgres_adapter.py` exista). No se inventa ningún requisito de seguridad adicional que `spec.md` no pida. |
| Art. 6 (contratos/errores) | `GET /health` no usa el sobre RFC 9457 (decisión ya cerrada en `spec.md §3`: es monitoreo). `hira-hub/docs/openapi.yaml` es el contrato Contract-First de esta frontera; **no** es todavía el contrato compartido `CT-license`/`CT-crash-report`/`CT-updates` de `docs/contracts/` — esos llegan cuando Hub sirva esas rutas (H1/H2). |
| Art. 10 (regla de raíz) | `adapters/factory.py` nace en el paso donde el router lo necesita (§6, paso 7), no "más adelante por prolijidad" — aplicando de forma proactiva la lección de la Directiva de Pausa de `SRV-001` (§7) en vez de repetirla. Sin `NotificationPort` ni puertos de negocio sin consumidor real. |
| Art. 11 (documentación) | §8 de este plan — 4 filas, cada una se convierte en tarea `[doc]` en `tasks.md`. |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio
- Este sprint **no introduce entidades de negocio** (licencias, crash reports,
  versiones — explícitamente fuera de alcance en `spec.md §2`). El único artefacto de
  dominio es la **regla de agregación de salud**: `status = "ok"` si Postgres y Redis
  están `ok`, `"degraded"` si al menos uno falla (RF-002) — lógica pura, sin I/O ni
  mocks: `backend/services/health_service.py::aggregate_status(results: dict[str, bool]) -> Literal["ok","degraded"]`.
  A diferencia de `SRV-001` (3 servicios, 8 combinaciones), aquí son **2 servicios, 4
  combinaciones**. Vive junto a la coordinación porque no hay más código de dominio
  todavía, pero se testea como núcleo (unit puro).

### Coordinación (casos de uso / fronteras de entrada)
- **`get_health()`** — `backend/services/health_service.py` ← implementa **RF-002,
  RF-005, RF-007**. Llama en paralelo a `DatabasePort.ping()` y `CachePort.ping()`,
  cada una envuelta en `asyncio.wait_for(timeout=2)` (RNF-002); una excepción o
  timeout se captura y marca ese servicio como `error` sin propagar (RF-007); agrega
  el `trace_id` vigente en el `contextvar` de la request y arma el payload exacto de
  `spec.md §3`.
- **`CorrelationIdMiddleware`** — `backend/core/middleware.py`, registrado en
  `backend/main.py` ← implementa **RF-005**: lee `X-Trace-ID`, genera `uuid4()` si no
  viene, lo fija en un `contextvars.ContextVar` que `core/logger.py` lee
  automáticamente y lo devuelve en la respuesta.
- **Arranque validado** — `backend/core/config.py` (`Settings(BaseSettings)`, Pydantic
  v2) ← implementa **RF-003**: `pydantic.ValidationError` se captura en el `lifespan`
  de `main.py`, se loguea en JSON (`level: error`) nombrando el/los campo(s)
  faltante(s) y se aborta el arranque (`sys.exit(1)`) — nunca arranque parcial. Las
  variables exigidas en este sprint son **solo** las de infraestructura que este
  walking skeleton consume de verdad (`DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`,
  `REDIS_PASSWORD`, `ENVIRONMENT`, `LOG_LEVEL`) — **sin** `SECRET_KEY` ni
  `ADMIN_PASSWORD_HASH` (`VUL-HUB-03`), que pertenecen al Panel Admin de H1 y no
  tienen consumidor real todavía (Art. 10, no anticipar).

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| PostgreSQL (contenedor del propio compose, imagen `postgres:16-alpine`) | Persistencia futura de licencias/crash-reports/versiones (`HUB-ADR-02`+); en este sprint solo *liveness* | `backend/adapters/db/postgres_adapter.py` implementa `DatabasePort.ping()` — engine async (SQLAlchemy 2.x + `asyncpg`), `SELECT 1`, respeta el timeout de 2s de quien lo llama (RNF-002) |
| Redis (`redis:7.4-alpine`) | Cache / rate-limiting futuro (H1: `/api/licenses/validate`); en este sprint solo *liveness* | `backend/adapters/cache/redis_adapter.py` implementa `CachePort.ping()` — `redis.asyncio`, comando `PING` |

> Sin fila de Mosquitto/`NotificationPort`: Hub no tiene protocolo de campo
> (`HUB-ADR-01`) y no hay ningún caso de uso de este sprint que envíe notificaciones
> (SMTP/webhook llega con H2, cuando exista un crash report real que notificar).

### Adaptadores de entrada
- `backend/routers/monitor.py::GET /health` (FastAPI) — único router de este sprint;
  contrato = `hira-hub/docs/openapi.yaml#/paths/~1health`.
- El Panel Admin (adaptador de entrada del producto, HTML/Jinja2 según
  `dev-guide.md` H1-06) **no se instancia en este sprint** — sin licencias ni crash
  reports que administrar todavía; fuera de alcance explícito.

### `adapters/factory.py`
- Instancia explícitamente Postgres/Redis — un solo perfil de despliegue (cloud
  single-tenant, sin variantes). Nace en el **paso 7** de §6, no después: el router
  necesita un punto de inyección desde el momento en que existe (regla de oro Art. 1:
  `routers/`/`services/` nunca importan un adaptador concreto) — aplicando de forma
  proactiva la lección que `SRV-001` tuvo que corregir con una Directiva de Pausa
  (ver su `plan.md §7`). Nace con 2 funciones placeholder in-memory (siempre `ok`, sin
  `branching`, sin importar infraestructura concreta) que implementan los `Protocol`
  ya definidos; el paso 9 reemplaza solo el **cuerpo**, no la firma.

### Infraestructura de contenedores *(fuera de las zonas del patrón, pero exigida por RF-001)*
- `hira-hub/docker-compose.yml` (perfil producción) + `docker-compose.dev.yml`
  (override hot-reload): servicios `backend`, `postgres` (imagen `postgres:16-alpine`),
  `redis` (`redis:7.4-alpine`), `nginx` (`nginx:1.27-alpine`) — **4 servicios, no 5**:
  sin Mosquitto (`HUB-ADR-01`). `HEALTHCHECK` propio en cada servicio (Postgres:
  `pg_isready`; Redis: `redis-cli ping`; backend: `curl -f /health` con criterio
  propio de "healthy" — el compose no depende de que `/health` diga `ok`, solo de que
  el proceso responda) + `depends_on` con `condition: service_healthy` — implementa
  **RF-001, RNF-001**.
- `hira-hub/nginx/nginx.conf` — proxy reverso genérico (`server_name` por defecto /
  `localhost`, **sin** `hub.hira.cjhirashi.com` todavía) hacia `backend` — implementa
  **RF-006**. El dominio real, TLS/Let's Encrypt y el `nginx.conf` de producción de
  `docs/hira-hub/spec/deployment.md` son un sprint operativo posterior (decisión ya
  cerrada en `spec.md §2`).

## 3. Modelo de datos
- **Ninguno en este sprint.** Explícitamente fuera de alcance (`spec.md §2`: licencias/
  crash-reports/versiones/Panel Admin llegan con H1/H2/H3). Sin migraciones Alembic
  todavía. `backend/models/` y `backend/schemas/` quedan creados (estructura ya
  documentada en `docs/hira-hub/spec/detailed-design.md`, actualizada en §8) con un
  único archivo real: `backend/schemas/health.py` (Pydantic response model del payload
  de `/health`).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/HUB-001-walking-skeleton/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** que consume el backend es `hira-hub/docs/openapi.yaml` | `GET /health` | `gate/check.sh` bloque 5: se activa automáticamente en cuanto exista un `*openapi.yaml` committeado (`git ls-files`) → Spectral lint. **Hoy el gate marca warn** (`spectral no instalado`) — no bloquea (`exit 0`), mismo estado ya aceptado como deuda conocida en `SRV-001`. |

> `hira-hub/docs/openapi.yaml` de este sprint **no** es todavía `CT-license` /
> `CT-crash-report` / `CT-updates` (los contratos compartidos de `docs/contracts/`,
> Art. 6) — Hub aún no sirve esas rutas. Se activan cuando lleguen H1/H2.

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`aggregate_status`) | Las 4 combinaciones de 2 booleanos → `ok`/`degraded` correcto | unit puro (pytest, **sin mocks**) — RF-002 |
| Coordinación (`health_service.get_health`) | Timeout a 2s por servicio (RNF-002); no cuelga si uno falla (RF-007); agrega `trace_id` (RF-005) | unit + dobles (`Protocol` fakes que duermen o lanzan excepción) de `DatabasePort`/`CachePort` |
| `core/config.py` | Variable de entorno faltante → error nombrando la variable, sin arranque parcial | unit, `monkeypatch` de env vars — RF-003 |
| `core/logger.py` + middleware | Cada log es JSON válido con `timestamp, level, service, module, trace_id, message`; `trace_id` propagado del header o generado | unit, captura de stdout — RF-004, RF-005 |
| Adaptadores (Postgres/Redis) | `ping()` contra los **contenedores reales** del compose (sin Mosquitto), no contra dobles | integración — `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` + pytest marcado `@pytest.mark.integration` |
| Sistema (e2e) | `docker compose up` → los 4 contenedores `healthy` en < 60s (RF-001/RNF-001) → `curl :8001/health` (puerto interno de Hub, `docs/hira-hub/spec/deployment.md`) → 200 con Postgres y Redis `ok` (RF-002); Nginx responde en el puerto local expuesto (RF-006) | e2e, script documentado en `tasks.md`; evidencia = **salida de terminal pegada** (Constitución Art. 3) |

## 6. Secuenciación de archivos (tests antes que código)
1. `backend/tests/test_health_policy.py` (falla) → `backend/services/health_service.py::aggregate_status` — RF-002.
2. `backend/tests/test_config.py` (falla) → `backend/core/config.py` — RF-003.
3. `backend/tests/test_logger.py` (falla) → `backend/core/logger.py` — RF-004.
4. `backend/tests/test_health_service.py` (dobles de puertos, falla) → `backend/core/ports/{database_port.py,cache_port.py}` (`Protocol`) + `backend/services/health_service.py::get_health` — RF-002, RF-005, RF-007.
5. `backend/tests/test_correlation_id.py` (falla) → `backend/core/middleware.py` + registro en `backend/main.py` — RF-005.
6. `hira-hub/docs/openapi.yaml` (Contract-First, antes del router) — congela el contrato de `/health`.
7. `backend/tests/test_health_router.py` (TestClient, falla) → `backend/routers/monitor.py` + `backend/schemas/health.py` + **`backend/adapters/factory.py`** (nace aquí con 2 funciones placeholder in-memory, sin `branching` ni lógica de negocio, ver §2/§7 — evita repetir la Directiva de Pausa de `SRV-001`) — expone RF-002 vía HTTP.
8. `hira-hub/docker-compose.yml` + `docker-compose.dev.yml` + `hira-hub/nginx/nginx.conf` + `hira-hub/.env.example` — RF-001, RF-006.
9. `backend/tests/integration/test_adapters.py` (falla, requiere contenedores del paso 8) → `backend/adapters/db/postgres_adapter.py`, `backend/adapters/cache/redis_adapter.py`, **reemplazan el cuerpo** (no la firma, ya fijada en el paso 7) de `backend/adapters/factory.py` — RF-002 (real).
10. Verificación e2e (`docker compose up` + `curl /health`, evidencia pegada) — RF-001, RNF-001, RNF-002.
11. `.harness/gate/services.txt`: añadir `hira-hub/backend:python` — activa el bloque 5 del gate para esta suite.
12. Tareas `[doc]` de §8 — pueden ejecutarse en paralelo desde el paso 1; no bloquean código.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `adapters/factory.py` sin *branching* real (un solo perfil, instancia directa de Postgres/Redis) | El patrón elegido en la Génesis (`E-ADR-002`, Art. 1) ya exige el archivo como punto único de selección de adaptadores para *todos* los sprints futuros (licencias, crash reports, updates, SMTP/webhook, GHCR/S3). No es abstracción especulativa de este plan: la interfaz (`Protocol`) la impone la Constitución Art. 1–2, no la inventamos aquí. Nace en el paso 7 (no en el 9) de forma **proactiva** para no repetir la Directiva de Pausa que `SRV-001` tuvo que abrir a mitad de implementación por la misma razón (`SRV-001/plan.md §7`). |
| `DatabasePort`/`CachePort` sin métodos de negocio (`save`, `get`, `set_ttl`, etc.) todavía | Ningún caso de uso de este sprint los necesita (Art. 10, no anticipar). Se amplían cuando `LicenseStoragePort`/`CrashReportPort` (Art. 2) tengan un caso de uso real que los consuma, en H1/H2. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-hub/spec/conceptual-design.md` | La sección embebida "ADR -5 — Arquitectura directa" se presenta como decisión vigente (estructura `core/`+`models/`+`schemas/`+`routers/`+`services/`, "no hay puertos ni adaptadores"), sin la nota de *superseded* que **sí** tiene el archivo `HUB-ADR-05` independiente — choca con `E-ADR-002` (Art. 1) que este sprint implementa en código real | `[doc]` añadir la misma nota de *superseded por `E-ADR-002`* que ya lleva `docs/hira-hub/decisions/HUB-ADR-05-arquitectura-directa.md`, sin reescribir el resto del contenido histórico |
| `docs/hira-hub/spec/detailed-design.md` | El árbol "Estructura de Carpetas del Proyecto" no tiene `core/ports/` ni `adapters/` — asume la arquitectura directa superseded; `core/database.py` como conexión monolítica no refleja el `DatabasePort`/`postgres_adapter.py` que este sprint crea | `[doc]` corregir el árbol: agregar `core/ports/{database_port.py,cache_port.py}` y `adapters/{db/postgres_adapter.py,cache/redis_adapter.py,factory.py}`; retirar `core/database.py` monolítico (su lógica de conexión pasa a `adapters/db/postgres_adapter.py`) |
| `docs/hira-hub/spec/dev-guide.md` | Tabla del Sprint H0 (H0-05 `core/database.py`, H0-06 sin mención de puertos/factory) no refleja Hexagonal; H0-08 asume Nginx apuntando ya a `hub.hira.cjhirashi.com` en H0, pero `spec.md §2` (confirmado 2026-09-13) deja dominio/TLS fuera de este sprint | `[doc]` actualizar la tabla H0 con los archivos reales de puertos/adaptadores/`factory.py`; aclarar que el `nginx.conf` de H0 es genérico/local — el dominio real llega con el sprint de despliegue (`docs/hira-hub/spec/deployment.md`) |
| `docs/hira-hub/spec/validation.md` | Checklist de Sprint H0 dice "Nginx sirve correctamente en el dominio configurado" (no aplica a este sprint) y omite `trace_id` en los campos de log esperados | `[doc]` corregir: "Nginx sirve correctamente como proxy reverso local (dominio real fuera de alcance, ver `deployment.md`)"; añadir `trace_id` a la lista de campos de log obligatorios |

`docs/hira-hub/decisions/HUB-ADR-05-arquitectura-directa.md` **no** requiere cambio — ya
lleva la nota de *superseded* correcta. `hira-hub/docs/openapi.yaml` **no** es un doc del
mapa Art. 11 — es un contrato de producto, ya cubierto en §4.

## 9. Implementación por requisito

### Implementación de RF-001
- `hira-hub/docker-compose.yml`, `hira-hub/docker-compose.dev.yml`.
- `HEALTHCHECK` por servicio + `depends_on: condition: service_healthy`.
- Test: verificación e2e (paso 10 de §6), evidencia de terminal pegada en el cierre.
- `covers`: `hira-hub/docker-compose*.yml`.

### Implementación de RF-002
- `backend/services/health_service.py` (`aggregate_status`, `get_health`).
- `backend/core/ports/{database_port.py,cache_port.py}`.
- `backend/adapters/{db/postgres_adapter.py,cache/redis_adapter.py,factory.py}`.
- `backend/routers/monitor.py`, `backend/schemas/health.py`.
- `hira-hub/docs/openapi.yaml#/paths/~1health`.
- Tests: `backend/tests/test_health_policy.py`, `test_health_service.py`, `test_health_router.py`, `tests/integration/test_adapters.py`.

### Implementación de RF-003
- `backend/core/config.py` (`Settings(BaseSettings)`, variables de infra únicamente — ver §2).
- Manejo del error en el `lifespan` de `backend/main.py`.
- `hira-hub/.env.example` (variables de este sprint, sin `SECRET_KEY`/`ADMIN_PASSWORD_HASH`).
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
- `hira-hub/nginx/nginx.conf` (proxy reverso genérico hacia `backend`, sin dominio/TLS real).
- Verificación e2e: `curl` local a través de Nginx responde lo mismo que directo al backend.
- Test: verificación e2e (paso 10 de §6).

### Implementación de RF-007
- `backend/services/health_service.py::get_health` — `asyncio.wait_for(timeout=2)` por servicio, captura de excepción/timeout sin colgar la respuesta.
- Test: `backend/tests/test_health_service.py` (dobles que duermen > 2s o lanzan excepción).

> No hay RF-008 en `spec.md` de Hub (a diferencia de `SRV-001`) — sin Mosquitto, no hay
> credencial de broker que reintentar con backoff.
