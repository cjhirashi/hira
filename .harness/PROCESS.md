---
título: PROCESS — Harness SDD-Anchored del ecosistema Hira
tipo: Proceso
status: activo
última_actualización: 2026-09-02
---

# Proceso SDD-Anchored

**SDD** = Spec-Driven Development. **Anchored** = todo artefacto de código traza a un
identificador estable ("ancla") que vive en la especificación, y la deriva spec↔código
se detecta automáticamente antes de cada merge.

Este documento define cómo se desarrolla el ecosistema Hira. Es de lectura obligatoria
antes de tocar código en cualquiera de los tres componentes (`hira-server`, `hira-hub`,
`hira-studio`).

---

## 1. Piezas del harness

| Pieza | Qué es | Ruta |
|---|---|---|
| **Especificación** | La fuente de verdad del *qué* y el *por qué*. Solo se implementa lo que está aquí. | `.harness/spec/` |
| **ADRs** | Decisiones de arquitectura con contexto, alternativas y consecuencias. Inmutables — se superseden, no se editan. | `.harness/adr/` |
| **Registro de anclas** | Mapa `ancla → spec → código → tests → estado`. La columna vertebral. | `.harness/anchors/registry.yaml` |
| **Contratos** | API/eventos entre componentes. Fuente única. | `.harness/contracts/` |
| **Coordinación** | Roadmap del ecosistema y sprint(s) activo(s). | `.harness/coordination/` |
| **Gates de CI** | Scripts que fallan el build si hay deriva. | `.harness/ci/` |
| **Desviaciones** | Registro de "no se pudo implementar como se especifica". | `.harness/deviations/LOG.md` |
| **Instrucciones de agente** | `AGENTS.md` / `CLAUDE.md` (raíz y por app), generados de `.harness/claude/`. | `.harness/claude/` |

---

## 2. El ancla

Un ancla es un ID estable que aparece **a la vez** en la spec y en el código/tests que la
realizan. Convenciones completas en [`anchors/SCHEMA.md`](anchors/SCHEMA.md). Resumen:

| Prefijo | Significado |
|---|---|
| `E-ADR-###` | Decisión de ecosistema (gobierna ≥2 componentes) |
| `SRV-ADR-###`, `SRV-ADR-UI-##` | Decisión de Hira Server |
| `HUB-ADR-##` | Decisión de Hira Hub |
| `STU-ADR-###` | Decisión de Hira Studio |
| `REQ-<COMP>-###` | Requisito funcional |
| `AC-<COMP>-##[.n]` | Criterio de aceptación verificable |
| `VUL-<COMP>-###` | Vulnerabilidad / riesgo técnico con seguimiento |
| `CT-<nombre>` | Contrato entre componentes |

`<COMP>` ∈ `SRV` (server), `HUB` (hub), `STU` (studio).

Cada carpeta de módulo de código lleva un `MODULE.md` (plantilla en
`templates/module-readme.md`) cuyo frontmatter declara sus anclas:

```yaml
---
module: alarms
anchors: [SRV-ADR-005, AC-SRV-07, AC-SRV-07.1, VUL-SRV-005]
spec: .harness/spec/hira-server/modules/alarms-historicals.md
---
```

---

## 3. Ciclo de un sprint

Un sprint pertenece a un componente y se identifica `<COMP>-Sprint-N` (o `HUB-HN` para
los sprints históricos de Hub). El sprint activo vive en
[`coordination/SPRINT.md`](coordination/SPRINT.md).

```
1. PLANIFICAR   Cada tarea del sprint declara:
                  - anchors:  las anclas que toca (ADR, REQ)
                  - valida:   los AC-<COMP>-* que deja verificables
                Sin esas dos listas, la tarea no entra al sprint.

2. CONTRATO     Si la tarea añade o cambia un endpoint / evento:
                  - entre componentes  → primero a .harness/contracts/
                  - interno de una app → primero a <app>/docs/openapi.yaml
                Nunca al revés. Un endpoint que no está en el contrato no existe.

3. IMPLEMENTAR  Código que sigue el contrato y la spec. Cada carpeta nueva lleva su
                MODULE.md con las anclas. Commit con el formato de la sección 5.

4. VALIDAR      Un test por cada AC-<COMP>-* de la tarea. El test cita el ancla en su
                nombre o en un comentario (`# AC-SRV-07.1`).
                Se corre `.harness/ci/run_all.sh` — debe salir en verde.

5. CERRAR       - Actualizar registry.yaml: estado de las anclas tocadas.
                - Reporte de sesión (plantilla session-report.md) al final de
                  .harness/deviations/LOG.md — dice si funciona y si se probó.
                - Mover la tarea a coordination/sprint-history.md al cerrar el sprint.
```

---

## 4. Definition of Done

Una tarea está *hecha* cuando **todo** esto es cierto:

- [ ] Las anclas que toca están citadas en el código (`MODULE.md`) y en los commits.
- [ ] El contrato (`.harness/contracts/` o `<app>/docs/openapi.yaml`) está actualizado **antes** que el router.
- [ ] Cada `AC-<COMP>-*` de la tarea tiene ≥1 test que lo cita y pasa.
- [ ] `.harness/ci/run_all.sh` sale en verde (traceability + contract + lint).
- [ ] `registry.yaml` refleja el estado real de las anclas (`in-progress` → `implemented` → `verified`).
- [ ] Reporte de sesión escrito en `.harness/deviations/LOG.md`.
- [ ] Cada carpeta nueva tiene su `README.md` / `MODULE.md`.

---

## 5. Formato de commit

```
[<COMP>-Sprint-N][TIPO][MÓDULO] qué se hizo en imperativo · Anchors: <lista>
```

- `<COMP>` ∈ `SRV` | `HUB` | `STU`
- **TIPO** — `CREA` · `IMPL` · `CONTRACT` · `CONFIG` · `TEST` · `README` · `FIX` · `REFACTOR` · `SECURITY` · `SPEC` · `ADR`
- **MÓDULO** — nombre corto del módulo tocado (`INFRA`, `PORTS`, `ADAPTERS`, `ROUTERS`, `ALARMS`, `LICENSE`, …). Catálogo por componente en su overlay de `.harness/claude/`.
- **Anchors** — IDs separados por coma. Obligatorio salvo `CONFIG`/`README` puramente mecánicos.
- Si el commit resuelve una desviación: añadir `· Resuelve DEV-XXX` al final.

Un commit por módulo o funcionalidad cohesiva. El `README.md` en commit aparte con tipo `README`.

---

## 6. Contract-First

`.harness/contracts/` es la fuente única de los contratos **entre** componentes:

| Contrato | Dirección |
|---|---|
| `CT-license` (`license.openapi.yaml`) | server/studio → hub |
| `CT-crash-report` (`crash-report.openapi.yaml`) | server/studio → hub |
| `CT-updates` (`updates.openapi.yaml`) | server/studio → hub |
| `CT-engineering-session` (`engineering-session.openapi.yaml`) | studio ↔ server |
| `CT-marketplace` (`marketplace.openapi.yaml`) | studio/server → hub (v0.3) |

Flujo obligatorio:

1. Cambio de contrato → commit `[<COMP>-Sprint-N][CONTRACT][…]` sobre `.harness/contracts/`.
2. `.harness/ci/contract_gate.py` verifica que el `openapi.yaml` de cada app que implementa
   o consume ese contrato sigue siendo coherente.
3. Recién entonces se implementa el cliente/servidor.

Los contratos internos de cada app viven en `<app>/docs/openapi.yaml` y se rigen por la
misma regla (contrato antes que router).

---

## 7. Protocolo de desviaciones

Si algo **no** puede implementarse como se especifica, hay contradicción entre documentos,
o falta una decisión de diseño:

1. **No lo resuelvas por tu cuenta.**
2. Añade una entrada a [`deviations/LOG.md`](deviations/LOG.md) con la plantilla
   `templates/deviation.md` (ID `DEV-###`, tipo, contexto, qué necesita, qué bloquea,
   anclas afectadas).
3. Continúa con las demás tareas del sprint.
4. La decisión se toma como edición de spec o como ADR nuevo. Cuando se aplica y se
   valida, la entrada `DEV-###` se marca `Resuelta` con la referencia (commit / ADR / spec)
   — el histórico permanente queda en `LOG.md`.

Contradicción entre un ADR vigente y una necesidad nueva → **ADR nuevo que lo supersede**
(los ADRs no se editan), más el banner de supersesión en el ADR viejo.

---

## 8. Gates de CI (`.harness/ci/`)

| Gate | Falla si… |
|---|---|
| `traceability_gate.py` | `registry.yaml` no parsea · un ancla con `code:`/`tests:` apunta a ruta inexistente · un router declara un endpoint que no está en el `openapi.yaml` de su app · un `AC-*` en estado `verified` sin ≥1 test citado · un ADR con banner `superseded` está citado por código nuevo · el checksum de un archivo de `spec/` no coincide con `spec_checksum` |
| `contract_gate.py` | el `openapi.yaml` de una app diverge del contrato de `.harness/contracts/` que implementa/consume |
| `openapi_lint.py` | cualquier `*.openapi.yaml` (contratos o apps) no es OpenAPI 3.x válido |

`run_all.sh` los encadena. Es el comando que corre en CI y localmente antes de cerrar tarea.

---

## 9. Roles

- **Orquestador** (sesión principal de Claude Code): lee `SPRINT.md`, reparte a los
  especialistas, integra, corre los gates, cierra el sprint.
- **Especialistas de módulo** (`.claude/agents/`): cada uno dueño de un módulo, con su
  rango de anclas como límite de alcance. No tocan módulos ajenos — si necesitan un cambio
  fuera de su alcance, lo piden al orquestador.

Detalle en [`claude/ORCHESTRATION.md`](claude/ORCHESTRATION.md).

---

## 10. Qué NUNCA se hace

| Prohibición | Por qué |
|---|---|
| Implementar algo que no está en `.harness/spec/` | La spec es la fuente de verdad; lo no especificado se documenta como `DEV-###` y se espera |
| Resolver una contradicción de diseño por tu cuenta | Va a `deviations/LOG.md` o a un ADR nuevo |
| Editar un ADR aceptado | Se supersede con uno nuevo |
| Añadir un endpoint sin pasarlo antes por el contrato | Rompe Contract-First |
| Cerrar una tarea con un `AC-*` sin test que lo cite | Rompe la trazabilidad |
| Citar desde código nuevo un ADR marcado `superseded` | El gate de trazabilidad lo rechaza |
| Editar a mano `AGENTS.md` / `CLAUDE.md` | Se generan de `.harness/claude/` con `build_claude.py` |
