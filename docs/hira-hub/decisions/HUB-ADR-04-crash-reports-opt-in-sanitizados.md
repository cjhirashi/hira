---
título: "HUB-ADR-04 — Crash reports opt-in con datos sanitizados"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-07-24
origen_vault: "7.2 - Hira Hub/7.2.3 - Diseño Conceptual.md (ADR-H04)"
tags: [adr, hira-hub, privacidad, seguridad]
---

## Contexto

Los Servers corren en redes privadas de clientes. Enviar datos técnicos al exterior
requiere consentimiento explícito del integrador. Relacionado: `VUL-SRV-012` (el crash
reporter puede filtrar datos del proyecto en stack traces).

## Decisión

`CRASH_REPORTER_ENABLED=false` por defecto. El integrador lo activa desde el panel con un
texto de consentimiento explícito. Los crash reports contienen SOLO: versión de Hira,
módulo afectado, stack trace de código propio (no de datos del cliente), `key_prefix`,
timestamp. NUNCA: IPs, nombres de dispositivos, valores de puntos, datos de usuarios.
Hub agrupa por `stack_trace_hash` (SHA-256). Contrato: `CT-crash-report`.

## Alternativas consideradas

- Opt-out (activo por defecto) — descartada: rompe la expectativa de privacidad.
- Siempre activo sin opción — descartada por lo mismo.

## Consecuencias

Confianza del integrador; menor volumen de reports (solo de quienes consientan); el Server
debe implementar el sanitizador (verificado con test unitario, ver `VUL-SRV-012`) y Hub
debe rechazar/sanitizar reports con patrones sensibles.
