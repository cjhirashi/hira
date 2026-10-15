"""`MqttPublisherAdapter` — implementación real de `MqttPublisherPort` vía
`paho-mqtt` (`SRV-006-simuladores`, T-025, `plan.md §2`/§5).

**Archivo separado** de `mosquitto_adapter.py`/`mqtt_scan_adapter.py`: mismo
broker físico, pero otro ciclo de vida de conexión — aquí una conexión por
simulador que vive hasta `stop()` (`plan.md §1`, Registro de decisiones).

Notas de `paho-mqtt==2.1.0` (verificadas con ejecución real):
- `client.publish()` valida el topic de forma **síncrona** (`ValueError` con
  wildcard o vacío, sin round-trip al broker). El primer publish se hace antes
  de arrancar el bucle periódico, así que un topic inválido falla en
  `start()` como `MqttInvalidPublishError` (RF-014) sin dejar nada corriendo.
- `connect()` es bloqueante → `run_in_executor` (RNF-001); el hilo de red de
  `loop_start()` corre aparte y `publish()` solo encola, así que el bucle
  periódico puede vivir en el *event loop* con `asyncio.wait_for`.
- En `stop()`, `disconnect()` va antes que `loop_stop()` (ver
  `mqtt_scan_adapter.py`: al revés, `loop_stop()` tarda hasta ~1s).
- Conexión siempre autenticada (`VUL-SRV-001`).

Solo `adapters/mqtt/*` importa `paho.mqtt` (`SRV-ADR-017`).
"""
import asyncio
import threading
import uuid
from dataclasses import dataclass

import paho.mqtt.client as mqtt

from core.logger import get_logger
from core.ports.mqtt_publisher_port import MqttInvalidPublishError

_logger = get_logger("adapters.mqtt.mqtt_publisher_adapter")

_CONNACK_TIMEOUT_SECONDS = 5.0


@dataclass
class _RunningPublisher:
    client: mqtt.Client
    stop_event: asyncio.Event
    task: asyncio.Task


class MqttPublisherAdapter:
    """Implementa `MqttPublisherPort` contra un broker Mosquitto real."""

    def __init__(self, host: str, port: int, user: str, password: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._publishers: dict[str, _RunningPublisher] = {}

    async def start(self, *, topic: str, payload: str, interval_seconds: float) -> str:
        loop = asyncio.get_running_loop()
        token = uuid.uuid4().hex
        client = await loop.run_in_executor(None, self._connect_sync, token)
        try:
            client.publish(topic, payload)
        except ValueError as exc:
            await loop.run_in_executor(None, _disconnect_sync, client)
            raise MqttInvalidPublishError(str(exc)) from exc

        stop_event = asyncio.Event()
        task = asyncio.create_task(
            _publish_periodically(client, topic, payload, interval_seconds, stop_event)
        )
        self._publishers[token] = _RunningPublisher(client=client, stop_event=stop_event, task=task)
        _logger.info("Simulador MQTT publicando en %s cada %ss", topic, interval_seconds)
        return token

    async def stop(self, token: str) -> None:
        running = self._publishers.pop(token, None)
        if running is None:
            return
        running.stop_event.set()
        await running.task
        await asyncio.get_running_loop().run_in_executor(None, _disconnect_sync, running.client)
        _logger.info("Simulador MQTT detenido")

    def _connect_sync(self, token: str) -> mqtt.Client:
        connack_event = threading.Event()
        connack_result: dict[str, int | None] = {"rc": None}

        def _on_connect(client, userdata, flags, reason_code, properties) -> None:
            connack_result["rc"] = reason_code.value
            connack_event.set()

        client = mqtt.Client(
            client_id=f"hira-server-mqtt-sim-{token[:12]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        client.username_pw_set(self._user, self._password)
        client.on_connect = _on_connect
        client.connect(self._host, self._port, keepalive=60)
        client.loop_start()
        try:
            if not connack_event.wait(timeout=_CONNACK_TIMEOUT_SECONDS):
                raise TimeoutError("sin respuesta CONNACK del broker MQTT")
            if connack_result["rc"] != 0:
                raise ConnectionRefusedError(
                    f"broker MQTT rechazó la conexión (CONNACK rc={connack_result['rc']})"
                )
        except Exception:
            _disconnect_sync(client)
            raise
        return client


async def _publish_periodically(
    client: mqtt.Client,
    topic: str,
    payload: str,
    interval_seconds: float,
    stop_event: asyncio.Event,
) -> None:
    while True:
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
            return
        except asyncio.TimeoutError:
            client.publish(topic, payload)


def _disconnect_sync(client: mqtt.Client) -> None:
    client.disconnect()
    client.loop_stop()
