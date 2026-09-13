---
tipo: memoria
subtipo: state
actualizado: 2026-09-13
---

# Estado del arnés — ecosistema Hira

## ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)

### [2026-09-10] Toda feature de frontend pasa por el especialista `experto-ux-ui`
- **Qué pasó:** el usuario quiere que las interfaces de los 3 productos estén siempre
  bien diseñadas, profesionales y con excelente UX.
- **Corrección:** especialista `experto-ux-ui` añadido (`ADR-003`). Complementa a
  `hira-frontend` (que implementa): `experto-ux-ui` diseña y **revisa** la UX/UI.
  Interviene en Fase 1/2 (flujos, estados, `RF-` de UX contra el sistema de diseño
  `docs/hira-server/spec/ui-ux/`) y en Fase 4 (revisión contra estándar: WCAG AA,
  consistencia MD3+Cyan, accesibilidad, responsive, microcopy). Constitución Art. 8.
- **Cómo aplicar:** feature que toque interfaz → delega en `experto-ux-ui`; sin su
  sección de UX la spec no pasa el Gate 1. No escribe código de producción.

### [2026-09-04] Los 3 productos son Hexagonal, no solo hira-server
- **Qué pasó:** al confirmar la restructuración del arnés, el usuario aclaró que
  quiere Hexagonal en **los 3 productos**, no solo en `hira-server` (que ya lo era
  por `SRV-ADR-017`). `hira-studio` y `hira-hub` tenían "directa" por sus propios ADR
  (`STU-ADR-001`, `HUB-ADR-05`), con un argumento válido bajo ese criterio.
- **Corrección:** `E-ADR-002` homogeneiza a Hexagonal los 3 productos; supersede
  `HUB-ADR-05` (completo) y la sección de arquitectura de `STU-ADR-001` (el hosting/
  stack de esa decisión se mantiene). `constitution.md` Art. 1–2 actualizado con
  puertos/adaptadores para Studio y Hub.
- **Cómo aplicar:** cualquier `plan.md` de Studio o Hub debe diseñar por puertos
  (`core/ports/`), igual que Server — no "directa".

### [2026-09-04] Forzar la Fase 1 (corrección propagada desde cjhirashi-career)
- **Qué pasó:** en `cjhirashi-career` el arnés no forzaba Fase 1 ante "corrige esta
  falla" — faltaba el hook `Stop`, `CLAUDE.md` sin reglas duras, rúbrica sin rama para
  "esto es un rediseño". Ver `ADR-002`.
- **Cómo aplicar aquí:** añadido `.claude/settings.json` (hook Stop → gate), reglas
  duras en `CLAUDE.md`, y las dos ramas nuevas en `method.md §2`. Relevante en `hira`
  porque casi todo está "sin ancla" (fase de diseño) — eso no es luz verde.

### [2026-09-02] Studio es un producto cloud independiente, no un perfil de Server
- **Qué pasó:** el diseño previo (`SRV-ADR-015/016/017`) definía Server y Studio como un
  solo producto/instalador con `HIRA_DEPLOY_MODE=server|studio`.
- **Corrección del usuario:** Studio se reorganiza en 3 vertientes con frontera nube/local
  clara — Hub (nube), Studio (nube), Server (on-premise, con instalador).
- **Cómo aplicar:** `E-ADR-001` es la fuente de verdad; los 3 ADRs quedan con banner de
  supersesión parcial. `HIRA_DEPLOY_MODE` se retira de Server (un solo perfil de producción).

### [2026-09-04] El patrón de arquitectura no es uniforme entre productos
- **Qué pasó:** al reestructurar el arnés se confirmó con el usuario que **sí habrá
  arquitectura hexagonal** en este repo.
- **Corrección / matiz:** es **`hira-server`** el que es hexagonal (`SRV-ADR-017`, ya
  decidido desde julio). `hira-studio` y `hira-hub` usan arquitectura **directa**, por
  decisión propia y justificada (`STU-ADR-001`, `HUB-ADR-05`): un solo deployment target
  no justifica puertos/adaptadores.
- **Cómo aplicar:** no uniformar el patrón entre productos. El perfil de arquitectura de
  cada uno vive por separado en `constitution.md` Art. 2.

## Estado del backlog

- **Reestructuración del arnés al esquema simplificado completada** (2026-09-04). Ver
  `ADR-001`. Sin código todavía en `hira-server/`, `hira-studio/`, `hira-hub/` — fase de
  diseño (F0 cerrada: "diseño de plataforma de Hira Studio", SQ-1..SQ-8 resueltas).
- **Roadmap y sprint activo:** `docs/planning/ROADMAP.md` (3 tracks: SRV/HUB/STU),
  `docs/planning/SPRINT.md` (sprint detallado vigente antes de esta reestructuración —
  revisar si sigue siendo el siguiente paso real).
- **Bitácoras previas** (pre-restructuración, no re-narradas aquí): `docs/planning/sprint-history.md`,
  `docs/planning/hira-server-bitacora.md`, `docs/planning/hira-hub-bitacora.md`,
  `docs/planning/hira-hub-sprint-plan.md`.
- **Desviaciones históricas:** `docs/legacy/deviations/LOG.md` (DEV-000, resuelta →
  `E-ADR-001`; sin desviaciones abiertas al momento de la reestructuración).

## Decisiones tomadas (2026-09-04)

- Adoptar el esquema simplificado del arnés genérico (repo `harness`). `ADR-001`.
- Todo el corpus de especificación/ADRs/contratos/roadmap (~115 archivos) se relocalizó
  de `.harness/` a `docs/` (es documentación de producto, no del arnés — Constitución,
  separación estricta).
- Se retira el sistema de anclas paralelo (`anchors/registry.yaml` + checksums) y los
  gates de CI standalone (`contract_gate.py`, `openapi_lint.py`, `traceability_gate.py`):
  quedan en `docs/legacy/` como referencia; el anclaje simplificado (`covers` +
  `anchor_commit` en el front-matter de cada `spec.md`) los reemplaza.

## Decisiones tomadas (2026-09-13)

- **`ADR-004`** — refresco de rutas pendiente desde `ADR-001` en `.harness/claude/*.md`
  (5 overlays), los 16 especialistas de `.claude/agents/`, `README.md` raíz,
  `docs/contracts/README.md` y los 3 `README.md` de producto. `hira-hub`/`hub-infra`/
  `ORCHESTRATION.md` corregidos de "`HUB-ADR-05` directa" a **Hexagonal** (`E-ADR-002`,
  vigente desde 2026-09-04 pero no propagado a esos archivos). `build_claude.py` ya no
  genera la raíz (dejaba de estar en sincronía con el stub manual del `CLAUDE.md` raíz).
- **`MODULE.md` retirado** (resolvía un pendiente de `ADR-001`): cada carpeta nueva lleva
  solo `README.md`; el anclaje vive en `covers`/`tasks.md`, no en un frontmatter aparte.
- Regenerados `hira-{server,hub,studio}/{AGENTS,CLAUDE}.md` con `build_claude.py`
  (`--check` → "al día"). Gate verde tras la corrección.

## Obstáculos y desviaciones abiertas

- **Pendiente de decisión:** si `docs/planning/SPRINT.md` (el sprint SRV-Sprint-1 que
  estaba detallado antes de esta reestructuración) sigue siendo la prioridad, o si el
  operador quiere reconsiderar el orden ahora que el arnés cambió de forma.
- **Fuera de alcance de `ADR-004`:** el corpus de `docs/<producto>/spec/` (~40 archivos)
  tiene enlaces internos cruzados que siguen citando rutas pre-`ADR-001`
  (`.harness/spec/`, `.harness/adr/`, `.harness/ci/`, etc.). `ADR-001` ya decidió no
  reescribir ese corpus — es documentación de producto cerrada, no maquinaria del
  arnés. Si algún agente sigue uno de esos enlaces y encuentra 404, es una **doc de
  producto** desactualizada, no un problema del arnés — regla de raíz: no parchear el
  arnés para tapar esto, es un backlog de higiene documental de producto, separado.

## Próximo paso concreto

- Antes de tocar nada: `bash .harness/gate/check.sh`.
- **[2026-09-13] Primera feature real arrancada:** `SRV-001-walking-skeleton` (Walking
  Skeleton de Hira Server, ex `SRV-Sprint-1`). Fase 1 (Specify) cerrada — usuario
  confirmó "así es". `spec.md` en `.harness/specs/SRV-001-walking-skeleton/spec.md`,
  `estado: in-review`, `aprobaciones.fase_1` firmada. `[NEEDS CLARIFICATION] = 0`.
- De paso se corrigió drift de documentación: `docs/planning/ROADMAP.md` (ancla de
  `HUB-H0`) y `docs/hira-studio/spec/OPEN-QUESTIONS.md` (SQ-4) citaban "arquitectura
  directa / `HUB-ADR-05`" — desactualizado desde `E-ADR-002` (2026-09-04, homogeneiza a
  Hexagonal). Corregido a citar `E-ADR-002`.
- **Siguiente paso:** Fase 2 (Plan) de `SRV-001-walking-skeleton` con el agente
  `arquitecto` → `plan.md` conforme a `SRV-ADR-017` (Hexagonal) → Gate 2 (aprobación
  humana) → Fase 3 (Tasks) → Fase 4 (Implement, TDD, una tarea a la vez).
