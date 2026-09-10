---
tipo: memoria
subtipo: history
---

# Bitácora del arnés — ecosistema Hira

Append-only, orden cronológico inverso (lo más reciente arriba). Una entrada
Session-End por sesión, con el formato fijo de `method.md §10`. Las bitácoras
**previas** a esta reestructuración (siembra del harness, sprints F0) viven en
`docs/planning/sprint-history.md` y `docs/planning/*-bitacora.md` — no se re-narran aquí.

```markdown
## [YYYY-MM-DD] <feature o tema> — <resultado>
- **Fase alcanzada:** specify | plan | tasks | implement | verified | (prompt-directo)
- **Rebotes del verificador:** <n>
- **Directiva de Pausa:** no | sí (<qué asunción, cómo se resolvió de raíz>)
- **Drift / re-anchor:** no | sí (<specs afectadas>)
- **Anclas movidas:** <spec → commit> | ninguna
- **Gate:** verde | cerrado por <bloque> (<detalle>)
- **Docs actualizadas:** <lista> | ninguna
- **Decisiones de diseño / límites de integración:** <1-3 líneas>
- **Próximo paso:** <acción concreta>
```

---

## [2026-09-10] Especialista `experto-ux-ui` añadido al arnés — ADR-003

- **Fase alcanzada:** (mantenimiento del arnés — no aplica ciclo de feature)
- **Gate:** verde
- **Docs actualizadas:** `.claude/agents/experto-ux-ui.md` (nuevo),
  `.claude/agents/README.md`, `AGENTS.md`, `.harness/constitution.md` Art. 8 + historial,
  `.harness/decisions/ADR-003-especialista-ux-ui.md` (nuevo)
- **Decisiones de diseño:** el usuario quiere UX/UI profesional y consistente en las
  interfaces de los 3 productos. `experto-ux-ui` (sonnet) diseña y revisa; complementa a
  `hira-frontend` (implementa). Revisión de UX/UI obligatoria antes de `verified` para
  features de interfaz. Sistema de diseño de referencia: `docs/hira-server/spec/ui-ux/`.
  Propagado a `cjhirashi-career` y al `reference/`.
- **Próximo paso:** ninguno; aplica cuando arranque la implementación de frontend.

---

## [2026-09-04] Homogeneizar a Hexagonal los 3 productos — E-ADR-002

- **Fase alcanzada:** (decisión de arquitectura registrada por ADR — no aplica ciclo de feature)
- **Rebotes del verificador:** 0
- **Directiva de Pausa:** no
- **Drift / re-anchor:** sí — cambia el perfil de arquitectura (Constitución Art. 1–2)
- **Anclas movidas:** ninguna (sin código todavía)
- **Gate:** verde
- **Docs actualizadas:** `docs/decisions/ecosystem/E-ADR-002-*` (nuevo),
  `docs/hira-hub/decisions/HUB-ADR-05-*` (banner superseded),
  `docs/hira-studio/decisions/STU-ADR-001-*` (banner parcialmente superseded),
  `.harness/constitution.md` Art. 1–3, `AGENTS.md`
- **Decisiones de diseño / límites de integración:**
  - El usuario confirmó: quiere Hexagonal en **los 3 productos**, no solo
    `hira-server`. `hira-studio` y `hira-hub` pasan de "directa" a Hexagonal.
  - `hira-hub`: puertos `LicenseStoragePort`, `CrashReportPort`,
    `UpdateDistributionPort`, `NotificationPort`, `PaymentPort` (reservado).
  - `hira-studio`: puertos `ProjectStoragePort`, `PairingPort`,
    `EngineeringSessionPort`, `LicensePort`, `SimulationPort`.
  - El hosting/tenancy y el stack de `STU-ADR-001` **no cambian** — solo su sección de
    arquitectura interna.
  - Coste aceptado explícitamente por el propietario: Hub y Studio ganan superficie de
    mantenimiento que su criterio original no justificaba por sí solo; se acepta a
    cambio de consistencia entre los 3 codebases.
- **Próximo paso:** ninguno bloqueante; el perfil queda fijado para cuando arranque
  la implementación de cada producto.

---

## [2026-09-04] Corrección de diseño del arnés (propagada desde cjhirashi-career)

- **Fase alcanzada:** (mantenimiento del arnés — no aplica ciclo de feature)
- **Gate:** verde
- **Docs actualizadas:** `CLAUDE.md`, `.harness/method.md §2`, `.claude/settings.json`
  (nuevo), `.harness/decisions/ADR-002-*`
- **Decisiones de diseño:** en `cjhirashi-career` se detectó que el arnés no forzaba
  Fase 1 ante "corrige fallas" (faltaba el hook `Stop`, `CLAUDE.md` sin reglas duras,
  rúbrica sin rama de "rediseño"). Corrección propagada aquí preventivamente,
  relevante porque casi todo `hira` está sin ancla (fase de diseño). Ver `ADR-002`.
- **Próximo paso:** ninguno específico; aplica desde ahora.

---

## [2026-09-04] Reestructuración del arnés al esquema simplificado — completada

- **Fase alcanzada:** (reestructuración de la maquinaria — no aplica ciclo de feature)
- **Rebotes del verificador:** 0
- **Directiva de Pausa:** no
- **Drift / re-anchor:** no aplica (sin código ni specs de feature todavía)
- **Anclas movidas:** ninguna
- **Gate:** `.harness/gate/check.sh` — pendiente de primera corrida
- **Docs actualizadas:** relocalizado TODO el corpus de especificación/ADRs/contratos/
  roadmap (~115 archivos) de `.harness/` a `docs/` (ver `docs/README.md` para el mapa
  completo old→new)
- **Decisiones de diseño / límites de integración:**
  - Adoptado el esquema simplificado del arnés genérico (repo `harness`): `constitution.md`
    (12 artículos, perfil de arquitectura **por producto** — 3 perfiles), `method.md`
    (1 archivo, agnóstico), `memory/{state.md,history.md}`, `gate/check.sh` (genérico) +
    `gate/project.sh`, `specs/_template/` (3 archivos).
  - **Separación estricta aplicada:** el corpus de diseño (spec/ecosistema, spec/producto,
    ADRs de producto, contratos, roadmap, glosario) es documentación de **producto**, no
    del arnés → movido a `docs/` organizado por producto (`docs/ecosystem/`,
    `docs/hira-server/`, `docs/hira-studio/`, `docs/hira-hub/`, `docs/decisions/ecosystem/`,
    `docs/contracts/`, `docs/planning/`).
  - **Perfiles de arquitectura registrados tal como ya estaban decididos** (Génesis =
    registro de ADRs existentes, no elección de cero): `hira-server` = **hexagonal**
    (`SRV-ADR-017`); `hira-studio` = **directa** (`STU-ADR-001`); `hira-hub` = **directa**
    (`HUB-ADR-05`). Confirmado con el usuario: la asimetría es deliberada, no un error.
  - **Retirado el sistema de anclas paralelo** (`anchors/registry.yaml` + checksums +
    `check_traceability.py`/`spec_checksum.py`) y los **gates de CI standalone**
    (`contract_gate.py`, `openapi_lint.py`, `traceability_gate.py`, `run_all.sh`):
    redundantes con el anclaje simplificado (`covers`/`anchor_commit` en el front-matter
    de `spec.md`). Conservados sin editar en `docs/legacy/anchors-system/` y
    `docs/legacy/ci-scripts/` por si hace falta consultarlos.
  - **Conservado `.harness/claude/`** (genera `AGENTS.md`/`CLAUDE.md` por producto vía
    `build_claude.py`) — es maquinaria del arnés, no documentación. Sus fuentes siguen
    apuntando a rutas viejas; actualizarlas es tarea pendiente antes de regenerar.
  - **Plantillas legacy** (`templates/adr.md`, `deviation.md`, `module-readme.md`,
    `requirement.md`, `session-report.md`, `sprint.md`) → `docs/legacy/templates/`,
    superseded por `specs/_template/` + `decisions/ADR-000-template.md` (falta crearlo).
  - **Agentes:** añadidos los 6 base (`orquestador`, `autor-de-spec`, `arquitecto`,
    `implementador`, `revisor`, `explorador`) en `.claude/agents/`. Los 16 especialistas de
    módulo pre-existentes (`hira-*`, `hub-*`) se **conservan sin refrescar** — referencian
    rutas retiradas; actualizar antes de invocarlos.
- **Próximo paso:** el operador corre el gate, confirma si se retoma `docs/planning/SPRINT.md`
  o se re-prioriza, y decide cuándo refrescar los 16 especialistas de módulo y las fuentes
  de `.harness/claude/`.
