"""`scan_bacnet` — caso de uso de escaneo BACnet (`SRV-003-bacnet-adapter`,
`plan.md §2`, RF-001, RF-002, RF-006, RF-007, RF-008, RNF-001).

Importa solo de `core/ports/`, `core/bacnet_address.py` y `core/logger.py` —
nunca `BAC0`/`sqlalchemy` directamente (`SRV-ADR-017`). Recibe ambos puertos
por parámetro (`adapters/factory.py` los inyecta desde `routers/devices.py`,
batch posterior).

RF-007 (nunca promover un candidato a tabla operable, `SRV-ADR-012`) se cumple
por omisión de diseño: este módulo no tiene ningún método que escriba en una
tabla `points` — no existe ningún `PointsRepositoryPort` importado ni
referenciado.
"""
import asyncio

from core.bacnet_address import format_device_address
from core.logger import get_logger
from core.ports.bacnet_transport_port import BacnetReadTimeoutError, BacnetTransportPort
from core.ports.device_repository_port import DeviceRecord, DeviceRepositoryPort

WHOIS_TIMEOUT_SECONDS = 3.0
READ_TIMEOUT_SECONDS = 2.0

_logger = get_logger("device_scan_service")


async def _scan_one(
    announcement, transport: BacnetTransportPort, device_repo: DeviceRepositoryPort
) -> DeviceRecord:
    """Persiste el dispositivo anunciado y, si responde a la lectura de
    objetos dentro de `READ_TIMEOUT_SECONDS`, sus candidatos (RF-002, RF-006)."""
    address = format_device_address(
        announcement.instance_number, announcement.network_address
    )
    device = await device_repo.upsert_device(
        name=f"BACnet {announcement.instance_number}",
        protocol="bacnet",
        address=address,
        is_simulator=False,
    )

    try:
        readings = await transport.read_device_objects(
            announcement.network_address, READ_TIMEOUT_SECONDS
        )
    except BacnetReadTimeoutError as exc:
        _logger.warning(
            "Timeout leyendo objetos de dispositivo BACnet device_id=%s address=%s: %s",
            device.id,
            address,
            exc,
        )
        return device

    for reading in readings:
        await device_repo.upsert_candidate(
            device_id=device.id,
            object_type=reading.object_type,
            object_instance=reading.object_instance,
            object_name=reading.object_name,
            present_value=reading.present_value,
            units=reading.units,
        )

    return device


async def scan_bacnet(
    transport: BacnetTransportPort, device_repo: DeviceRepositoryPort
) -> list[DeviceRecord]:
    """Who-Is (3s, RF-001) → por cada I-Am, lee objetos (timeout 2s, RF-006/
    RF-010) en paralelo (`asyncio.gather`, RNF-001) → persiste device+
    candidatos (RF-002). Sin ningún I-Am, retorna `[]` sin tocar el
    repositorio (RF-008 — 200 con lista vacía, no es un error)."""
    announcements = await transport.who_is(WHOIS_TIMEOUT_SECONDS)
    if not announcements:
        return []

    devices = await asyncio.gather(
        *(_scan_one(announcement, transport, device_repo) for announcement in announcements)
    )
    return list(devices)
