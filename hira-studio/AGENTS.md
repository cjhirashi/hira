<!-- GENERADO por .harness/claude/build_claude.py — NO EDITAR A MANO.
     Editar los overlays en .harness/claude/ y volver a ejecutar el script. -->

# Ecosistema Hira — instrucciones base

Monorepo con tres componentes y un harness SDD-Anchored. **Antes de tocar código, lee
`.harness/PROCESS.md`.**

## Los tres componentes

| Carpeta | Qué es | Corre en | Arquitectura |
|---|---|---|---|
| `hira-server/` | Núcleo SCADA (protocolos, alarmas, históricos, lógica, tiempo real) | Local / on-premise, con instalador | Hexagonal (`SRV-ADR-017`) |
| `hira-studio/` | Ingeniería y diseño de proyectos (configurador, lógica/pruebas, mimics, Agente Integrador) | Nube | Por definir (`spec/hira-studio/OPEN-QUESTIONS.md` SQ-4) |
| `hira-hub/` | Licencias, crash reports, versiones, ventas, marketplace | Nube (VPS) | Directa (`HUB-ADR-05`) |

Frontera: **Hub y Studio en la nube, Server local** (`E-ADR-001`). Los proyectos viven
siempre en un Hira Server.

## Reglas transversales (todas las apps)

1. **Spec-first.** Solo se implementa lo que está en `.harness/spec/`. Lo no especificado
   → `DEV-###` en `.harness/deviations/LOG.md` y se espera. No inventes diseño.
2. **Anclas.** Toda tarea cita `anchors:` (ADR/REQ) y los `AC-<COMP>-*` que deja
   verificables. Cada carpeta de módulo lleva `MODULE.md` con su frontmatter `anchors:`.
3. **Contract-First.** Endpoint nuevo → primero al contrato (`.harness/contracts/` si es
   entre componentes, `<app>/docs/openapi.yaml` si es interno), luego el router.
4. **Observabilidad.** Logger JSON estructurado desde `core/logger.py`. Cero `print()` en
   producción. Todo log de un request lleva `trace_id` (middleware Correlation ID,
   header `X-Trace-ID`).
5. **Seguridad.** Secrets solo en variables de entorno. Nada de SQL por concatenación
   (ORM con parámetros). Ver el registro de vulnerabilidades de cada componente.
6. **READMEs.** Cada carpeta que creas lleva su `README.md`/`MODULE.md` en el mismo paso
   (plantilla `.harness/templates/module-readme.md`).
7. **No edites un ADR aceptado.** Se supersede con uno nuevo.
8. **No resuelvas contradicciones de diseño por tu cuenta.** `DEV-###` y esperar.

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
y pasa · `.harness/ci/run_all.sh` en verde · `registry.yaml` actualizado · reporte de
sesión en `.harness/deviations/LOG.md` · READMEs de las carpetas nuevas.

## Equipo de agentes

El orquestador (sesión principal) reparte a los especialistas de `.claude/agents/`, cada
uno dueño de un módulo con su rango de anclas como límite. Detalle:
`.harness/claude/ORCHESTRATION.md`.

# Overlay — `hira-studio/`

Producto **cloud** de ingeniería y diseño de proyectos (`E-ADR-001`). Se accede por
navegador. **No se instala, no aloja proyectos, no es runtime SCADA.** Es un cliente de
ingeniería sobre uno o varios Hira Server remotos.

## Estado: diseño no cerrado

`hira-studio/` **no tiene sprint activo todavía.** Antes de implementar hay que resolver
`.harness/spec/hira-studio/OPEN-QUESTIONS.md` (SQ-1..SQ-8: auth cloud, conexión a
múltiples Servers, tenancy/hosting, backend propio, ejecución de lógica/Agente, multi-
proyecto en cloud, licenciamiento de Studio, modo offline/demos). Cada una se cierra con
un `STU-ADR-###` en `.harness/adr/hira-studio/`.

Si te piden implementar Studio y las OPEN-QUESTIONS relevantes siguen abiertas → dilo y
para. No improvises la arquitectura de Studio.

## Orden de lectura

1. `.harness/adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
2. `.harness/spec/hira-studio/context.md`
3. `.harness/spec/hira-studio/OPEN-QUESTIONS.md`
4. `.harness/spec/hira-studio/inherited-from-server.md` — qué diseño se hereda de Server.
5. `.harness/contracts/engineering-session.openapi.yaml` — `CT-engineering-session`.

## Contratos que consume

- `CT-engineering-session` (Studio → Server) — **único** camino para modificar un proyecto.
  Lock exclusivo por proyecto, heartbeat 60s, `409` si ocupado.
- `CT-license`, `CT-crash-report` (Studio → Hub) con `product: studio`.
- `CT-marketplace` (v0.3).

## Herencia de diseño

Configurador, edición de lógica/pruebas, mimics y Agente del Integrador se especifican
sobre la base de `.harness/spec/hira-server/` — ver el índice en
`inherited-from-server.md`. La **ejecución** de lógica/pruebas se queda en Server; Studio
edita y empuja vía la sesión de ingeniería (pendiente de cerrar SQ-5).

## Módulos para el commit (provisional — se afina con el diseño)

`INFRA` `BFF` `AUTH` `SERVERS` (gestión de conexiones a Servers) `CONFIGURATOR` `LOGIC`
`TESTS` `MIMICS` `AI` `PROJECTS` `CONTRACT` `FRONTEND`

## Reglas

Mismas transversales del ecosistema (`.harness/claude/ecosystem.md`): spec-first, anclas,
Contract-First, logger JSON, sin secrets en código, READMEs por carpeta, no editar ADRs
aceptados, no resolver contradicciones por tu cuenta.
