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
- **`SRV-001-walking-skeleton`** (primera feature real del ecosistema): Fase 1-3
  cerradas y aprobadas (`spec.md`/`plan.md` → `estado: approved`). Fase 4 en curso:
  **T-001..T-015 implementadas, verificadas por el `revisor` y commiteadas** (6
  commits en `main`, 37/37 tests, gate verde). Detalle de qué cubre cada tarea y su
  evidencia vive en `tasks.md` (tabla de Cobertura) y en los mensajes de commit — no
  se repite aquí (`method.md §10`, un canon por hecho).
- **Directiva de Pausa aplicada y aprobada** (2026-09-13): `adapters/factory.py` nace
  en T-015 (router) con placeholders in-memory, no en T-020 como preveía el plan
  original — `SRV-ADR-017` exige el punto de inyección desde que el router existe.
  Ver `plan.md §7`.
- Convención de commits fijada: Conventional Commits + `(RF-NNN)` en todo el
  ecosistema (se corrigió un overlay de `hira-server/AGENTS.md` que aún decía
  `[<COMP>-Sprint-N][TIPO][MÓDULO]`).
- **Siguiente paso:** T-016..T-018 (infra contenedores: compose, `mosquitto.conf`,
  `.env.example`, `nginx.conf`) → T-019..T-023 (adaptadores reales + seguridad,
  requieren Docker — confirmado disponible: `docker 29.7.2`, `compose v5.4.0`) →
  T-024/T-025 (e2e + gate) → T-026..T-030 (`[doc]`). Mismo flujo: `hira-infra`
  implementa por batch → `revisor` verifica → commit → siguiente.
