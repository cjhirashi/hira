---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.2 - ADR-002 - Python como lenguaje único del backend.md"
título: SRV-ADR-002 — Python como lenguaje único del backend
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, backend]
---

## Contexto

Las mejores librerías para BACnet (BAC0), Modbus (pymodbus) y el ecosistema de IA (LangChain) son Python.

## Decisión

FastAPI como framework, todo el backend en Python.

## Alternativas consideradas

Node.js para el API + Python solo para protocolos

## Consecuencias

Stack unificado, más fácil de mantener; cjhirashi lo domina; ecosistema de librerías industriales disponible
