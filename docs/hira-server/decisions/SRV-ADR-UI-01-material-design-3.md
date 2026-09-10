---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.21 - ADR-UI-01 - Material Design 3 con soporte Light-Dark-Sistema.md"
título: SRV-ADR-UI-01 — Material Design 3 con soporte Light / Dark / Sistema
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-24
tags: [adr, arquitectura, hira-server, ui, diseño-visual]
---

## Contexto

Hira Server corre en salas de control (oscuro preferido) pero también en tablets y en configuración desde oficina (claro preferido). El integrador y el operador pueden tener preferencias distintas.

## Decisión

Material Design 3 con seed Cyan. Soporte de tres modos de tema: **Claro**, **Oscuro**, **Sistema** (sigue `prefers-color-scheme` del SO). La preferencia se guarda por usuario en `localStorage` y, en versiones futuras, en la cuenta.

## Alternativas consideradas

No aplica — decisión de sistema de diseño base, sin alternativas de framework visual evaluadas en el documento original.

## Consecuencias

MD3 genera automáticamente esquemas Light y Dark coherentes desde el mismo seed — no hay coste doble de diseño. El toggle da autonomía al operador sin forzar un tema inadecuado para su entorno. Los tokens de alarma (`--hira-alarm-*`) son estables en ambos temas para mantener consistencia operativa. El CSS expone `--md-sys-color-*` vía custom properties conmutadas por `data-theme` en el root.
