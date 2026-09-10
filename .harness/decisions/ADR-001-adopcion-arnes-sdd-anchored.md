---
id: ADR-001
tipo: adr
estado: accepted
fecha: 2026-09-04
---

# ADR-001 · Reestructuración al esquema simplificado del arnés + perfiles de arquitectura

## Contexto y planteamiento del problema

El ecosistema Hira (3 productos: `hira-server`, `hira-studio`, `hira-hub`) sembró un
arnés SDD-Anchored el 2026-09-02, migrando ~90 documentos de diseño desde un vault de
Obsidian. El resultado fue un sistema muy completo pero **muy cargado** para la etapa
actual (sin código todavía): `.harness/` mezclaba maquinaria del arnés con
documentación de producto (spec/, adr/, contracts/, coordination/), mantenía un sistema
de anclas paralelo (`anchors/registry.yaml` + checksums + tooling Python) y gates de CI
standalone sin nada real que verificar todavía. Se quiere adoptar el **esquema
simplificado** ya diseñado y aplicado en `cjhirashi-career` y `cjhirashi-srv`
(repo `harness`, `docs/model/` + `docs/structure/`).

## Decisión

1. **Separación estricta aplicada de raíz:** todo el corpus de diseño (especificación,
   ADRs de producto, contratos, roadmap, glosario) es **documentación de producto**, no
   del arnés → se relocaliza a `docs/`, organizado por producto:
   - `docs/GLOSSARY.md`, `docs/ecosystem/spec/`, `docs/decisions/ecosystem/` (`E-ADR-`)
   - `docs/hira-server/{spec,decisions}/` (`SRV-ADR-`), `docs/hira-studio/{spec,decisions}/`
     (`STU-ADR-`), `docs/hira-hub/{spec,decisions}/` (`HUB-ADR-`)
   - `docs/contracts/` (5 OpenAPI compartidos), `docs/planning/` (roadmap, sprint, bitácoras)
   - `docs/legacy/` (sistema de anclas, gates de CI, plantillas, `PROCESS.md`/`README.md`
     viejos del arnés) — conservado **sin editar**, como referencia histórica.

2. **`.harness/` queda con la maquinaria mínima**: `constitution.md` (12 artículos,
   **perfil de arquitectura por producto** — no uno solo para todo el ecosistema),
   `method.md` (1 archivo, agnóstico), `memory/{state.md,history.md}`, `gate/check.sh` +
   `gate/project.sh`, `specs/_template/` (3 archivos: `spec.md`, `plan.md`, `tasks.md`),
   `decisions/` (ADRs **del arnés**, distintos de los ADRs de producto).

3. **Se retira el sistema de anclas paralelo** (`anchors/registry.yaml`, `SCHEMA.md`,
   checksums, `check_traceability.py`, `spec_checksum.py`): el anclaje simplificado
   (`covers` + `anchor_commit` + `anchor_mode` en el front-matter de cada `spec.md`, más
   la tabla de cobertura de `tasks.md`) cubre el mismo propósito con menos superficie.

4. **Se retiran los gates de CI standalone** (`contract_gate.py`, `openapi_lint.py`,
   `traceability_gate.py`, `run_all.sh`): no hay código ni contratos activos que
   verifiquen todavía; mantenerlos "en verde" sin nada real que chequear sería un gate
   de fachada. Se reintroducen como bloques de `gate/project.sh` cuando el primer
   producto tenga código y contratos reales.

5. **Se conserva `.harness/claude/`** (genera `AGENTS.md`/`CLAUDE.md` por producto vía
   `build_claude.py`, con `ORCHESTRATION.md` describiendo el equipo de agentes): es
   maquinaria del arnés (cómo los agentes obtienen su contexto), no documentación de
   producto. Sus fuentes siguen apuntando a rutas de `.harness/spec/`/`.harness/adr/`
   que ya no existen — **actualizarlas es tarea pendiente**, registrada en `memory/state.md`.

6. **Perfiles de arquitectura registrados tal como ya estaban decididos** (esta Génesis
   fue de **registro**, no de elección — las decisiones ya existían como ADR):
   - `hira-server` → **Hexagonal** (`SRV-ADR-017`): núcleo puro, puertos `ProtocolPort`/
     `StoragePort`/`NotificationPort`, adaptadores de protocolo (BACnet/Modbus/MQTT) y de
     storage (PostgreSQL+TimescaleDB / SQLite) intercambiables.
   - `hira-studio` → **Directa** (`STU-ADR-001`): SPA + BFF (FastAPI + PostgreSQL + Redis
     propios), multi-tenant, un solo deployment target.
   - `hira-hub` → **Directa** (`HUB-ADR-05`): mismo criterio que Studio; mismo stack que
     Server (`HUB-ADR-01`) pero sin puertos/adaptadores.
   - Detalle completo: `constitution.md` Art. 1–2.

7. **Agentes:** se añaden los 6 base (`orquestador`, `autor-de-spec`, `arquitecto`,
   `implementador`, `revisor`, `explorador`) en `.claude/agents/`, consistentes con el
   resto de proyectos. Los 16 especialistas de módulo pre-diseñados (`hira-*`, `hub-*`)
   se conservan **sin refrescar** (fuera de alcance de esta reestructuración) — referencian
   rutas retiradas; refrescarlos antes de invocarlos.

## Opciones consideradas

- **Dejar el arnés como estaba.** Descartada: divergiría del esquema ya adoptado en los
  otros dos repos, y mezclaba documentación de producto con maquinaria del arnés
  (justo el error que `cjhirashi-career` ya corrigió una vez — ver su `memory.md` histórico).
- **Reescribir todo el corpus de spec/ADR a EARS y `RF-` desde ya.** Descartada: son
  decisiones y diseño ya cerrados (`SRV-ADR-*`, `STU-ADR-*`, `HUB-ADR-*`, specs de
  arquitectura/módulos), no features en curso. Reescribirlos no aporta y arriesga perder
  matices; EARS/`RF-` se usa para las features **nuevas** a partir de ahora.
- **Un `.harness/` por producto** (3 arneses). Descartada: es un solo monorepo con
  decisiones de ecosistema que cruzan los 3 productos (`E-ADR-001`, contratos
  compartidos); un `.harness/` único con perfiles por producto refleja mejor la realidad
  (mismo patrón que `cjhirashi-career`, monorepo de microservicios con un solo arnés).

## Consecuencias

- **Buenas:** `.harness/` pasa de ~150 archivos a ~10; el corpus de diseño (que sigue
  siendo igual de valioso) queda donde nuestra propia Constitución dice que va — `docs/`.
  Formato de Session-End homogéneo con `cjhirashi-career`/`cjhirashi-srv` → monitoreo barato.
- **Coste:** `.harness/claude/*.md` y los 16 especialistas de módulo necesitan una pasada
  de actualización de rutas antes de volver a usarse (no se hizo en esta sesión).
  `docs/legacy/ci-scripts/` y `docs/legacy/anchors-system/` quedan inertes hasta que se
  decida si valen la pena reactivar o si el gate simplificado basta indefinidamente.

## Enlaces

- Esquema genérico: repo `harness`, `docs/model/` + `docs/structure/` + `reference/`.
- Constitución: `.harness/constitution.md`. Método: `.harness/method.md`.
- Mapa completo de la relocalización: `docs/README.md`.
