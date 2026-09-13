#!/usr/bin/env bash
# Genera `password_file` para Mosquitto (`allow_anonymous false`) a partir de
# MQTT_USER/MQTT_PASSWORD del entorno — RF-006, VUL-SRV-001
# (`.harness/specs/SRV-001-walking-skeleton/`).
#
# La credencial NUNCA se commitea en claro: este script produce
# `password_file` (hasheado por `mosquitto_passwd`), que está en `.gitignore`.
#
# Uso:
#   cd hira-server
#   set -a && source .env && set +a   # carga MQTT_USER/MQTT_PASSWORD del .env real
#   ./mosquitto/generate_password_file.sh
#
# Regenerar (rotar credencial): exporta el nuevo MQTT_USER/MQTT_PASSWORD y
# vuelve a correr este script — sobreescribe `password_file` (-c).
#
# No requiere `mosquitto_passwd` instalado en el host: usa la misma imagen
# del compose (`eclipse-mosquitto:2`) vía un contenedor descartable.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -z "${MQTT_USER:-}" || -z "${MQTT_PASSWORD:-}" ]]; then
  echo "Error: define MQTT_USER y MQTT_PASSWORD en el entorno antes de correr este script." >&2
  echo "       (p. ej.: set -a && source ../.env && set +a)" >&2
  exit 1
fi

# El proceso `mosquitto` del compose corre como uid/gid 1883 (usuario
# `mosquitto` de la imagen, ver `docker logs`: "running mosquitto as user:
# mosquitto") — el archivo generado debe quedar legible solo por ese usuario
# (chown + chmod 600 dentro del mismo contenedor, que sí corre como root).
docker run --rm \
  -v "${SCRIPT_DIR}:/mosquitto/config" \
  --entrypoint sh \
  eclipse-mosquitto:2 \
  -c "mosquitto_passwd -b -c /mosquitto/config/password_file '${MQTT_USER}' '${MQTT_PASSWORD}' && chown 1883:1883 /mosquitto/config/password_file && chmod 600 /mosquitto/config/password_file"

echo "password_file generado en ${SCRIPT_DIR}/password_file (no se commitea — ver .gitignore)."
