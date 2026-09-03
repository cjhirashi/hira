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
navegador. **No se instala.** Guarda **borradores de diseño offline**; el proyecto que
opera vive en un Hira Server, al que Studio lo **publica**.

## Diseño de plataforma — CERRADO (`STU-ADR-001..005`, 2026-09-03)

| Tema | Decisión | ADR |
|---|---|---|
| Hosting | Instancia multi-tenant única junto a Hub; aislamiento por `integrator_id` | `STU-ADR-001` |
| Arquitectura | SPA (React/TS, MD3+Cyan) + BFF FastAPI con PostgreSQL + Redis; **estructura directa** (como `HUB-ADR-05`) | `STU-ADR-001` |
| Identidad | Un `integrator_user` por integrador (store en el BFF); JWT de sesión con `integrator_id` | `STU-ADR-002` |
| Licencia | Gestionada en Hub. Licencia de integrador (`product: studio`) enlazada al usuario, validada por `CT-license`. Sin licencia válida → **solo lectura** | `STU-ADR-002` |
| Conexión a Servers | **Emparejamiento por token** generado en el Server → credencial rotable, **cifrada** en Studio (`STUDIO_PAIRING_ENCRYPTION_KEY`) | `STU-ADR-003` |
| Ejecución | **Offline en Studio** (motor de simulación + sandbox RestrictedPython) para validar el diseño; **en línea siempre en el Server** | `STU-ADR-004` |
| Publicación | Serializar el borrador (`.hira` extendido) y cargarlo al Server por la sesión de ingeniería; simuladores → mapeo a dispositivos reales por escaneo | `STU-ADR-004` |
| Agente del Integrador | En el BFF de Studio, con la API key del integrador; tools offline/online/Hub; `ai_usage_log` propio. El Agente del Cliente se queda en Server | `STU-ADR-005` |

## Estado de implementación

**Falta la spec por módulo** (`spec/hira-studio/` — auth, servers/pairing, projects,
configurator, offline-runner, publish, ai) y los `AC-STU-*` detallados (grupos
`AC-STU-01..06` ya en el registry). Y falta que SRV exponga `CT-engineering-session`
**ampliado** (`REQ-CT-engsession-v2`: pair + publish + consultas). Ver
`.harness/coordination/ROADMAP.md`, track STU.

No arranques `STU-Sprint-1` hasta que exista la spec por módulo. Si un cambio necesita
tocar el contrato de la sesión de ingeniería y la ampliación aún no está, regístralo como
`DEV-###`.

## Orden de lectura

1. `.harness/adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
2. `.harness/spec/hira-studio/context.md` y `architecture.md`
3. `.harness/adr/hira-studio/STU-ADR-001..005`
4. `.harness/spec/hira-studio/inherited-from-server.md` — qué diseño se hereda de Server.
5. `.harness/contracts/engineering-session.openapi.yaml` — `CT-engineering-session` (+ ampliación pendiente).

## Contratos que consume

- `CT-engineering-session` (Studio → Server) — **único** canal hacia un Server: sesión con
  lock por proyecto, emparejamiento, publicación de proyecto, consultas del agente.
- `CT-license`, `CT-crash-report` (Studio → Hub) con `product: studio`.
- `CT-marketplace` (v0.3).

## Herencia de diseño

Configurador, modelo de puntos/asociaciones, API `hira` de scripts y formato de mimic se
**especifican en `spec/hira-server/`**; Studio los **implementa**, no los redefine. El
`offline-runner` implementa el mismo contrato de la API `hira` y las mismas restricciones
de RestrictedPython que el Server. Índice: `inherited-from-server.md`.

## Módulos para el commit

`INFRA` `CORE` `AUTH` `SERVERS` `PROJECTS` `CONFIGURATOR` `OFFLINE-RUNNER` `PUBLISH`
`AI` `MIMICS` `CONTRACT` `FRONTEND`

## Reglas

Transversales del ecosistema (`.harness/claude/ecosystem.md`). Además:
- Todo acceso a datos del BFF filtra por `integrator_id` del JWT — es la frontera de
  aislamiento (`AC-STU-02`). No hay endpoint que devuelva datos de otro integrador.
- Credenciales de emparejamiento: cifradas en reposo, nunca en logs, nunca al SPA.
- El `offline-runner` nunca toca un Server ni un dispositivo real.
