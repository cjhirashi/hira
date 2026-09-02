---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.10 - ADR-010 - Auto-documentación desde código y configuración del sistema.md"
título: SRV-ADR-010 — Auto-documentación desde código y configuración del sistema
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, documentación]
---

## Contexto

Cada instalación de Hira es única — dispositivos, puntos, lógica y roles distintos. Los manuales genéricos no sirven; los integradores tampoco tienen tiempo de escribir documentación manual.

## Decisión

El sistema genera documentación automáticamente desde dos fuentes: (1) análisis AST de los scripts Python para producir diagramas de flujo Mermaid, y (2) lectura de la configuración del proyecto (dispositivos, puntos, roles) para generar inventarios y guías operativas. La IA enriquece estas salidas con lenguaje natural cuando está activa. Todo se organiza en el Módulo de Documentación, filtrado por rol.

## Alternativas consideradas

Documentación manual por el integrador; editor de documentación tipo wiki dentro del panel

## Consecuencias

La documentación siempre está actualizada porque se genera desde la fuente de verdad (código + configuración); diferenciador comercial significativo; requiere un parser AST confiable para Python y plantillas de generación de contenido bien diseñadas
