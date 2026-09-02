---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.11 - ADR-011 - Módulo de Documentación como base de conocimiento RAG.md"
título: SRV-ADR-011 — Módulo de Documentación como base de conocimiento RAG del Agente IA
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, ia, rag, documentación]
---

## Contexto

Un agente IA genérico no puede predecir fallas ni asesorar con precisión sin conocer el proyecto específico. Cada instalación de Hira es diferente — dispositivos distintos, lógica propia, procedimientos únicos.

## Decisión

El Módulo de Documentación actúa como base de conocimiento RAG (Retrieval Augmented Generation). Todo su contenido — lista de puntos escaneados, diagramas de flujo de scripts, manuales, fichas técnicas, diagramas de conexionado, resultados de pruebas — se indexa en un vector store embebido (pgvector como extensión de PostgreSQL, sin base de datos adicional). El Agente IA consulta este índice antes de responder, convirtiéndose en especialista del proyecto.

## Alternativas consideradas

RAG en base de datos vectorial separada (ChromaDB, Weaviate); contexto manual por el operador en cada conversación

## Consecuencias

La IA conoce el sistema como un técnico experimentado; las predicciones de falla tienen base en documentación real; pgvector evita un contenedor adicional; la calidad del RAG depende de la calidad de la documentación cargada por el integrador
