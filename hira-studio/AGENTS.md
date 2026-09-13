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

Features nuevas → **Conventional Commits** + sufijo con la ancla:

```
<tipo>(<scope>): qué se hizo en imperativo (RF-NNN)
```

`<tipo>` ∈ `feat` `fix` `refactor` `test` `docs` `chore` `security`.
`<scope>` = componente o módulo tocado — catálogo por componente en su sección de abajo.
Fin del commit: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

> Los commits previos a la reestructuración del arnés (`ADR-001`) usan
> `[<COMP>-Sprint-N][TIPO][MÓDULO] … · Anchors: <lista>` — convención histórica, **no
> se retroactiva**.

## Definition of Done

Anclas citadas · contrato actualizado antes del router · cada `AC-*` con test que lo cita
y pasa · `.harness/gate/check.sh` en verde · tabla de cobertura de `tasks.md` al día ·
READMEs de las carpetas nuevas.

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
| Arquitectura | SPA (React/TS, MD3+Cyan) + BFF FastAPI con PostgreSQL + Redis; **Hexagonal** (homogeneizada por `E-ADR-002`, supersede la sección de arquitectura de `STU-ADR-001`) | `STU-ADR-001`, `E-ADR-002` |
| Identidad | Un `integrator_user` por integrador (store en el BFF); JWT de sesión con `integrator_id` | `STU-ADR-002` |
| Licencia | Gestionada en Hub. Licencia de integrador (`product: studio`) enlazada al usuario, validada por `CT-license`. Sin licencia válida → **solo lectura** | `STU-ADR-002` |
| Conexión a Servers | **Emparejamiento por token** generado en el Server → credencial rotable, **cifrada** en Studio (`STUDIO_PAIRING_ENCRYPTION_KEY`) | `STU-ADR-003` |
| Ejecución | **Offline en Studio** (motor de simulación + sandbox RestrictedPython) para validar el diseño; **en línea siempre en el Server** | `STU-ADR-004` |
| Publicación | Serializar el borrador (`.hira` extendido) y cargarlo al Server por la sesión de ingeniería; simuladores → mapeo a dispositivos reales por escaneo | `STU-ADR-004` |
| Agente del Integrador | En el BFF de Studio, con la API key del integrador; tools offline/online/Hub; `ai_usage_log` propio. El Agente del Cliente se queda en Server | `STU-ADR-005` |

## Estado de implementación

**Falta la spec por módulo** (`docs/hira-studio/spec/` — auth, servers/pairing, projects,
configurator, offline-runner, publish, ai) y los `AC-STU-*` detallados (grupos
`AC-STU-01..06`, ver `tasks.md` de cada feature). Y falta que SRV exponga
`CT-engineering-session` **ampliado** (`REQ-CT-engsession-v2`: pair + publish +
consultas). Ver `docs/planning/ROADMAP.md`, track STU.

No arranques una feature de Studio hasta que exista la spec por módulo. Si un cambio
necesita tocar el contrato de la sesión de ingeniería y la ampliación aún no está,
Directiva de Pausa (`.harness/method.md §5`).

## Orden de lectura

1. `docs/decisions/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
2. `docs/hira-studio/spec/context.md` y `architecture.md`
3. `docs/hira-studio/decisions/STU-ADR-001..005`
4. `docs/hira-studio/spec/inherited-from-server.md` — qué diseño se hereda de Server.
5. `docs/contracts/engineering-session.openapi.yaml` — `CT-engineering-session` (+ ampliación pendiente).

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
