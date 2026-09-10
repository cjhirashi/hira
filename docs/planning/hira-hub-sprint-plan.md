---
origen_vault: "7.2 - Hira Hub/7.2.14 - Claude Code.md"
título: Claude Code — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: transversal
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, claude-code, tareas]
ecosistema: Hira
nota: Este archivo es la cola de tareas activa para sesiones de Claude Code en Hira Hub. Cowork lo actualiza al inicio de cada ciclo con las tareas del sprint activo.
---

## Sprint Activo

**Sprint H0 — Walking Skeleton Hub**

Hub debe responder `/health` con PostgreSQL y Redis vivos. Nada más.

---

## Tareas Pendientes

### T-00 — Copiar CLAUDE.md al repo (SIEMPRE primero)

```
Acción: Copiar el contenido de .harness/coordination/hira-hub-sprint-plan.md - CLAUDE.md al archivo hira-hub/CLAUDE.md en la raíz del repositorio
Verificación: El archivo CLAUDE.md existe en la raíz del repo
```

---

### T-01 — Docker Compose base

```
Archivos a crear:
  docker-compose.yml
  docker-compose.prod.yml
  .env.example

Servicios en docker-compose.yml:
  backend (FastAPI :8001)
  postgres:16-alpine (:5432)
  redis:7.4-alpine (:6379)
  nginx:1.27-alpine (:80/:443)

docker-compose.prod.yml:
  restart: unless-stopped en todos los servicios
  healthcheck en postgres y redis

.env.example:
  DATABASE_URL=postgresql+asyncpg://hub:CHANGE_ME@postgres:5432/hubdb
  POSTGRES_PASSWORD=CHANGE_ME
  POSTGRES_DB=hubdb
  POSTGRES_USER=hub
  REDIS_URL=redis://:CHANGE_ME@redis:6379/0
  REDIS_PASSWORD=CHANGE_ME
  SECRET_KEY=                    # openssl rand -hex 32
  ADMIN_EMAIL=cjhirashi@gmail.com
  ADMIN_PASSWORD_HASH=           # bcrypt del password del Panel Admin
  ENVIRONMENT=production
  LOG_LEVEL=INFO
  DOMAIN=hub.hira.cjhirashi.com

Criterio de éxito: docker compose up -d → todos los contenedores en estado healthy
```

---

### T-02 — Logger JSON estructurado

```
Archivo a crear: backend/core/logger.py

Requisitos (mismo estándar que Hira Server):
  - Clase JSONFormatter que formatea logs como JSON
  - Función get_logger(module_name) → logger configurado
  - LOG_LEVEL leído de variable de entorno (default: INFO)
  - Campos fijos en cada log: timestamp, level, service, module, trace_id, message
  - service = "hira-hub"
  - CERO print() en código de producción

Criterio de éxito: logger.info("Hub iniciado", extra={"trace_id": "test"}) produce JSON válido con todos los campos
```

---

### T-03 — Configuración con Pydantic Settings

```
Archivo a crear: backend/core/config.py

Requisitos:
  - Clase Settings(BaseSettings) con todas las variables de .env.example
  - Validación en startup: si ADMIN_PASSWORD_HASH está vacío → raise ValueError con mensaje claro
  - Singleton: instancia única importada en todos los módulos que la necesiten
```

---

### T-04 — Conexión a PostgreSQL

```
Archivo a crear: backend/core/database.py

Requisitos:
  - Engine async con SQLAlchemy + asyncpg
  - AsyncSessionLocal como factory de sesiones
  - Función get_session() como dependency de FastAPI
  - Base declarativa para los modelos ORM
```

---

### T-05 — Contrato API base

```
Archivo a crear: docs/openapi.yaml

Contenido mínimo (Sprint H0):
  info: { title: Hira Hub API, version: 0.1.0 }
  servers: [{ url: https://hub.hira.cjhirashi.com }]
  paths:
    /health:
      get:
        summary: Estado del sistema
        responses:
          200: { schema: { status, services: { postgres, redis }, version, trace_id } }

Nota: Contract-First — el contrato se define ANTES de implementar el router
```

---

### T-06 — Endpoint /health

```
Archivos a crear:
  backend/main.py
  backend/routers/monitor.py

Requisitos de main.py:
  - FastAPI app con título y versión
  - Incluir router de monitor
  - Startup: verificar que ADMIN_PASSWORD_HASH está configurado (VUL-HUB-03)

Requisitos de monitor.py:
  - GET /health: verifica conexión a postgres (SELECT 1) y redis (ping)
  - Responde: { "status": "ok", "services": { "postgres": "ok", "redis": "ok" }, "version": "0.1.0", "trace_id": "..." }
  - Si un servicio falla: status = "degraded", el servicio específico = "error"
  - trace_id generado con uuid4 para cada request (Correlation ID básico — middleware completo en Sprint H1)

Criterio de éxito: curl http://localhost:8001/health → 200 con JSON correcto
```

---

### T-07 — Nginx básico (HTTP)

```
Archivo a crear: nginx/nginx.conf

Requisitos Sprint H0 (solo HTTP — HTTPS en Sprint H1):
  - Proxy pass de :80 a backend :8001
  - Headers: X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
  - Location / → proxy al backend

Nota: HTTPS + rate limiting se agrega en Sprint H1 cuando llegue certbot
```

---

### T-08 — READMEs

```
Carpetas que necesitan README.md:
  backend/
  backend/core/
  backend/routers/
  docs/
  nginx/

Contenido mínimo de cada README:
  - Propósito (2-3 líneas)
  - Archivos con descripción de una línea cada uno
  - Cómo funciona (flujo de uso)
  - Dependencias (qué importa y por qué)
```

---

### T-09 — Validación final Sprint H0

```
Checklist antes de cerrar el sprint:

[ ] docker compose up -d → todos los contenedores en estado healthy
[ ] curl http://localhost:8001/health → {"status": "ok", "services": {"postgres": "ok", "redis": "ok"}}
[ ] Los logs del backend son JSON válido (no texto plano)
[ ] Los logs incluyen los campos: timestamp, level, service, module, message
[ ] Nginx sirve correctamente en :80
[ ] README.md presente en todas las carpetas creadas
[ ] .env.example cubre todas las variables requeridas

Si algún check falla: documentar en DEVIATIONS.md y continuar con los demás
```

---

## Historial de Sprints

| Sprint | Objetivo | Estado | Fecha |
|---|---|---|---|
| H0 — Walking Skeleton | Hub responde /health con postgres y redis vivos | Pendiente | — |
| H1 — Licencias | Emitir y validar license keys | Pendiente | — |
| H2 — Crash Reports + Versiones | Recepción de reports y consulta de versiones | Pendiente | — |
| H3 — Operación | Backup, healthchecks, dashboard básico | Pendiente | — |

---

## Notas para Cowork

**Al cerrar una sesión de Claude Code:**
1. Revisar `DEVIATIONS.md` en la raíz del repo — documenta contradicciones encontradas durante la implementación
2. Actualizar este archivo (.harness/coordination/hira-hub-sprint-plan.md) con el estado actual de las tareas
3. Hacer commit con formato `[SPRINT-H0][TIPO][MÓDULO] descripción`
