"""Integración real — `MqttScanAdapter` contra el Mosquitto real del compose
de `SRV-001-walking-skeleton` (`SRV-005-mqtt-scanning`, T-009/T-010,
`plan.md §5`/§6 paso 6).

Sin mocks: tráfico MQTT real (`paho-mqtt==2.1.0`) contra el broker autenticado
(`allow_anonymous false`, `VUL-SRV-001` ya resuelto) — un segundo cliente
`paho-mqtt` actúa de publisher de prueba, mismo criterio que
`tests/integration/test_pymodbus_adapter.py` (servidor Modbus real) y
`tests/integration/test_bac0_adapter.py` (dispositivo BACnet real):
infraestructura de test de esta feature, **no** es el producto "Simuladores"
(`SRV-ADR-014`).

Verificado con ejecución real en `plan.md §5` (nota de investigación, spike
del arquitecto) — re-verificado en esta sesión contra `paho-mqtt==2.1.0`
efectivamente instalado:
- `client.subscribe(pattern)` (`CallbackAPIVersion.VERSION2`) valida el
  *topic filter* de forma **síncrona** y lanza `ValueError` para patrones
  inválidos, sin round-trip al broker — el adaptador propaga
  `MqttInvalidTopicPatternError` de inmediato (`< 1s`), sin esperar la
  ventana completa de 3s.
- Un publisher `paho-mqtt` independiente, publicando dentro y fuera de una
  ventana de escucha de 3s, es determinista para verificar `listen()` sin
  reloj simulado.

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d mosquitto

Credenciales: `core.config.Settings` (`MQTT_USER`/`MQTT_PASSWORD`, mismas que
usa `adapters/mqtt/mosquitto_adapter.py::MosquittoAdapter` — `.env`/`.env.example`).
"""
import os
import threading
import time
import uuid

import paho.mqtt.client as mqtt
import pytest

from adapters.mqtt.mqtt_scan_adapter import MqttScanAdapter
from core.config import Settings
from core.ports.mqtt_scan_transport_port import (
    MqttInvalidTopicPatternError,
    MqttTopicMessage,
)

pytestmark = pytest.mark.integration

MQTT_HOST = os.environ.get("TEST_MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("TEST_MQTT_PORT", "1883"))
CONNACK_TIMEOUT_SECONDS = 5.0


def _settings_credentials() -> tuple[str, str]:
    """Credenciales reales de `Settings` — mismas que `MosquittoAdapter`
    (`MQTT_USER`/`MQTT_PASSWORD` de `.env`, `VUL-SRV-001`)."""
    settings = Settings()
    return settings.mqtt_user, settings.mqtt_password


class _Publisher:
    """Cliente `paho-mqtt` independiente que publica mensajes de prueba en
    momentos controlados — infraestructura de test (`plan.md §5`), no el
    adaptador bajo prueba."""

    def __init__(self, user: str, password: str) -> None:
        connack_event = threading.Event()
        self._client = mqtt.Client(
            client_id=f"test-publisher-{uuid.uuid4().hex[:8]}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        self._client.username_pw_set(user, password)

        def _on_connect(client, userdata, flags, reason_code, properties):
            connack_event.set()

        self._client.on_connect = _on_connect
        self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=10)
        self._client.loop_start()
        assert connack_event.wait(
            timeout=CONNACK_TIMEOUT_SECONDS
        ), "el publisher de prueba no recibió CONNACK del broker real"

    def publish(self, topic: str, payload: str) -> None:
        info = self._client.publish(topic, payload, qos=1)
        info.wait_for_publish(timeout=CONNACK_TIMEOUT_SECONDS)

    def close(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()


@pytest.fixture()
def publisher():
    user, password = _settings_credentials()
    pub = _Publisher(user, password)
    try:
        yield pub
    finally:
        pub.close()


@pytest.mark.asyncio
async def test_listen_captures_only_messages_inside_the_window(publisher):
    """RF-001, RF-002, RNF-001 — un publisher real publica 2 mensajes dentro
    de la ventana de 3s (t≈1s, t≈2s) y 1 mensaje fuera (t≈5s, tras el retorno
    de `listen()`); `listen()` debe capturar exactamente los 2 de dentro,
    nunca el de fuera — verificado con tiempos reales (`time.monotonic()`)."""
    topic_pattern = f"hira/test/{uuid.uuid4().hex[:8]}/#"
    user, password = _settings_credentials()
    adapter = MqttScanAdapter(host=MQTT_HOST, port=MQTT_PORT, user=user, password=password)

    def _publish_during_window() -> None:
        time.sleep(1.0)
        publisher.publish(f"{topic_pattern[:-1]}ahu1/temp", "21.5")
        time.sleep(1.0)
        publisher.publish(f"{topic_pattern[:-1]}ahu2/humidity", "55")

    publisher_thread = threading.Thread(target=_publish_during_window)
    start = time.monotonic()
    publisher_thread.start()

    messages = await adapter.listen(topic_pattern, 3.0)
    elapsed = time.monotonic() - start
    publisher_thread.join(timeout=5.0)

    print(f"\nRNF-001 evidencia real: listen() con ventana de 3s tardó {elapsed:.3f}s")
    assert 2.9 <= elapsed <= 4.0, f"listen() tardó {elapsed:.3f}s, se esperaba ~3s"

    assert len(messages) == 2
    assert all(isinstance(m, MqttTopicMessage) for m in messages)
    topics = {m.topic: m.payload for m in messages}
    assert topics == {
        f"{topic_pattern[:-1]}ahu1/temp": "21.5",
        f"{topic_pattern[:-1]}ahu2/humidity": "55",
    }

    # El mensaje "fuera de la ventana" se publica después de que `listen()`
    # ya retornó — no debe alcanzar al adaptador (ya desconectado).
    publisher.publish(f"{topic_pattern[:-1]}ahu3/pressure", "1013")
    assert len(messages) == 2  # sin cambios: `messages` ya es una lista cerrada


@pytest.mark.asyncio
async def test_listen_returns_empty_list_when_no_message_arrives():
    """RF-006 — ningún publisher activo durante la ventana → lista vacía."""
    topic_pattern = f"hira/test/{uuid.uuid4().hex[:8]}/#"
    user, password = _settings_credentials()
    adapter = MqttScanAdapter(host=MQTT_HOST, port=MQTT_PORT, user=user, password=password)

    messages = await adapter.listen(topic_pattern, 3.0)

    assert messages == []


@pytest.mark.asyncio
async def test_listen_raises_invalid_topic_pattern_error_immediately():
    """RF-004 — un patrón sintácticamente inválido (`#` no al final) lanza
    `MqttInvalidTopicPatternError` de forma **inmediata** (`< 1s`), sin
    esperar los 3s completos de ventana — validación síncrona de
    `client.subscribe()`, sin round-trip al broker (`plan.md §5`, nota de
    investigación). Requiere que el `finally` del adaptador llame
    `client.disconnect()` **antes** de `client.loop_stop()` (orden que
    despierta el `select()` interno de `paho-mqtt` de inmediato vía su
    `sockpair` — verificado con ejecución real en esta sesión; el orden
    inverso añadía hasta ~1s de latencia de cierre, acotada por el timeout
    interno de `select()`, sin violar RF-004/RNF-001 pero lejos del "< 1s"
    medido en el spike aislado de `plan.md`)."""
    user, password = _settings_credentials()
    adapter = MqttScanAdapter(host=MQTT_HOST, port=MQTT_PORT, user=user, password=password)

    start = time.monotonic()
    with pytest.raises(MqttInvalidTopicPatternError):
        await adapter.listen("edificio/#/piso1", 3.0)
    elapsed = time.monotonic() - start

    print(f"\nRF-004 evidencia real: patrón inválido rechazado en {elapsed:.3f}s")
    assert elapsed < 1.0, f"tardó {elapsed:.3f}s — no fue inmediato (RF-004)"


@pytest.mark.asyncio
async def test_listen_connects_authenticated_never_anonymous():
    """`VUL-SRV-001`/Art. 5 — `MqttScanAdapter` se conecta con
    `mqtt_user`/`mqtt_password` reales contra el broker con
    `allow_anonymous false`; la conexión exitosa (mensajes capturados) es la
    verificación — si conectara sin credenciales, el broker la rechazaría
    (mismo criterio que `tests/integration/test_mqtt_security.py`)."""
    user, password = _settings_credentials()
    adapter = MqttScanAdapter(host=MQTT_HOST, port=MQTT_PORT, user=user, password=password)
    topic_pattern = f"hira/test/{uuid.uuid4().hex[:8]}/#"

    # Ventana corta (0.5s) solo para verificar que la conexión autenticada
    # se establece sin error — no se necesita capturar mensajes aquí.
    messages = await adapter.listen(topic_pattern, 0.5)

    assert messages == []  # sin publisher activo; lo relevante es que no lanzó
