---
id: ADR-002
tipo: adr
estado: accepted
fecha: 2026-09-04
---

# ADR-002 · Forzar la Fase 1 y el gate automático (corrección de diseño del arnés)

## Contexto y planteamiento del problema

En `cjhirashi-career` se detectó que el arnés no forzaba pasar por Fase 1 (Specify)
ante peticiones de "corrige esta falla" — se resolvían con commits directos. Causas
(arquitecto de arnés, `cjhirashi-career/.harness/decisions/ADR-002-*`):

1. Faltaba `.claude/settings.json` con el hook `Stop` que corría el gate cada turno.
2. `CLAUDE.md` no tenía reglas duras explícitas contra saltar Fase 1.
3. La rúbrica (`method.md §2`) no distinguía "esto exige rediseñar una decisión ya
   tomada" de un cambio trivial.

Es un defecto del **esquema simplificado**; se corrige aquí preventivamente — `hira`
no tiene código todavía, pero cuando lo tenga heredará el mismo defecto si no se aplica.

## Decisión

1. **`.claude/settings.json`** con hook `Stop` → `bash .harness/gate/check.sh`.
2. **`CLAUDE.md`** gana una sección "Reglas duras" (aplicar la rúbrica siempre, en
   duda ir a SDD, no saltar Fase 1, "sin ancla" no es luz verde).
3. **`method.md §2`** gana las ramas "rediseña una decisión existente" y "área sin
   `spec.md` que la cubra + toca negocio/contrato" → ambas a Carril SDD. Desempate:
   en caso de duda, SDD. En `hira`, "decisión ya tomada" incluye los ADRs de producto
   (`SRV-`/`STU-`/`HUB-ADR-`) — tocar código que contradiga uno de ellos es rediseño.

## Consecuencias

- El gate corre solo al cerrar cada turno.
- La rúbrica tiene un desempate explícito hacia el rigor — relevante aquí porque casi
  todo el ecosistema está "sin ancla" (fase de diseño, sin `spec.md` de feature todavía).

## Enlaces

- Origen: `cjhirashi-career/.harness/decisions/ADR-002-forzar-fase-1-y-gate-automatico.md`.
- Afecta a: `CLAUDE.md`, `.harness/method.md §2`, `.claude/settings.json` (nuevo).
- Relacionado: `ADR-001` (adopción del esquema simplificado + perfiles de arquitectura).
