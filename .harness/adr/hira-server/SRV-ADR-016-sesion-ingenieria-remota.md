---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.16 - ADR-016 - Sesión de ingeniería remota de Studio a Server.md"
título: SRV-ADR-016 — Sesión de ingeniería remota de Studio a Server
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-31
tags: [adr, arquitectura, hira-server, sesión-ingeniería]
---

> **Parcialmente superseded por [E-ADR-001](../ecosystem/E-ADR-001-studio-producto-cloud-independiente.md).**
> El mecanismo descrito aquí se conserva íntegro y se promueve al contrato de ecosistema
> `CT-engineering-session`. Cambio: la sesión de ingeniería remota deja de ser "una de dos
> variantes" y pasa a ser el **único** modo de operación de Studio (que ahora es cloud).

## Contexto

Bajo SRV-ADR-015, Hira Studio siempre está conectado a un Server — local o remoto. Cuando la conexión es remota (el integrador trabaja desde su propia PC contra el Server real del cliente), hace falta evitar configuraciones concurrentes de dos integradores sobre el mismo proyecto al mismo tiempo.

## Decisión

Toda conexión de Studio a un Server remoto pasa por una **sesión de ingeniería** con lock exclusivo:

- El Server registra la sesión en `engineering_sessions` (UUID, usuario integrador, IP de origen, estado)
- Espejo en Redis con TTL de 300s — Studio envía heartbeat cada 60s para mantenerlo vivo
- Solo una sesión activa por proyecto a la vez — un segundo intento recibe `409 Conflict`
- Si Studio se desconecta sin cerrar sesión, el TTL expira y el lock se libera automáticamente
- El panel de operadores del proyecto muestra un banner mientras hay sesión de ingeniería activa
- Los cambios hechos en sesión remota se registran en auditoría con `source: studio_remote`

Este mecanismo es el único camino por el que Studio afecta datos de un proyecto que no está corriendo localmente en la misma máquina.

## Alternativas consideradas

- Sin lock — permitir múltiples sesiones de ingeniería concurrentes (descartado — riesgo de condiciones de carrera en la configuración del proyecto)
- Lock a nivel de Server completo en vez de por proyecto (a reevaluar cuando el modelo multi-proyecto de licencia de integrador esté implementado — ver SRV-ADR-020)

## Consecuencias

- El integrador nunca queda bloqueado para modificar un proyecto: si no está en el sitio, se conecta remoto con la misma garantía de exclusividad que si estuviera presente
- La UI debe comunicar claramente quién tiene la sesión activa y desde cuándo
- El diseño de este mecanismo no cambia con SRV-ADR-015 — ya asumía conexión remota de Studio a Server, solo se generaliza como el único modo de operación de Studio (antes era una de dos variantes junto al modo offline aislado)
