---
título: Registro de desviaciones y reportes de sesión
tipo: Coordinación
status: activo
última_actualización: 2026-09-02
---

# Desviaciones y reportes de sesión

Ver `PROCESS.md` §7. Plantillas: `templates/deviation.md`, `templates/session-report.md`.

- Una **desviación** (`DEV-###`) es "no se pudo implementar como se especifica". Se resuelve
  editando la spec o con un ADR nuevo. Una vez aplicada y validada, se marca `Resuelta` con
  la referencia — el histórico permanece aquí.
- Un **reporte de sesión** se añade al cerrar cada sesión de trabajo: dice *qué* se hizo,
  *si funciona* y *si se probó*.

---

## Desviaciones abiertas

*(ninguna)*

---

## Desviaciones resueltas

### DEV-000 · 2026-09-02 · tipo: diseño · Estado: Resuelta

- **Contexto:** siembra del harness. El corpus de diseño (`SRV-ADR-015/016/017`) definía
  Hira Server y Studio como un solo producto/instalador con perfil `HIRA_DEPLOY_MODE`
  `server`/`studio`. El usuario decidió que Studio es un producto cloud independiente.
- **Qué necesitaba:** una decisión de ecosistema que reconcilie los tres ADRs con el
  modelo de tres vertientes (Hub y Studio cloud, Server local).
- **Bloqueaba:** toda la organización del harness y el arranque de la vertiente Studio.
- **Anclas afectadas:** `SRV-ADR-015`, `SRV-ADR-016`, `SRV-ADR-017`.
- **Resolución:** `E-ADR-001 — Hira Studio como producto cloud independiente`
  (`.harness/adr/ecosystem/`). Los tres ADRs llevan banner de supersesión parcial. Las
  preguntas de diseño que abre quedan en `spec/hira-studio/OPEN-QUESTIONS.md`.

---

## Reportes de sesión

### Reporte de Sesión — 2026-09-03

- **Sprint:** F0 — cierre del diseño de plataforma de Hira Studio.
- **Tareas trabajadas:** resolver `spec/hira-studio/OPEN-QUESTIONS.md` SQ-1..SQ-8.
- **Qué se implementó (diseño, no código):**
  - `STU-ADR-001..005` en `.harness/adr/hira-studio/` (hosting multi-tenant + SPA/BFF;
    identidad + licencia vía Hub; emparejamiento por token; diseño/pruebas offline +
    publicación al Server; Agente del Integrador en el BFF de Studio).
  - `spec/hira-studio/architecture.md` (contenedores + módulos del BFF + fronteras).
  - `context.md` y `OPEN-QUESTIONS.md` actualizados (diseño cerrado, SQ marcadas resueltas).
  - `SRV-ADR-020` con banner de supersesión parcial (→ `STU-ADR-004`).
  - `registry.yaml`: +5 `STU-ADR`, +`SPEC-STU-architecture`/`-inherited`, +6 `AC-STU-*`
    (grupos), +3 requisitos (`REQ-SRV-studio-pairing`, `REQ-SRV-project-publish`,
    `REQ-CT-engsession-v2`). 93 → 109 anclas.
  - `ROADMAP.md` track STU reescrito (STU-Spec + STU-Sprint-1..7); SRV-Sprint-12 ampliado.
  - Nota de ampliación pendiente de `CT-engineering-session` en el contrato y su README.
  - Overlay `.harness/claude/hira-studio.md` actualizado → `hira-studio/AGENTS.md`/`CLAUDE.md` regenerados.
- **Pruebas ejecutadas y resultado:** `.harness/ci/run_all.sh` → verde (0 errores, 109 anclas, 20 secciones de spec con checksum).
- **Desviaciones abiertas:** ninguna.
- **Pendiente:** STU-Spec (spec por módulo de Studio + `AC-STU-*` detallados) y la
  ampliación de `CT-engineering-session` en SRV-Sprint-12 — ambos en el roadmap, no bloquean.

### Reporte de Sesión — 2026-09-02

- **Sprint:** F0 (siembra del harness, no es un sprint de código).
- **Tareas trabajadas:** montaje completo de `.harness/`.
- **Qué se implementó:**
  - Árbol `.harness/` con `PROCESS.md`, `README.md`, `GLOSSARY.md`, `anchors/SCHEMA.md`,
    plantillas y gates de CI.
  - Migración del corpus del vault (`7.1`/`7.2`, ~90 docs) a `spec/` y `adr/` con esquema
    de anclas nuevo (`SRV-ADR-*`, `HUB-ADR-*`, `AC-SRV-*`, `VUL-SRV-*`, `VUL-HUB-*`).
  - Contenido nuevo: `E-ADR-001`, `HUB-ADR-01..05`, spec de ecosistema
    (`vision`/`business-model`/`ecosystem-architecture`), spec de Studio
    (`context`/`inherited-from-server`/`OPEN-QUESTIONS`), 5 contratos en `contracts/`.
  - `anchors/registry.yaml` sembrado (ADRs, contratos, AC de Server y Hub, 21
    vulnerabilidades, secciones de spec, 2 requisitos heredados).
  - `coordination/`: `ROADMAP.md` (3 tracks), `SPRINT.md` (SRV-Sprint-1 detallado),
    `sprint-history.md` (histórico de la implementación previa, descartada).
  - `.claude/agents/` (orquestador + especialistas), `AGENTS.md` / `CLAUDE.md` de raíz
    generados de `.harness/claude/`.
  - Código previo de Hira Server archivado en rama `legacy/hira-server-snapshot`; carpetas
    `7.1`/`7.2` eliminadas del repo.
- **Pruebas ejecutadas y resultado:** `.harness/ci/run_all.sh` — (completar al ejecutar).
- **Pendiente o bloqueado:** ninguno para F0. Siguiente: SRV-Sprint-1 y HUB-H0.
