---
título: "SRV-Sprint-1 — Walking Skeleton de Hira Server"
componente: hira-server
sprint: SRV-Sprint-1
estado: no-iniciado
fecha_inicio: —
---

> Sprint activo del ecosistema. Un solo sprint a la vez por track. HUB-H0 puede correr en
> paralelo — cuando arranque, se añade aquí una segunda sección `## HUB-H0`.

## Objetivo

`docker compose up` levanta el stack base de Hira Server y `GET /health` responde con el
estado real de PostgreSQL/TimescaleDB, Redis y Mosquitto. Nada de lógica de negocio
todavía — la infraestructura base es prerrequisito de todo lo demás.

## Anclas del sprint

- Realiza: `SRV-ADR-001`, `SRV-ADR-002`, `SRV-ADR-003`, `SRV-ADR-004`, `SRV-ADR-017`
- Deja verificable: `AC-SRV-01` (subítems 1.1, 1.2, 1.3, 1.4)

## Contexto de arranque

- Repo `hira-server/` está vacío (solo `README.md` stub). Se implementa desde cero.
- La estructura de carpetas objetivo está en
  `.harness/spec/hira-server/implementation-guide/estructura-de-repositorio.md` y
  `.../guia-backend.md`. **Ojo:** esos docs asumen todavía perfil `studio`/SQLite —
  `E-ADR-001` lo retira. Server tiene **un solo perfil** (PostgreSQL + TimescaleDB +
  pgvector). Si el doc y `E-ADR-001` chocan, gana `E-ADR-001` y se registra `DEV-###`.

## Tareas

### T-1 — Estructura de repo + `.gitignore` + `docs/openapi.yaml` inicial

- **anchors:** `SRV-ADR-017`
- **valida:** —
- **contrato:** `hira-server/docs/openapi.yaml` (nuevo — solo `/health` por ahora)
- Crear el árbol `backend/{core,adapters,routers,models,schemas,services,workers,websocket}`,
  `frontend/` (stub), `nginx/`, `mosquitto/`, `docs/`. Cada carpeta con su `README.md` /
  `MODULE.md` (plantilla `templates/module-readme.md`).
- `docs/openapi.yaml` con `GET /health` (schema: `status`, `services{postgres,redis,mosquitto}`, `version`, `trace_id`).

### T-2 — Docker Compose base

- **anchors:** `SRV-ADR-001`, `SRV-ADR-003`, `SRV-ADR-004`
- **valida:** `AC-SRV-01` (1.1, 1.2)
- **contrato:** n/a
- `docker-compose.yml` (perfil producción) + `docker-compose.dev.yml` (hot reload, puertos):
  servicios `backend` (FastAPI :8000), `postgres` (TimescaleDB image, :5432), `redis` (7.4, :6379),
  `mosquitto` (2.0, con `allow_anonymous false` + password_file — `VUL-SRV-001`), `nginx` (1.27).
- `.env.example` con todas las variables (sin `HIRA_DEPLOY_MODE` — retirado por `E-ADR-001`).
- Healthchecks en postgres, redis, mosquitto.

### T-3 — `core/logger.py` — logging JSON estructurado

- **anchors:** `SRV-ADR-002`
- **valida:** `AC-SRV-01` (indirecto)
- `get_logger(module)` → JSON con `timestamp`, `level`, `service` (`hira-server`), `module`,
  `trace_id`, `message`. `LOG_LEVEL` por env (default `INFO`). Cero `print()`.

### T-4 — `core/config.py` — Pydantic Settings

- **anchors:** `SRV-ADR-002`
- **valida:** `AC-SRV-01` (1.4)
- Todas las variables de `.env.example`. Validación en startup: variable faltante → error
  explícito nombrando la variable, sin arranque parcial.

### T-5 — Puertos + factory + adaptadores stub

- **anchors:** `SRV-ADR-017`
- **valida:** —
- `core/ports/` con `DatabasePort`, `CachePort`, `NotificationPort` (Protocols).
- `adapters/factory.py` — inyecta implementaciones concretas (sin `HIRA_DEPLOY_MODE`; un
  solo perfil). `adapters/db/postgresql_adapter.py` (conexión async + `SELECT 1`),
  `adapters/cache/redis_adapter.py` (ping).

### T-6 — `main.py` + `routers/monitor.py` — `GET /health`

- **anchors:** `SRV-ADR-003`, `SRV-ADR-004`
- **valida:** `AC-SRV-01` (1.3)
- Middleware de Correlation ID (`X-Trace-ID`). `GET /health` verifica postgres (`SELECT 1`),
  redis (`ping`), mosquitto (conexión). `status: ok|degraded`. Sigue el contrato de `docs/openapi.yaml`.

### T-7 — Tests de `AC-SRV-01`

- **anchors:** `SRV-ADR-001`
- **valida:** `AC-SRV-01` (1.1–1.4)
- `backend/tests/test_health.py` — `# AC-SRV-01.3` `/health` 200 con los tres servicios `ok`.
- `backend/tests/test_config.py` — `# AC-SRV-01.4` variable faltante → error nombrado.
- Test/lint de que el compose levanta (documentar si el entorno no puede correr Docker →
  `DEV-###`, no bloqueo silencioso).

## Gate de cierre

- [ ] `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` → todos los
      contenedores `healthy` en < 60s.
- [ ] `curl :8000/health` → `{"status":"ok","services":{"postgres":"ok","redis":"ok","mosquitto":"ok"}, ...}`.
- [ ] Logs del backend en JSON con `timestamp, level, service, module, trace_id, message`.
- [ ] Variable faltante → error explícito, sin arranque parcial.
- [ ] `.harness/ci/run_all.sh` en verde (traceability + contract + lint).
- [ ] `registry.yaml`: `AC-SRV-01` → `verified`; ADRs del sprint → citados por `MODULE.md`.
- [ ] Reporte de sesión en `.harness/deviations/LOG.md`.
