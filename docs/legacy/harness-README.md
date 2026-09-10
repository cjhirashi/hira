---
título: .harness — Andamiaje SDD-Anchored del ecosistema Hira
tipo: README
status: activo
última_actualización: 2026-09-02
---

# `.harness/`

Todo lo que gobierna *cómo* se desarrolla el ecosistema Hira vive aquí. El código de los
tres componentes vive en `hira-server/`, `hira-hub/`, `hira-studio/` en la raíz del
monorepo.

## Mapa

| Carpeta | Contenido | Empieza por |
|---|---|---|
| [`PROCESS.md`](PROCESS.md) | El proceso SDD-Anchored completo | **léelo primero** |
| [`GLOSSARY.md`](GLOSSARY.md) | Términos del ecosistema | referencia |
| [`spec/`](spec/) | Especificación — fuente de verdad del *qué* y el *por qué* | `spec/ecosystem/vision.md` |
| [`adr/`](adr/) | Decisiones de arquitectura (ecosistema + por componente) | `adr/ecosystem/` |
| [`anchors/`](anchors/) | Registro de anclas (`registry.yaml`) + convenciones + tooling | `anchors/SCHEMA.md` |
| [`contracts/`](contracts/) | Contratos API/eventos entre componentes | `contracts/README.md` |
| [`coordination/`](coordination/) | Roadmap del ecosistema y sprint(s) activo(s) | `coordination/ROADMAP.md` |
| [`claude/`](claude/) | Fuentes de `AGENTS.md`/`CLAUDE.md` + orquestación de agentes | `claude/ORCHESTRATION.md` |
| [`templates/`](templates/) | Plantillas (ADR, sprint, reporte de sesión, desviación, módulo, requisito) | — |
| [`ci/`](ci/) | Gates de CI (trazabilidad, contratos, lint) | `ci/run_all.sh` |
| [`deviations/`](deviations/) | Registro de desviaciones y reportes de sesión | `deviations/LOG.md` |
| [`legacy/`](legacy/) | Puntero al código previo de Hira Server (rama git) | `legacy/README.md` |

## Origen

Este harness se sembró el 2026-09-02 extrayendo el corpus de diseño previo de un vault de
Obsidian (proyectos `7.1 - Hira Server` y `7.2 - Hira Hub`). El vault dejó de ser fuente de
verdad: toda la especificación vive ahora en `spec/` y `adr/`. Los documentos migrados
conservan en su frontmatter `origen_vault:` con la fecha de última actualización original.
