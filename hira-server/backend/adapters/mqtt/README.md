# adapters/mqtt

Dos adaptadores, mismo `paho-mqtt`, mismo broker físico, **puertos de dominio
distintos** con ciclos de vida de conexión incompatibles (`SRV-005-mqtt-scanning/
plan.md §1`, Registro de decisiones — nunca fusionarlos en una sola clase).

- `mosquitto_adapter.py::MosquittoAdapter` — implementa `NotificationPort`
  contra Mosquitto (credencial `MQTT_USER`/`MQTT_PASSWORD`) — `tasks.md`
  T-021/T-022, RF-006/RF-008. Conexión **persistente** (una vez en `lifespan`).
  - `connect()` — invocación de arranque: backoff fijo (1s → 2s → 4s, 3 reintentos
    tras el intento inicial = 4 intentos totales), log `level: error` en cada
    fallo, nunca un loop ciego. Verificado con credencial inválida contra el
    broker real (`tests/integration/test_adapters.py`).
  - `ping()` — un único intento de conexión por chequeo (sin el backoff de
    `connect()`); el timeout de 2s lo aplica `services/health_service.py`.
  - API v1 de `paho-mqtt` (`mqtt.Client(client_id=..., protocol=mqtt.MQTTv311)`,
    deprecada) — deuda pre-existente, fuera de alcance de `SRV-005-mqtt-scanning`
    (Art. 10: no se refactoriza código ya `verified` sin que ningún `RF-` lo pida).

- `mqtt_scan_adapter.py::MqttScanAdapter` — implementa `MqttScanTransportPort`
  (`SRV-005-mqtt-scanning`, `tasks.md` T-009/T-010, RF-001/RF-002/RF-004).
  Conexión **efímera por request** (conecta, suscribe, espera `window_seconds`,
  desconecta — una vez por cada `POST /devices/scan/mqtt`), mismas
  credenciales `MQTT_USER`/`MQTT_PASSWORD`.
  - `listen(topic_pattern, window_seconds)` — se suscribe (`client.subscribe`,
    `CallbackAPIVersion.VERSION2`, API moderna no deprecada) y acumula
    mensajes durante la ventana vía `on_message` en un hilo de red propio.
    `client.subscribe()` valida el patrón de forma **síncrona**
    (`ValueError` → `MqttInvalidTopicPatternError`, RF-004) sin round-trip al
    broker para esa validación puntual. Payload decodificado a `str`
    (`errors="replace"`) dentro del adaptador — `core/ports/` no conoce bytes.
  - Orden del `finally` — `disconnect()` **antes** que `loop_stop()` (despierta
    el `select()` interno de `paho-mqtt` de inmediato vía su `sockpair`;
    al revés, `loop_stop()` puede bloquear hasta ~1s — verificado con
    ejecución real, ver docstring del módulo).
  - Verificado con ejecución real contra el Mosquitto del compose
    (`tests/integration/test_mqtt_scan_adapter.py`): ventana de 3s con
    publisher `paho-mqtt` real, patrón inválido rechazado en ~4ms.
