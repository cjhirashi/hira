"""`BacnetSimulatorPort` — interfaz abstracta del simulador BACnet/IP
(`Protocol`, `SRV-ADR-017`), `SRV-006-simuladores` (`plan.md §2`).

`services/simulator_service.py` importa este contrato y su value object,
nunca `BAC0`/`bacpypes3` directamente (overlay de `hira-server/CLAUDE.md`).
La implementación real (`adapters/bacnet/bacnet_simulator_adapter.py::
BacnetSimulatorAdapter`) llega en un batch posterior de `tasks.md` (T-020/
T-021) — fuera de alcance aquí. Sin test propio, igual que
`bacnet_transport_port.py`/`device_repository_port.py`: es una interfaz, no
lógica.

**Puerto nuevo, distinto de `BacnetTransportPort`** (`SRV-003`, rol
*cliente*, efímero por escaneo) — este puerto modela un rol *servidor*
persistente hasta `DELETE` (`plan.md §2`/Registro de decisiones: forzar
ambos roles en un solo `Protocol` violaría Anti-Abstraction).
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BacnetSimulatedObjectSpec:
    """Un objeto BACnet inicial del simulador (RF-001). `object_type` ∈ los 6
    valores soportados (`schemas/simulators.py::BacnetSimulatedObjectIn`,
    validados en el borde HTTP, `plan.md §1` Registro de decisiones).
    `present_value` en texto — el adaptador lo convierte al tipo BACnet real
    (float para analog-*, "active"/"inactive" para binary-*)."""

    object_type: str
    object_instance: int
    present_value: str


class BacnetSimulatorPort(Protocol):
    async def start(
        self, *, device_instance: int, objects: list[BacnetSimulatedObjectSpec]
    ) -> str:
        """Arranca una instancia BACnet/IP real (RF-001) que responde a
        Who-Is con `device_instance` y expone `objects` como objetos BACnet
        reales, leíbles por cualquier cliente BACnet real (incl.
        `BacnetTransportPort`, `SRV-003`). No bloquea el *event loop*
        (RNF-001 — mismo patrón ya `verified` de `BAC0Adapter`, construcción
        síncrona de `BAC0.lite()`, `plan.md §5`). Retorna un token opaco que
        identifica esta instancia, para pasar a `stop()`."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene la instancia identificada por `token` (RF-009), liberando
        su socket UDP local."""
        ...
