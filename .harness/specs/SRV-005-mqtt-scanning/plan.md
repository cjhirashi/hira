---
id: PLAN-SRV-005
tipo: plan
feature: SRV-005-mqtt-scanning
estado: approved
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# PLAN-SRV-005 · Escaneo MQTT — suscripción wildcard y candidatos

> El *cómo*. Traduce cada `RF-001..RF-006`/`RNF-001` de `spec.md` al patrón
> **Hexagonal** (Constitución Art. 1–2, `SRV-ADR-017`), construyendo sobre
> `SRV-004-modbus-adapter` (`verified`): **reutiliza sin tocar**
> `core/security/dependencies.py::require_role`, `core/errors.py::
> ProblemDetailError` (+ `schemas/errors.py`, `E-ADR-003`), `core/ports/
> device_repository_port.py::DeviceRepositoryPort` (ya soporta cualquier
> `protocol`, `'mqtt'` ya está en el `CHECK` de `models/device_model.py`
> desde `SRV-003`), `adapters/db/device_repository_adapter.py::
> PostgreSQLDeviceRepository` (**sin migración nueva**),
> `adapters/factory.py::get_device_repository_port()` (se usa tal cual) y
> `routers/devices.py` (`GET /devices`, `GET /devices/{id}/candidates`,
> `POST /devices/scan/bacnet`, `POST /devices/scan/modbus` — **no se
> tocan**). Quinta feature real de `hira-server/backend/`; tercer adaptador
> de protocolo de campo, primero **push-based** (a diferencia de BACnet/
> Modbus, request/response) — reutiliza `paho-mqtt` (ya en
> `requirements.txt` desde `SRV-001-walking-skeleton`, usado por
> `adapters/mqtt/mosquitto_adapter.py::MosquittoAdapter`, el `NotificationPort`
> de notificaciones salientes) con un **adaptador nuevo y separado** para el
> puerto de escaneo — ver Registro de decisiones.

## 0. Gates de simplicidad
- [x] **Simplicity** — 1 puerto nuevo (`MqttScanTransportPort`, un solo
      método `listen`), 0 tablas nuevas (reutiliza `devices`/
      `device_points_candidates`), 1 endpoint nuevo
      (`POST /devices/scan/mqtt`), 1 función pura nueva
      (`core/mqtt_topic_key.py::topic_instance_key`, necesaria por un
      conflicto real de esquema — ver Registro de decisiones). Sin
      variables de entorno nuevas en `Settings`: reutiliza
      `mqtt_broker_host`/`mqtt_user`/`mqtt_password` ya existentes
      (`SRV-001`), mismas que usa `get_notification_port()`.
- [x] **Anti-Abstraction** — Un único método de puerto (`listen`) cubre
      suscripción + acumulación de mensajes durante la ventana — no se
      exponen `subscribe()`/`collect()`/`unsubscribe()` por separado sin un
      caso de uso real que los necesite. `MqttInvalidTopicPatternError` se
      modela como excepción de dominio (mismo patrón que
      `BacnetReadTimeoutError`, `SRV-003`) — a diferencia de
      `ModbusReadFailure` (`SRV-004`, valor de retorno): aquí un patrón de
      suscripción inválido es **excepcional por diseño** (una sola
      evaluación por invocación, no 500 evaluaciones independientes como en
      un rango Modbus) — ver Registro de decisiones.
- [x] **Integration-First** — `hira-server/docs/openapi.yaml` se amplía
      **antes** que `routers/devices.py` (paso 4 de §6); `core/ports/
      mqtt_scan_transport_port.py` se define antes que `adapters/mqtt/
      mqtt_scan_adapter.py`. El comportamiento real de `paho-mqtt==2.1.0`
      (validación de `topic_pattern` al suscribirse, comportamiento de la
      ventana de escucha con un publisher real) se **verificó con ejecución
      real** en esta fase, contra el Mosquitto real del compose de
      `SRV-001` — ver §5, nota de investigación. Ninguna duda de API queda
      abierta para Fase 4, mismo estándar que `SRV-004-modbus-adapter/
      plan.md`.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/device_scan_service.py` solo importa de `core/ports/` (`MqttScanTransportPort` nuevo, `DeviceRepositoryPort` ya existente) + `core/mqtt_topic_key.py`/`core/errors.py`/`core/logger.py` (todos `core/`); `adapters/factory.py` inyecta `MqttScanAdapter`. Ningún router instancia un adaptador directamente (`SRV-ADR-017`, overlay `hira-server/CLAUDE.md`: "si un módulo de `services/` importa... `paho`... viola la arquitectura"). |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo (`core/mqtt_topic_key.py`) sin mocks; coordinación (`services/device_scan_service.py::scan_mqtt`) con dobles de `MqttScanTransportPort`/`DeviceRepositoryPort`; adaptador `paho-mqtt` con el **Mosquitto real** del compose de `SRV-001` (`spec.md §2`, ya decidido — sin broker de test aparte), con un segundo cliente `paho-mqtt` como publisher de prueba para verificar la ventana de 3s de forma determinista; router con `TestClient` + dobles propios (mismo patrón que `test_devices_router.py`); sistema (e2e) con Mosquitto + Postgres reales. |
| Art. 4 (persistencia) | `DeviceRepositoryPort` (`SRV-003`, `verified`) es el `StoragePort` de dominio reutilizado tal cual — esta feature añade filas con `protocol='mqtt'` al mismo esquema multi-protocolo (`CHECK` ya lo permite desde `SRV-003`). |
| Art. 5 (seguridad) | `MqttScanAdapter` se conecta **siempre** con `mqtt_user`/`mqtt_password` de `Settings` (nunca anónimo) — mismo criterio que `MosquittoAdapter`/`VUL-SRV-001` (`SRV-001`, ya resuelto: el broker real tiene `allow_anonymous false`). RBAC ya cubierto por `SRV-002`/reutilizado tal cual de `SRV-003`/`SRV-004` (`require_role("admin", "operador")`, RF-003). |
| Art. 6 (contratos/errores) | `POST /devices/scan/mqtt` usa el sobre RFC 9457 solo donde hay error de negocio: 403 `insufficient-role` (reutilizado) y 400 `mqtt-invalid-topic-pattern` (slug **nuevo**, RF-004). `type` = `https://hira.dev/errors/<slug>` (`E-ADR-003`, catálogo distribuido por `plan.md`). |
| Art. 10 (regla de raíz) | `MqttScanTransportPort` nuevo, **no** se fuerza en `NotificationPort` (dominio y ciclo de vida de conexión distintos — ver Registro de decisiones, mismo razonamiento ya aplicado 4 veces en el ecosistema: `DeviceRepositoryPort` vs. `DatabasePort`/`UserRepositoryPort`, `ModbusTransportPort` vs. `BacnetTransportPort`). El conflicto real entre `spec.md §2` (`object_instance` = topic real, un string) y el esquema ya `verified` de `device_points_candidates.object_instance` (`INTEGER NOT NULL`, `SRV-003`) se resuelve en el **puerto/servicio** (una función pura de traducción determinista), no con un parche de esquema ad-hoc ni con un cast silencioso — ver Registro de decisiones, **marcado para confirmación en Gate 2**. |
| Art. 11 (documentación) | §8 de este plan — 1 fila, tarea `[doc]` en `tasks.md` (actualiza la nota de estado ya dejada por `SRV-003`/`SRV-004`, no crea una sección nueva). |

## Registro de decisiones de diseño (nuevas de este plan)
| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| `MqttScanTransportPort` con **un solo método** (`listen(topic_pattern, window_seconds) -> list[MqttTopicMessage]`) que suscribe, acumula y retorna | MQTT es push-based: no hay una operación de "leer" análoga a BACnet/Modbus — el único caso de uso de esta feature es "suscribirse y ver qué llega en una ventana fija" (`spec.md §1`). Separar `subscribe()`/`wait()`/`unsubscribe()` en el puerto expondría el ciclo de vida de una conexión MQTT (estado mutable) a `services/`, que debe seguir siendo async-simple y sin gestionar sockets (Anti-Abstraction, `plan.md §0`) | Puerto con `subscribe()`/`collect_for(seconds)`/`disconnect()` separados — más "flexible" pero sin un segundo caso de uso real que lo necesite hoy |
| Adaptador nuevo `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter` — **archivo separado** de `adapters/mqtt/mosquitto_adapter.py::MosquittoAdapter`, misma carpeta | Ambos usan `paho-mqtt` contra el mismo broker físico, pero implementan **puertos de dominio distintos** con ciclos de vida de conexión incompatibles: `MosquittoAdapter` es una conexión **persistente** (una vez en `lifespan`, con backoff 1s/2s/4s, reutilizada para `ping()`); `MqttScanAdapter` es una conexión **efímera por request** (conecta, suscribe, espera `window_seconds`, desconecta — una vez por cada `POST /devices/scan/mqtt`). Mezclarlos en una clase forzaría un solo objeto a sostener dos modelos de reconexión/estado distintos (violación de responsabilidad única) y complicaría los tests de ambos (`test_mqtt_security.py`/futuros tests de `MosquittoAdapter` no deben arrancar/parar un ciclo de escaneo, y viceversa). Mismo criterio que `adapters/bacnet/bac0_adapter.py` y `adapters/modbus/pymodbus_adapter.py` siendo archivos separados aunque ambos son "adaptadores de protocolo de campo" | (a) Añadir `listen()` como método nuevo de `MosquittoAdapter` (un solo archivo/clase implementando 2 `Protocol` distintos) — descartado por mezclar ciclos de vida de conexión incompatibles; (b) un `MqttClientFactory` compartido entre ambos adaptadores para no duplicar la construcción de `mqtt.Client` — descartado por Anti-Abstraction: la construcción es 3 líneas (`mqtt.Client(...)`, `username_pw_set(...)`), extraerla a una fábrica es indirección sin beneficio real hoy |
| `MqttScanAdapter` usa `paho.mqtt.client.CallbackAPIVersion.VERSION2` (API moderna, no deprecada) — **no** replica el patrón `mqtt.Client(client_id=..., protocol=mqtt.MQTTv311)` sin `callback_api_version` que ya usa `MosquittoAdapter`/`test_mqtt_security.py` (API v1, deprecada en `paho-mqtt==2.1.0`, confirmado con ejecución real — ver §5) | Código **nuevo**: no hay razón para escribirlo ya deprecado. `MosquittoAdapter`/`test_mqtt_security.py` no se tocan en este plan (Art. 10: corregir la causa raíz de *esta* feature, no salir a refactorizar código no relacionado y ya `verified` sin que ningún RF lo pida) — queda como deuda pre-existente, fuera de alcance | Replicar el estilo v1 "por consistencia visual" — genera un `DeprecationWarning` nuevo a propósito, sin beneficio |
| RF-004: `MqttScanAdapter.listen()` captura el `ValueError` que **`paho-mqtt` ya lanza de forma síncrona** dentro de `client.subscribe(topic_pattern)` para patrones sintácticamente inválidos, y lo traduce a `MqttInvalidTopicPatternError` (dominio) — la validación ocurre **antes** de tocar la red (ni siquiera se conecta al broker con ese intento, ver nota de investigación §5) | Verificado con ejecución real (§5): `client.subscribe()` valida el *topic filter* client-side (longitud, caracteres de wildcard mal ubicados, QoS fuera de rango) y lanza `ValueError` de forma **síncrona**, sin esperar CONNACK/SUBACK del broker — exactamente el criterio ya cerrado en `spec.md §6` ("validación delegada a la librería MQTT/broker... `paho-mqtt` ya valida la sintaxis al suscribirse") | Validar el patrón con una regex propia en `core/` antes de llamar al puerto — descartado explícitamente en `spec.md §6` (duplicaría lógica ya cubierta por la librería, Art. 10) |
| `MqttInvalidTopicPatternError` es una **excepción** (dominio), no un valor de retorno — a diferencia de `ModbusReadFailure` (`SRV-004`, valor de retorno) | Un patrón de suscripción inválido es una única evaluación por invocación completa del escaneo (no una de N direcciones independientes como en un rango Modbus, donde "no responde" es el resultado esperado de la mayoría) — aquí es, estructuralmente, el mismo tipo de fallo que `BacnetReadTimeoutError` (`SRV-003`): una condición que aborta *todo* el intento, no un elemento de una colección que se puede seguir procesando | Modelarlo como un valor de retorno (`MqttSubscribeFailure`) envuelto en una lista de 1 elemento — fuerza a `services/` a un `isinstance` para lo que es, en efecto, un `raise` de una sola rama |
| **Conflicto real de esquema resuelto**: `object_instance` (columna `INTEGER NOT NULL`, `models/device_model.py`, parte de `UNIQUE(device_id, object_type, object_instance)`, `SRV-003`, `verified`, **no se toca**) no puede almacenar el topic real como texto (`spec.md §2` lo describe literalmente así, "topic real recibido"). Resuelto con `core/mqtt_topic_key.py::topic_instance_key(topic: str) -> int` — `zlib.crc32(topic.encode("utf-8")) & 0x7FFFFFFF` (determinista: el mismo topic siempre produce la misma clave, requisito de RF-002 "actualiza si ya existía, no duplica" en escaneos repetidos del mismo patrón) — y `object_name` (columna `String(255)`, ya nullable, ya usada por BACnet para su nombre legible) pasa a llevar el **topic real completo** como texto, que es lo que expone `GET /devices/{id}/candidates` para que el integrador lo lea | Cambiar el tipo de `object_instance` a `String`/`Text` afectaría una columna **compartida** por BACnet (`object_instance` = número de instancia del objeto) y Modbus (`object_instance` = dirección de registro) — ambos protocolos ya `verified`, ya en producción del propio proceso de desarrollo; alterar su tipo es una migración destructiva sin beneficio para ellos, y viola el criterio ya cerrado en `SRV-003-bacnet-adapter/plan.md §3`/`SRV-004-modbus-adapter/plan.md §3` de que la columna es `INTEGER`. CRC32 de 32 bits sobre el universo de topics reales de un proyecto de automatización de edificios (cientos, no millones, por dispositivo/patrón) tiene una probabilidad de colisión despreciable para este caso de uso — **no** es un identificador criptográfico, es una clave de deduplicación determinista dentro del alcance de un solo `device` (patrón de suscripción) | (a) Cambiar `object_instance` a `String`/`Text` — migración destructiva sobre 2 features `verified`, fuera de alcance de esta feature y del propio Art. 10 (no se "corrige" algo que no está roto para BACnet/Modbus); (b) contador secuencial por `device` en vez de hash — descartado porque rompe la idempotencia de RF-002: un segundo escaneo del mismo patrón asignaría un contador distinto al mismo topic real, produciendo un candidato **duplicado** en vez de actualizar el existente; (c) usar `object_type` para llevar el topic real y una constante para `object_instance` — descartado porque `object_type` es la columna que ya lleva la semántica de "tipo" (`"mqtt_topic"`, consistente con BACnet/Modbus, que usan `object_type` para el tipo de objeto/registro, no para un identificador único) |
| `object_name` (`String(255)`) sin ampliar a `Text` para el topic real, aun cuando MQTT permite topics de hasta 65535 bytes | `spec.md` no fija un límite de longitud de topic ni lo discute — los ejemplos del dominio (`"edificio/piso1/ahu1/temp"`) caben cómodamente en 255 caracteres; ampliar la columna sin un caso de uso real que la exceda sería anticipación (Art. 10). Riesgo residual documentado: un topic real >255 caracteres se truncaría al persistir — **no cubierto** por esta feature, no reportado como `spec.md` no lo exige; si aparece en producción, es una corrección de causa raíz futura (ampliar la columna vía migración, `RF-`/`ADR-` explícito, Art. 10) | Ampliar `object_name` a `Text` preventivamente — over-engineering sin caso de uso real hoy |
| Deduplicación "último mensaje gana por topic" (`spec.md §2`, `present_value` = payload del último mensaje) se hace en **`services/device_scan_service.py::scan_mqtt`** (agrupa `list[MqttTopicMessage]` en un `dict[str, MqttTopicMessage]` por orden de llegada), no en el adaptador | Es una regla de negocio explícita de `spec.md` ("cada topic real... es un candidato... `present_value` = payload del **último** mensaje"), no un detalle de transporte — mismo criterio que `scan_modbus` hace su propia agrupación/validación en `services/`, dejando al puerto devolver datos crudos sin interpretar | Deduplicar dentro de `MqttScanAdapter.listen()` (el adaptador ya podría acumular en un `dict` en el callback `on_message`) — técnicamente más simple, pero mueve una regla de negocio explícita del spec fuera de `services/`, donde el resto de la coordinación vive |
| `MqttScanAdapter.listen()` decodifica el payload MQTT (`bytes`) a `str` con `payload.decode("utf-8", errors="replace")` dentro del adaptador, antes de construir `MqttTopicMessage` | `core/ports/` no debe conocer que MQTT transmite `bytes` — mismo criterio que `ModbusRegisterReading.value` (el adaptador ya traduce el tipo crudo de `pymodbus` al tipo de dominio). `errors="replace"` evita que un payload binario no-UTF8 (fuera de alcance declarado, `spec.md` no contempla payloads binarios) tumbe el escaneo completo | Exponer `payload: bytes` en `MqttTopicMessage` y decodificar en `services/` — filtraría un detalle de transporte (bytes vs. texto) a la capa de dominio |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks
- **`core/mqtt_topic_key.py`** ← única regla de negocio pura nueva de esta
  feature: `topic_instance_key(topic: str) -> int` (RF-002: resuelve el
  conflicto de esquema del Registro de decisiones — `zlib.crc32(topic.encode
  ("utf-8")) & 0x7FFFFFFF`, determinista, siempre `>= 0`, cabe en
  `INTEGER` de Postgres). Lanza `ValueError` si `topic` está vacío.
- **`core/errors.py`** (ya existe) — reutilizado tal cual; esta feature
  añade un sitio de uso nuevo (`services/device_scan_service.py`) del slug
  **nuevo** `mqtt-invalid-topic-pattern` (400, RF-004) — ver §4.

### Coordinación (casos de uso / fronteras de entrada)
- **`services/device_scan_service.py`** (ya existe de `SRV-003`/`SRV-004`,
  se amplía con una tercera función de escaneo, mismo módulo — mismo
  criterio ya registrado: mismo dominio de coordinación, misma dependencia
  de `DeviceRepositoryPort`):
  - Constante nueva: `MQTT_SCAN_WINDOW_SECONDS = 3.0` (RF-001).
  - `scan_mqtt(*, topic_pattern: str, transport: MqttScanTransportPort, device_repo: DeviceRepositoryPort) -> list[DeviceCandidateRecord]` ← **RF-001, RF-002, RF-004, RF-005, RNF-001** (RF-006 es la ausencia de un `device` cuando la ventana no captura nada; ver abajo):
    1. `try: messages = await transport.listen(topic_pattern, MQTT_SCAN_WINDOW_SECONDS)` — **RF-001**.
       `except MqttInvalidTopicPatternError as exc: raise ProblemDetailError(400, ".../mqtt-invalid-topic-pattern", "Patrón de topic MQTT inválido", ...)` — **RF-004**, antes de tocar `device_repo`.
    2. Si `messages` está vacío: `return []` — **RF-006** (sin `device_repo.upsert_device`, sin device "fantasma").
    3. Agrupa `messages` en `last_by_topic: dict[str, MqttTopicMessage]`
       (recorre en orden de llegada, cada topic repetido sobreescribe al
       anterior — último mensaje gana, `spec.md §2`).
    4. `device = await device_repo.upsert_device(name=f"MQTT {topic_pattern}", protocol="mqtt", address=topic_pattern, is_simulator=False)` — **RF-002** (una sola vez, solo si `messages` no estaba vacío).
    5. Por cada `(topic, msg)` en `last_by_topic.items()`:
       `candidate = await device_repo.upsert_candidate(device_id=device.id, object_type="mqtt_topic", object_instance=topic_instance_key(topic), object_name=topic, present_value=msg.payload, units=None)` — **RF-002**; `candidates.append(candidate)`.
    6. Retorna `candidates`.
  - **RF-005** (nunca promover un candidato a tabla operable) se cumple por
    **omisión de diseño**, igual que `scan_bacnet`/`scan_modbus`:
    `services/device_scan_service.py` sigue sin ningún método que escriba
    en una tabla `points` — verificado por inspección de imports del
    módulo en el test de coordinación (mismo test, ya existente, se
    reutiliza sin cambios de intención).
  - **RNF-001**: `listen()` es la única llamada de I/O de `scan_mqtt` — su
    duración está acotada por diseño a `MQTT_SCAN_WINDOW_SECONDS` (más el
    tiempo de conexión/suscripción, medido en §5) — el resto de `scan_mqtt`
    es CPU/DB local, sin overhead adicional significativo sobre la ventana.

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| Mosquitto (broker real ya autenticado de `SRV-001`) — suscripción wildcard, captura de mensajes durante una ventana | Descubrir topics activos de un patrón de suscripción | `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter` implementa `MqttScanTransportPort` con `paho-mqtt==2.1.0` real (ya en `requirements.txt` desde `SRV-001`, sin cambio de versión) |
| PostgreSQL (`devices`, `device_points_candidates`) | Repositorio de dominio de dispositivos y candidatos | `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository` (`SRV-003`, **ya existe, sin cambios**) |

#### `core/ports/mqtt_scan_transport_port.py` (nuevo)
```python
from dataclasses import dataclass
from typing import Protocol


class MqttInvalidTopicPatternError(Exception):
    """`topic_pattern` rechazado por la librería MQTT al suscribirse (RF-004).
    Señal de dominio, no la excepción cruda de `paho-mqtt` — mismo criterio
    que `BacnetReadTimeoutError` (`SRV-003`)."""


@dataclass(frozen=True)
class MqttTopicMessage:
    """Un mensaje recibido en un topic real durante la ventana de escucha
    (RF-001, RF-002). `payload` ya decodificado a texto por el adaptador
    (`plan.md §1`, Registro de decisiones)."""

    topic: str
    payload: str


class MqttScanTransportPort(Protocol):
    async def listen(
        self, topic_pattern: str, window_seconds: float
    ) -> list[MqttTopicMessage]:
        """Se suscribe a `topic_pattern` (wildcard MQTT, p. ej.
        `edificio/piso1/#`) y acumula todos los mensajes recibidos durante
        `window_seconds` (RF-001), en el orden en que llegaron — puede haber
        varios mensajes del mismo topic; la deduplicación es responsabilidad
        de quien llama (`services/device_scan_service.py::scan_mqtt`, RF-002).
        Lista vacía si ningún mensaje llega (RF-006).

        Lanza `MqttInvalidTopicPatternError` si `topic_pattern` es
        sintácticamente inválido (RF-004) — la validación ocurre al
        suscribirse, **antes** de esperar la ventana completa (verificado
        con ejecución real, `plan.md §5`)."""
        ...
```

### Adaptadores de entrada
- `routers/devices.py` (ya existe, se amplía con un endpoint nuevo — los 4
  endpoints existentes **no se tocan**):
  - `POST /devices/scan/mqtt` — `require_role("admin", "operador")` (RF-003,
    ya cubierto por la `dependencies=[Depends(require_role(...))]` del
    `APIRouter`, sin cambios); valida el body con
    `schemas/devices.py::ScanMqttRequest`; invoca
    `services/device_scan_service.py::scan_mqtt` con
    `MqttScanTransportPort`/`DeviceRepositoryPort` inyectados vía
    `Depends(adapters.factory.*)`; responde 200 con
    `list[DeviceCandidateOut]` (puede ser `[]`, RF-006 — mismo *shape* de
    respuesta que `POST /devices/scan/modbus`, mismo razonamiento: el
    llamador ya conoce el `topic_pattern` que pidió escanear, lo que aporta
    valor es la lista de topics reales descubiertos). `ProblemDetailError`
    (400, RF-004) propaga sin captura explícita — el `exception_handler`
    ya registrado en `main.py` la traduce a HTTP.
  - No instancia `MqttScanAdapter`/`PostgreSQLDeviceRepository`
    directamente (`SRV-ADR-017`).

### `adapters/factory.py` (se amplía)
- Nueva función `get_mqtt_scan_transport_port() -> MqttScanTransportPort`:
  nace en el **mismo paso** en que nace el endpoint del router (paso 5 de
  §6), con un **doble in-memory** (`_PlaceholderMqttScanTransport`,
  `listen()` siempre retorna `[]` — sin `paho-mqtt` real) — mismo patrón
  aplicado ya 5 veces en este ecosistema (`get_database_port`,
  `get_cache_port`, `get_notification_port`, `get_bacnet_transport_port`,
  `get_modbus_transport_port`): `MqttScanAdapter` real llega después (paso
  6) sin cambiar la firma.
- Cacheada a nivel de módulo (singleton perezoso por proceso), mismo patrón
  que las 7 funciones ya existentes. `get_device_repository_port()`,
  `get_notification_port()` (`MosquittoAdapter`, `NotificationPort` de
  `SRV-001`) **no se tocan** — se reutilizan tal cual; `get_mqtt_scan_transport_port()`
  es una función **independiente**, no una variante de
  `get_notification_port()` (ver Registro de decisiones).

## 3. Modelo de datos
**Sin migración nueva.** Reutiliza `devices`/`device_points_candidates`
(`hira-server/backend/models/device_model.py`, ya `verified` desde
`SRV-003-bacnet-adapter`). El `CHECK (protocol IN ('bacnet', 'modbus',
'mqtt'))` de `devices` ya admite `'mqtt'` desde que se escribió. Esta
feature solo añade **filas** con `protocol='mqtt'`, sin tocar
`models/device_model.py`, `models/base.py` ni `alembic/env.py`.

`devices.address` para MQTT: el `topic_pattern` de suscripción tal cual
(p. ej. `"edificio/piso1/#"`, `spec.md §2`) — cabe en el `VARCHAR(255)`
existente (patrones de suscripción reales son cortos, mismo criterio que
BACnet/Modbus con sus propios formatos de `address`).

`device_points_candidates` para MQTT: `object_type` = constante
`"mqtt_topic"` (dentro del `VARCHAR(50)` existente, sin `CHECK`, igual que
BACnet/Modbus); `object_instance` = `core/mqtt_topic_key.py::
topic_instance_key(topic)` (`INTEGER`, ver Registro de decisiones —
**no** el topic real, que no cabe en esa columna); `object_name` = el
topic real completo (`VARCHAR(255)`, ya nullable — aquí siempre poblado
para MQTT); `present_value` = payload del último mensaje de ese topic
(`TEXT`, sin tipar, mismo criterio que BACnet/Modbus); `units` = siempre
`NULL` para MQTT (MQTT no expone unidades, mismo criterio que Modbus).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-005-mqtt-scanning/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** es `hira-server/docs/openapi.yaml` (se **amplía**, no se reemplaza — los 8 paths existentes intactos) | `POST /devices/scan/mqtt` | `gate/check.sh` bloque 5 (Spectral lint, mismo warn conocido de tooling ya aceptado en `SRV-001`/`SRV-002`/`SRV-003`/`SRV-004`) |

### Sobre de error — RFC 9457 (reutiliza `ProblemDetail`, `E-ADR-003`)
| Endpoint | HTTP | `type` (slug) | `title` | Cuándo |
|---|---|---|---|---|
| `POST /devices/scan/mqtt` | 403 | `insufficient-role` | "Rol insuficiente" | Visor invoca el escaneo (RF-003) — slug reutilizado, no se redefine |
| `POST /devices/scan/mqtt` | 400 | `mqtt-invalid-topic-pattern` | "Patrón de topic MQTT inválido" | `topic_pattern` rechazado por `paho-mqtt` al suscribirse (RF-004) — slug **nuevo** de esta feature |

`POST /devices/scan/mqtt` no tiene una rama de error de negocio propia para
"ningún mensaje llegó" (RF-006: 0 candidatos es 200, no error).

### Esquema nuevo (`hira-server/docs/openapi.yaml` — extracto)
```yaml
ScanMqttRequest:
  type: object
  required: [topic_pattern]
  additionalProperties: false
  properties:
    topic_pattern:
      type: string
      minLength: 1
      example: "edificio/piso1/#"
      description: >
        Patrón de suscripción MQTT (wildcard `#`/`+` soportados por el
        broker). Validado por la librería MQTT al suscribirse (RF-004).
```
`POST /devices/scan/mqtt` → `200: DeviceCandidateOut[]` (reutilizado de
`SRV-003`/`SRV-004`, puede ser `[]`, RF-006) | `400: ProblemDetail`
(RF-004) | `403: ProblemDetail` (RF-003).

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`core/mqtt_topic_key.py`) | `topic_instance_key` es determinista (mismo topic → misma clave en 2 llamadas), produce enteros `>= 0` y `<= 2147483647` (cabe en `INTEGER`), topics distintos producen (típicamente) claves distintas; rechaza topic vacío | unit puro, **sin mocks** — RF-002 |
| Coordinación (`services/device_scan_service.py::scan_mqtt`) | *Camino feliz*: 3 mensajes de 2 topics distintos → 1 `upsert_device` + 2 `upsert_candidate` (RF-001, RF-002); *mismo topic 2 veces en la ventana*: el candidato final lleva el `present_value` del **último** mensaje, sin duplicar filas (`spec.md §2`); *patrón inválido* (doble que lanza `MqttInvalidTopicPatternError`): `ProblemDetailError(400)` **antes** de invocar `device_repo` (RF-004); *ventana sin mensajes*: `[]`, `device_repo.upsert_device` nunca invocado (RF-006); *RF-005*: ningún método de `services/device_scan_service.py` escribe en una tabla de puntos operables — test ya existente (`scan_bacnet`/`scan_modbus`) se extiende para cubrir también `scan_mqtt` sin cambiar su intención | unit + dobles (`Protocol` fakes) de `MqttScanTransportPort`/`DeviceRepositoryPort` |
| Adaptador `paho-mqtt` (`adapters/mqtt/mqtt_scan_adapter.py`) — **verificación de integración real, contra el Mosquitto real del compose de `SRV-001`, sin broker de test aparte** (`spec.md §2`, ya decidido) | (a) *Patrón inválido*: `listen("edificio/#/piso1", 3.0)` lanza `MqttInvalidTopicPatternError` de forma **inmediata** (verificado: `< 1s`, no espera los 3s completos — RF-004, evidencia de terminal con tiempo medido); (b) *ventana real de 3s*: un segundo cliente `paho-mqtt` (publisher de prueba, mismo broker) publica 2 mensajes dentro de la ventana (t≈1s, t≈2s) y 1 mensaje fuera (t≈5s) — `listen()` retorna exactamente los 2 mensajes dentro de la ventana, el de t≈5s **no** aparece (determinismo verificado con tiempos reales medidos, `time.monotonic()`, RF-001/RNF-001); (c) *autenticación*: `MqttScanAdapter` se conecta con `mqtt_user`/`mqtt_password` reales contra el broker con `allow_anonymous false` — la conexión exitosa **es** la verificación (si conectara sin credenciales, el broker la rechazaría, mismo criterio que `test_mqtt_security.py`/`VUL-SRV-001`) | integración — Mosquitto real del compose (`docker compose up -d mosquitto`) + un segundo cliente `paho-mqtt` como publisher de prueba, **no** es el producto "Simuladores" (`SRV-ADR-014`), es infraestructura de test de esta feature |
| Adaptador de repositorio (`PostgreSQLDeviceRepository`, `SRV-003`) | **Sin test nuevo** — el contrato ya está verificado (`tests/integration/test_device_repository_adapter.py`); esta feature solo ejercita `upsert_device`/`upsert_candidate` con `protocol='mqtt'`, ya cubierto por el `CHECK` genérico del esquema | — (reutilizado) |
| Router (`routers/devices.py`) | Contrato exacto de `openapi.yaml` (`TestClient`, con `MqttScanTransportPort`/`DeviceRepositoryPort` sustituidos por dobles propios vía `app.dependency_overrides`, mismo patrón que `test_devices_router.py` ya existente) — 200 con lista de candidatos (vacía y no vacía), 400 `mqtt-invalid-topic-pattern` con *shape* RFC 9457 exacto (doble que lanza `MqttInvalidTopicPatternError`, sin necesidad del broker real para este caso), 403 con Visor (reutiliza `require_role` ya verificado) | unit + `TestClient`, sin contenedores |
| Sistema (e2e) | `POST /devices/scan/mqtt` real (`paho-mqtt` real + Postgres real, con un publisher de prueba publicando durante la ventana) → `GET /devices` refleja el dispositivo MQTT (`protocol='mqtt'`, `address` = `topic_pattern`) → `GET /devices/{id}/candidates` refleja sus candidatos (`object_name` = topic real) — recorrido completo | integración — contenedores reales del compose + publisher `paho-mqtt` real |

> **Nota de investigación (ejecutada en esta fase, con evidencia real —
> mismo estándar que `SRV-004-modbus-adapter/plan.md §5`):** se levantó el
> Mosquitto real del compose (`docker compose -f docker-compose.yml -f
> docker-compose.dev.yml up -d mosquitto`, con `password_file` generado por
> `mosquitto/generate_password_file.sh`) y se ejecutaron 2 experimentos con
> `paho-mqtt==2.1.0` (ya instalado, `requirements.txt`) contra
> `localhost:1883`:
> 1. **Validación de `topic_pattern` al suscribirse** (`client.subscribe(pattern)`,
>    `CallbackAPIVersion.VERSION2`): patrones válidos (`"edificio/piso1/#"`,
>    `"edificio/+/temp"`) retornan `(MQTT_ERR_SUCCESS, mid)` sin lanzar.
>    Patrones inválidos lanzan **`ValueError`** de forma **síncrona**, antes
>    de tocar la red: `""` → `"Invalid topic."`; `"edificio/#/piso1"` (`#`
>    no al final) → `"Invalid subscription filter."`;
>    `"edificio/piso1/#extra"` (`#` no ocupa el segmento completo) →
>    `"Invalid subscription filter."`; un topic de 70000 caracteres (excede
>    el límite MQTT de 65535 bytes) → `"Invalid subscription filter."`;
>    `qos=5` (fuera de `{0,1,2}`) → `ValueError("Invalid QoS level.")`.
>    Confirma la decisión ya cerrada en `spec.md §6`: la librería valida
>    sin necesitar una regex propia, y lo hace **sin round-trip al
>    broker** — el `MqttScanAdapter` puede propagar `MqttInvalidTopicPatternError`
>    de inmediato, sin esperar los 3s de ventana.
> 2. **Ventana de escucha de 3s con publisher real**: un cliente `paho-mqtt`
>    se suscribió a `"edificio/piso1/#"` (SUBACK confirmado en ~6ms) y
>    esperó `time.sleep(3.0)`; en paralelo, un segundo cliente (publisher)
>    publicó en `t≈1s` y `t≈2s` (dentro de la ventana) y en `t≈5s` (fuera).
>    El listener capturó **exactamente** los 2 mensajes dentro de la
>    ventana (`edificio/piso1/ahu1/temp`→`"21.5"`,
>    `edificio/piso1/ahu2/humidity`→`"55"`); el mensaje de `t≈5s` nunca
>    llegó al listener (ya desconectado). Confirma que un publisher de
>    prueba independiente, con el mismo `paho-mqtt`, es determinista para
>    verificar la ventana en un test de integración — sin necesidad de un
>    reloj simulado.
>
> Este plan no deja ninguna duda abierta de API de `paho-mqtt` para
> Fase 4.

## 6. Secuenciación de archivos (tests antes que código)
1. `tests/test_mqtt_topic_key.py` (falla) → `core/mqtt_topic_key.py` —
   RF-002.
2. `core/ports/mqtt_scan_transport_port.py` (`MqttScanTransportPort`,
   `MqttTopicMessage`, `MqttInvalidTopicPatternError` — `Protocol`, sin
   test propio, igual que `bacnet_transport_port.py`/
   `modbus_transport_port.py`/`device_repository_port.py`).
3. `tests/test_device_scan_service.py` (se amplía con los casos de
   `scan_mqtt`, dobles de ambos puertos, falla) → `services/
   device_scan_service.py::scan_mqtt` (+ `MQTT_SCAN_WINDOW_SECONDS`) —
   RF-001, RF-002, RF-004, RF-005, RF-006, RNF-001.
4. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) —
   amplía con `POST /devices/scan/mqtt` + `ScanMqttRequest`, sin tocar los
   8 endpoints existentes.
5. `tests/test_devices_router.py` (se amplía, `TestClient`, falla) →
   `routers/devices.py` (nuevo endpoint) + `schemas/devices.py`
   (`ScanMqttRequest`) + **`adapters/factory.py::
   get_mqtt_scan_transport_port()`** (nace aquí con placeholder in-memory
   — mismo patrón ya aplicado 5 veces: el router necesita el punto de
   inyección desde que existe) — RF-001, RF-003, RF-004, RF-006 vía HTTP
   con dobles in-memory (los del propio archivo de test, sin depender del
   placeholder de `factory.py` para las respuestas).
6. `tests/integration/test_mqtt_scan_adapter.py` (falla, requiere el
   Mosquitto real del compose — ver §5) → `adapters/mqtt/
   mqtt_scan_adapter.py::MqttScanAdapter` — reemplaza el **cuerpo** (no la
   firma) de `adapters/factory.py::get_mqtt_scan_transport_port()` —
   RF-001, RF-002, RF-004, RNF-001 (reales).
7. `tests/integration/test_devices_scan_e2e.py` (se amplía — contenedores
   reales + publisher `paho-mqtt` real) — recorrido completo
   `POST /devices/scan/mqtt` → `GET /devices` → `GET /devices/{id}/
   candidates` (RF-001, RF-002, RF-003, RF-004, RF-006, RNF-001 medido con
   evidencia real).
8. `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` —
   nota `[doc]` de §8, actualiza la ya existente de `SRV-003`/`SRV-004`
   (puede ejecutarse en paralelo desde el paso 1).
9. READMEs ampliados (carpetas ya existentes, sin carpeta nueva que
   crear): `hira-server/backend/adapters/mqtt/README.md` (añade
   `mqtt_scan_adapter.py` a su historial, junto a `mosquitto_adapter.py`);
   `hira-server/backend/adapters/README.md` (añade la 8ª función de
   `factory.py`); `hira-server/backend/core/README.md` (añade
   `mqtt_topic_key.py`); `hira-server/backend/core/ports/README.md`
   (añade `mqtt_scan_transport_port.py`).

> `.harness/gate/services.txt` ya declara `hira-server/backend:python`
> (`SRV-001`) — sin cambios necesarios, la suite nueva se integra en la
> misma suite de `pytest`.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `core/mqtt_topic_key.py::topic_instance_key` — una función pura nueva que traduce un string a un entero determinista para una columna `INTEGER` que, en su diseño original (`SRV-003`), no anticipó un protocolo cuyo identificador natural de punto es texto | Ver Registro de decisiones §1: es la traducción de causa raíz del conflicto real entre `spec.md §2` (MQTT) y el esquema ya `verified` de BACnet/Modbus — la alternativa de tocar el esquema compartido es más invasiva y sin beneficio para los otros 2 protocolos (Art. 10: no se repara lo que no está roto en BACnet/Modbus). Marcado explícitamente para confirmación en Gate 2 por ser una interpretación de plan sobre una frase literal de `spec.md` que no se puede cumplir tal cual está escrita contra el esquema actual. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` | La nota de estado ya añadida por `SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter` ("Implementado a la fecha... BACnet/IP... Modbus TCP... MQTT... siguen siendo diseño, no código") queda **desactualizada** en la parte de MQTT tras esta feature: la suscripción wildcard y la persistencia de candidatos pasan a ser código real. La tabla "Escaneo y descubrimiento" (fila MQTT: "Suscripción wildcard → captura de topics activos (paho-mqtt)") sigue siendo correcta tal como está escrita — esta feature la implementa | `[doc]` editar la nota de estado (no crear una nueva): "Implementado a la fecha (`SRV-003-bacnet-adapter`, `SRV-004-modbus-adapter`, `SRV-005-mqtt-scanning`): escaneo BACnet/IP (Who-Is/I-Am), escaneo de rangos Modbus TCP y suscripción wildcard MQTT (captura de topics activos durante una ventana de 3s), los tres con persistencia de candidatos. Polling, escritura, `asyncio.Lock` por dispositivo, BACnet MSTP, Modbus RTU y Simuladores siguen siendo diseño, no código — ver `ROADMAP.md`/`.harness/specs/` para el estado real por sub-feature." |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es el
contrato de producto de esta frontera, ya cubierto en §4 (se amplía, no se
reemplaza).

`docs/hira-server/spec/validation/acceptance-criteria.md` **no** se toca:
`spec.md` de esta feature ya declara qué subconjunto de `AC-SRV-04` cubre
(4.2, 4.4) en su encabezado — sin un `AC-SRV-0X` dedicado nuevo que
redactar.

`docs/hira-server/spec/validation/vulnerabilities.md::VUL-SRV-001` **no**
se toca: sigue 🟢 Resuelto (`SRV-001`) — esta feature **refuerza** ese
cierre (el nuevo adaptador también se conecta autenticado, nunca anónimo,
`plan.md §5(c)`) pero no cambia su estado ni añade una vulnerabilidad
nueva — no hay escritura ni polling concurrente sobre un broker en esta
feature.

## 9. Implementación por requisito

### Implementación de RF-001
- `core/ports/mqtt_scan_transport_port.py::MqttScanTransportPort.listen`.
- `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter.listen` (suscribe, acumula durante la ventana, desconecta).
- `services/device_scan_service.py::scan_mqtt` (`MQTT_SCAN_WINDOW_SECONDS = 3.0`).
- `routers/devices.py::POST /devices/scan/mqtt`.
- `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1mqtt`.
- Tests: `tests/test_device_scan_service.py`, `tests/integration/test_mqtt_scan_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.
- `covers`: `hira-server/backend/core/ports/mqtt_scan_transport_port.py`, `hira-server/backend/adapters/mqtt/mqtt_scan_adapter.py`, `hira-server/backend/services/device_scan_service.py`, `hira-server/backend/routers/devices.py`.

### Implementación de RF-002
- `core/mqtt_topic_key.py::topic_instance_key`.
- `core/ports/device_repository_port.py::DeviceRepositoryPort.upsert_device/upsert_candidate` (`SRV-003`, ya existente, sin cambios).
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.upsert_device/upsert_candidate` (`SRV-003`, ya existente, sin cambios).
- `services/device_scan_service.py::scan_mqtt` (agrupación por topic, último mensaje gana; `upsert_device` solo si hubo al menos un mensaje).
- Tests: `tests/test_mqtt_topic_key.py`, `tests/test_device_scan_service.py`, `tests/integration/test_mqtt_scan_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.
- `covers`: `hira-server/backend/core/mqtt_topic_key.py`.

### Implementación de RF-003
- `core/security/dependencies.py::require_role("admin", "operador")` — **reutilizado tal cual** de `SRV-002`, ya aplicado al `router` completo de `routers/devices.py` desde `SRV-003`, sin cambios.
- Tests: `tests/test_devices_router.py` (403 con Visor), `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-004
- `core/ports/mqtt_scan_transport_port.py::MqttInvalidTopicPatternError`.
- `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter.listen` (captura el `ValueError` síncrono de `paho-mqtt` en `client.subscribe()`, lo traduce).
- `services/device_scan_service.py::scan_mqtt` (`try/except MqttInvalidTopicPatternError` → `ProblemDetailError(400, .../mqtt-invalid-topic-pattern)`).
- `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1mqtt` (respuesta 400).
- Tests: `tests/test_device_scan_service.py` (doble que lanza la excepción), `tests/test_devices_router.py` (400 con *shape* RFC 9457), `tests/integration/test_mqtt_scan_adapter.py` (patrones inválidos reales, tiempo medido `<1s`).

### Implementación de RF-005
- Ausencia de diseño verificada: `services/device_scan_service.py` no importa ni referencia ninguna tabla/puerto de `points` (mismo criterio que `SRV-003`/`SRV-004`, módulo compartido).
- Tests: `tests/test_device_scan_service.py` (test existente extendido, inspección de imports del módulo — cubre `scan_bacnet`/`scan_modbus`/`scan_mqtt` a la vez).

### Implementación de RF-006
- `services/device_scan_service.py::scan_mqtt` (retorna `[]` si `listen()` no capturó ningún mensaje, `device_repo` nunca tocado).
- `routers/devices.py::POST /devices/scan/mqtt` (200 con lista vacía, no 4xx/5xx).
- Tests: `tests/test_device_scan_service.py`, `tests/test_devices_router.py`, `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RNF-001
- `services/device_scan_service.py::scan_mqtt` (única llamada de I/O es `listen()`, acotada a `MQTT_SCAN_WINDOW_SECONDS`).
- `adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter.listen` (conexión + suscripción medidas en milisegundos, ver §5 nota de investigación — el tiempo total es la ventana más un overhead despreciable).
- Medición: `tests/integration/test_mqtt_scan_adapter.py`/`tests/integration/test_devices_scan_e2e.py` (duración total del escaneo contra Postgres/Mosquitto reales, evidencia de terminal pegada — Art. 3 "verificación real, nunca esperada").
