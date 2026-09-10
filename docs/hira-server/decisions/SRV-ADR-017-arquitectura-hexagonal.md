---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.17 - ADR-017 - Arquitectura Hexagonal para el backend.md"
título: SRV-ADR-017 — Arquitectura Hexagonal para el backend de Hira Server
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, hexagonal, backend]
---

> **Parcialmente superseded por [E-ADR-001](../ecosystem/E-ADR-001-studio-producto-cloud-independiente.md).**
> La Arquitectura Hexagonal de Hira Server se mantiene en su totalidad. Cambio: se retira
> el perfil `HIRA_DEPLOY_MODE=studio` y el adaptador SQLite — Server queda con un único
> perfil de despliegue (producción on-premise: PostgreSQL + TimescaleDB + pgvector).

## Contexto

La Metodología General de Proyectos exige documentar explícitamente la decisión de arquitectura del backend. Hira Server tiene múltiples perfiles de despliegue (`HIRA_DEPLOY_MODE=server` y `HIRA_DEPLOY_MODE=studio`, ver SRV-ADR-015), debe integrarse con protocolos industriales heterogéneos (BACnet, Modbus, MQTT), y puede requerir backends de base de datos distintos según el perfil (PostgreSQL + TimescaleDB en Server de producción, SQLite en instalación local ligera). Esta variabilidad hace crítica la separación entre núcleo y adaptadores.

## Decisión

Hira Server usa **Arquitectura Hexagonal**:

- **Núcleo (dominio):** lógica de negocio pura — modelos de puntos, alarmas, scripts de lógica, históricos. Sin dependencia de protocolo, framework HTTP ni base de datos
- **Puertos (interfaces abstractas):** `ProtocolPort` (lectura/escritura de puntos), `StoragePort` (persistencia de datos), `NotificationPort` (envío de alertas)
- **Adaptadores primarios (entrada):** FastAPI REST + WebSocket, CLI de administración
- **Adaptadores secundarios (salida):** BACnet (BAC0), Modbus (pymodbus), MQTT (paho-mqtt), PostgreSQL + TimescaleDB, SQLite (perfil local ligero), Redis Pub/Sub

**Regla de oro:** `services/` solo importa de `core/ports/`. Nunca de `adapters/` directamente. `adapters/factory.py` selecciona la implementación concreta según `HIRA_DEPLOY_MODE`.

## Alternativas consideradas

Arquitectura en capas clásica (descartada — acople entre lógica y protocolos dificulta simuladores); microservicios (descartada — sobre-ingeniería para un solo equipo)

## Consecuencias

Los adaptadores de protocolo pueden intercambiarse sin tocar la lógica de negocio. El mismo núcleo corre en un Server de producción (PostgreSQL + hardware real) y en una instalación local del integrador (SQLite + simuladores) solo cambiando qué adaptadores se inyectan. Los simuladores son ciudadanos de primera clase (SRV-ADR-014 — pueden reemplazar cualquier adaptador). La lógica central es testeable en aislamiento sin levantar dispositivos reales ni BD. Añadir un protocolo nuevo es crear un adaptador sin tocar el núcleo.
