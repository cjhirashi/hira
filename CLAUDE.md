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
