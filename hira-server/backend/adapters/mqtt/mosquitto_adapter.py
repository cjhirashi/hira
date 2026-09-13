"""`MosquittoAdapter` — implementación real de `NotificationPort` (RF-006, RF-008,
T-021/T-022).

Usa `paho-mqtt` (cliente síncrono con hilo de red propio, `loop_start()`); como
`NotificationPort` es async, cada intento de conexión se ejecuta en un
`ThreadPoolExecutor` implícito (`loop.run_in_executor`) para no bloquear el event
loop de FastAPI.

- **`connect()`** — se invoca una vez en el arranque (`main.py::lifespan`, batch
  posterior). Si la credencial es inválida o el broker no responde, registra el
  fallo en `level: error` y aplica **backoff fijo** (1s → 2s → 4s) entre reintentos
  — nunca un loop ciego. Tras agotar los reintentos, se rinde: el adaptador queda
  `is_connected = False` sin lanzar excepción y sin seguir reintentando.
- **`ping()`** — no repite el ciclo de backoff de `connect()`: hace **un único**
  intento de conexión de bajo costo (RF-007 ya envuelve esta llamada con
  `asyncio.wait_for(timeout=2)` en `services/health_service.py`). Si el intento
  falla, `/health` lo refleja como `mosquitto: error` en la siguiente consulta —
  "lazy retry en cada chequeo" (`plan.md §2`).

Solo `adapters/*` puede importar `paho.mqtt` — `services/` sigue importando
únicamente `core/ports/notification_port.py` (`SRV-ADR-017`).
"""
import asyncio
import threading

import paho.mqtt.client as mqtt

from core.logger import get_logger

_logger = get_logger("adapters.mqtt.mosquitto_adapter")

# RF-008 — backoff fijo entre reintentos de `connect()`: 1s, 2s, 4s (3 reintentos
# tras el intento inicial fallido = 4 intentos de conexión en total, luego se
# rinde). Nunca un loop ciego/indefinido.
_RETRY_BACKOFF_SECONDS = (1.0, 2.0, 4.0)
_CONNACK_TIMEOUT_SECONDS = 5.0


class MosquittoAdapter:
    """Implementa `NotificationPort` contra un broker Mosquitto real."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        client_id: str = "hira-server-backend",
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._client_id = client_id
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _connect_once_sync(self) -> None:
        """Un único intento de conexión (bloqueante); lanza si falla o no hay CONNACK.

        `client.connect()` (paho-mqtt) solo abre el socket TCP y envía el paquete
        CONNECT — el resultado real de la autenticación llega en el callback
        `on_connect` (CONNACK), que requiere el hilo de red (`loop_start`). Por eso
        se espera explícitamente ese callback con un `threading.Event` en vez de
        asumir éxito por que `connect()` no lanzó excepción de socket.
        """
        connack_event = threading.Event()
        result: dict[str, int | None] = {"rc": None}

        def _on_connect(client, userdata, flags, rc) -> None:  # noqa: ANN001 — firma fija de paho-mqtt v1
            result["rc"] = rc
            connack_event.set()

        client = mqtt.Client(client_id=self._client_id, protocol=mqtt.MQTTv311)
        client.username_pw_set(self._user, self._password)
        client.on_connect = _on_connect
        try:
            client.connect(self._host, self._port, keepalive=10)
            client.loop_start()
            if not connack_event.wait(timeout=_CONNACK_TIMEOUT_SECONDS):
                raise TimeoutError("sin respuesta CONNACK del broker Mosquitto")
            if result["rc"] != 0:
                raise ConnectionRefusedError(
                    f"broker Mosquitto rechazó la conexión (CONNACK rc={result['rc']})"
                )
        finally:
            client.loop_stop()
            client.disconnect()

    async def connect(self) -> None:
        """RF-006/RF-008 — conecta con credencial propia; backoff fijo sin loop ciego."""
        loop = asyncio.get_running_loop()
        total_attempts = len(_RETRY_BACKOFF_SECONDS) + 1

        for attempt in range(1, total_attempts + 1):
            try:
                await loop.run_in_executor(None, self._connect_once_sync)
                self._connected = True
                return
            except Exception as exc:  # noqa: BLE001 — cualquier fallo se loguea y se reintenta con backoff
                _logger.error(
                    "Fallo de conexión MQTT (intento %d/%d): %s",
                    attempt,
                    total_attempts,
                    exc,
                )
                if attempt == total_attempts:
                    self._connected = False
                    return
                await asyncio.sleep(_RETRY_BACKOFF_SECONDS[attempt - 1])

    async def ping(self) -> bool:
        """RF-002/RF-007 — un único intento de conexión, sin el backoff de `connect()`.

        El timeout de 2s (RNF-002) lo aplica quien llama
        (`services/health_service.py::_ping_with_timeout`).
        """
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._connect_once_sync)
            self._connected = True
            return True
        except Exception as exc:  # noqa: BLE001 — se refleja como `error` en /health (RF-007)
            _logger.error("Chequeo de salud MQTT falló: %s", exc)
            self._connected = False
            return False
