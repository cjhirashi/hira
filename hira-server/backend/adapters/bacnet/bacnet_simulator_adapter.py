"""`BacnetSimulatorAdapter` — implementación real de `BacnetSimulatorPort` vía
`BAC0`/`bacpypes3` (`SRV-006-simuladores`, T-021, `plan.md §2`/§5).

Cada `start()` crea una instancia `BAC0.lite(deviceId=...)` **independiente**
(rol *servidor*: responde a Who-Is con el `device_instance` pedido) — distinta
del `BAC0Adapter` cliente de `SRV-003`. Los objetos iniciales se registran con
`Application.add_object` (`bacpypes3.local.{analog,binary}`), mismo mecanismo
verificado en `tests/integration/test_bac0_adapter.py::_make_simulated_device`.

Puerto UDP local **efímero** (`plan.md §1`, Registro de decisiones): el menor
puerto libre desde `port_range_start`, liberado en `stop()` — la identidad
restart-safe del simulador es `device_instance` (`core/bacnet_address.py::
format_simulator_device_address`), no el puerto.

Solo `adapters/bacnet/*` importa `BAC0`/`bacpypes3` (`SRV-ADR-017`).
"""
import asyncio
import uuid
from dataclasses import dataclass
from typing import Any

import BAC0
from bacpypes3.local.analog import AnalogInputObject, AnalogOutputObject, AnalogValueObject
from bacpypes3.local.binary import BinaryInputObject, BinaryOutputObject, BinaryValueObject

from core.logger import get_logger
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec

_logger = get_logger("bacnet_simulator_adapter")

# `object_type` del contrato (`schemas/simulators.py`) → (clase local de
# `bacpypes3`, identificador BACnet en camelCase, es analógico).
_OBJECT_KINDS: dict[str, tuple[type, str, bool]] = {
    "analog-value": (AnalogValueObject, "analogValue", True),
    "analog-input": (AnalogInputObject, "analogInput", True),
    "analog-output": (AnalogOutputObject, "analogOutput", True),
    "binary-value": (BinaryValueObject, "binaryValue", False),
    "binary-input": (BinaryInputObject, "binaryInput", False),
    "binary-output": (BinaryOutputObject, "binaryOutput", False),
}

# `BAC0.lite()` retorna antes de que `bacpypes3` enlace el socket UDP (tarea
# de fondo de `IPv4DatagramServer`); sin esperar a `local_transport`, un
# Who-Is inmediato tras `start()` no obtiene respuesta.
_READY_TIMEOUT_SECONDS = 3.0


@dataclass
class _RunningInstance:
    lite: Any
    port: int


class BacnetSimulatorAdapter:
    """Implementa `BacnetSimulatorPort` con instancias `BAC0.lite()` reales."""

    def __init__(self, *, ip: str | None, port_range_start: int) -> None:
        self._ip = ip
        self._port_range_start = port_range_start
        self._instances: dict[str, _RunningInstance] = {}

    async def start(
        self, *, device_instance: int, objects: list[BacnetSimulatedObjectSpec]
    ) -> str:
        port = self._next_free_port()
        lite = BAC0.lite(ip=self._ip, port=port, deviceId=device_instance, ping=False)
        try:
            for spec in objects:
                lite.this_application.app.add_object(_build_object(spec))
            await _wait_until_ready(lite)
        except Exception:
            await lite.disconnect()
            raise

        token = uuid.uuid4().hex
        self._instances[token] = _RunningInstance(lite=lite, port=port)
        _logger.info(
            "Simulador BACnet %s arrancado en el puerto UDP %s", device_instance, port
        )
        return token

    async def stop(self, token: str) -> None:
        instance = self._instances.pop(token, None)
        if instance is None:
            return
        await instance.lite.disconnect()
        _logger.info("Simulador BACnet detenido (puerto UDP %s liberado)", instance.port)

    def _next_free_port(self) -> int:
        used = {instance.port for instance in self._instances.values()}
        port = self._port_range_start
        while port in used:
            port += 1
        return port


def _build_object(spec: BacnetSimulatedObjectSpec) -> Any:
    object_class, identifier, is_analog = _OBJECT_KINDS[spec.object_type]
    present_value: Any = float(spec.present_value) if is_analog else spec.present_value
    return object_class(
        objectIdentifier=(identifier, spec.object_instance),
        objectName=f"{spec.object_type}-{spec.object_instance}",
        presentValue=present_value,
        statusFlags=[0, 0, 0, 0],
    )


async def _wait_until_ready(lite: Any) -> None:
    link_layers = list(lite.this_application.app.link_layers.values())
    loop = asyncio.get_running_loop()
    deadline = loop.time() + _READY_TIMEOUT_SECONDS
    while any(link.server.local_transport is None for link in link_layers):
        if loop.time() >= deadline:
            raise RuntimeError(
                f"El socket UDP del simulador BACnet no quedó enlazado en "
                f"{_READY_TIMEOUT_SECONDS}s"
            )
        await asyncio.sleep(0.01)
