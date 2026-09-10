# CLAUDE.md

Contexto de proyecto: **lee `AGENTS.md`** (mapa del repo).
Cómo trabajamos: el arnés vive en **`.harness/`** — empieza por `.harness/method.md §0`
y respeta `.harness/constitution.md`.

Protocolo de arranque:
1. `bash .harness/gate/check.sh` — si cierra la compuerta, PARA y reporta.
2. Lee `.harness/memory/state.md` (correcciones del usuario arriba).
3. Ojea `.harness/specs/` (vacío por ahora — fase de diseño).

## Reglas duras (no negociables, aplican SIEMPRE — también a "arregla esto"/"corrige X")

- **Aplica la rúbrica de `method.md §2` antes de tocar un archivo.** Una petición que
  suena urgente o pequeña no te exime de clasificarla.
- **En caso de duda, o si "arreglar" implica revisar una decisión ya tomada en un spec
  o ADR (rediseño), entra al carril SDD.** Nunca "prompt directo porque es rápido".
- **No saltes la Fase 1 (Specify)** para nada que no sea trivial por la rúbrica.
- **Área sin `spec.md` que la cubra ≠ vía libre.**
- **No te autoapruebas** y no marcas nada `verified`.

Aquí abajo van sólo detalles específicos de Claude Code (hooks, skills, subagentes),
no contexto de proyecto (eso va en `AGENTS.md`).

<!-- Nota de migración (2026-09-04): antes este archivo era un GENERADO idéntico a
     AGENTS.md vía .harness/claude/build_claude.py. Se reemplaza por el stub estándar
     del esquema simplificado (un canon por hecho — Constitución Art. 12). Los
     AGENTS.md/CLAUDE.md por producto (hira-server/, hira-studio/, hira-hub/) siguen
     generados por build_claude.py hasta que se decida si migran también. -->
