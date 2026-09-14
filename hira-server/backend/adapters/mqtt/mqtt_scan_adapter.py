"""`MqttScanAdapter` — implementación real de `MqttScanTransportPort` vía
`paho-mqtt` (`SRV-005-mqtt-scanning`, T-009/T-010, `plan.md §2`).

Solo `adapters/mqtt/*` importa `paho.mqtt` — `services/` sigue importando
únicamente `core/ports/mqtt_scan_transport_port.py` (`SRV-ADR-017`).

**Archivo separado** de `adapters/mqtt/mosquitto_adapter.py::MosquittoAdapter`
(mismo `paho-mqtt`, mismo broker físico, pero puertos de dominio distintos con
ciclos de vida de conexión incompatibles — `plan.md §1`, Registro de
decisiones): `MosquittoAdapter` es una conexión **persistente** (una vez en
`lifespan`); `MqttScanAdapter` es una conexión **efímera por request**
(conecta, suscribe, espera `window_seconds`, desconecta — una vez por cada
`POST /devices/scan/mqtt`).

Usa `paho.mqtt.client.CallbackAPIVersion.VERSION2` (API moderna, no deprecada
— a diferencia de `MosquittoAdapter`, que sigue en API v1 como deuda
pre-existente fuera de alcance de esta feature, `plan.md §1`).

Notas de implementación (verificadas con ejecución real contra
`paho-mqtt==2.1.0`, `plan.md §5` nota de investigación — re-verificadas en
esta sesión):
- `client.subscribe(topic_pattern)` valida el *topic filter* de forma
  **síncrona** (`ValueError` para patrones inválidos: longitud, wildcard mal
  ubicado, QoS fuera de rango), sin round-trip al broker para *esa llamada*
  (RF-004, confirmado con ejecución real: ~4ms en aislamiento, coincide con
  `plan.md §5`). Se captura y traduce a `MqttInvalidTopicPatternError`
  (dominio).
- **Orden del `finally` — `disconnect()` antes que `loop_stop()`** (verificado
  con ejecución real en esta sesión, no estaba en el spike de `plan.md`):
  `client.disconnect()` escribe en el `sockpair` interno de `paho-mqtt` para
  despertar de inmediato el `select()` bloqueante del hilo de red
  (`loop_start()`); `loop_stop()` **después** retorna casi al instante. Con
  el orden inverso (`loop_stop()` primero), `loop_stop().join()` bloquea
  hasta que el hilo de red note la señal de término por su cuenta — acotado
  por el timeout interno de `select()` (1.0s por defecto) — midiendo hasta
  ~1s de latencia adicional en el camino de error de RF-004 (no llegaba a
  violar RF-004/RNF-001, pero se alejaba del "< 1s" del spike aislado que
  nunca ejercitó `loop_stop()`).
- La ventana de escucha se implementa con `asyncio.sleep(window_seconds)`
  mientras el hilo de red de `paho-mqtt` (`loop_start()`) acumula mensajes
  vía el callback `on_message` en una lista protegida por `threading.Lock`
  (el callback corre en el hilo de red de `paho-mqtt`, no en el event loop).
- El payload (`bytes`) se decodifica a `str` con `errors="replace"` dentro
  del adaptador — `core/ports/` no debe conocer que MQTT transmite bytes
  (`plan.md §1`, Registro de decisiones).
- Conexión siempre autenticada (`username_pw_set`, `VUL-SRV-001` — nunca
  anónima, mismo criterio que `MosquittoAdapter`).
"""
import asyncio
import threading
import time

import paho.mqtt.client as mqtt

from core.logger import get_logger
from core.ports.mqtt_scan_transport_port import MqttInvalidTopicPatternError, MqttTopicMessage

_logger = get_logger("adapters.mqtt.mqtt_scan_adapter")

_CONNACK_TIMEOUT_SECONDS = 5.0


class MqttScanAdapter:
    """Implementa `MqttScanTransportPort` contra un broker Mosquitto real."""

    def __init__(self, host: str, port: int, user: str, password: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password

    def _listen_sync(self, topic_pattern: str, window_seconds: float) -> list[MqttTopicMessage]:
        """Conecta, se suscribe y acumula mensajes durante `window_seconds`
        (bloqueante — se ejecuta en un hilo aparte vía `run_in_executor`).

        Lanza `MqttInvalidTopicPatternError` si `client.subscribe()` rechaza
        el patrón (RF-004) — **antes** de esperar la ventana completa.
        """
        messages: list[MqttTopicMessage] = []
        messages_lock = threading.Lock()
        connack_event = threading.Event()
        connack_result: dict[str, int | None] = {"rc": None}

        def _on_connect(client, userdata, flags, reason_code, properties) -> None:
            # `reason_code` es `paho.mqtt.reasoncodes.ReasonCode` en
            # `CallbackAPIVersion.VERSION2` (no un `int` crudo) — `.value` es
            # el código numérico real (0 = éxito).
            connack_result["rc"] = reason_code.value
            connack_event.set()

        def _on_message(client, userdata, message) -> None:
            payload = message.payload.decode("utf-8", errors="replace")
            with messages_lock:
                messages.append(MqttTopicMessage(topic=message.topic, payload=payload))

        client = mqtt.Client(
            client_id=f"hira-server-mqtt-scan-{id(self)}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
        client.username_pw_set(self._user, self._password)
        client.on_connect = _on_connect
        client.on_message = _on_message

        client.connect(self._host, self._port, keepalive=int(window_seconds) + 10)
        client.loop_start()
        try:
            if not connack_event.wait(timeout=_CONNACK_TIMEOUT_SECONDS):
                raise TimeoutError("sin respuesta CONNACK del broker MQTT")
            if connack_result["rc"] != 0:
                raise ConnectionRefusedError(
                    f"broker MQTT rechazó la conexión (CONNACK rc={connack_result['rc']})"
                )

            try:
                client.subscribe(topic_pattern)
            except ValueError as exc:
                raise MqttInvalidTopicPatternError(str(exc)) from exc

            time.sleep(window_seconds)
        finally:
            # Orden importa: `disconnect()` escribe en el `sockpair` interno
            # de `paho-mqtt` para despertar el `select()` del hilo de red de
            # inmediato; `loop_stop()` **después** retorna casi al instante.
            # Al revés (`loop_stop()` primero), `loop_stop()` bloquea su
            # `join()` hasta que el hilo de red note la señal de término por
            # su cuenta — acotado por el timeout interno de `select()` (1.0s
            # por defecto) — verificado con ejecución real en esta sesión.
            client.disconnect()
            client.loop_stop()

        with messages_lock:
            return list(messages)

    async def listen(
        self, topic_pattern: str, window_seconds: float
    ) -> list[MqttTopicMessage]:
        """RF-001, RF-002, RF-004, RF-006 — delega el trabajo bloqueante de
        `paho-mqtt` a un hilo (`run_in_executor`) para no bloquear el event
        loop de FastAPI durante la ventana de escucha."""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(
                None, self._listen_sync, topic_pattern, window_seconds
            )
        except MqttInvalidTopicPatternError:
            raise
        except Exception as exc:  # noqa: BLE001 — fallo de conexión real, se loguea
            _logger.error("Fallo en escaneo MQTT topic_pattern=%s: %s", topic_pattern, exc)
            raise
