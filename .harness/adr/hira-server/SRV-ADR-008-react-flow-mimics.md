---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.8 - ADR-008 - React Flow para mimics y editor visual.md"
título: SRV-ADR-008 — React Flow para mimics y editor visual
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, frontend, mimics]
---

## Contexto

Se necesita un canvas donde el integrador coloque bloques de equipos animados y los conecte a puntos BACnet/Modbus/MQTT.

## Decisión

React Flow como base del editor visual de mimics (ya en el stack para el editor de lógica FBD futuro).

## Alternativas consideradas

Canvas custom con Konva.js, SVG.js

## Consecuencias

Una sola librería sirve para dos propósitos (mimics + FBD futuro); ecosistema activo; curva de aprendizaje manejable
