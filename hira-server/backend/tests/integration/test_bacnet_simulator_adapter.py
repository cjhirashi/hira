"""Integración real — `BacnetSimulatorAdapter` (`SRV-006-simuladores`,
T-020/T-021, `plan.md §5` fila "Adaptador BACnet").

El simulador es el **producto bajo prueba**: una instancia `BAC0.lite(deviceId=...)`
arrancada por el adaptador, verificada con un **cliente BACnet real** separado
(`BAC0.lite()` sin `deviceId`, sin `BAC0Adapter` ni mocks) que hace Who-Is
unicast y lee `presentValue` por UDP en loopback.

Rango de puertos propio (`48200+`), distinto del `479xx` de
`tests/integration/test_bac0_adapter.py` y del default de producción
(`47900`) — evita colisiones con el registro interno de IPs en uso de `BAC0`
entre tests.
"""
import asyncio

import BAC0
import pytest

from adapters.bacnet.bacnet_simulator_adapter import BacnetSimulatorAdapter
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec

pytestmark = pytest.mark.integration

_IP = "127.0.0.1"


async def _who_is(client, port: int) -> list[int]:
    iams = await client.who_is(address=f"{_IP}:{port}", timeout=3)
    return [int(iam.iAmDeviceIdentifier[1]) for iam in iams]


@pytest.mark.asyncio
async def test_start_answers_who_is_and_exposes_initial_objects():
    """RF-001 — el simulador responde I-Am con su `device_instance` y un
    cliente real lee el `presentValue` de cada objeto inicial (analog → float,
    binary → active/inactive)."""
    adapter = BacnetSimulatorAdapter(ip=_IP, port_range_start=48200)
    client = BAC0.lite(ip=_IP, port=48299, ping=False)
    token = await adapter.start(
        device_instance=999123,
        objects=[
            BacnetSimulatedObjectSpec("analog-value", 1, "42.0"),
            BacnetSimulatedObjectSpec("analog-input", 2, "1.5"),
            BacnetSimulatedObjectSpec("binary-output", 3, "active"),
        ],
    )
    try:
        assert await _who_is(client, 48200) == [999123]
        assert await client.read(f"{_IP}:48200 analogValue 1 presentValue") == 42.0
        assert await client.read(f"{_IP}:48200 analogInput 2 presentValue") == 1.5
        assert str(await client.read(f"{_IP}:48200 binaryOutput 3 presentValue")) == "active"
    finally:
        await adapter.stop(token)
        await client.disconnect()


@pytest.mark.asyncio
async def test_stop_releases_udp_port_for_a_later_start():
    """RF-009 — `stop(token)` libera el puerto UDP: el siguiente `start()`
    vuelve a ocupar el primero del rango y responde con su propio
    `device_instance`."""
    adapter = BacnetSimulatorAdapter(ip=_IP, port_range_start=48210)
    client = BAC0.lite(ip=_IP, port=48298, ping=False)
    first = await adapter.start(device_instance=1001, objects=[])
    await adapter.stop(first)
    await asyncio.sleep(0.3)

    second = await adapter.start(device_instance=1002, objects=[])
    try:
        assert await _who_is(client, 48210) == [1002]
    finally:
        await adapter.stop(second)
        await client.disconnect()


@pytest.mark.asyncio
async def test_two_concurrent_simulators_do_not_collide():
    """RNF-001 — 2 simuladores simultáneos ocupan puertos distintos del rango
    y cada uno responde con su propio `device_instance`."""
    adapter = BacnetSimulatorAdapter(ip=_IP, port_range_start=48220)
    client = BAC0.lite(ip=_IP, port=48297, ping=False)
    token_a = await adapter.start(device_instance=2001, objects=[])
    token_b = await adapter.start(device_instance=2002, objects=[])
    try:
        assert token_a != token_b
        assert await _who_is(client, 48220) == [2001]
        assert await _who_is(client, 48221) == [2002]
    finally:
        await adapter.stop(token_a)
        await adapter.stop(token_b)
        await client.disconnect()


@pytest.mark.asyncio
async def test_start_does_not_block_the_event_loop():
    """RNF-001 — mientras `start()` corre, otra corutina del mismo loop sigue
    avanzando (un *ticker* de 10 ms registra varios ticks)."""
    adapter = BacnetSimulatorAdapter(ip=_IP, port_range_start=48230)
    ticks = 0
    stop_ticker = asyncio.Event()

    async def ticker():
        nonlocal ticks
        while not stop_ticker.is_set():
            ticks += 1
            await asyncio.sleep(0.01)

    ticker_task = asyncio.create_task(ticker())
    token = await adapter.start(device_instance=3001, objects=[])
    stop_ticker.set()
    await ticker_task
    try:
        assert ticks >= 2
    finally:
        await adapter.stop(token)
