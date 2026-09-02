---
título: "HUB-ADR-05 — Arquitectura directa (no Hexagonal)"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-07-24
origen_vault: "7.2 - Hira Hub/7.2.3 - Diseño Conceptual.md (ADR-H05)"
tags: [adr, hira-hub, arquitectura]
---

## Contexto

El proceso exige documentar explícitamente la decisión de arquitectura del backend —
Hexagonal o alternativa con justificación. Hira Server usa Hexagonal (`SRV-ADR-017`)
porque tiene varios perfiles de despliegue y protocolos heterogéneos. Hub no.

## Decisión

Hub usa arquitectura **directa**. Estructura: `core/` + `models/` + `schemas/` +
`routers/` + `services/`. No hay puertos ni adaptadores. `services/` puede importar de
`models/` y `core/`.

**Por qué no Hexagonal:** Hub tiene un único deployment target (VPS en producción). No hay
variantes de despliegue (embedded, edge, multi-cloud). La capa de puertos/adaptadores no
agrega valor para un solo operador — solo superficie de mantenimiento.

## Alternativas consideradas

- Arquitectura Hexagonal — descartada: sobre-ingeniería para este caso de uso.

## Consecuencias

Código más simple y directo; menor carga cognitiva para el único mantenedor. Si en el
futuro Hub requiere variantes de deployment, se refactoriza a hexagonal entonces, con
contexto real de necesidad.
