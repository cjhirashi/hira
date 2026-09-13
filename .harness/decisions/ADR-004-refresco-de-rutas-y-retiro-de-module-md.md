---
id: ADR-004
tipo: adr
estado: accepted
fecha: 2026-09-13
---

# ADR-004 · Refresco de rutas post-`ADR-001` y retiro de `MODULE.md`

## Contexto y planteamiento del problema

`ADR-001` (2026-09-04) reestructuró el arnés y relocalizó ~115 archivos de `.harness/`
a `docs/`, pero dejó explícitamente pendiente actualizar tres piezas que seguían
citando las rutas retiradas (`.harness/spec/`, `.harness/adr/`, `.harness/coordination/`,
`.harness/ci/`, `.harness/anchors/registry.yaml`, `.harness/deviations/LOG.md`,
`.harness/PROCESS.md`): `.harness/claude/*.md` (overlays del generador de
`AGENTS.md`/`CLAUDE.md`), los 16 especialistas de dominio en `.claude/agents/`, y los
`README.md` de cada producto. Con la primera feature real ya arrancada
(`SRV-001-walking-skeleton`), el usuario pidió cerrar esta deuda para que ningún agente
tropiece con una ruta muerta a mitad de una tarea.

`ADR-001` también dejó sin resolver si la convención `MODULE.md` (plantilla
`.harness/templates/module-readme.md`, con frontmatter `anchors:`) se retomaba o se
retiraba — no existe en `method.md` del esquema simplificado, que solo pide un
`README.md` por carpeta nueva (regla 6 de `ecosystem.md`).

## Decisión

1. **Refresco mecánico de rutas** en `.harness/claude/{ecosystem,hira-server,hira-hub,
   hira-studio,ORCHESTRATION}.md`, los 16 especialistas de `.claude/agents/`, `README.md`
   raíz, `docs/contracts/README.md` y los 3 `README.md` de producto: toda referencia a
   `.harness/{spec,adr,coordination,ci,anchors,deviations,templates,PROCESS}` pasa a su
   equivalente vigente (`docs/<producto>/{spec,decisions}/`, `docs/planning/`,
   `docs/contracts/`, `.harness/gate/`, `.harness/method.md`). No es una decisión nueva:
   es aplicar la que ya tomó `ADR-001`.
2. **`registry.yaml` y `DEV-###`/`LOG.md`** en el texto de agentes/overlays se reemplazan
   por sus equivalentes ya vigentes desde `ADR-001`: la tabla de cobertura de `tasks.md`
   (anclaje) y la **Directiva de Pausa** (`method.md §5`, contradicción de diseño).
3. **`HUB-ADR-05` como "arquitectura directa"** en `hira-hub.md`, `hub-infra.md` y
   `ORCHESTRATION.md` se corrige a **Hexagonal** (`E-ADR-002`, ya vigente desde
   2026-09-04 — el overlay y el especialista no se habían actualizado).
4. **`MODULE.md` se retira** (decisión nueva, resuelve el pendiente de `ADR-001`): cada
   carpeta nueva lleva únicamente su `README.md`, sin frontmatter `anchors:` — el
   anclaje vigente vive en `covers` de `spec.md` y en la tabla de cobertura de
   `tasks.md`. Se elige "retirar" sobre "retomar" por el mismo criterio de simplicidad
   que ya rigió `ADR-001`: no hay lector activo de ese frontmatter en el esquema
   simplificado, mantenerlo sería ceremonia sin efecto.
5. **`build_claude.py`** deja de generar la raíz (`AGENTS.md`/`CLAUDE.md`): desde la
   nota de migración del `CLAUDE.md` raíz (2026-09-04) la raíz sigue el stub manual del
   esquema simplificado, no el overlay `ecosystem.md` — el generador seguía intentando
   sobrescribirla, lo que habría revertido el stub en la próxima corrida.

## Opciones consideradas

- **Dejar `MODULE.md` y escribirle un lector en el gate.** Descartada: añade una pieza
  de anclaje paralela a `covers`/`tasks.md` que ya cubre el mismo propósito — el mismo
  error que `ADR-001` corrigió con `registry.yaml`.
- **No tocar la raíz de `build_claude.py`** (dejar `"."` en `TARGETS`, confiar en que no
  se vuelva a correr). Descartada: es un bug latente — la próxima vez que alguien corra
  el generador sin este contexto, sobreescribe silenciosamente el stub manual.

## Consecuencias

- **Buenas:** ningún agente (base, `experto-ux-ui`, o los 16 de dominio) parte de una
  instrucción que apunta a una ruta muerta. `build_claude.py --check` reporta "al día".
  Gate verde tras la corrección.
- **Fuera de alcance de este ADR:** el corpus de `docs/<producto>/spec/` (~40 archivos)
  tiene enlaces internos cruzados que todavía usan rutas pre-`ADR-001` — `ADR-001` ya
  decidió no reescribir ese corpus ("el contenido no cambió, solo la ubicación"); es
  documentación de producto, no maquinaria del arnés, y su volumen excede el alcance de
  una pasada de higiene del arnés. Queda anotado en `memory/state.md` como deuda
  conocida, separada de esta corrección.

## Enlaces

- Decisión que esta ADR ejecuta: `ADR-001`.
- Mapa de rutas old→new: `docs/README.md`.
- Mecanismo vigente de anclaje: `.harness/method.md §9` (glosario: `covers`,
  `anchor_commit`). Mecanismo vigente de pausa: `.harness/method.md §5`.
