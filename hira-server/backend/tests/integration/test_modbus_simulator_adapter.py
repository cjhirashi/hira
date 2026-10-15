"""Integración real — `ModbusSimulatorAdapter` (`SRV-006-simuladores`,
T-022/T-023, `plan.md §5` fila "Adaptador Modbus").

El simulador es el **producto bajo prueba**: un `ModbusTcpServer` real
arrancado por el adaptador, verificado con un **cliente Modbus real**
(`AsyncModbusTcpClient`, sin `PymodbusAdapter` ni mocks) por TCP en loopback.
Solo las direcciones configuradas responden; cualquier otra (o un tipo de
registro sin valores) devuelve una excepción Modbus real, como un PLC real.
"""
import asyncio

import pytest
from pymodbus.client import AsyncModbusTcpClient

from adapters.modbus.modbus_simulator_adapter import ModbusSimulatorAdapter
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec
from core.ports.modbus_transport_port import ModbusRegisterType

pytestmark = pytest.mark.integration

_HOST = "127.0.0.1"


async def _client(port: int) -> AsyncModbusTcpClient:
    client = AsyncModbusTcpClient(_HOST, port=port, timeout=1.0, retries=0)
    await client.connect()
    return client


@pytest.mark.asyncio
async def test_start_serves_loaded_registers_of_the_four_types():
    """RF-002 — un cliente real lee los valores cargados: holding/input →
    int, coil/discrete → bool, con `unit_id` como *device id*."""
    adapter = ModbusSimulatorAdapter()
    token = await adapter.start(
        host=_HOST,
        port=15700,
        unit_id=3,
        registers=[
            ModbusSimulatedRegisterSpec(ModbusRegisterType.COIL, 4, True),
            ModbusSimulatedRegisterSpec(ModbusRegisterType.DISCRETE_INPUT, 0, False),
            ModbusSimulatedRegisterSpec(ModbusRegisterType.HOLDING_REGISTER, 0, 42),
            ModbusSimulatedRegisterSpec(ModbusRegisterType.HOLDING_REGISTER, 10, 7),
            ModbusSimulatedRegisterSpec(ModbusRegisterType.INPUT_REGISTER, 2, 77),
        ],
    )
    client = await _client(15700)
    try:
        assert (await client.read_coils(4, count=1, device_id=3)).bits[0] is True
        assert (await client.read_discrete_inputs(0, count=1, device_id=3)).bits[0] is False
        assert (await client.read_holding_registers(0, count=1, device_id=3)).registers == [42]
        assert (await client.read_holding_registers(10, count=1, device_id=3)).registers == [7]
        assert (await client.read_input_registers(2, count=1, device_id=3)).registers == [77]
    finally:
        client.close()
        await adapter.stop(token)


@pytest.mark.asyncio
async def test_unconfigured_addresses_answer_with_a_modbus_exception():
    """RF-002 — una dirección no cargada (o un tipo sin valores) responde
    con excepción Modbus real, no con un valor inventado."""
    adapter = ModbusSimulatorAdapter()
    token = await adapter.start(
        host=_HOST,
        port=15701,
        unit_id=1,
        registers=[ModbusSimulatedRegisterSpec(ModbusRegisterType.HOLDING_REGISTER, 0, 42)],
    )
    client = await _client(15701)
    try:
        assert (await client.read_holding_registers(5, count=1, device_id=1)).isError()
        assert (await client.read_coils(0, count=1, device_id=1)).isError()
        assert (await client.read_input_registers(0, count=1, device_id=1)).isError()
    finally:
        client.close()
        await adapter.stop(token)


@pytest.mark.asyncio
async def test_stop_closes_the_server():
    """RF-009 — tras `stop(token)` un cliente nuevo no puede conectar."""
    adapter = ModbusSimulatorAdapter()
    token = await adapter.start(host=_HOST, port=15702, unit_id=1, registers=[])

    await adapter.stop(token)

    client = AsyncModbusTcpClient(_HOST, port=15702, timeout=1.0, retries=0)
    try:
        assert await client.connect() is False
    finally:
        client.close()


@pytest.mark.asyncio
async def test_start_on_a_port_already_in_use_raises_without_hanging():
    """Un `host:port` ya ocupado por otro servidor falla de inmediato
    (`< 2s`), sin dejar una tarea de fondo colgada."""
    adapter = ModbusSimulatorAdapter()
    token = await adapter.start(host=_HOST, port=15703, unit_id=1, registers=[])
    loop = asyncio.get_running_loop()
    try:
        started = loop.time()
        with pytest.raises(RuntimeError):
            await adapter.start(host=_HOST, port=15703, unit_id=2, registers=[])
        assert loop.time() - started < 2.0
    finally:
        await adapter.stop(token)
