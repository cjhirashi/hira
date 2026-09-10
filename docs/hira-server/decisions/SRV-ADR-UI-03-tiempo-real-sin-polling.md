---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.23 - ADR-UI-03 - Datos en tiempo real sin polling.md"
título: SRV-ADR-UI-03 — Datos en tiempo real sin polling
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-24
tags: [adr, arquitectura, hira-server, ui, tiempo-real]
---

## Contexto

Los valores de puntos cambian continuamente.

## Decisión

Socket.io WebSocket bidireccional — el cliente suscribe a los puntos que está visualizando; el backend solo envía lo que cambió.

## Alternativas consideradas

Polling HTTP periódico desde el cliente.

## Consecuencias

Polling HTTP generaría carga innecesaria; WebSocket es más eficiente y la latencia es menor. `<LiveIndicator>` siempre visible para que el operador sepa que la conexión está activa.
