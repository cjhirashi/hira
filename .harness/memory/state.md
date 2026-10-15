---
tipo: memoria
subtipo: state
actualizado: 2026-10-15
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

- **Reestructuración del arnés al esquema simplificado** (2026-09-04, `ADR-001`) y
  refresco de rutas (2026-09-13, `ADR-004`) — completos. Convención de commits:
  Conventional Commits + `(RF-NNN)` (corregido un overlay que aún decía el formato
  histórico con corchetes).
- **`SRV-001-walking-skeleton` — `estado: implemented`.** Primera feature real del
  ecosistema, ciclo completo Fase 1→4 (30/30 tareas, `T-001..T-030`), verificada por
  el `revisor` en cada batch, ancla movida a `b4248e749d6a9eceaa68b9f117b79116222c1eb9`.
  Incluyó 2 Directivas de Pausa (secuenciación de `adapters/factory.py`; wiring de
  `MosquittoAdapter.connect()` en el `lifespan`) y un fix genérico al arnés
  (`.harness/gate/check.sh` excluye `-m integration` del bloque 5 por defecto).
  Detalle completo: entrada Session-End `[2026-09-13]` en `memory/history.md` y
  tabla de Cobertura de `tasks.md` — no se repite aquí (`method.md §10`).
- `docs/planning/SPRINT.md` (el sprint pre-reestructuración) lleva banner de
  superseded — ya no es fuente viva, la reemplazó `SRV-001-walking-skeleton`.
- **Bitácoras previas** (pre-reestructuración): `docs/planning/sprint-history.md`,
  `docs/planning/hira-{server,hub}-bitacora.md`, `docs/planning/hira-hub-sprint-plan.md`.

## Obstáculos y desviaciones abiertas

- **Fuera de alcance de `ADR-004`:** el corpus de `docs/<producto>/spec/` (~40 archivos)
  tiene enlaces internos cruzados que siguen citando rutas pre-`ADR-001`. `ADR-001` ya
  decidió no reescribir ese corpus — es documentación de producto cerrada, no
  maquinaria del arnés. 404 en uno de esos enlaces = doc de producto desactualizada,
  no un problema del arnés; backlog de higiene separado, no se parchea el arnés.
- Ninguno abierto — `SRV-001-walking-skeleton` y `SRV-002-auth-rbac` `verified`;
  `HUB-001-walking-skeleton` `implemented` (pendiente confirmación `verified`).

## Estado de features (2026-10-15)

### ✅ Verificadas (Gate 4, Carlos)
- **`SRV-001-walking-skeleton`**: `estado: verified`, 30/30 tareas, ancla b4248e7
- **`SRV-002-auth-rbac`**: `estado: verified`
- **`SRV-003-bacnet-adapter`**: `estado: verified`
- **`SRV-004-modbus-adapter`**: `estado: verified`
- **`SRV-005-mqtt-scanning`**: `estado: verified`, 13/13 tareas, ancla d93243a
- **`HUB-001-walking-skeleton`**: `estado: verified`, 25/25 tareas, ancla 4d18044

### 🔶 Implementadas, pendientes de Gate 4
- **`SRV-006-simuladores`**: `estado: implemented`, 28/28 tareas (T-001..T-028), ancla
  `5b29160` (320/320 tests: 252 unit + 68 integración). Tabla de cobertura de
  `tasks.md` corregida de `Pendiente` a `Pass` (mismo bug recurrente del gate ya
  visto en SRV-001/003/004/005 — el gate no la autollena, el revisor la corrige
  citando precedente). `anchor_mode` pasó a `strict`.

### ⏳ Próximos Pasos
- **`SRV-006-simuladores` → Gate 4 (Verificación):** aplicar `method.md §4` con
  `revisor`; única pieza pendiente es el veredicto de Carlos contra los criterios
  de aceptación (spec.md/plan.md ya están sincronizados, tests pasan, ancla fijada).
- **Posterior a SRV-006 `verified`:**
  - `SRV-007` (asociación explícita de puntos) — bloqueada hasta SRV-006 verified
  - `HUB-H1` (gestión de licencias) — backlog futuro
  - `STU-001` (Walking Skeleton Studio) — requiere decisiones previas

## Nota operativa (2026-10-15, AIRA)

- **Infra de tests de integración:** `hira-server-postgres-1` publica el puerto
  **55432** (no 5432 — colisiona con otro proyecto del servidor que ya lo usa).
  Los tests de integración asumen por defecto `localhost:5432`; correr con
  `TEST_DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:55432/hiradb`.
  `Settings` (`core/config.py`, `env_file=None` deliberado) requiere las variables
  de `.env` exportadas al shell (`set -a && source ../.env && set +a`); `.env` trae
  `BACNET_PORT`/`BACNET_IP` vacíos, que `pydantic-settings` no coacciona a `None`
  — hace falta `unset BACNET_PORT BACNET_IP` para que `Settings()` no falle.
- **`spectral` instalado** (`npm install -g @stoplight/spectral-cli`, global en el
  servidor) + `.spectral.yaml` (`extends: spectral:oas`) en la raíz — activa el
  bloque 5 del gate. Mismos contratos tenían solo warnings de estilo (sin bloquear).
