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

## Perfil de Despliegue

Un solo código base, un solo repositorio, **un solo perfil de despliegue** — producción,
PostgreSQL + TimescaleDB (+ pgvector cuando llegue el módulo de IA). `E-ADR-001` retiró
`HIRA_DEPLOY_MODE` y el perfil local ligero (`studio`, SQLite): Studio es hoy un producto
cloud independiente (`hira-studio/`), no un perfil de este repositorio. No reintroducir
`HIRA_DEPLOY_MODE`, `docker-compose.studio.yml` ni un adaptador SQLite.

## Árbol de Carpetas

Estructura real, verificada en `SRV-001-walking-skeleton` (T-001..T-023):

```
hira-server/
├── docker-compose.yml          # Compose base (único perfil — PostgreSQL/TimescaleDB, Redis, Mosquitto, backend, nginx)
├── docker-compose.dev.yml      # Override: hot reload, puertos expuestos para debug
├── .env.example                # Template de variables de entorno (sin valores reales)
│
├── docs/
│   └── openapi.yaml            # [CONTRACT-FIRST] Contrato de API — se define ANTES de implementar routers
│
├── backend/                    # Ver implementation-guide/guia-backend.md — Guía Backend
│   ├── Dockerfile
│   ├── requirements.txt        # Versiones exactas fijadas, sin rangos ^ ni ~
│   ├── main.py
│   ├── core/                   # config.py, logger.py, middleware.py, ports/ (Protocol)
│   ├── adapters/                # db/ (PostgreSQL), cache/ (Redis), mqtt/ (Mosquitto), factory.py
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   ├── websocket/
│   └── tests/                  # unit + tests/integration/ (contra contenedores reales)
│
├── frontend/                   # Ver implementation-guide/guia-frontend.md — Guía Frontend (stub en este sprint)
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│
├── mosquitto/
│   ├── mosquitto.conf           # allow_anonymous false, password_file
│   └── generate_password_file.sh
│
└── nginx/
    ├── nginx.conf
    └── ssl/                    # Certificados (no en repo)
```

Cada carpeta lleva su propio `README.md` (regla del arnés — sin `MODULE.md`).

## Prerrequisitos

- Docker Desktop (Windows) con WSL2 habilitado, o Docker Engine (Linux)
- Node.js 20 LTS (para desarrollo local del frontend sin Docker)
- Python 3.12 (para debug local del backend sin Docker)
- VS Code con extensiones: Python, ESLint, Prettier, Docker

## Levantar el Entorno de Desarrollo

```bash
git clone <repo>
cd hira-server

cp .env.example .env
# Editar .env con valores locales

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
# ─── Base de datos (único perfil — PostgreSQL + TimescaleDB) ─────────────────
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

- [x] Árbol de carpetas actualizado al perfil único de despliegue (`E-ADR-001`, sin `HIRA_DEPLOY_MODE`/SQLite)
- [x] Variables de entorno completas
- [ ] Revisado y aprobado por Charlie
