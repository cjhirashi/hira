"""`scan_bacnet`/`scan_modbus` — casos de uso de escaneo de dispositivos
(`SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter`, `plan.md §2`).

Importa solo de `core/ports/`, `core/bacnet_address.py`, `core/modbus_address.py`,
`core/errors.py` y `core/logger.py` — nunca `BAC0`/`pymodbus`/`sqlalchemy`
directamente (`SRV-ADR-017`). Recibe los puertos por parámetro
(`adapters/factory.py` los inyecta desde `routers/devices.py`).

`scan_modbus` vive en este mismo módulo que `scan_bacnet` (`SRV-004-modbus-
adapter/plan.md §1`, Registro de decisiones: mismo dominio de coordinación,
misma dependencia de `DeviceRepositoryPort`, no se separa por protocolo).

RF-006/RF-007 (nunca promover un candidato a tabla operable, `SRV-ADR-012`)
se cumple por omisión de diseño: este módulo no tiene ningún método que
escriba en una tabla `points` — no existe ningún `PointsRepositoryPort`
importado ni referenciado.
"""
import asyncio

from core.bacnet_address import format_device_address
from core.errors import ProblemDetailError
from core.logger import get_logger
from core.modbus_address import format_modbus_address
from core.ports.bacnet_transport_port import BacnetReadTimeoutError, BacnetTransportPort
from core.ports.device_repository_port import (
    DeviceCandidateRecord,
    DeviceRecord,
    DeviceRepositoryPort,
)
from core.ports.modbus_transport_port import (
    ModbusReadFailure,
    ModbusRegisterReading,
    ModbusRegisterType,
    ModbusTransportPort,
)

WHOIS_TIMEOUT_SECONDS = 3.0
READ_TIMEOUT_SECONDS = 2.0
MODBUS_MAX_RANGE_ADDRESSES = 125
MODBUS_READ_TIMEOUT_SECONDS = 1.0

_ERRORS_BASE_URL = "https://hira.dev/errors"

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


async def scan_modbus(
    *,
    host: str,
    port: int,
    unit_id: int,
    ranges: dict[ModbusRegisterType, tuple[int, int]],
    transport: ModbusTransportPort,
    device_repo: DeviceRepositoryPort,
) -> list[DeviceCandidateRecord]:
    """Sondea un rango de registros Modbus TCP por cada tipo indicado en
    `ranges` (RF-001) y persiste candidatos (RF-002).

    RF-004: rechaza con `ProblemDetailError(400, .../modbus-range-too-large)`
    si algún rango excede `MODBUS_MAX_RANGE_ADDRESSES` — **antes** de invocar
    `transport`/`device_repo` (ni siquiera se construye `address`).

    Las lecturas se ejecutan **secuencialmente** por tipo de registro
    (RNF-001, `plan.md §1` Registro de decisiones — a diferencia de
    `scan_bacnet`, las 4 lecturas apuntan al mismo dispositivo físico).

    RF-002: `device_repo.upsert_device` solo se invoca la primera vez que
    alguna dirección responde con éxito en todo el escaneo — RF-007: sin
    ninguna respuesta exitosa, retorna `[]` sin tocar `device_repo`.

    RF-005: una dirección que falla (`ModbusReadFailure`) se loguea y no
    aborta el resto del rango ni del escaneo.
    """
    for register_type, (start, count) in ranges.items():
        if count > MODBUS_MAX_RANGE_ADDRESSES:
            raise ProblemDetailError(
                status=400,
                type_=f"{_ERRORS_BASE_URL}/modbus-range-too-large",
                title="Rango de registros demasiado grande",
                detail=(
                    f"El rango solicitado para '{register_type.value}' tiene "
                    f"{count} direcciones; el máximo permitido por tipo de "
                    f"registro es {MODBUS_MAX_RANGE_ADDRESSES}."
                ),
            )

    address = format_modbus_address(host, port, unit_id)
    device: DeviceRecord | None = None
    candidates: list[DeviceCandidateRecord] = []

    for register_type, (start, count) in ranges.items():
        results = await transport.read_range(
            host=host,
            port=port,
            unit_id=unit_id,
            register_type=register_type,
            start=start,
            count=count,
            timeout_seconds=MODBUS_READ_TIMEOUT_SECONDS,
        )
        for result in results:
            if isinstance(result, ModbusReadFailure):
                _logger.warning(
                    "Dirección Modbus sin respuesta register_type=%s address=%s reason=%s",
                    result.register_type.value,
                    result.address,
                    result.reason,
                )
                continue
            assert isinstance(result, ModbusRegisterReading)
            if device is None:
                device = await device_repo.upsert_device(
                    name=f"Modbus {address}",
                    protocol="modbus",
                    address=address,
                    is_simulator=False,
                )
            candidate = await device_repo.upsert_candidate(
                device_id=device.id,
                object_type=result.register_type.value,
                object_instance=result.address,
                object_name=None,
                present_value=str(result.value),
                units=None,
            )
            candidates.append(candidate)

    return candidates
