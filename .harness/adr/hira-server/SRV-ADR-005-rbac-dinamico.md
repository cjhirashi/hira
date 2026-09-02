---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.5 - ADR-005 - RBAC dinámico, roles no hardcodeados.md"
título: SRV-ADR-005 — RBAC dinámico, roles no hardcodeados
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, rbac]
---

## Contexto

Hira se despliega en proyectos muy distintos (HVAC, iluminación, energía, incendios, IoT) con estructuras organizacionales diferentes.

## Decisión

Los roles y permisos de operación se definen en base de datos por el superusuario de cada instalación. Ver SRV-ADR-020 para el alcance de este RBAC dinámico frente a usuarios integrador (globales) en instalaciones multi-proyecto.

## Alternativas consideradas

Roles fijos (Admin, Operador, Visor) — este modelo fijo de 3 roles es el implementado en MVP (v0.1) como paso intermedio; el RBAC dinámico completo llega en v0.2

## Consecuencias

Máxima flexibilidad por proyecto; mayor complejidad en el modelo de datos de permisos; el superusuario tiene responsabilidad sobre la configuración de accesos
