---
tipo: memoria
subtipo: state
actualizado: 2026-09-04
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

## Decisiones tomadas (esta sesión)

- Adoptar el esquema simplificado del arnés genérico (repo `harness`). `ADR-001`.
- Todo el corpus de especificación/ADRs/contratos/roadmap (~115 archivos) se relocalizó
  de `.harness/` a `docs/` (es documentación de producto, no del arnés — Constitución,
  separación estricta).
- Se retira el sistema de anclas paralelo (`anchors/registry.yaml` + checksums) y los
  gates de CI standalone (`contract_gate.py`, `openapi_lint.py`, `traceability_gate.py`):
  quedan en `docs/legacy/` como referencia; el anclaje simplificado (`covers` +
  `anchor_commit` en el front-matter de cada `spec.md`) los reemplaza.
- `.harness/claude/` (generador de `AGENTS.md`/`CLAUDE.md` por producto) **se conserva**
  — es maquinaria del arnés. Pendiente: actualizar sus fuentes a los `docs/` nuevos antes
  de volver a `build_claude.py`.

## Obstáculos y desviaciones abiertas

- **Pendiente de decisión:** si `docs/planning/SPRINT.md` (el sprint SRV-Sprint-1 que
  estaba detallado antes de esta reestructuración) sigue siendo la prioridad, o si el
  operador quiere reconsiderar el orden ahora que el arnés cambió de forma.
- **`.claude/agents/`:** hay 16 especialistas de módulo pre-diseñados (`hira-*`, `hub-*`)
  que referencian rutas retiradas (`.harness/ci/run_all.sh`, `registry.yaml`,
  `.harness/coordination/SPRINT.md`). **No se han refrescado en esta sesión** (fuera de
  alcance de la reestructuración del arnés) — hacerlo antes de invocarlos.
- **`.harness/claude/*.md`** (fuentes de los `AGENTS.md`/`CLAUDE.md` por producto) también
  referencian rutas viejas de `.harness/spec/`, `.harness/adr/` — actualizar antes de
  correr `build_claude.py` de nuevo.

## Próximo paso concreto

- Antes de tocar nada: `bash .harness/gate/check.sh`.
- El operador confirma si se retoma `docs/planning/SPRINT.md` o se re-prioriza.
- Cuando arranque la primera feature real: aplicar la rúbrica (`method.md §2`); Fase 1 =
  elicitación interactiva con `autor-de-spec`.
