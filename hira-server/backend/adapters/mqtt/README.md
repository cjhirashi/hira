# adapters/mqtt

Implementa `NotificationPort` contra Mosquitto (`mosquitto_adapter.py`, `paho-mqtt`,
credencial `MQTT_USER`/`MQTT_PASSWORD`, backoff fijo sin loop infinito — RF-006/RF-008).
Pendiente — requiere el contenedor `mosquitto` del compose (`tasks.md` T-021/T-022,
fuera de este batch).
