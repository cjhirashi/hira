---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.5 - Dispositivos, Protocolos y Asociación de Puntos.md"
título: Dispositivos, Protocolos y Asociación de Puntos — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, dispositivos, protocolos, puntos]
---

## Responsabilidad

Motor de Protocolos: comunicación con dispositivos BACnet, Modbus y MQTT — descubrimiento, lectura, escritura y publicación a Redis. Solo opera sobre puntos asociados (ver SRV-ADR-012, SRV-ADR-019); nunca sobre candidatos crudos de un escaneo.

## Escaneo y descubrimiento

| Protocolo | Mecanismo |
|---|---|
| BACnet | Who-Is broadcast → I-Am responses → lectura de objetos por dispositivo (BAC0, soporta IP y MSTP) |
| Modbus | Escaneo de rangos de registros configurables (pymodbus, TCP/RTU) |
| MQTT | Suscripción wildcard → captura de topics activos (paho-mqtt) |

El resultado de cualquier escaneo se almacena en `device_points_candidates` — nunca directamente en `points`.

## Asociación explícita de puntos

1. El integrador revisa los candidatos descubiertos en el panel (Configurador → Puntos candidatos)
2. Por cada candidato que quiere usar, crea un registro en `points` vía `POST /points/associate`, definiendo:
   - `access_mode`: `read` o `read_write`
   - `bacnet_write_priority` (1-16) si el protocolo del dispositivo es BACnet y `access_mode=read_write`
3. Solo a partir de ese momento el punto participa en polling, escritura, alarmas, históricos, mimics y RAG
4. Un punto también puede crearse como `kind=internal` sin ningún candidato asociado — variable interna de la plataforma (ver SRV-ADR-019)

## Polling

- Intervalo configurable por punto asociado (`project_config.scan_interval_ms` como default, override por punto)
- El worker de polling (Celery) lee del Motor de Protocolos y publica cada valor a Redis Pub/Sub por canal de punto
- Un punto `offline` (dispositivo sin respuesta) se marca como tal en el dashboard en menos de 2 ciclos de polling

## Escritura

- Toda escritura pasa por: RBAC → `access_mode=read_write` del punto → Motor de Protocolos → dispositivo
- Para puntos BACnet, la escritura respeta la prioridad definida en la asociación (`bacnet_write_priority`)
- Confirmación de vuelta al frontend tras la escritura

## Concurrencia

- BAC0 no está diseñado para escrituras concurrentes desde múltiples threads. Se implementa `asyncio.Lock` por dispositivo en el adaptador BACnet — todas las operaciones sobre un mismo dispositivo (polling + escritura desde lógica) adquieren el lock antes de ejecutar. Los locks son por dispositivo, no globales

## Simuladores

- Se registran en `devices` con el mismo esquema que un dispositivo real, con el flag `is_simulator: true` (ver SRV-ADR-014)
- Reciben datos por el mismo pipeline que hardware real — el Motor de Protocolos, Redis, alarmas, históricos y frontend no distinguen origen
- El cambio de simulador a dispositivo real es un cambio de configuración (dirección/flag), no un cambio de estructura

## BACnet MSTP

Requiere acceso al puerto serial del host (`/dev/ttyUSB0` en Linux, `COM3` en Windows) — configuración opcional en Docker Compose (`devices:`), activa solo si el proyecto tiene dispositivos MSTP.

---

## Gate de Salida

- [x] Escaneo y asociación explícita de puntos documentados (SRV-ADR-012, SRV-ADR-019)
- [x] Reglas de polling, escritura y concurrencia documentadas
- [x] Simuladores documentados como ciudadanos de primera clase (SRV-ADR-014)
- [ ] Revisado y aprobado por Charlie
