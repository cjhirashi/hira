"""Integración real — `PymodbusAdapter` contra un servidor Modbus TCP real de
`pymodbus` en `127.0.0.1` (`SRV-004-modbus-adapter`, T-009/T-010, `plan.md §5`/
§6 paso 6).

Sin mocks: tráfico TCP Modbus real, con el mismo códec del protocolo
(`pymodbus`) — no es hardware real, pero tampoco una simulación de la interfaz
del adaptador (`spec.md §2`), mismo criterio que `tests/integration/
test_bac0_adapter.py` con BAC0.

Verificado con ejecución real (spike previo a este archivo, ver `plan.md §5`
nota de investigación — re-verificado en esta sesión contra `pymodbus==3.15.0`
efectivamente instalado):
- `pymodbus.datastore.ModbusServerContext`/`ModbusDeviceContext` (API
  "clásica") está roto en 3.15.0 (`async_getValues()` devuelve
  incondicionalmente `ExcCodes.DEVICE_BUSY`) — se usa
  `pymodbus.simulator.simdata.SimData`/`pymodbus.simulator.simdevice.SimDevice`
  (API nueva, recomendada por la propia librería), con `ModbusTcpServer`
  aceptando el `SimDevice` directamente como `context=`.
- Una dirección fuera del rango configurado o un `unit_id`/`device_id` no
  registrado en el `SimDevice` → `ExceptionResponse` real del servidor
  (`isError() == True`), no una excepción de Python ni un timeout.
- Con `AsyncModbusTcpClient(..., timeout=1.0, retries=0)` contra un servidor
  TCP que acepta la conexión pero nunca responde: `read_holding_registers(...)`
  lanza `ModbusIOException` real a los **≈1.002s** medidos
  (`time.monotonic()`) — confirma que `retries=0` es imprescindible para que
  el timeout real sea 1s y no ~4s (RF-008), valor por defecto de `pymodbus`
  es `retries=3`.

Requiere `pip install pymodbus==3.15.0` (`requirements.txt`) — sin
contenedores, sin Postgres, solo TCP real en loopback. El servidor de prueba
(`ModbusTcpServer` + `SimDevice`/`SimData`) es infraestructura de test de esta
feature, **no** es el producto "Simuladores" (`SRV-ADR-014`, feature aparte).
"""
import asyncio
import logging
import time

import pytest
from pymodbus.server import ModbusTcpServer
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice

from adapters.modbus.pymodbus_adapter import PymodbusAdapter
from core.ports.modbus_transport_port import (
    ModbusReadFailure,
    ModbusRegisterReading,
    ModbusRegisterType,
)

pytestmark = pytest.mark.integration

# El framer/decodificador de `pymodbus` emite tráfico TCP crudo (`>>>>> send/
# recv`) en `INFO` — silenciado para no ensuciar la evidencia de terminal de
# esta suite (no afecta el comportamiento verificado, solo el logging).
logging.getLogger("pymodbus").setLevel(logging.WARNING)


async def _make_simulated_device(port: int, unit_id: int = 1) -> ModbusTcpServer:
    """Servidor Modbus TCP real con los 4 tipos de registro cargados — 5
    direcciones cada uno (`start=0`), valores conocidos para verificar
    RF-001/RF-002. Infraestructura de test (`spec.md §2`), no el adaptador
    bajo prueba."""
    coils = [SimData(address=0, count=5, values=1, datatype=DataType.BITS)]
    discrete_inputs = [SimData(address=0, count=5, values=0, datatype=DataType.BITS)]
    holding_registers = [SimData(address=0, count=5, values=42, datatype=DataType.UINT16)]
    input_registers = [SimData(address=0, count=5, values=77, datatype=DataType.UINT16)]

    device = SimDevice(
        id=unit_id,
        simdata=(coils, discrete_inputs, holding_registers, input_registers),
    )
    server = ModbusTcpServer(context=device, address=("127.0.0.1", port))
    server._test_task = asyncio.create_task(server.serve_forever())  # noqa: SLF001 — helper de test
    await asyncio.sleep(0.3)  # deja que el servidor termine de escuchar
    return server


async def _shutdown_server(server: ModbusTcpServer) -> None:
    await server.shutdown()
    await asyncio.wait_for(server._test_task, timeout=3.0)  # noqa: SLF001


@pytest.mark.asyncio
async def test_read_range_holding_registers_real_values():
    """RF-001, RF-002 — lee un rango de holding registers de un servidor
    Modbus TCP real; los valores devueltos coinciden exactamente con los
    cargados en el servidor."""
    server = await _make_simulated_device(15502)
    adapter = PymodbusAdapter()
    try:
        results = await adapter.read_range(
            host="127.0.0.1",
            port=15502,
            unit_id=1,
            register_type=ModbusRegisterType.HOLDING_REGISTER,
            start=0,
            count=3,
            timeout_seconds=1.0,
        )

        assert len(results) == 3
        for offset, result in enumerate(results):
            assert isinstance(result, ModbusRegisterReading)
            assert result.register_type == ModbusRegisterType.HOLDING_REGISTER
            assert result.address == offset
            assert result.value == 42
    finally:
        await _shutdown_server(server)


@pytest.mark.asyncio
async def test_read_range_all_four_register_types_real_values():
    """RF-001, RF-002 — los 4 tipos de registro devuelven exactamente los
    valores reales cargados en el servidor, cada uno con su propio método
    de `pymodbus` internamente (coil/discrete_input → bool, holding/input →
    int)."""
    server = await _make_simulated_device(15503)
    adapter = PymodbusAdapter()
    try:
        coil_results = await adapter.read_range(
            host="127.0.0.1", port=15503, unit_id=1,
            register_type=ModbusRegisterType.COIL, start=0, count=1,
            timeout_seconds=1.0,
        )
        discrete_results = await adapter.read_range(
            host="127.0.0.1", port=15503, unit_id=1,
            register_type=ModbusRegisterType.DISCRETE_INPUT, start=0, count=1,
            timeout_seconds=1.0,
        )
        input_results = await adapter.read_range(
            host="127.0.0.1", port=15503, unit_id=1,
            register_type=ModbusRegisterType.INPUT_REGISTER, start=0, count=1,
            timeout_seconds=1.0,
        )

        assert isinstance(coil_results[0], ModbusRegisterReading)
        assert coil_results[0].value is True

        assert isinstance(discrete_results[0], ModbusRegisterReading)
        assert discrete_results[0].value is False

        assert isinstance(input_results[0], ModbusRegisterReading)
        assert input_results[0].value == 77
    finally:
        await _shutdown_server(server)


@pytest.mark.asyncio
async def test_read_range_out_of_range_address_is_read_failure():
    """RF-005 — una dirección fuera del rango configurado en el servidor real
    responde con `ExceptionResponse` (`isError() == True`) → `ModbusReadFailure`,
    no una excepción de Python."""
    server = await _make_simulated_device(15504)
    adapter = PymodbusAdapter()
    try:
        results = await adapter.read_range(
            host="127.0.0.1",
            port=15504,
            unit_id=1,
            register_type=ModbusRegisterType.HOLDING_REGISTER,
            start=999,
            count=1,
            timeout_seconds=1.0,
        )

        assert len(results) == 1
        assert isinstance(results[0], ModbusReadFailure)
        assert results[0].address == 999
        assert results[0].register_type == ModbusRegisterType.HOLDING_REGISTER
    finally:
        await _shutdown_server(server)


@pytest.mark.asyncio
async def test_read_range_wrong_unit_id_is_read_failure():
    """RF-005 — un `unit_id` no registrado en el servidor real responde con
    `ExceptionResponse` real → `ModbusReadFailure` (mismo tratamiento que una
    dirección fuera de rango, sin caso especial en el adaptador)."""
    server = await _make_simulated_device(15505, unit_id=1)
    adapter = PymodbusAdapter()
    try:
        results = await adapter.read_range(
            host="127.0.0.1",
            port=15505,
            unit_id=99,
            register_type=ModbusRegisterType.HOLDING_REGISTER,
            start=0,
            count=1,
            timeout_seconds=1.0,
        )

        assert len(results) == 1
        assert isinstance(results[0], ModbusReadFailure)
    finally:
        await _shutdown_server(server)


@pytest.mark.asyncio
async def test_read_range_partial_failure_does_not_abort_rest_of_range():
    """RF-005 — un rango que mezcla direcciones válidas (0-4, cargadas) e
    inválidas (5-6, fuera de rango) devuelve `count` resultados, con
    `ModbusRegisterReading`/`ModbusReadFailure` mezclados en orden — ninguna
    dirección fallida aborta el resto del rango."""
    server = await _make_simulated_device(15506)
    adapter = PymodbusAdapter()
    try:
        results = await adapter.read_range(
            host="127.0.0.1",
            port=15506,
            unit_id=1,
            register_type=ModbusRegisterType.HOLDING_REGISTER,
            start=3,
            count=4,  # direcciones 3, 4 (válidas) + 5, 6 (fuera del rango cargado)
            timeout_seconds=1.0,
        )

        assert len(results) == 4
        assert isinstance(results[0], ModbusRegisterReading)  # address 3
        assert isinstance(results[1], ModbusRegisterReading)  # address 4
        assert isinstance(results[2], ModbusReadFailure)  # address 5
        assert isinstance(results[3], ModbusReadFailure)  # address 6
    finally:
        await _shutdown_server(server)


@pytest.mark.asyncio
async def test_read_range_timeout_is_real_and_close_to_one_second():
    """RF-005, RF-008 — contra un servidor TCP real que acepta la conexión y
    nunca responde, cada dirección falla por timeout real medido (`retries=0`
    imprescindible, ver docstring del módulo) — cercano a 1.0s, no ~4s (valor
    por defecto de `pymodbus`, `retries=3`)."""
    connections: list[asyncio.StreamWriter] = []

    async def _silent_handler(reader, writer):
        connections.append(writer)
        await asyncio.sleep(3600)

    silent_server = await asyncio.start_server(_silent_handler, "127.0.0.1", 15507)
    adapter = PymodbusAdapter()
    try:
        start = time.monotonic()
        results = await asyncio.wait_for(
            adapter.read_range(
                host="127.0.0.1",
                port=15507,
                unit_id=1,
                register_type=ModbusRegisterType.HOLDING_REGISTER,
                start=0,
                count=1,
                timeout_seconds=1.0,
            ),
            timeout=5.0,
        )
        elapsed = time.monotonic() - start

        print(
            f"\nRF-008 evidencia real: timeout de 1 dirección sin respuesta "
            f"tardó {elapsed:.3f}s (retries=0)"
        )
        assert len(results) == 1
        assert isinstance(results[0], ModbusReadFailure)
        assert results[0].address == 0
        # Cercano a 1.0s (spike real midió 1.002s) — muy por debajo de los
        # ~4s que produciría el valor por defecto de pymodbus (retries=3).
        assert 0.9 <= elapsed <= 2.5, f"timeout tardó {elapsed:.3f}s (RF-008)"
    finally:
        for writer in connections:
            writer.close()
        silent_server.close()
        await asyncio.wait_for(silent_server.wait_closed(), timeout=3.0)
