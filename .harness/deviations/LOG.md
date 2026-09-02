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
