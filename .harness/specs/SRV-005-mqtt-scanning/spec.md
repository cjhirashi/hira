---
id: SPEC-SRV-005
tipo: spec
feature: SRV-005-mqtt-scanning
estado: verified
anchor_commit: d93243a33dfbd26db59c59451d99c76f5a13d9f4
anchor_mode: strict
covers:
  - hira-server/backend/**
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-14 }
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# SPEC-SRV-005 · Escaneo MQTT — suscripción wildcard y candidatos

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Base:
> `SRV-ADR-012` (escaneo + candidatos), `AC-SRV-04` (subconjunto: 4.2, 4.4 —
> 4.1 ya resuelto en `SRV-001`/`VUL-SRV-001`; 4.3 es escritura/asociación,
> diferido), `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md`
> ("MQTT: suscripción wildcard → captura de topics activos, paho-mqtt").
> Tercera de 4 features en que se partió `SRV-Sprint-3` — ver `memory/state.md`
> (2026-09-14). Construye sobre `SRV-004-modbus-adapter` (`verified`):
> reutiliza `devices`/`device_points_candidates` ya existentes, no las recrea.

## 1. Contexto del dominio
- Suscribirse a un patrón de topic MQTT (wildcard, p. ej. `edificio/piso1/#`)
  durante una ventana de tiempo, y persistir los topics que publicaron mensajes
  como candidatos — mismo modelo `devices`/`device_points_candidates` de
  `SRV-003`/`SRV-004`, sin asociación explícita (feature posterior).
- Diferencia clave: MQTT es **push-based** (a diferencia de BACnet/Modbus,
  request/response) y **no tiene un concepto de "dispositivo" con identidad
  fija** — un patrón de suscripción puede capturar mensajes de topics muy
  distintos. Decidido (2026-09-14): **un `device` = el patrón de suscripción
  completo**; cada topic real que publicó durante la ventana es un candidato
  de ese `device`. Sin inferencia de sub-dispositivos por segmento de topic.
- Reutiliza el broker Mosquitto ya autenticado de `SRV-001` (`VUL-SRV-001`
  resuelto) — sin necesidad de un broker de prueba falso, a diferencia de
  BACnet/Modbus (que sí necesitaron servidor/dispositivo de test dedicado).

## 2. Alcance
### En alcance (propuesto)
- Adaptador MQTT (paho-mqtt): dado un patrón de topic, se suscribe durante una
  ventana de tiempo (3s, mismo criterio que BACnet) y captura los mensajes
  publicados.
- `devices.address` para MQTT: el patrón de suscripción tal cual (p. ej.
  `"edificio/piso1/#"`). `device_points_candidates`: `object_type` =
  constante `"mqtt_topic"`; el topic real recibido (p. ej.
  `"edificio/piso1/ahu1/temp"`) identifica al candidato — **resuelto en Fase 2
  (Gate 2, 2026-09-14, aprobado):** `object_instance` (`INTEGER`, columna
  compartida con BACnet/Modbus, no se migra) guarda un hash determinista
  (`crc32`) del topic para poder "actualizar si ya existía"; el topic
  completo real vive en `object_name` (`String(255)` — límite conocido, no
  cubierto por ningún RF-, ver `plan.md §2`). `present_value` = payload del
  último mensaje.
- Endpoint HTTP protegido por RBAC (mismo criterio: Admin+Operador).
- Verificación de integración real: contra el Mosquitto real ya autenticado
  del compose de `SRV-001` (no un broker de test aparte).

### Fuera de alcance (propuesto, mismo criterio que BACnet/Modbus)
- Asociación explícita de puntos, publicación/escritura (`AC-SRV-04.3`),
  polling continuo — diferidos.
- Dashboard/UI — backend/contrato únicamente.

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `POST /devices/scan/mqtt` | entrada | REST | `hira-server/docs/openapi.yaml` (ampliar) |
| `GET /devices`, `GET /devices/{id}/candidates` | entrada | REST | ya existen, sin cambios |
| Mosquitto (broker real ya autenticado de `SRV-001`) | salida | adaptador paho-mqtt | interno |
| PostgreSQL (`devices`, `device_points_candidates`) | salida | `DeviceRepositoryPort` (reutilizado) | interno |

**Request de `POST /devices/scan/mqtt`**: `topic_pattern` (string, p. ej.
`"edificio/piso1/#"`).

## 4. Criterios de aceptación (EARS)
> A partir de `AC-SRV-04.2`/`.4`, confirmado en la ronda de elicitación.

- **RF-001** — CUANDO Admin u Operador invoca `POST /devices/scan/mqtt` con un
  `topic_pattern`, el sistema DEBE suscribirse a ese patrón y esperar mensajes
  durante **3 segundos** antes de responder.
- **RF-002** — CUANDO un mensaje llega en un topic durante la ventana, el
  sistema DEBE persistir/actualizar `devices` (`protocol='mqtt'`, `address` =
  `topic_pattern`, creándolo si no existe) y el candidato correspondiente en
  `device_points_candidates` (`object_type='mqtt_topic'`, `object_instance` =
  topic real, `present_value` = payload) — actualiza si ya existía, no duplica.
- **RF-003** — SI un usuario con rol Visor invoca `POST /devices/scan/mqtt`
  ENTONCES el sistema DEBE responder 403.
- **RF-004** — SI `topic_pattern` es inválido (rechazado por la librería MQTT
  al suscribirse) ENTONCES el sistema DEBE responder 400 con el sobre RFC 9457.
- **RF-005** — El sistema NUNCA DEBE promover automáticamente un candidato a
  una tabla de puntos operables (`SRV-ADR-012`) — mismo criterio que
  BACnet/Modbus.

## 5. Casos límite y manejo de errores
- **RF-006** — SI ningún mensaje llega durante la ventana ENTONCES el sistema
  DEBE responder 200 con una lista vacía de candidatos, sin crear `device`.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| Un `device` = el patrón de suscripción completo | Simple, sin inventar una heurística de agrupación por segmento de topic que Hira no puede adivinar sin una convención de proyecto | Inferir sub-dispositivos por segmento intermedio del topic | — |
| Ventana de escucha: 3 segundos (mismo criterio que BACnet) | Consistencia con el grupo; dispositivos MQTT típicos publican con frecuencia de segundos | Ventana más larga (10s) | — |
| Verificación contra el Mosquitto real de `SRV-001`, sin broker de test aparte | Ya existe autenticado y funcional (`VUL-SRV-001`); a diferencia de BACnet/Modbus, MQTT no necesita "simular" un dispositivo — el broker real ya cumple ese rol | Levantar un segundo broker Mosquitto solo para tests | — |
| Sin `device` si ningún mensaje llega durante la ventana | Mismo criterio que BACnet/Modbus — evita "devices fantasma" por un patrón inactivo | Crear el device igual, aunque no haya candidatos | — |
| Validación del `topic_pattern` delegada a la librería MQTT/broker | `paho-mqtt` ya valida la sintaxis al suscribirse; reimplementar esa validación en Hira sería duplicar lógica ya cubierta por la librería (Art. 10) | Validar con regex propia antes de tocar `paho-mqtt` | — |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — `POST /devices/scan/mqtt` NO DEBE tardar significativamente
  más que la ventana de escucha (3s).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-14).
