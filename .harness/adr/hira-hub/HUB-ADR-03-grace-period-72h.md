---
título: "HUB-ADR-03 — Grace period de 72h para Servers sin conexión a Hub"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-07-24
origen_vault: "7.2 - Hira Hub/7.2.3 - Diseño Conceptual.md (ADR-H03)"
tags: [adr, hira-hub, licenciamiento, resiliencia]
---

## Contexto

Si Hub cae, los Servers de los clientes no deben dejar de operar — el SCADA es crítico
para la operación del cliente. Esto complementa `SRV-ADR-001` (el núcleo SCADA opera sin
internet).

## Decisión

Al validar la licencia con éxito (`CT-license` → `POST /api/licenses/validate`), el Server
almacena el timestamp de esa validación. Si Hub no está accesible, el Server sigue
operando hasta **72h** desde la última validación exitosa antes de entrar en modo
degradado (solo lectura, sin configuración).

## Alternativas consideradas

- Sin grace period — el Server cae si Hub cae. Descartada: inaceptable para el cliente.
- Grace period indefinido — la licencia nunca expira en la práctica. Descartada: elimina
  el control de licenciamiento.

## Consecuencias

El uptime de Hub no bloquea el SCADA del cliente; cjhirashi tiene 72h para restaurar Hub
antes de que las instalaciones se vean afectadas. El Server debe implementar el contador
de grace period y el paso a modo degradado.
