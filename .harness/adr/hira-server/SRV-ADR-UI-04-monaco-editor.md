---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.24 - ADR-UI-04 - Monaco Editor para scripts Python.md"
título: SRV-ADR-UI-04 — Monaco Editor para scripts Python
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-24
tags: [adr, arquitectura, hira-server, ui, motor-de-lógica]
---

## Contexto

El módulo de lógica permite al integrador escribir scripts Python.

## Decisión

Monaco Editor (mismo motor que VS Code) con tema oscuro y autocompletado básico del API Hira.

## Alternativas consideradas

Textarea simple sin resaltado de sintaxis ni autocompletado.

## Consecuencias

El integrador es técnico — espera un editor real, no un textarea. Monaco es estándar y embebible en React. Dependencia de Monaco vía npm; el autocompletado requiere definir las tipings del API Hira interno.
