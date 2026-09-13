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

## [2026-09-13] SRV-002-auth-rbac — implemented

- **Fase alcanzada:** implement (40/40 tareas, T-001..T-040)
- **Rebotes del verificador:** 2 — (1) durante la investigación de la
  Directiva de Pausa de RNF-001, la primera solución propuesta ("solo migrar
  a ASGI puro") resultó insuficiente al medirla con la lógica real (~29ms,
  seguía sobre el umbral) — el revisor la rebotó con evidencia propia antes de
  aceptar el diseño completo; (2) el batch de cierre (T-029..T-031) fue
  rebotado porque el contenido de las 3 tareas estaba bien pero faltaba el
  protocolo de Session-End (`estado`, `anchor_commit`, esta entrada,
  `state.md`) — responsabilidad del coordinador, no del implementador.
- **Directiva de Pausa:** sí, 1 — `RNF-001` (middleware RBAC <5ms, 100
  concurrentes) medía ~54ms por 2 causas aditivas confirmadas de forma
  independiente en 2 rondas de revisor: el piso propio de
  `starlette.middleware.base.BaseHTTPMiddleware` (~20-36ms sin lógica) y el
  round-trip real a Redis por request en *cache-hit* (~27-30ms, persiste sin
  middleware). Solución de raíz aprobada por Carlos: middleware ASGI puro +
  `LocalPermissionsCache` (caché en memoria del proceso, TTL 30s) con
  invalidación por *pub/sub* de Redis. Verificado real: overhead final
  ~0.1ms, confirmado en 5 corridas independientes por 2 rondas de revisor
  contra Postgres/Redis reales. RF-006 (`spec.md`) ganó una nota de semántica
  *best-effort* entre procesos/réplicas, confirmada por Carlos.
- **Drift / re-anchor:** no (primer anclaje de la feature)
- **Anclas movidas:** `SRV-002-auth-rbac` → `f8157ed6efb7668b90c3dd4a61a97a2616301cf3`
- **Gate:** verde (21 ok · 1 warn preexistente — `spectral` no instalado)
- **Docs actualizadas:** `hira-server/docs/openapi.yaml` (ampliado, `GET
  /health` de `SRV-001` intacto); `hira-server/README.md` (paso operativo
  Alembic); `docs/hira-server/spec/modules/auth-rbac-seguridad.md`
  ("Superusuario" → "Admin", MVP de 3 roles fijos); `docs/hira-server/spec/
  validation/vulnerabilities.md` (`VUL-SRV-004` 🟡→🟢); `docs/decisions/
  ecosystem/E-ADR-003-convencion-rfc9457-type.md` (nuevo, aplica a los 3
  productos, no solo a esta feature).
- **Decisiones de diseño / límites de integración:** MVP de `SRV-ADR-005`
  (3 roles fijos: Admin/Operador/Visor; RBAC dinámico completo queda para
  v0.2). `UserRepositoryPort` nuevo (no se fuerza en `DatabasePort`, que sigue
  siendo *liveness*-only). `CachePort` ampliado con key-value genérico +
  `publish`/`subscribe` (mismo puerto, no uno nuevo). Autenticación como
  middleware ASGI puro + autorización fina como `Depends()` (Starlette no
  resuelve *path params* antes del middleware ASGI). Sobre RFC 9457
  formalizado como convención de ecosistema (`E-ADR-003`). Solo backend/
  contrato — la vista de login queda para el sprint de frontend con
  `experto-ux-ui`.
- **Próximo paso:** decidir con el usuario la siguiente feature real —
  `SRV-Sprint-3` (protocolos BACnet/Modbus/MQTT + simuladores, sigue el orden
  del roadmap sobre Server) o `HUB-H0` (Walking Skeleton de Hira Hub, puede
  arrancar en paralelo). Aprobación humana final de `estado: verified`
  pendiente (Gate 4) — el orquestador no se autoaprueba.

---

## [2026-09-13] SRV-001-walking-skeleton — implemented

- **Fase alcanzada:** implement (30/30 tareas, T-001..T-030)
- **Rebotes del verificador:** 5 (RF-003 sin matiz + drift de `covers` en T-001..T-007;
  secuenciación de `adapters/factory.py` en T-013..T-015; RF-008 código muerto en
  T-019..T-023; higiene de tests en el mismo batch; `check.sh --full` cerraba la
  compuerta sin Docker en T-024..T-030)
- **Directiva de Pausa:** sí, 2 — (1) `adapters/factory.py` nace en el router (T-015),
  no en T-020 como ataba el plan aprobado: `SRV-ADR-017` exige el punto de inyección
  desde que el router existe; (2) `MosquittoAdapter.connect()` no se invocaba en
  ningún camino real (backoff de RF-008 era código muerto): se amplió T-022 para
  invocarlo en el `lifespan` de `main.py`, sin abortar el arranque si falla. Ambas
  documentadas en `plan.md §7`, revisadas por *git diff* y aprobadas por Carlos antes
  de reanudar.
- **Drift / re-anchor:** no (primer anclaje de la feature, no un re-anchor)
- **Anclas movidas:** `SRV-001-walking-skeleton` → `b4248e749d6a9eceaa68b9f117b79116222c1eb9`
- **Gate:** verde (19 ok · 1 warn preexistente — `spectral` no instalado)
- **Docs actualizadas:** `docs/planning/ROADMAP.md`, `docs/hira-studio/spec/OPEN-QUESTIONS.md`
  (drift `HUB-ADR-05`/"directa" → `E-ADR-002`, detectado al arrancar);
  `docs/hira-server/spec/implementation-guide/{estructura-de-repositorio.md,guia-backend.md}`
  (retirado `HIRA_DEPLOY_MODE`/perfil `studio`/SQLite); `docs/planning/SPRINT.md`
  (banner superseded); `hira-server/README.md`; `docs/hira-server/spec/validation/
  vulnerabilities.md` (`VUL-SRV-001` 🟡→🟢); `.harness/gate/check.sh` (fix: excluir
  `-m integration` del bloque 5 por defecto — gap genérico del arnés, no solo de esta
  feature); overlays `.harness/claude/{ecosystem,hira-server}.md` (convención de
  commits: Conventional Commits + `(RF-NNN)`, no el formato con corchetes).
- **Decisiones de diseño / límites de integración:** Walking Skeleton de Hira Server
  por puertos/adaptadores (`SRV-ADR-017`) — núcleo puro (`aggregate_status`),
  coordinación (`health_service.get_health`, timeout 2s/servicio, nunca cuelga),
  3 adaptadores reales (Postgres/Redis/Mosquitto) verificados contra contenedores
  reales, no mocks. `VUL-SRV-001` (Mosquitto sin auth, crítico) resuelto en el mismo
  sprint, no diferido. `GET /health` siempre HTTP 200 (detalle en el body, sin sobre
  RFC 9457 — es monitoreo, no negocio).
- **Próximo paso:** decidir con el usuario si sigue `SRV-Sprint-2` (Auth + RBAC
  dinámico) o `HUB-H0` (Walking Skeleton de Hira Hub, puede correr en paralelo).
  Aprobación humana final de `estado: verified` sigue pendiente (Gate 4) — el
  orquestador no se autoaprueba.

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
