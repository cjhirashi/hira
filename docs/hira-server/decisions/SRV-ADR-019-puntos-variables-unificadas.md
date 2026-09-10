---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.19 - ADR-019 - Puntos como variables unificadas multi-protocolo.md"
título: SRV-ADR-019 — Puntos como variables unificadas multi-protocolo
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-31
tags: [adr, arquitectura, hira-server, modelo-de-datos]
---

## Contexto

El modelo de datos original definía `points` con `device_id` obligatorio — cada punto pertenece a un dispositivo. En la práctica, Hira necesita variables internas de la plataforma (cálculos, banderas, resultados intermedios de scripts de lógica) que no representan un punto de ningún controlador físico.

## Decisión

Un **punto** en Hira es una variable unificada que vive en el Server, independiente del protocolo de origen:

- Puede estar enlazado a un punto real de un controlador — BACnet, Modbus, MQTT, o cualquier protocolo que se integre en el futuro. Actúa como variable espejo del valor del controlador.
- Puede ser una **variable interna** sin controlador asociado, para operaciones internas de la plataforma (variables intermedias de scripts de lógica, banderas de estado, valores calculados).
- El límite de licencia por puntos en línea (SRV-ADR-018) cuenta **todos** los puntos activos, enlazados e internos por igual — no hay distinción de licencia entre ellos.

**Ningún punto crudo de un controlador es utilizable directamente en línea.** El escaneo de dispositivos (Who-Is/I-Am, escaneo de registros Modbus, discovery de topics MQTT) descubre puntos disponibles, pero esos puntos crudos no fluyen al sistema hasta que se **asocian explícitamente a un punto de Hira**. Solo el punto de Hira asociado es el que se pollea, se historiza, dispara alarmas y se expone a scripts de lógica.

Cada asociación punto de Hira ↔ punto de controlador define:
- **Capacidad de acceso:** solo lectura, o lectura + escritura
- **Para BACnet específicamente:** además de lectura/escritura, la asociación incluye la **prioridad de escritura** (BACnet priority array) con la que Hira escribe al punto

`points.device_id` pasa de obligatorio a **opcional** en el modelo de datos — nulo para variables internas, presente cuando el punto está asociado a un punto crudo de un controlador.

## Alternativas consideradas

Mantener `device_id` obligatorio y crear una tabla separada `internal_variables` para variables sin controlador (descartado — duplica lógica de licenciamiento, permisos y consumo en tiempo real que ya existe para `points`)

## Consecuencias

- `backend/models/point.py` — `device_id: int | None` en vez de `device_id: int`, más campos de asociación: `access_mode` (`read` | `read_write`) y `bacnet_write_priority` (nulo salvo protocolo BACnet)
- El Motor de Protocolos ignora puntos sin `device_id` — no intenta hacer polling sobre ellos
- El escaneo de dispositivos (`POST /devices/scan`) devuelve puntos crudos candidatos — no crea puntos de Hira automáticamente. El integrador (o un flujo guiado) confirma la asociación explícita antes de que el punto quede en línea
- El Motor de Lógica puede leer/escribir puntos internos exactamente igual que puntos de dispositivo, vía la misma API `hira.read/write`
- La escritura a un punto respeta su `access_mode` — un punto de solo lectura rechaza `hira.write()` y escritura desde panel
- Actualizar el modelo de datos del módulo de Dispositivos y Protocolos con este cambio
