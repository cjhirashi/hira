"""`ModbusSimulatorAdapter` — implementación real de `ModbusSimulatorPort` vía
`pymodbus` (`SRV-006-simuladores`, T-023, `plan.md §2`/§5).

Cada `start()` levanta un `ModbusTcpServer` real con un `SimDevice` cargado
con los registros pedidos y lo sirve en una tarea de fondo
(`serve_forever()`, RNF-001) — mismo mecanismo `SimData`/`SimDevice` que
`tests/integration/test_pymodbus_adapter.py` usa como infraestructura de test
(`SRV-004`), aquí como producto.

Notas de `pymodbus==3.15.0` (verificadas con ejecución real):
- `SimDevice` con `simdata=(coils, discrete, holding, input)` exige que cada
  una de las 4 listas tenga al menos un bloque y que coils/discrete sean
  `DataType.BITS` (un `bool` por dirección). Un tipo sin valores pedidos
  recibe un bloque de relleno, y el `action` del `SimDevice` rechaza con
  `ILLEGAL_ADDRESS` toda dirección no configurada — un cliente solo ve los
  registros que el Admin cargó, igual que un PLC real.
- `ModbusTcpServer.transport` deja de ser `None` cuando ya escucha; si el
  puerto está ocupado, la tarea de `serve_forever()` termina con
  `RuntimeError` en vez de quedar colgada.

Solo `adapters/modbus/*` importa `pymodbus` (`SRV-ADR-017`).
"""
import asyncio
import uuid
from dataclasses import dataclass

from pymodbus.constants import ExcCodes
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice

from core.logger import get_logger
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec
from core.ports.modbus_transport_port import ModbusRegisterType

_logger = get_logger("modbus_simulator_adapter")

_READY_TIMEOUT_SECONDS = 3.0
_SHUTDOWN_TIMEOUT_SECONDS = 3.0

# Códigos de función Modbus de lectura/escritura → tipo de registro afectado.
_FUNCTION_CODE_TYPES: dict[int, ModbusRegisterType] = {
    1: ModbusRegisterType.COIL,
    5: ModbusRegisterType.COIL,
    15: ModbusRegisterType.COIL,
    2: ModbusRegisterType.DISCRETE_INPUT,
    3: ModbusRegisterType.HOLDING_REGISTER,
    6: ModbusRegisterType.HOLDING_REGISTER,
    16: ModbusRegisterType.HOLDING_REGISTER,
    4: ModbusRegisterType.INPUT_REGISTER,
}

_BIT_TYPES = frozenset({ModbusRegisterType.COIL, ModbusRegisterType.DISCRETE_INPUT})

# Orden exigido por `SimDevice(simdata=(...))`.
_SIMDATA_ORDER = (
    ModbusRegisterType.COIL,
    ModbusRegisterType.DISCRETE_INPUT,
    ModbusRegisterType.HOLDING_REGISTER,
    ModbusRegisterType.INPUT_REGISTER,
)


@dataclass
class _RunningServer:
    server: ModbusTcpServer
    task: asyncio.Task


class ModbusSimulatorAdapter:
    """Implementa `ModbusSimulatorPort` con `ModbusTcpServer` real."""

    def __init__(self) -> None:
        self._servers: dict[str, _RunningServer] = {}

    async def start(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        registers: list[ModbusSimulatedRegisterSpec],
    ) -> str:
        values = _values_by_type(registers)
        device = SimDevice(
            id=unit_id,
            simdata=tuple(_blocks(register_type, values[register_type]) for register_type in _SIMDATA_ORDER),
            action=_only_configured_addresses(values),
        )
        server = ModbusTcpServer(context=device, address=(host, port))
        task = asyncio.create_task(server.serve_forever())
        try:
            await _wait_until_listening(server, task)
        except Exception:
            await _shutdown(server, task)
            raise

        token = uuid.uuid4().hex
        self._servers[token] = _RunningServer(server=server, task=task)
        _logger.info("Simulador Modbus arrancado en %s:%s (unit %s)", host, port, unit_id)
        return token

    async def stop(self, token: str) -> None:
        running = self._servers.pop(token, None)
        if running is None:
            return
        await _shutdown(running.server, running.task)
        _logger.info("Simulador Modbus detenido")


def _values_by_type(
    registers: list[ModbusSimulatedRegisterSpec],
) -> dict[ModbusRegisterType, dict[int, bool | int]]:
    values: dict[ModbusRegisterType, dict[int, bool | int]] = {
        register_type: {} for register_type in ModbusRegisterType
    }
    for spec in registers:
        is_bit = spec.register_type in _BIT_TYPES
        values[spec.register_type][spec.address] = bool(spec.value) if is_bit else int(spec.value)
    return values


def _blocks(register_type: ModbusRegisterType, values: dict[int, bool | int]) -> list[SimData]:
    is_bit = register_type in _BIT_TYPES
    datatype = DataType.BITS if is_bit else DataType.UINT16
    if not values:
        return [SimData(address=0, count=1, values=False if is_bit else 0, datatype=datatype)]
    return [
        SimData(address=address, count=1, values=value, datatype=datatype)
        for address, value in sorted(values.items())
    ]


def _only_configured_addresses(values: dict[ModbusRegisterType, dict[int, bool | int]]):
    async def action(function_code, _start_address, address, count, _registers, _set_values):
        register_type = _FUNCTION_CODE_TYPES.get(function_code)
        if register_type is None:
            return None
        configured = values[register_type]
        if any(addr not in configured for addr in range(address, address + count)):
            return ExcCodes.ILLEGAL_ADDRESS
        return None

    return action


async def _wait_until_listening(server: ModbusTcpServer, task: asyncio.Task) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + _READY_TIMEOUT_SECONDS
    while server.transport is None:
        if task.done():
            task.result()
            raise RuntimeError("El servidor Modbus terminó sin llegar a escuchar")
        if loop.time() >= deadline:
            raise RuntimeError(
                f"El servidor Modbus no quedó escuchando en {_READY_TIMEOUT_SECONDS}s"
            )
        await asyncio.sleep(0.01)


async def _shutdown(server: ModbusTcpServer, task: asyncio.Task) -> None:
    if task.done():
        return
    await server.shutdown()
    await asyncio.wait_for(task, timeout=_SHUTDOWN_TIMEOUT_SECONDS)
