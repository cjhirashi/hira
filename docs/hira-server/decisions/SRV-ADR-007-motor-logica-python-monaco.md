---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.7 - ADR-007 - Motor de Lógica Python con Monaco Editor.md"
título: SRV-ADR-007 — Motor de Lógica Python con Monaco Editor (sin FBD en v1)
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, motor-de-lógica]
---

## Contexto

Se necesita un motor de lógica embebido para operar dispositivos sin PLC externo.

## Decisión

Scripts Python con API interna (`hira.read/write/subscribe`) editados en Monaco Editor. FBD visual se evalúa en versión futura.

## Alternativas consideradas

Editor de bloques FBD (Function Block Diagram), reglas condicionales por formulario

## Consecuencias

Máximo poder desde v1; requiere que el integrador conozca Python; la capa FBD se puede añadir después sin cambiar el runtime
