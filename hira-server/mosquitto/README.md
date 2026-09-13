# mosquitto

Broker MQTT del compose. `mosquitto.conf` (`allow_anonymous false` + `password_file`) y
el script de generación del `password_file` desde `MQTT_USER`/`MQTT_PASSWORD` son
pendientes — batch posterior (`tasks.md` T-017, `VUL-SRV-001`, RF-006).
