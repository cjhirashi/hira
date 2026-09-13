# mosquitto

Broker MQTT del compose (`SRV-001-walking-skeleton`, T-017; RF-006, `VUL-SRV-001`).

`mosquitto.conf` fija `allow_anonymous false` + `password_file
/mosquitto/config/password_file` — Mosquitto rechaza cualquier conexión sin
credencial válida. El `backend` se conecta con `MQTT_USER`/`MQTT_PASSWORD`
(`core/config.py::Settings`, mismos valores usados para generar el
`password_file`).

## Generar / regenerar `password_file`

`password_file` **no se commitea** (contiene el hash de la credencial, está en
`.gitignore`). Se genera con `generate_password_file.sh` a partir de
`MQTT_USER`/`MQTT_PASSWORD` del entorno (`.env` real, nunca `.env.example`):

```bash
cd hira-server
set -a && source .env && set +a
./mosquitto/generate_password_file.sh
```

El script usa un contenedor descartable de `eclipse-mosquitto:2` (la misma
imagen del compose) para correr `mosquitto_passwd -b -c` — no requiere
`mosquitto_passwd` instalado en el host.

**Rotar la credencial:** actualiza `MQTT_USER`/`MQTT_PASSWORD` en `.env`,
vuelve a correr el script (sobreescribe `password_file`, `-c`) y reinicia el
contenedor `mosquitto` (`docker compose restart mosquitto`).

## Por qué no hay volumen de persistencia

`persistence false` en `mosquitto.conf` — este sprint no retiene mensajes en
disco (sin *retained messages* ni QoS con `store`); se añadirá cuando exista
un caso de uso real de notificaciones (regla de oro Art. 10, no anticipar).
