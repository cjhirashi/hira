---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.13 - ADR-013 - Dos instancias de Agente IA independientes por stakeholder.md"
título: SRV-ADR-013 — Dos instancias de Agente IA con API keys y tools independientes por nivel de stakeholder
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, ia]
---

## Contexto

El integrador necesita asistencia durante la construcción del proyecto (scripts, documentación, mimics). El cliente necesita asistencia durante la operación (consultas, control, predicción de fallas). Sus herramientas, permisos y costos son completamente distintos.

## Decisión

Dos agentes LangChain separados, configurados de forma independiente. El Agente del Integrador tiene tools de construcción (configurador, editor de lógica, documentación, mimics). El Agente del Cliente tiene tools de operación (monitoreo, alarmas, históricos, análisis) con RAG sobre la documentación del proyecto. Cada agente se activa con su propia API key — el integrador y el cliente eligen y pagan su propio modelo (Claude, OpenAI u Ollama).

## Alternativas consideradas

Un solo agente con todos los tools filtrados por RBAC; agente compartido con una sola API key de Hira

## Consecuencias

Costos de IA completamente separados por stakeholder; cada parte elige su modelo según su presupuesto; separación clara de responsabilidades; si uno no está configurado, el otro puede funcionar igual; mayor flexibilidad comercial
