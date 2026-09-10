---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.1 - ADR-001 - Despliegue on-premise con conectividad a internet recomendada.md"
título: SRV-ADR-001 — Despliegue on-premise con conectividad a internet recomendada
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, despliegue]
---

## Contexto

Los dispositivos BACnet, Modbus y MQTT viven en redes locales industriales. Sin embargo, Hira requiere internet para sus servicios de valor agregado: validación de licencia, actualizaciones de software, crash reports al desarrollador, AI APIs externas y notificaciones a sistemas externos.

## Decisión

Docker + Docker Compose como única forma de despliegue. El servidor Hira debe tener acceso a internet. El núcleo SCADA (protocolos, alarmas, históricos, lógica) opera 100% en la red local. La capa de servicios externos requiere conectividad.

**Separación de capas:**
- **Capa local (sin internet):** BACnet/Modbus/MQTT polling, dashboard tiempo real, alarmas, históricos, scripts de lógica, simuladores — siempre disponible
- **Capa de servicios (requiere internet):** validación de licencia online, crash reporter, actualizaciones Docker, AI APIs (Claude/OpenAI), notificaciones email/webhook externos

## Alternativas consideradas

Cloud híbrido con gateway local; operación completamente air-gapped

## Consecuencias

Instalación simple en servidor Linux o Windows con internet; el cliente controla sus datos (on-premise); cjhirashi puede validar y desactivar licencias remotamente; Hira puede notificar al desarrollador de fallas automáticamente; instalaciones sin internet pierden la capa de servicios pero conservan el núcleo SCADA
