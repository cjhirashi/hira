---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.6 - ADR-006 - Módulo IA completamente desacoplado y opcional.md"
título: SRV-ADR-006 — Módulo IA completamente desacoplado y opcional
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, ia]
---

## Contexto

No todos los clientes tendrán acceso a APIs de IA o querrán el costo adicional; instalaciones sin internet no pueden usar APIs externas.

## Decisión

El agente IA es un módulo independiente que se activa solo cuando hay una API key configurada. El sistema opera al 100% sin él.

## Alternativas consideradas

IA integrada como función core no opcional

## Consecuencias

Mayor adopción por precio más accesible; arquitectura más limpia; soporte de Ollama como alternativa local
