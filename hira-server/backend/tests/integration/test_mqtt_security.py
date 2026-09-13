"""Seguridad — Mosquitto rechaza clientes sin credenciales (T-023, RF-006,
`VUL-SRV-001`).

Cliente MQTT externo con `paho-mqtt` **directo** (sin pasar por
`adapters/mqtt/mosquitto_adapter.py`), sin usuario/contraseña, contra el broker
Mosquitto real del compose (`allow_anonymous false` + `password_file`,
`mosquitto/mosquitto.conf`). El broker debe rechazar la conexión (CONNACK con
`rc != 0`) — formaliza como test automatizado lo que el revisor ya verificó
manualmente con `mosquitto_pub` en el batch T-016/T-017.

Requiere el mismo `docker compose up -d mosquitto` que `test_adapters.py`.
"""
import os
import threading

import paho.mqtt.client as mqtt
import pytest

pytestmark = pytest.mark.integration

MQTT_HOST = os.environ.get("TEST_MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("TEST_MQTT_PORT", "1883"))
CONNACK_TIMEOUT_SECONDS = 5.0


def test_anonymous_mqtt_client_is_rejected_by_real_broker():
    """RF-006/`VUL-SRV-001` — sin credenciales, el broker real no debe aceptar la
    conexión (`allow_anonymous false`)."""
    connack_event = threading.Event()
    result: dict[str, int | None] = {"rc": None}

    def on_connect(client, userdata, flags, rc):  # noqa: ANN001 — firma fija de paho-mqtt v1
        result["rc"] = rc
        connack_event.set()

    client = mqtt.Client(client_id="test-security-anonymous-rejected", protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    # Deliberadamente SIN client.username_pw_set(...) — cliente anónimo.
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
    client.loop_start()
    try:
        assert connack_event.wait(
            timeout=CONNACK_TIMEOUT_SECONDS
        ), "el broker no respondió CONNACK dentro del timeout"
        assert result["rc"] != 0, (
            "el broker aceptó una conexión MQTT anónima sin credenciales "
            "(VUL-SRV-001 sigue abierto)"
        )
    finally:
        client.loop_stop()
        client.disconnect()
