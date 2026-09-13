# adapters/mqtt

Implementa `NotificationPort` contra Mosquitto (`mosquitto_adapter.py`, `paho-mqtt`,
credencial `MQTT_USER`/`MQTT_PASSWORD`) — `tasks.md` T-021/T-022, RF-006/RF-008.

- `connect()` — invocación de arranque: backoff fijo (1s → 2s → 4s, 3 reintentos
  tras el intento inicial = 4 intentos totales), log `level: error` en cada
  fallo, nunca un loop ciego. Verificado con credencial inválida contra el
  broker real (`tests/integration/test_adapters.py`).
- `ping()` — un único intento de conexión por chequeo (sin el backoff de
  `connect()`); el timeout de 2s lo aplica `services/health_service.py`.
