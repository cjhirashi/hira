---
título: "<COMP>-Sprint-N — <Objetivo en una frase>"
componente: <hira-server | hira-hub | hira-studio>
sprint: <COMP>-Sprint-N
estado: activo
fecha_inicio: <YYYY-MM-DD>
---

## Objetivo

Una frase. Qué queda funcionando y verificable al cerrar el sprint.

## Anclas del sprint

ADRs / requisitos que este sprint realiza: `<lista>`
Criterios de aceptación que deja verificables: `<lista de AC-COMP-*>`

## Tareas

### T-1 — <título>

- **anchors:** `<IDs>`
- **valida:** `<AC-COMP-*>`
- **contrato:** `<archivo de .harness/contracts/ o <app>/docs/openapi.yaml, o "n/a">`
- **descripción:** qué se hace, archivos a crear/tocar.

### T-2 — <título>

…

## Gate de cierre

- [ ] Cada tarea cumple la Definition of Done (`PROCESS.md` §4).
- [ ] `.harness/ci/run_all.sh` en verde.
- [ ] `registry.yaml` actualizado.
- [ ] Reporte de sesión en `.harness/deviations/LOG.md`.
