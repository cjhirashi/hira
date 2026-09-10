---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.4 - ADR-004 - TimescaleDB para series de tiempo.md"
título: SRV-ADR-004 — TimescaleDB para series de tiempo
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, base-de-datos, históricos]
---

## Contexto

Los históricos de sensores son series de tiempo con alta frecuencia de escritura y consultas por rango temporal.

## Decisión

TimescaleDB como extensión de PostgreSQL, sin base de datos separada.

## Alternativas consideradas

InfluxDB (base de datos separada), MongoDB

## Consecuencias

Un solo motor de base de datos para todo (relacional + series de tiempo); menos contenedores; queries SQL estándar funcionan
