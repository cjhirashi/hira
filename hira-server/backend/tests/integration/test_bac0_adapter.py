"""Integración real — `BAC0Adapter` contra 2 instancias reales de `BAC0.lite()`
en `127.0.0.1` (`SRV-003-bacnet-adapter`, T-013/T-014, `plan.md §5`/§6 paso 10).

Sin mocks: Who-Is/I-Am y lectura de objetos BACnet reales por UDP, con el mismo
códec del protocolo (`bacpypes3`) — no es hardware real, pero tampoco una
simulación de la interfaz de `BAC0` (`spec.md §2`). Una instancia "dispositivo"
expone 2 objetos BACnet reales (`bacpypes3.local.analog.AnalogValueObject`/
`bacpypes3.local.binary.BinaryValueObject`, vía
`Application.add_object` — API "for sample applications" del propio código de
`bacpypes3`); la otra es el `BAC0Adapter` bajo prueba.

Who-Is dirigido **unicast** (`target_address`, parámetro propio de `BAC0Adapter`,
no forma parte de `BacnetTransportPort`) a la dirección/puerto del "dispositivo"
simulado — no depende de que un broadcast UDP atraviese la red/namespace del
entorno de test (`plan.md §5`, nota "Who-Is broadcast" del test de adaptador).
Sigue siendo Who-Is/I-Am real por UDP con el mismo códec; solo cambia el modo de
direccionamiento. El broadcast real de RF-001 en producción no se re-verifica
aquí (mismo criterio ya documentado en `plan.md §5`).

Puertos UDP únicos por test (`479xx`) — evita colisiones con el registro interno
de IPs en uso de `BAC0` (`Base._used_ips`) si el `disconnect()` (asíncrono, no
bloqueante) de un test anterior aún no liberó el puerto cuando arranca el
siguiente.

Requiere `pip install BAC0==2026.7.25` (`requirements.txt`) — sin contenedores,
sin Postgres, solo UDP real en loopback.
"""
import asyncio

import pytest
from bacpypes3.local.analog import AnalogValueObject
from bacpypes3.local.binary import BinaryValueObject

from adapters.bacnet.bac0_adapter import BAC0Adapter
from core.ports.bacnet_transport_port import BacnetReadTimeoutError

pytestmark = pytest.mark.integration


async def _make_simulated_device(port: int):
    """Crea una instancia real de `BAC0.lite()` que actúa de "dispositivo" con
    2 objetos reales — infraestructura de test (`spec.md §2`), no el adaptador
    bajo prueba (no es el producto "Simuladores", `SRV-ADR-014`)."""
    import BAC0  # solo este helper de test conoce BAC0 directamente

    device = BAC0.lite(ip="127.0.0.1", port=port, ping=False)
    device.this_application.app.add_object(
        AnalogValueObject(
            objectIdentifier=("analogValue", 1),
            objectName="Zone Temperature",
            presentValue=21.5,
            statusFlags=[0, 0, 0, 0],
            covIncrement=0.1,
            units="degreesCelsius",
        )
    )
    device.this_application.app.add_object(
        BinaryValueObject(
            objectIdentifier=("binaryValue", 1),
            objectName="Fan Command",
            presentValue="active",
            statusFlags=[0, 0, 0, 0],
        )
    )
    await asyncio.sleep(0.3)  # deja que el stack BACnet termine de registrarse
    return device


@pytest.mark.asyncio
async def test_who_is_unicast_discovers_real_device_iam():
    """RF-001 — Who-Is real (unicast) recibe el I-Am del "dispositivo" con su
    `instance_number` y dirección de red correctos."""
    device = await _make_simulated_device(47900)
    adapter = BAC0Adapter(
        ip="127.0.0.1", port=47901, target_address="127.0.0.1:47900"
    )
    try:
        announcements = await adapter.who_is(timeout_seconds=3.0)

        assert len(announcements) == 1
        assert announcements[0].instance_number == device.Boid
        assert announcements[0].network_address == "127.0.0.1:47900"
    finally:
        await adapter.disconnect()
        await device.disconnect()


@pytest.mark.asyncio
async def test_read_device_objects_matches_real_objects():
    """RF-002 — los objetos leídos coinciden con los creados en el
    "dispositivo" real (nombre, valor, unidades); ni `device` ni `network-port`
    se persisten como candidatos (no son "puntos")."""
    device = await _make_simulated_device(47902)
    adapter = BAC0Adapter(
        ip="127.0.0.1", port=47903, target_address="127.0.0.1:47902"
    )
    try:
        announcements = await adapter.who_is(timeout_seconds=3.0)
        assert announcements

        readings = await adapter.read_device_objects(
            announcements[0].network_address, timeout_seconds=2.0
        )

        by_key = {(r.object_type, r.object_instance): r for r in readings}
        assert set(by_key) == {("analog-value", 1), ("binary-value", 1)}

        av = by_key[("analog-value", 1)]
        assert av.object_name == "Zone Temperature"
        assert av.present_value == "21.5"
        assert av.units == "degrees-celsius"

        bv = by_key[("binary-value", 1)]
        assert bv.object_name == "Fan Command"
        assert bv.present_value == "active"
    finally:
        await adapter.disconnect()
        await device.disconnect()


@pytest.mark.asyncio
async def test_read_device_objects_times_out_if_device_disconnects():
    """RF-006/RF-010 — dispositivo apagado tras el I-Am y antes de la lectura:
    `BacnetReadTimeoutError` real, medido en ~2s (RF-010) — no cuelga el
    proceso ni excede significativamente el timeout configurado."""
    device = await _make_simulated_device(47904)
    adapter = BAC0Adapter(
        ip="127.0.0.1", port=47905, target_address="127.0.0.1:47904"
    )
    try:
        announcements = await adapter.who_is(timeout_seconds=3.0)
        assert announcements
        network_address = announcements[0].network_address

        await device.disconnect()
        await asyncio.sleep(0.2)

        loop = asyncio.get_event_loop()
        start = loop.time()
        with pytest.raises(BacnetReadTimeoutError):
            await adapter.read_device_objects(network_address, timeout_seconds=2.0)
        elapsed = loop.time() - start

        assert 1.8 <= elapsed <= 4.0
    finally:
        await adapter.disconnect()
