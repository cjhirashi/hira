---
origen_vault: "7.2 - Hira Hub/7.2.6 - Guía de Desarrollo.md"
título: Guía de Desarrollo — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 06 — Guía de Desarrollo
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, guía-desarrollo]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Repositorio

```
github.com/cjhirashi/hira-hub
```

Repositorio privado. CI con GitHub Actions. Imágenes en GHCR.

---

## Convenciones de código

Igual que Hira Server — mismo stack, mismas reglas:

- Python 3.12, tipado estricto, type hints en todas las funciones
- `async def` por defecto en routers y servicios
- Pydantic Settings para configuración
- `snake_case` para archivos/funciones/variables; `PascalCase` para clases
- Logger JSON estructurado (mismo `core/logger.py` que Server)
- Cero `print()` en código de producción

---

## Sprints de Desarrollo

### Sprint H0 — Walking Skeleton Hub

**Objetivo:** Hub responde `/health` con PostgreSQL y Redis vivos.

| Tarea | Módulo | Descripción |
|---|---|---|
| H0-01 | INFRA | Docker Compose: backend, postgres:16, redis:7.4, nginx:1.27 |
| H0-02 | INFRA | `.env.example` con todas las variables requeridas |
| H0-03 | LOGGER | `core/logger.py` — JSON estructurado, mismo estándar que Server |
| H0-04 | INFRA | `core/config.py` con Pydantic Settings |
| H0-05 | DB | `core/database.py` — conexión async PostgreSQL |
| H0-06 | ROUTERS | `routers/monitor.py` — `/health` verificando postgres y redis |
| H0-07 | CONTRACT | `docs/openapi.yaml` — solo `/health` |
| H0-08 | INFRA | Nginx configurado para hub.hira.cjhirashi.com (HTTP → Sprint H1 agrega HTTPS) |
| H0-09 | README | READMEs en todas las carpetas creadas |

**Gate:** `docker compose up -d` → `curl /health` → `{"status": "ok"}`

---

### Sprint H1 — Gestión de Licencias

**Objetivo:** cjhirashi puede emitir license keys manualmente y los Servers pueden validarlas.

| Tarea | Módulo | Descripción |
|---|---|---|
| H1-01 | MODELS | `models/licenses.py` — `LicenseKey`, `LicenseActivation` con Alembic migration |
| H1-02 | CONTRACT | `/api/licenses/validate` y `/api/licenses/activate` en `openapi.yaml` |
| H1-03 | SERVICES | `services/license_service.py` — generación de key (secrets.token_hex), hash bcrypt, validación |
| H1-04 | ROUTERS | `routers/licenses.py` — implementa contratos de `openapi.yaml` |
| H1-05 | SECURITY | `core/security.py` — funciones de hash y verificación bcrypt |
| H1-06 | ADMIN | `/admin/licenses` — vista para emitir, listar y revocar keys (HTML simple — Jinja2) |
| H1-07 | INFRA | Nginx rate limiting: 10 req/min por IP en `/api/licenses/validate` |
| H1-08 | CONTRACT | Actualizar `openapi.yaml` con errores 403 y 409 |
| H1-09 | INFRA | Certbot + SSL (Let's Encrypt) para hub.hira.cjhirashi.com |

**Gate:** Emitir key desde Panel Admin → Server valida → `{"valid": true}`

---

### Sprint H2 — Crash Reports y Versiones

**Objetivo:** Server puede enviar crash reports y consultar si hay versión nueva.

| Tarea | Módulo | Descripción |
|---|---|---|
| H2-01 | MODELS | `models/crash_reports.py` — `CrashReport` con deduplicación por hash |
| H2-02 | MODELS | `models/versions.py` — `HiraVersion` con flag `is_latest` |
| H2-03 | CONTRACT | `/api/crash-reports` y `/api/updates/latest` en `openapi.yaml` |
| H2-04 | SERVICES | `services/crash_service.py` — sanitización, hash, agrupación de duplicados |
| H2-05 | ROUTERS | `routers/crash_reports.py` y `routers/updates.py` |
| H2-06 | ADMIN | `/admin/crash-reports` — lista agrupada con contadores y campo github_issue_url |
| H2-07 | ADMIN | `/admin/versions` — publicar nueva versión (product, version, notes, image_tag) |
| H2-08 | INFRA | Rate limiting para `/api/crash-reports`: 100 req/hora por IP |

**Gate:** `POST /api/crash-reports` → Panel Admin muestra el report agrupado; `GET /api/updates/latest` devuelve versión correcta

---

### Sprint H3 — Backups y Operación

**Objetivo:** Hub es resiliente a reinicios y tiene backup automatizado.

| Tarea | Módulo | Descripción |
|---|---|---|
| H3-01 | INFRA | Script de backup diario: `pg_dump` → comprimido → copia a destino externo |
| H3-02 | INFRA | Healthcheck en Docker Compose para postgres y redis |
| H3-03 | INFRA | `restart: unless-stopped` en todos los servicios |
| H3-04 | INFRA | UptimeRobot configurado para `/health` de Hub |
| H3-05 | ADMIN | Dashboard Hub: licencias activas, crash reports sin revisar, última versión publicada |

**Gate:** Reiniciar VPS → Hub vuelve solo → `/health` OK; backup ejecuta y persiste

---

## Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://hub:CHANGE_ME@postgres:5432/hubdb
POSTGRES_PASSWORD=CHANGE_ME
POSTGRES_DB=hubdb
POSTGRES_USER=hub

# Redis
REDIS_URL=redis://:CHANGE_ME@redis:6379/0
REDIS_PASSWORD=CHANGE_ME

# Seguridad
SECRET_KEY=                    # min 32 chars, generado con: openssl rand -hex 32
ADMIN_EMAIL=cjhirashi@gmail.com
ADMIN_PASSWORD_HASH=           # bcrypt del password del Panel Admin

# App
ENVIRONMENT=production
LOG_LEVEL=INFO
DOMAIN=hub.hira.cjhirashi.com
```

---

## Flujo de CI/CD

```
git push origin main
  → GitHub Actions: lint (ruff) + tests (pytest)
  → Si pasa: build Docker image → push a GHCR
  → git tag v0.X.X (manual por cjhirashi)
  → GitHub Actions: build y push imagen tagged
  → Deployment en VPS (manual o via SSH action):
      ssh vps "cd /opt/hira-hub && git pull && docker compose pull && docker compose up -d"
```

---

## Comandos de operación frecuentes

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs del backend
docker compose logs -f backend

# Reiniciar solo el backend
docker compose restart backend

# Verificar health
curl https://hub.hira.cjhirashi.com/health

# Acceder a postgres
docker compose exec postgres psql -U hub -d hubdb

# Backup manual
docker compose exec postgres pg_dump -U hub hubdb > backup_$(date +%Y%m%d).sql
```

---

## Gate de Salida

- [x] Sprints H0–H3 definidos con tareas claras
- [x] Variables de entorno documentadas
- [x] Flujo CI/CD definido
- [x] Comandos de operación documentados
- [ ] Revisado y aprobado por Charlie
