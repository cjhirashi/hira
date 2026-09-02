---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.20 - ADR-020 - Multi-proyecto exclusivo de licencia de integrador.md"
título: SRV-ADR-020 — Multi-proyecto exclusivo de licencia de integrador
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-31
tags: [adr, arquitectura, hira-server, licenciamiento, rbac]
---

## Contexto

Bajo SRV-ADR-015, un Server puede alojar más de un proyecto. Hace falta definir el alcance de esa capacidad y cómo se relaciona con el RBAC — quién ve qué proyecto.

## Decisión

**Solo la licencia de integrador soporta múltiples proyectos en un mismo Server.** Las licencias comerciales (Starter, Professional, Enterprise) alojan un único proyecto por servidor — cada instalación de cliente es de un solo proyecto, como estaba definido originalmente.

RBAC según tipo de usuario:

- **Usuarios de operación** (Operador, Visor y roles configurables de instalación) son **por proyecto** — un usuario de operación pertenece a un proyecto y solo ve ese proyecto. En una licencia comercial (un solo proyecto) esto no cambia el modelo actual de roles globales al Server, porque solo hay un proyecto.
- **Usuarios integrador** son **globales al Server/Studio** — el mismo usuario integrador accede a todos los proyectos que aloja esa instancia. Relevante principalmente en la instalación local del integrador (licencia de integrador, multi-proyecto).

## Alternativas consideradas

- Multi-proyecto disponible en todas las licencias (descartado — no hay necesidad de negocio; cada cliente comercial opera una sola instalación)
- RBAC global sin distinción de proyecto (descartado — un operador de un proyecto no debe ver datos de otro proyecto alojado en la misma instancia del integrador)

## Consecuencias

- El modelo de datos de una licencia comercial no requiere cambios de fondo en el esquema de usuarios/roles existente — sigue siendo efectivamente un solo proyecto por instalación
- El modelo de datos de la instalación del integrador sí requiere una tabla de proyectos y roles de operación con `project_id` como alcance — a definir en el módulo de Autenticación y RBAC
- Simplifica significativamente el trabajo de implementación: la complejidad multi-tenant queda acotada a un solo tipo de licencia, no a todo el sistema
