# CLAUDE.md

Contexto de proyecto: **lee `AGENTS.md`** (mapa del repo).
Cómo trabajamos: el arnés vive en **`.harness/`** — empieza por `.harness/method.md §0`
y respeta `.harness/constitution.md`.

Protocolo de arranque:
1. `.harness/gate/check.sh` — si cierra la compuerta, PARA y reporta.
2. Lee `.harness/memory/state.md` (correcciones del usuario arriba).
3. Ojea `.harness/specs/`.

## Reglas duras (no negociables)

- **Aplica la rúbrica de `method.md §2` antes de tocar un archivo.**
- **En caso de duda, o si "arreglar" implica revisar una decisión ya tomada, entra al carril SDD.** Nunca "prompt directo porque es rápido".
- **No saltes la Fase 1 (Specify)** para nada que no sea trivial.
- **Área sin `spec.md` que la cubra ≠ vía libre.** Es brownfield sin ancla todavía.
- **No te autoapruebas** y no marcas nada `verified`.
- 🔴 **Código:** Comentado (lógica no obvia), ordenado (patrones visuales, mismo patrón en archivos similares), profesional (reflejar metodología, no aleatoriedad).
- 🔴 **Fallas:** Resolver SIEMPRE desde la raíz — nunca parches (if temporales, TODOs, hacks). Investigar causa → Fixar origen → Validar tests → Limpiar workarounds.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- When graphify-out/graph.json exists, run `graphify query "<question>"` before your first grep, search or source-file read for a codebase question, and put this rule in every subagent prompt that explores code. Read raw files only for lines the graph or an earlier read already located. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
- A committed graphify-out/graph.json is rewritten whole on every build, so a large diff to it in a pull request is expected. Do not flag it as churn or suggest skipping the graph rebuild or its hooks.

## Diagramas: Archify + Diagram Design

Ambas skills ya están instaladas globalmente (`~/.agents/skills/`) — disponibles
sin paso de instalación adicional.

- **Archify** — architecture/workflow/sequence/dataflow/lifecycle (5 tipos),
  exploración rápida dentro de la sesión, salida interactiva.
- **Diagram Design** — el resto de los 45 tipos (ER, swimlane, kanban, Gantt,
  etc.) o cuando el destino es publicación con marca editorial.

No preguntar cuál usar — seguir el criterio de arriba.
