---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.14 - ADR-014 - Simuladores como ciudadanos de primera clase.md"
título: SRV-ADR-014 — Simuladores como ciudadanos de primera clase del sistema
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, simuladores]
---

## Contexto

El integrador necesita diseñar y validar proyectos completos antes de tener acceso al hardware del cliente. Los simuladores solo son útiles si el sistema los trata exactamente igual que dispositivos reales.

## Decisión

Los simuladores se registran en la tabla `devices` con el mismo esquema que un dispositivo real, con un único flag diferenciador `is_simulator: true`. El Motor de Protocolos, el bus Redis, el Motor de Alarmas, los históricos TimescaleDB y el frontend reciben datos de simuladores por el mismo pipeline que datos de hardware real. El switch de simulador a dispositivo real es un cambio de configuración (IP/address/flag), no un cambio de estructura.

## Alternativas consideradas

Simuladores como herramienta de desarrollo separada sin integración en la plataforma; simuladores solo en el entorno de desarrollo local

## Consecuencias

Habilita el flujo "diseño con simuladores → reemplaza por hardware real" como flujo de trabajo estándar del integrador. Los simuladores se convierten en un diferenciador comercial significativo.
