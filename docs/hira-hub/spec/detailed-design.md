---
origen_vault: "7.2 - Hira Hub/7.2.5 - Diseño Detallado.md"
título: Diseño Detallado — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 05 — Diseño Detallado
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, diseño-detallado]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Stack y Versiones

| Componente | Versión | Imagen Docker |
|---|---|---|
| Python | 3.12 | python:3.12-slim |
| FastAPI | 0.115.x | — |
| PostgreSQL | 16 | postgres:16-alpine |
| Redis | 7.4 | redis:7.4-alpine |
| Nginx | 1.27 | nginx:1.27-alpine |

> Versiones exactas fijadas en `requirements.txt`. Sin rangos `^` ni `~`.

---

## Estructura de Carpetas del Proyecto

```
hira-hub/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── core/
│   │   ├── config.py          # Variables de entorno con pydantic-settings
│   │   ├── security.py        # Hash de license keys, JWT para Panel Admin
│   │   ├── logger.py          # JSON structurado — mismo estándar que Hira Server
│   │   └── database.py        # Conexión async PostgreSQL
│   ├── models/
│   │   ├── licenses.py        # LicenseKey, LicenseActivation
│   │   ├── crash_reports.py   # CrashReport
│   │   └── versions.py        # HiraVersion
│   ├── schemas/
│   │   ├── licenses.py        # Request/Response Pydantic
│   │   └── crash_reports.py
│   ├── routers/
│   │   ├── licenses.py        # /api/licenses/*
│   │   ├── crash_reports.py   # /api/crash-reports
│   │   ├── updates.py         # /api/updates/latest
│   │   ├── admin.py           # /admin/* (Panel Admin — autenticado)
│   │   └── monitor.py         # /health
│   └── services/
│       ├── license_service.py # Lógica de emisión y validación
│       └── crash_service.py   # Agrupación y deduplicación de reports
│
└── nginx/
    └── nginx.conf
```

---

## Modelos de Base de Datos

### `license_keys`

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID PK | |
| key_hash | VARCHAR(256) | Hash bcrypt de la key — nunca la key en claro |
| key_prefix | VARCHAR(20) | `HIRA-XXXX` — para identificar en Panel Admin sin exponer la key |
| product | ENUM | `server`, `studio` |
| tier | ENUM | `starter`, `professional`, `enterprise` |
| integrator_email | VARCHAR(255) | Email del integrador propietario |
| issued_at | TIMESTAMPTZ | |
| expires_at | TIMESTAMPTZ | NULL = licencia perpetua |
| is_active | BOOLEAN | False cuando se revoca |
| max_activations | INT | Cuántas instalaciones puede activar esta key |
| notes | TEXT | Notas internas de cjhirashi |

### `license_activations`

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID PK | |
| license_key_id | UUID FK | |
| hardware_fingerprint | VARCHAR(512) | Hash del hardware del servidor donde se activó |
| activated_at | TIMESTAMPTZ | |
| last_validated_at | TIMESTAMPTZ | Última validación exitosa |
| hira_version | VARCHAR(20) | Versión de Hira en esa instalación |
| is_active | BOOLEAN | False si se desactiva esa instalación |

### `crash_reports`

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID PK | |
| product | ENUM | `server`, `studio` |
| hira_version | VARCHAR(20) | |
| module | VARCHAR(100) | Módulo donde ocurrió el crash |
| stack_trace_hash | VARCHAR(64) | SHA-256 del stack trace — para agrupar duplicados |
| stack_trace | TEXT | Stack trace sanitizado |
| occurrence_count | INT | Cuántas veces llegó este mismo error |
| first_seen_at | TIMESTAMPTZ | |
| last_seen_at | TIMESTAMPTZ | |
| is_reviewed | BOOLEAN | cjhirashi lo revisó |
| github_issue_url | VARCHAR(255) | Link al issue creado (nullable) |

### `hira_versions`

| Campo | Tipo | Descripción |
|---|---|---|
| id | UUID PK | |
| product | ENUM | `server`, `studio` |
| version | VARCHAR(20) | `v0.1.0` |
| release_notes | TEXT | Changelog público |
| docker_image_tag | VARCHAR(100) | Imagen en GHCR |
| is_latest | BOOLEAN | Solo uno por producto puede ser latest |
| released_at | TIMESTAMPTZ | |

---

## API v0.1 — Contratos

### `POST /api/licenses/validate`

Request:
```json
{
  "key": "HIRA-XXXX-XXXX-XXXX-XXXX",
  "hardware_fingerprint": "sha256-de-hardware",
  "product": "server",
  "version": "0.1.0"
}
```

Response 200:
```json
{
  "valid": true,
  "expires_at": "2027-07-24T00:00:00Z",
  "tier": "professional",
  "features": ["scada", "logic", "ai"],
  "trace_id": "abc123"
}
```

Response 403:
```json
{
  "valid": false,
  "reason": "key_revoked",
  "trace_id": "abc123"
}
```

### `POST /api/licenses/activate`

Primera activación de una key nueva.

Request:
```json
{
  "key": "HIRA-XXXX-XXXX-XXXX-XXXX",
  "hardware_fingerprint": "sha256-de-hardware",
  "product": "server",
  "version": "0.1.0"
}
```

Response 201: igual a `/validate` con `valid: true`
Response 409: `{"error": "max_activations_reached"}`

### `GET /api/updates/latest?product=server`

Response 200:
```json
{
  "product": "server",
  "latest_version": "0.1.2",
  "current_is_latest": false,
  "release_notes": "...",
  "docker_image_tag": "ghcr.io/hira/hira-server:0.1.2"
}
```

### `POST /api/crash-reports`

Request:
```json
{
  "product": "server",
  "version": "0.1.0",
  "module": "workers.polling_worker",
  "stack_trace": "Traceback (most recent call last):\n  ...",
  "license_key_prefix": "HIRA-XXXX"
}
```

Response 201: `{"received": true, "trace_id": "abc123"}`

### `GET /health`

Response 200:
```json
{
  "status": "ok",
  "services": {
    "postgres": "ok",
    "redis": "ok"
  },
  "version": "0.1.0",
  "trace_id": "abc123"
}
```

---

## Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://hub:pass@postgres:5432/hubdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=                  # min 32 chars — JWT del Panel Admin
ADMIN_EMAIL=cjhirashi@gmail.com
ADMIN_PASSWORD_HASH=         # bcrypt del password del Panel Admin
ENVIRONMENT=production
LOG_LEVEL=INFO
```

---

## Seguridad

| Aspecto | Implementación |
|---|---|
| License keys en tránsito | HTTPS con cert Let's Encrypt (Nginx) |
| License keys en BD | Almacenadas como hash bcrypt — nunca en claro |
| Rate limiting `/api/licenses/validate` | `limit_req_zone` Nginx — máx 10 req/min por IP |
| Rate limiting `/api/crash-reports` | Máx 100 req/hora por IP |
| Panel Admin `/admin/*` | JWT session — solo cjhirashi |
| Logs | Ninguna key ni dato sensible en logs (solo `key_prefix`) |

---

## Gate de Salida

- [x] Stack y versiones definidos
- [x] Modelos de BD completos
- [x] Contratos API v0.1 definidos
- [x] Variables de entorno documentadas
- [x] Estrategia de seguridad documentada
- [ ] Revisado y aprobado por Charlie
