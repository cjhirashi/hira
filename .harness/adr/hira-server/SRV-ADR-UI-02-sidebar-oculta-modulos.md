---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.22 - ADR-UI-02 - Sidebar oculta módulos sin acceso.md"
título: SRV-ADR-UI-02 — Sidebar oculta módulos sin acceso (no los deshabilita)
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-24
tags: [adr, arquitectura, hira-server, ui, rbac]
---

## Contexto

RBAC diferencia roles con permisos muy distintos.

## Decisión

Los módulos sin acceso no aparecen en sidebar — no se ven en gris ni bloqueados.

## Alternativas consideradas

Mostrar los módulos sin acceso en estado deshabilitado/gris (descartado).

## Consecuencias

Un operador que nunca verá "Configurador" no debe ver la opción ni procesar que existe. Menor complejidad perceptual. El backend igualmente rechaza requests no autorizados — la ocultación en UI es UX, no seguridad.
