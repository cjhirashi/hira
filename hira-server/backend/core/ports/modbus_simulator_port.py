"""`ModbusSimulatorPort` — interfaz abstracta del simulador Modbus TCP
(`Protocol`, `SRV-ADR-017`), `SRV-006-simuladores` (`plan.md §2`).

`services/simulator_service.py` importa este contrato y su value object,
nunca `pymodbus` directamente (overlay de `hira-server/CLAUDE.md`). La
implementación real (`adapters/modbus/modbus_simulator_adapter.py::
ModbusSimulatorAdapter`) llega en un batch posterior de `tasks.md` (T-022/
T-023) — fuera de alcance aquí. Sin test propio, igual que
`modbus_transport_port.py`/`device_repository_port.py`: es una interfaz, no
lógica.

**Puerto nuevo, distinto de `ModbusTransportPort`** (`SRV-004`, rol
*cliente*, efímero por escaneo) — este puerto modela un rol *servidor*
persistente hasta `DELETE` (`plan.md §2`/Registro de decisiones).
"""
from dataclasses import dataclass
from typing import Protocol

from core.ports.modbus_transport_port import ModbusRegisterType


@dataclass(frozen=True)
class ModbusSimulatedRegisterSpec:
    """Un registro inicial del simulador Modbus (RF-002). Reutiliza
    `ModbusRegisterType` de `modbus_transport_port.py` (`SRV-004`) — mismo
    vocabulario de tipo de registro que el escaneo, sin duplicarlo."""

    register_type: ModbusRegisterType
    address: int
    value: bool | int


class ModbusSimulatorPort(Protocol):
    async def start(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        registers: list[ModbusSimulatedRegisterSpec],
    ) -> str:
        """Arranca un servidor Modbus TCP real (RF-002) en `host:port` que
        responde con `unit_id` como *device id*, cargado con `registers`.
        No bloquea el *event loop* (RNF-001 — tarea de fondo,
        `ModbusTcpServer.serve_forever()`, `plan.md §5`). Retorna un token
        opaco."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene el servidor identificado por `token` (RF-009)."""
        ...
