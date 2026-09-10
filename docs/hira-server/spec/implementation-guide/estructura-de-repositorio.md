---
origen_vault: "7.1 - Hira Server/7.1.6 - Guías de Implementación/7.1.6.1 - Estructura de Repositorio.md"
título: Estructura de Repositorio — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Guías de Implementación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, repositorio, docker]
---

## Perfiles de Despliegue

Un solo código base, un solo repositorio (ver SRV-ADR-015). `HIRA_DEPLOY_MODE` distingue el perfil de despliegue, no un producto distinto (ver SRV-ADR-017):

| Valor | Perfil | Base de datos | Uso típico |
|---|---|---|---|
| `server` | Producción | PostgreSQL + TimescaleDB + pgvector | Instalación comercial del cliente, o instalación local del integrador cuando quiere el stack completo |
| `studio` | Local ligero | SQLite | Instalación local del integrador — diseño offline, multi-proyecto, simuladores |

## Árbol de Carpetas

```
hira/
├── docker-compose.yml          # Compose base (perfil server — PostgreSQL, stack completo)
├── docker-compose.dev.yml      # Override: hot reload, puertos expuestos para debug
├── docker-compose.prod.yml     # Override: restart policies, sin puertos extra
├── docker-compose.studio.yml   # Override: HIRA_DEPLOY_MODE=studio, SQLite, sin TimescaleDB
├── .env.example                # Template de variables de entorno (sin valores reales)
├── .gitignore
│
├── docs/
│   └── openapi.yaml            # [CONTRACT-FIRST] Contrato de API — se define ANTES de implementar routers
│
├── backend/                    # Ver .harness/spec/hira-server/implementation-guide/guia-backend.md - Guía Backend
│   ├── Dockerfile
│   ├── requirements.txt        # Versiones exactas fijadas, sin rangos ^ ni ~
│   ├── main.py
│   ├── core/
│   ├── adapters/
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   └── websocket/
│
├── frontend/                   # Ver .harness/spec/hira-server/implementation-guide/guia-frontend.md - Guía Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│
└── nginx/
    ├── nginx.conf
    └── ssl/                    # Certificados (no en repo)
```

## Prerrequisitos

- Docker Desktop (Windows) con WSL2 habilitado, o Docker Engine (Linux)
- Node.js 20 LTS (para desarrollo local del frontend sin Docker)
- Python 3.12 (para debug local del backend sin Docker)
- VS Code con extensiones: Python, ESLint, Prettier, Docker

## Levantar el Entorno de Desarrollo

```bash
git clone <repo>
cd hira

cp .env.example .env.development
# Editar .env.development con valores locales

docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Accesos en desarrollo:
# Frontend:  http://localhost:5173
# API:       http://localhost:8000
# API docs:  http://localhost:8000/docs
# Redis:     localhost:6379
# PostgreSQL: localhost:5432
```

## Variables de Entorno

```env
# ─── Perfil de despliegue ─────────────────────────────────────────────────────
# server  — PostgreSQL + TimescaleDB + pgvector, dispositivos reales, multi-usuario
# studio  — Local ligero: SQLite, sin TimescaleDB, pensado para multi-proyecto (SRV-ADR-020)
HIRA_DEPLOY_MODE=server

# ─── Base de datos ───────────────────────────────────────────────────────────
# Perfil server: postgresql+asyncpg://hira:hira@postgres:5432/hiradb
# Perfil studio: sqlite+aiosqlite:///./hira_local.db
DATABASE_URL=postgresql+asyncpg://hira:hira@postgres:5432/hiradb

# ─── Servicios ───────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0
SECRET_KEY=                     # min 32 chars, aleatorio
AI_ENCRYPTION_KEY=              # min 32 chars, para cifrar API keys de IA
LICENSE_KEY=                    # DEMO-MODE en desarrollo
CORS_ORIGINS=                   # http://localhost:5173 en dev, dominio real en prod
MQTT_BROKER_HOST=mosquitto
MQTT_USER=hira
MQTT_PASSWORD=

# ─── Hub (validación de licencia y crash reports) ────────────────────────────
HUB_API_URL=https://hub.hira.cjhirashi.com
HUB_API_KEY=
CRASH_REPORTER_ENABLED=false    # true en producción si el integrador consiente

# ─── Notificaciones ───────────────────────────────────────────────────────────
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=

# ─── IA (opcional, también configurable desde el panel) ──────────────────────
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ─── Entorno ───────────────────────────────────────────────────────────────
ENVIRONMENT=development         # development | production
LOG_LEVEL=INFO                  # DEBUG en desarrollo
```

## Simulación BACnet en Desarrollo

BAC0 permite crear un dispositivo BACnet simulado en la misma máquina. El script `scripts/bacnet_simulator.py` levanta un dispositivo simulado con puntos HVAC típicos (temperatura de sala, setpoint, estado de ventilador, posición de compuerta) para desarrollo sin hardware real.

---

## Gate de Salida

- [x] Árbol de carpetas actualizado a perfiles de despliegue (no productos separados)
- [x] Variables de entorno completas
- [ ] Revisado y aprobado por Charlie
