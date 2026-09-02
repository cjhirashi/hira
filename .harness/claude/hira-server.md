<!-- FUENTE del overlay de Hira Server. De-vaulteado de 7.1.9.3 - CLAUDE.md. -->

# Overlay — `hira-server/`

Plataforma SCADA on-premise para integradores de automatización de edificios (HVAC, BMS).
**Con instalador** (Docker Compose). Se conecta a Hira Hub (`CT-license`,
`CT-crash-report`, `CT-updates`) y recibe sesiones de ingeniería de Hira Studio
(`CT-engineering-session`).

Stack: FastAPI · PostgreSQL + TimescaleDB + pgvector · Redis · Celery · Mosquitto ·
React/TypeScript · Docker Compose.

> Tras `E-ADR-001`: **un solo perfil de despliegue** (producción). Se retiró
> `HIRA_DEPLOY_MODE`, el adaptador SQLite y las herramientas de ingeniería del frontend
> (migran a `hira-studio/`). Si un doc de `spec/hira-server/` todavía menciona el perfil
> `studio`/SQLite, gana `E-ADR-001` — registra `DEV-###`.

## Orden de lectura al iniciar sesión

1. `.harness/coordination/SPRINT.md` — sprint activo y tareas.
2. `.harness/coordination/ROADMAP.md` — track SRV.
3. `.harness/spec/hira-server/implementation-guide/` — estructura y decisiones de implementación.
4. `.harness/spec/hira-server/modules/` — modelo de datos, APIs, esquema por módulo.
5. `.harness/spec/hira-server/architecture/` y `.harness/adr/hira-server/` — el porqué.
6. `.harness/spec/hira-server/ui-ux/` — antes de tocar frontend.
7. `.harness/spec/hira-server/validation/` — criterios de aceptación (`AC-SRV-*`) y vulnerabilidades (`VUL-SRV-*`).

## Arquitectura — regla de oro (`SRV-ADR-017`)

```
core/ports/   → interfaces abstractas (Protocols de Python)
adapters/     → implementaciones concretas (PostgreSQL, BAC0, pymodbus, paho-mqtt, Redis)
services/     → lógica de negocio
```

**`services/` solo importa de `core/ports/`. Nunca de `adapters/`.** La implementación
concreta se inyecta vía `adapters/factory.py`. Si un módulo de `services/` importa
`psycopg2`, `sqlalchemy`, `BAC0`, `pymodbus` o `paho`, viola la arquitectura.

## Puntos — asociación explícita (`SRV-ADR-012`, `SRV-ADR-019`)

Un punto de escaneo es un **candidato** (`device_points_candidates`) hasta que se asocia
explícitamente a un registro en `points` con `access_mode` (`read`/`read_write`) y, si es
BACnet, `bacnet_write_priority`. Ningún candidato es escribible, historizable, alarmable ni
visible para el RAG. Nunca escribas un punto de escaneo directo en `points`.

## Contract-First

`hira-server/docs/openapi.yaml` es el contrato interno. Los contratos con Hub y Studio
viven en `.harness/contracts/` — no los dupliques, impórtalos/valídalos.

## Frontend (`hira-server/frontend/src/`)

Implementa lo de `.harness/spec/hira-server/ui-ux/` — no inventa diseño. Vista no
especificada → `DEV-###`.

- **Material Design 3 + Cyan.** No hardcodees hex: `var(--md-sys-color-*)`.
- **Tokens de alarma estables** (no cambian con el tema): `var(--hira-alarm-critical|high|medium|low)`, `var(--hira-status-ok|offline|writing)`.
- **Tema:** `localStorage` → `prefers-color-scheme`, aplicado antes del primer render.
- **Tiempo real sin polling** (`SRV-ADR-UI-03`): WebSocket, el cliente suscribe los puntos que ve.
- **Sidebar oculta módulos sin acceso** (`SRV-ADR-UI-02`) — la ocultación es UX; el backend igual rechaza con 403.
- Breakpoints MD3: Compact (sin Configurador ni Monaco) / Medium / Expanded.
- Componentes base en `components/`: `PointValue`, `AlarmBadge`, `DeviceStatusDot`, `LiveIndicator`, `ConnectionBanner`, `TrendChart` (Plotly), `MonacoEditor`.

## Módulos para el commit (`[<COMP>-Sprint-N][TIPO][MÓDULO]`)

`INFRA` `PORTS` `ADAPTERS` `ROUTERS` `SERVICES` `MODELS` `SCHEMAS` `WORKERS` `WEBSOCKET`
`LOGGER` `AUTH` `RBAC` `BACNET` `MQTT` `MODBUS` `SIMULATORS` `ALARMS` `HISTORICALS`
`LOGIC` `TESTS` `AI` `RAG` `BACKUP` `LICENSE` `PROJECTS` `FRONTEND` `SVG`

## Prohibiciones específicas

| No | Por qué |
|---|---|
| `print()` en producción | Usar `core/logger.py` |
| Importar infra en `services/` | Viola hexagonal — usar ports + inyección |
| SQL por concatenación | Inyección — ORM con parámetros |
| Hardcodear hex en componentes | `var(--md-sys-color-*)` / `var(--hira-alarm-*)` |
| Implementar vista no especificada en `ui-ux/` | `DEV-###` y esperar |
| Escribir puntos de escaneo directo en `points` | Viola `SRV-ADR-012`/`SRV-ADR-019` |
| Reintroducir `HIRA_DEPLOY_MODE` / SQLite / árbol de rutas "Studio" | Superado por `E-ADR-001` |
| Implementar lógica de negocio sin Walking Skeleton validado | La infra base es prerrequisito |
