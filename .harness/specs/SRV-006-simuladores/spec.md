---
id: SPEC-SRV-006
tipo: spec
feature: SRV-006-simuladores
estado: approved
anchor_commit: ‹pendiente›
anchor_mode: advisory
covers:
  - hira-server/backend/**
  - hira-server/docs/openapi.yaml
  - docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-14 }
  fase_2: pendiente
actualizado: 2026-09-14
---

# SPEC-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT)

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Base:
> `SRV-ADR-014` (simuladores como ciudadanos de primera clase), `AC-SRV-05`
> (5.1–5.5), `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md`
> §Simuladores. Cuarta y última feature en que se partió `SRV-Sprint-3` — ver
> `memory/state.md` (2026-09-14). Construye sobre `SRV-003-bacnet-adapter`,
> `SRV-004-modbus-adapter` y `SRV-005-mqtt-scanning` (las 3 `verified`):
> reutiliza `devices`/`device_points_candidates` y los endpoints
> `POST /devices/scan/{bacnet,modbus,mqtt}` ya construidos, sin recrearlos.

## 1. Contexto del dominio
- **Por qué esta feature, si BACnet/Modbus/MQTT ya se verificaron sin ella:**
  las 3 features de protocolo usaron infraestructura de prueba ad-hoc, interna
  a sus propios tests (2 instancias `BAC0.lite()`, `pymodbus.simulator`,
  Mosquitto ya autenticado) — invisible y sin valor para un **usuario final**
  de Hira Server. Esta feature expone esa misma capacidad de "hablar el
  protocolo sin hardware" como una **funcionalidad de producto**: un
  integrador sin acceso todavía al hardware del cliente puede arrancar un
  dispositivo virtual gestionado por su propio Hira Server, diseñar y
  demostrar el proyecto contra él, y más tarde sustituirlo por hardware real
  cambiando solo configuración (`SRV-ADR-014`). Es la primera vez que algo en
  el sistema escribe `is_simulator=true` — la columna existe desde `SRV-003`
  sin productor.
- Límite de esta feature: gestiona el **ciclo de vida** (arrancar/detener) de
  simuladores que hablan el protocolo real en la red/broker, y su
  **registro** en `devices` con `is_simulator=true`. No reimplementa
  descubrimiento — el simulador, una vez corriendo, es descubrible por los
  endpoints de escaneo ya existentes (`SRV-003`/`004`/`005`) sin tocarlos.
  El Motor de Protocolos (polling/escritura sobre puntos *asociados*) sigue
  sin existir — no es requisito de esta feature que un simulador participe
  en polling; solo que sea indistinguible de hardware real en el nivel de
  protocolo y descubrimiento.

## 2. Alcance
### En alcance (propuesto)
- Los **3 protocolos en una sola spec** (transversal, no una por protocolo
  como BACnet/Modbus/MQTT): no hay mecanismo nuevo de descubrimiento que
  inventar por protocolo — es el mismo patrón (arrancar proceso → registrar
  `devices` → opcionalmente el escaneo ya existente lo confirma) aplicado 3
  veces. Coherente con la pista de `memory/state.md`: la más pequeña del
  grupo.
- `POST /simulators/bacnet`: arranca un simulador BACnet/IP (responde a
  Who-Is con el `device_instance` indicado; objetos BACnet iniciales
  opcionales — tipo/instancia/valor).
- `POST /simulators/modbus`: arranca un simulador Modbus TCP (host/puerto/
  `unit_id`; valores iniciales opcionales por tipo de registro).
- `POST /simulators/mqtt`: arranca un publicador MQTT (topic, valor/payload,
  intervalo de publicación en segundos — `AC-SRV-05.3`).
- **Registro inmediato en `devices`** (`is_simulator=true`) al arrancar,
  sin depender de que el usuario ejecute además un escaneo — el simulador
  arrancado sigue siendo un respondedor de protocolo real y por tanto
  también descubrible por `POST /devices/scan/{bacnet,modbus,mqtt}` si el
  usuario lo invoca, pero no es requisito para verlo en `GET /devices`.
- `GET /simulators`: lista los simuladores **actualmente en ejecución**
  (protocolo, dirección/identidad, `device_id`, hora de arranque).
- `DELETE /simulators/{device_id}`: detiene el proceso; **no** borra el
  dispositivo ni sus candidatos — el flag `is_simulator=true` es permanente
  en esta feature (ver Fuera de alcance).
- Corrección necesaria en `upsert_device` (usado por `SRV-003`/`004`/`005`):
  un escaneo real posterior sobre la misma `(protocol, address)` de un
  simulador **no debe** resetear `is_simulator` a `false`.
- RBAC: arrancar/detener simuladores (`POST`/`DELETE`) — **solo Admin**
  (crea procesos y listeners de red reales, más sensible que un escaneo de
  3s de solo lectura). `GET /simulators` — Admin y Operador, mismo criterio
  que `GET /devices`.
- Verificación de integración real: cada simulador arrancado vía su propio
  endpoint, confirmado con un cliente real del protocolo (BAC0/pymodbus/
  paho-mqtt) — mismo rigor de evidencia que `SRV-003`/`004`/`005`, ya no
  como infraestructura de test interna sino como el propio producto bajo
  prueba.

### Fuera de alcance (propuesto)
- **Quitar el flag `is_simulator`** ("simulador → dispositivo real") con
  confirmación explícita (`AC-SRV-05.5`) — requiere edición/eliminación de
  `devices`, que no existe todavía (no hay `PATCH`/`DELETE /devices/{id}`).
  Se difiere a una feature de gestión de dispositivos; construir solo la
  mitad (el guardado, sin el mecanismo de edición que protege) sería un
  parche (Art. 10).
- Persistencia del proceso simulador entre reinicios de Hira Server — un
  reinicio detiene todos los simuladores en ejecución; sus filas en
  `devices`/`device_points_candidates` no se tocan (quedan visibles vía
  `GET /devices`, ausentes de `GET /simulators` hasta rearrancarlos).
- Límite de recursos / cupo máximo de simuladores concurrentes — sin
  evidencia de necesidad todavía; se añade si aparece un caso real.
- BACnet MSTP, Modbus RTU — mismo criterio que `SRV-003`/`004` (requieren
  hardware serial real para verificar con evidencia genuina).
- Participación de simuladores en polling/escritura del Motor de Protocolos
  — depende de la feature de asociación explícita de puntos, aún no
  existente (diferida desde `SRV-003 §6`).
- Dashboard/UI de simuladores — backend/contrato únicamente; se especifica
  con `experto-ux-ui` cuando llegue el sprint de frontend.

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `POST /simulators/bacnet` | entrada | REST | `hira-server/docs/openapi.yaml` (ampliar) |
| `POST /simulators/modbus` | entrada | REST | ídem |
| `POST /simulators/mqtt` | entrada | REST | ídem |
| `GET /simulators` | entrada | REST | ídem |
| `DELETE /simulators/{device_id}` | entrada | REST | ídem |
| Red BACnet/IP, Modbus TCP, broker Mosquitto | salida | mismos adaptadores de transporte de `SRV-003`/`004`/`005`, en modo "servidor/publicador" en vez de "cliente/suscriptor" | interno, sin contrato externo |
| PostgreSQL (`devices`, `device_points_candidates`) | salida | `DeviceRepositoryPort` (reutilizado; `upsert_device` ajustado) | interno |

**`POST /simulators/bacnet`**: `device_instance` (int, requerido), `objects`
(lista opcional de `{object_type, object_instance, present_value}` — sin
objetos, responde a Who-Is pero no ofrece candidatos hasta que se
configuren o se amplíe en una versión posterior).

**`POST /simulators/modbus`**: `host`, `port`, `unit_id`, valores iniciales
opcionales por tipo de registro (mismo shape que
`ScanModbusRequest.{coils,discrete_inputs,holding_registers,input_registers}`,
pero con valores en vez de rangos a leer).

**`POST /simulators/mqtt`**: `topic` (string, topic concreto — no wildcard,
a diferencia de `topic_pattern` de `SRV-005`), `payload` (string), `interval_seconds`
(int, > 0).

**Respuesta común** (`SimulatorOut`): `device_id` (el `id` en `devices`),
`protocol`, `address` (mismo formato que `SRV-003`/`004`/`005`: instance
number BACnet, `"host:port:unit_id"` Modbus, topic MQTT), `started_at`.

**El estado "en ejecución" vive en memoria/tiempo de ejecución del proceso
de Hira Server** (decisión de Fase 2 cómo — diccionario en memoria, tarea
asyncio, u otro), no en una columna de `devices`: `devices` solo guarda el
flag permanente `is_simulator`. `GET /simulators` refleja ese estado en
memoria, no una consulta a `devices`.

## 4. Criterios de aceptación (EARS)
> A partir de `AC-SRV-05.1`–`.4`, confirmado en la ronda de elicitación.
> `AC-SRV-05.5` diferido — ver §2 Fuera de alcance.

- **RF-001** — CUANDO Admin invoca `POST /simulators/bacnet` con
  `device_instance` válido, el sistema DEBE arrancar un simulador BACnet/IP
  que responde a Who-Is con ese `device_instance` y registrar/actualizar en
  `devices` un dispositivo (`protocol='bacnet'`, `is_simulator=true`) con
  sus `objects` (si los hay) como candidatos en `device_points_candidates`.
- **RF-002** — CUANDO Admin invoca `POST /simulators/modbus` con
  `host`/`port`/`unit_id`, el sistema DEBE arrancar un servidor Modbus TCP
  que responde en esa dirección y registrar/actualizar en `devices` un
  dispositivo (`protocol='modbus'`, `is_simulator=true`) con los valores
  iniciales indicados como candidatos.
- **RF-003** — CUANDO Admin invoca `POST /simulators/mqtt` con `topic`/
  `payload`/`interval_seconds`, el sistema DEBE arrancar un publicador que
  publique `payload` en `topic` cada `interval_seconds` segundos y
  registrar/actualizar en `devices` un dispositivo (`protocol='mqtt'`,
  `is_simulator=true`).
- **RF-004** — SI un usuario con rol Operador o Visor invoca cualquiera de
  `POST /simulators/{bacnet,modbus,mqtt}` o `DELETE /simulators/{device_id}`
  ENTONCES el sistema DEBE responder 403.
- **RF-005** — SI un usuario con rol Visor invoca `GET /simulators`
  ENTONCES el sistema DEBE responder 403; Admin y Operador DEBEN recibir 200.
- **RF-006** — SI la dirección/identidad solicitada en `POST /simulators/*`
  ya corresponde a un dispositivo real (`is_simulator=false`) o a un
  simulador ya en ejecución ENTONCES el sistema DEBE rechazar con 409, sin
  arrancar ningún proceso.
- **RF-007** — CUANDO la dirección solicitada coincide con un simulador
  previamente registrado pero no en ejecución (p. ej. tras un reinicio), el
  sistema DEBE reanudarlo reutilizando el mismo `device_id`, sin crear un
  dispositivo duplicado.
- **RF-008** — CUANDO un escaneo real (`POST /devices/scan/{bacnet,modbus,
  mqtt}`, `SRV-003`/`004`/`005`) encuentra un dispositivo cuya `(protocol,
  address)` ya está registrada como simulador, el sistema NO DEBE
  sobrescribir `is_simulator` a `false` — corrige `upsert_device` para
  preservarlo en cualquier `ON CONFLICT DO UPDATE`.
- **RF-009** — CUANDO Admin invoca `DELETE /simulators/{device_id}` sobre un
  simulador en ejecución, el sistema DEBE detener el proceso sin eliminar el
  dispositivo ni sus candidatos de `devices`/`device_points_candidates`.
- **RF-010** — CUANDO se invoca `GET /simulators`, el sistema DEBE listar
  únicamente los simuladores actualmente en ejecución — ni dispositivos
  reales ni simuladores detenidos.
- **RF-011** — El sistema NO DEBE ofrecer, en esta feature, un mecanismo
  para eliminar el flag `is_simulator` de un dispositivo (`AC-SRV-05.5`
  diferido — ver §2).

## 5. Casos límite y manejo de errores
- **RF-012** — SI `DELETE /simulators/{device_id}` se invoca sobre un
  `device_id` sin simulador actualmente en ejecución (no existe, es
  `is_simulator=false`, o ya está detenido) ENTONCES el sistema DEBE
  responder 404.
- **RF-013** — SI el proceso de Hira Server se reinicia ENTONCES todos los
  simuladores en ejecución se detienen; sus registros en `devices`/
  `device_points_candidates` permanecen sin cambios.
- **RF-014** — SI el `payload`/`topic` de `POST /simulators/mqtt` es
  inválido (rechazado por la librería MQTT al publicar) ENTONCES el sistema
  DEBE responder 400 con el sobre RFC 9457.
- **RF-015** — SI `interval_seconds` es ≤ 0 ENTONCES el sistema DEBE
  responder 400, sin arrancar el publicador.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| Los 3 protocolos en una sola spec (`SRV-006`) | Mismo patrón de arranque+registro aplicado 3 veces, sin mecanismo de descubrimiento nuevo que inventar — a diferencia de `SRV-003`/`004`/`005`, cada una con un protocolo con reglas propias de escaneo | Una spec por protocolo (`SRV-006/007/008`) | — |
| Registro inmediato en `devices` al arrancar (no depende de un escaneo posterior) | UX determinista: el integrador no debe esperar una ventana de escaneo (3s) ni adivinar si el simulador "se dejó ver"; el simulador sigue siendo descubrible si se escanea, sin lógica duplicada (RF-008 solo protege el flag) | Requerir que el usuario ejecute además `POST /devices/scan/*` para que el simulador aparezca en `devices` (más fiel a `AC-SRV-05.1` literal, pero UX peor y acoplada a una ventana de tiempo) | `SRV-ADR-014` |
| `is_simulator` permanente en esta feature; sin mecanismo de "des-flag" | `AC-SRV-05.5` exige que quitar el flag requiera confirmación explícita — construirlo a medias (guardar sin poder editar) sería un parche; requiere una feature de edición/eliminación de `devices` que no existe | Añadir un `PATCH /devices/{id}` mínimo solo para esto | — (diferido, ver §2) |
| `upsert_device` deja de sobrescribir `is_simulator` en conflicto | Sin esto, un escaneo real posterior resetearía a `false` un simulador ya registrado (hallazgo del código actual, `SRV-003`/`004`/`005`) — bug latente que esta feature expone y corrige de raíz (Art. 10) | Dejarlo como está, documentando el riesgo | — |
| `POST`/`DELETE /simulators/*` solo Admin; `GET /simulators` Admin+Operador | Arrancar un simulador crea un proceso/listener de red real — más sensible que un escaneo de solo lectura de 3s; la lectura del estado sigue el mismo criterio que `GET /devices` | Mismo criterio uniforme Admin+Operador que `SRV-003`/`004`/`005` para todo | — |
| Sin límite de simuladores concurrentes ni persistencia entre reinicios | Sin evidencia de necesidad; anticiparlo sería Art. 10 (over-engineering); un reinicio ya deja claro el estado (RF-013) | Cupo máximo configurable, o auto-rearranque al iniciar Hira Server | — |
| MQTT: `topic` concreto (no wildcard) en `POST /simulators/mqtt` | El simulador publica a un topic conocido y fijo — a diferencia de `SRV-005` (que suscribe con wildcard para *descubrir*), aquí el sistema es quien define el topic | Aceptar wildcard también en el simulador (sin sentido: no hay nada que "coincida" al publicar) | — |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — Arrancar o detener un simulador (`POST`/`DELETE
  /simulators/*`) NO DEBE bloquear el event loop principal de la API — el
  resto de endpoints (`/devices/*`, `/auth/*`, etc.) DEBEN seguir
  respondiendo con normalidad mientras hay simuladores en ejecución.

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Confirmado por Carlos (2026-09-14): nombre
  `SRV-006-simuladores`; RBAC de `POST`/`DELETE /simulators/*` solo Admin
  (`GET /simulators` Admin+Operador); registro inmediato en `devices` al
  arrancar (sin depender de un escaneo posterior); resto de §6 aprobado tal
  cual (3 protocolos en una sola spec, `AC-SRV-05.5` diferido, corrección de
  `upsert_device`, sin límite de concurrencia/persistencia entre reinicios).
