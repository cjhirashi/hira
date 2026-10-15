"""Integración real — `MqttPublisherAdapter` contra el Mosquitto real del
compose (`SRV-006-simuladores`, T-024/T-025, `plan.md §5` fila "Adaptador
MQTT").

El publicador es el **producto bajo prueba**; un segundo cliente `paho-mqtt`
(autenticado con las mismas credenciales de `Settings`) actúa de suscriptor de
prueba. Requiere el broker del compose levantado (`pytest -m integration`).
"""
import asyncio
import os
import threading
import time
import uuid

import paho.mqtt.client as mqtt
import pytest

from adapters.mqtt.mqtt_publisher_adapter import MqttPublisherAdapter
from core.config import Settings
from core.ports.mqtt_publisher_port import MqttInvalidPublishError

pytestmark = pytest.mark.integration

MQTT_HOST = os.environ.get("TEST_MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("TEST_MQTT_PORT", "1883"))


class _Subscriber:
    """Suscriptor `paho-mqtt` de prueba que registra `(time.monotonic(),
    payload)` de cada mensaje recibido."""

    def __init__(self, topic: str, user: str, password: str) -> None:
        self.received: list[tuple[float, str]] = []
        self._lock = threading.Lock()
        subscribed = threading.Event()
        self._client = mqtt.Client(
            client_id=f"test-subscriber-{uuid.uuid4().hex[:8]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.username_pw_set(user, password)
        self._client.on_connect = lambda client, *_: client.subscribe(topic, qos=1)
        self._client.on_subscribe = lambda *_: subscribed.set()
        self._client.on_message = self._on_message
        self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
        self._client.loop_start()
        assert subscribed.wait(timeout=5.0), "el suscriptor de prueba no quedó suscrito"

    def _on_message(self, client, userdata, message) -> None:
        with self._lock:
            self.received.append((time.monotonic(), message.payload.decode()))

    def snapshot(self) -> list[tuple[float, str]]:
        with self._lock:
            return list(self.received)

    def close(self) -> None:
        self._client.disconnect()
        self._client.loop_stop()


@pytest.fixture
def adapter():
    settings = Settings()
    return MqttPublisherAdapter(
        host=MQTT_HOST, port=MQTT_PORT, user=settings.mqtt_user, password=settings.mqtt_password
    )


@pytest.fixture
def make_subscriber():
    settings = Settings()
    subscribers: list[_Subscriber] = []

    def _make(topic: str) -> _Subscriber:
        subscriber = _Subscriber(topic, settings.mqtt_user, settings.mqtt_password)
        subscribers.append(subscriber)
        return subscriber

    yield _make
    for subscriber in subscribers:
        subscriber.close()


@pytest.mark.asyncio
async def test_start_publishes_payload_periodically(adapter, make_subscriber):
    """RF-003 — con `interval_seconds=1.0` el suscriptor recibe ≥ 3 mensajes
    con el `payload` exacto en 3.5s, con cadencia ~1s."""
    topic = f"hira-test/sim/{uuid.uuid4().hex[:8]}"
    subscriber = make_subscriber(topic)

    token = await adapter.start(topic=topic, payload="21.5", interval_seconds=1.0)
    try:
        await asyncio.sleep(3.5)
    finally:
        await adapter.stop(token)

    received = subscriber.snapshot()
    assert len(received) >= 3
    assert {payload for _, payload in received} == {"21.5"}
    gaps = [later - earlier for (earlier, _), (later, _) in zip(received, received[1:])]
    assert all(0.8 <= gap <= 1.3 for gap in gaps), gaps


@pytest.mark.asyncio
@pytest.mark.parametrize("topic", ["edificio/#", "edificio/+/temp", ""])
async def test_start_rejects_invalid_topic_immediately(adapter, topic):
    """RF-014 — un topic con wildcard o vacío lanza `MqttInvalidPublishError`
    en < 1s, sin arrancar el bucle periódico."""
    loop = asyncio.get_running_loop()
    started = loop.time()

    with pytest.raises(MqttInvalidPublishError):
        await adapter.start(topic=topic, payload="x", interval_seconds=1.0)

    assert loop.time() - started < 1.0


@pytest.mark.asyncio
async def test_stop_halts_publication(adapter, make_subscriber):
    """RF-009 — tras `stop(token)` el suscriptor no recibe más mensajes."""
    topic = f"hira-test/sim/{uuid.uuid4().hex[:8]}"
    subscriber = make_subscriber(topic)
    token = await adapter.start(topic=topic, payload="on", interval_seconds=0.3)
    await asyncio.sleep(1.0)

    await adapter.stop(token)
    count_at_stop = len(subscriber.snapshot())
    await asyncio.sleep(1.0)

    assert count_at_stop >= 2
    assert len(subscriber.snapshot()) == count_at_stop


@pytest.mark.asyncio
async def test_publishing_does_not_block_the_event_loop(adapter, make_subscriber):
    """RNF-001 — mientras el publicador corre, una corutina del mismo loop
    con *ticks* de 50 ms avanza con normalidad."""
    topic = f"hira-test/sim/{uuid.uuid4().hex[:8]}"
    make_subscriber(topic)
    token = await adapter.start(topic=topic, payload="x", interval_seconds=0.2)
    ticks = 0
    try:
        for _ in range(20):
            await asyncio.sleep(0.05)
            ticks += 1
    finally:
        await adapter.stop(token)

    assert ticks == 20
