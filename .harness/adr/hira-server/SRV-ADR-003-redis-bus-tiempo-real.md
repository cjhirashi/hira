---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.3 - ADR-003 - Redis como bus central de datos en tiempo real.md"
título: SRV-ADR-003 — Redis como bus central de datos en tiempo real
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, redis, tiempo-real]
---

## Contexto

Múltiples consumidores necesitan los datos de los dispositivos simultáneamente (frontend, motor de alarmas, agente IA, scripts de lógica).

## Decisión

Redis pub/sub como canal de distribución. El Motor de Protocolos publica; todos los demás se suscriben.

## Alternativas consideradas

WebSocket directo dispositivo→frontend; Kafka

## Consecuencias

Desacoplamiento total entre el motor de protocolos y los consumidores; escalable; Redis ya está en el stack para cache
