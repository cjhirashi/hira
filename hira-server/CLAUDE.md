<!-- GENERADO por .harness/claude/build_claude.py — NO EDITAR A MANO.
     Editar los overlays en .harness/claude/ y volver a ejecutar el script. -->

# Ecosistema Hira — instrucciones base

Monorepo con tres componentes y un harness SDD-Anchored. **Antes de tocar código, lee
`.harness/method.md §2` (rúbrica) y `.harness/constitution.md`.**

## Los tres componentes

| Carpeta | Qué es | Corre en | Arquitectura |
|---|---|---|---|
| `hira-server/` | Núcleo SCADA (protocolos, alarmas, históricos, lógica, tiempo real) | Local / on-premise, con instalador | Hexagonal (`docs/hira-server/decisions/SRV-ADR-017`) |
| `hira-studio/` | Ingeniería y diseño de proyectos (configurador, lógica/pruebas, mimics, Agente Integrador) | Nube | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |
| `hira-hub/` | Licencias, crash reports, versiones, ventas, marketplace | Nube (VPS) | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |

Frontera: **Hub y Studio en la nube, Server local** (`E-ADR-001`). Los proyectos viven
siempre en un Hira Server.

## Reglas transversales (todas las apps)

1. **Spec-first.** Solo se implementa lo que está especificado (`docs/<producto>/spec/`
   para el diseño ya cerrado; `.harness/specs/<PRODUCTO>-NNN-slug/spec.md` para features
   nuevas). Lo no especificado → Directiva de Pausa (`.harness/method.md §5`) y se espera.
   No inventes diseño.
2. **Anclas.** Toda tarea cita las anclas que toca (`RF-`/ADR de producto) y los
   `AC-<COMP>-*` que deja verificables. Cada carpeta que creas lleva su `README.md`.
3. **Contract-First.** Endpoint nuevo → primero al contrato (`docs/contracts/` si es
   entre componentes, `<app>/docs/openapi.yaml` si es interno), luego el router.
4. **Observabilidad.** Logger JSON estructurado desde `core/logger.py`. Cero `print()` en
   producción. Todo log de un request lleva `trace_id` (middleware Correlation ID,
   header `X-Trace-ID`).
5. **Seguridad.** Secrets solo en variables de entorno. Nada de SQL por concatenación
   (ORM con parámetros). Ver el registro de vulnerabilidades de cada componente.
6. **READMEs.** Cada carpeta que creas lleva su `README.md` en el mismo paso.
7. **No edites un ADR aceptado.** Se supersede con uno nuevo.
8. **No resuelvas contradicciones de diseño por tu cuenta.** Directiva de Pausa
   (`.harness/method.md §5`) y esperar revisión humana.

## Commits

```
[<COMP>-Sprint-N][TIPO][MÓDULO] qué se hizo en imperativo · Anchors: <lista>
```

`<COMP>` = `SRV` | `HUB` | `STU`.
TIPO ∈ `CREA` `IMPL` `CONTRACT` `CONFIG` `TEST` `README` `FIX` `REFACTOR` `SECURITY` `SPEC` `ADR`.
Catálogo de MÓDULO por componente en su sección de abajo.
Fin del commit: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

## Definition of Done

Anclas citadas · contrato actualizado antes del router · cada `AC-*` con test que lo cita
y pasa · `.harness/gate/check.sh` en verde · tabla de cobertura de `tasks.md` al día ·
READMEs de las carpetas nuevas.

## Equipo de agentes

El orquestador (sesión principal) reparte a los especialistas de `.claude/agents/`, cada
uno dueño de un módulo con su rango de anclas como límite. Detalle:
`.harness/claude/ORCHESTRATION.md`.

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

1. `.harness/memory/state.md` — próximo paso y correcciones del usuario.
2. `docs/planning/ROADMAP.md` — track SRV; `.harness/specs/SRV-*/` — feature activa.
3. `docs/hira-server/spec/implementation-guide/` — estructura y decisiones de implementación.
4. `docs/hira-server/spec/modules/` — modelo de datos, APIs, esquema por módulo.
5. `docs/hira-server/spec/architecture/` y `docs/hira-server/decisions/` — el porqué.
6. `docs/hira-server/spec/ui-ux/` — antes de tocar frontend.
7. `docs/hira-server/spec/validation/` — criterios de aceptación (`AC-SRV-*`) y vulnerabilidades (`VUL-SRV-*`).

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
viven en `docs/contracts/` — no los dupliques, impórtalos/valídalos.

## Frontend (`hira-server/frontend/src/`)

Implementa lo de `docs/hira-server/spec/ui-ux/` — no inventa diseño. Vista no
especificada → Directiva de Pausa (`.harness/method.md §5`).

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
| Implementar vista no especificada en `ui-ux/` | Directiva de Pausa (`method.md §5`) y esperar |
| Escribir puntos de escaneo directo en `points` | Viola `SRV-ADR-012`/`SRV-ADR-019` |
| Reintroducir `HIRA_DEPLOY_MODE` / SQLite / árbol de rutas "Studio" | Superado por `E-ADR-001` |
| Implementar lógica de negocio sin Walking Skeleton validado | La infra base es prerrequisito |
