"""`services/device_scan_service.py::scan_bacnet` — coordinación, sin I/O real
(`SRV-003-bacnet-adapter`, `plan.md §2`, RF-001, RF-002, RF-006, RF-007,
RF-008, RNF-001).

Dobles (`Protocol` fakes) de `BacnetTransportPort`/`DeviceRepositoryPort` —
sin BAC0/Postgres reales (`plan.md §5`: "unit + dobles"). Debe fallar antes de
T-006 (`services/device_scan_service.py` no existe todavía).
"""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from core.bacnet_address import format_device_address
from core.ports.bacnet_transport_port import (
    BacnetDeviceAnnouncement,
    BacnetObjectReading,
    BacnetReadTimeoutError,
)
from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord


class _FakeBacnetTransport:
    """`BacnetTransportPort` in-memory — controla anuncios/lecturas por test."""

    def __init__(
        self,
        announcements: list[BacnetDeviceAnnouncement],
        readings_by_address: dict[str, list[BacnetObjectReading]] | None = None,
        timeout_addresses: set[str] | None = None,
        read_delay_seconds: dict[str, float] | None = None,
    ) -> None:
        self._announcements = announcements
        self._readings_by_address = readings_by_address or {}
        self._timeout_addresses = timeout_addresses or set()
        self._read_delay_seconds = read_delay_seconds or {}
        self.who_is_calls: list[float] = []
        self.read_calls_started_at: dict[str, float] = {}
        self.read_calls_finished_at: dict[str, float] = {}

    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        self.who_is_calls.append(timeout_seconds)
        return self._announcements

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        self.read_calls_started_at[network_address] = time.monotonic()
        delay = self._read_delay_seconds.get(network_address, 0.0)
        if delay:
            await asyncio.sleep(delay)
        if network_address in self._timeout_addresses:
            raise BacnetReadTimeoutError(
                f"{network_address} no respondió dentro de {timeout_seconds}s"
            )
        self.read_calls_finished_at[network_address] = time.monotonic()
        return self._readings_by_address.get(network_address, [])


@dataclass
class _FakeDeviceRepository:
    """`DeviceRepositoryPort` in-memory — registra invocaciones para aserciones."""

    devices_by_key: dict[tuple[str, str], DeviceRecord] = field(default_factory=dict)
    candidates_by_device: dict[str, list[DeviceCandidateRecord]] = field(
        default_factory=dict
    )
    upsert_device_calls: list[dict] = field(default_factory=list)
    upsert_candidate_calls: list[dict] = field(default_factory=list)

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        self.upsert_device_calls.append(
            {"name": name, "protocol": protocol, "address": address}
        )
        key = (protocol, address)
        now = datetime.now(timezone.utc)
        existing = self.devices_by_key.get(key)
        record = DeviceRecord(
            id=existing.id if existing else str(uuid4()),
            name=name,
            protocol=protocol,
            address=address,
            is_simulator=is_simulator,
            last_seen_at=now,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self.devices_by_key[key] = record
        return record

    async def list_devices(self) -> list[DeviceRecord]:
        return list(self.devices_by_key.values())

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        for record in self.devices_by_key.values():
            if record.id == device_id:
                return record
        return None

    async def upsert_candidate(
        self,
        *,
        device_id: str,
        object_type: str,
        object_instance: int,
        object_name: str | None,
        present_value: str | None,
        units: str | None,
    ) -> DeviceCandidateRecord:
        self.upsert_candidate_calls.append(
            {
                "device_id": device_id,
                "object_type": object_type,
                "object_instance": object_instance,
            }
        )
        now = datetime.now(timezone.utc)
        record = DeviceCandidateRecord(
            id=str(uuid4()),
            device_id=device_id,
            object_type=object_type,
            object_instance=object_instance,
            object_name=object_name,
            present_value=present_value,
            units=units,
            discovered_at=now,
            updated_at=now,
        )
        self.candidates_by_device.setdefault(device_id, []).append(record)
        return record

    async def list_candidates_for_device(
        self, device_id: str
    ) -> list[DeviceCandidateRecord]:
        return list(self.candidates_by_device.get(device_id, []))


@pytest.mark.asyncio
async def test_scan_bacnet_camino_feliz_dos_dispositivos_persiste_device_y_candidatos():
    """RF-001, RF-002 — 2 I-Am → 2 `upsert_device` + N `upsert_candidate`."""
    from services.device_scan_service import scan_bacnet

    announcements = [
        BacnetDeviceAnnouncement(instance_number=101, network_address="10.0.0.1:47808"),
        BacnetDeviceAnnouncement(instance_number=202, network_address="10.0.0.2:47808"),
    ]
    readings_by_address = {
        "10.0.0.1:47808": [
            BacnetObjectReading(
                object_type="analogInput",
                object_instance=1,
                object_name="Temp",
                present_value="21.5",
                units="degreesCelsius",
            )
        ],
        "10.0.0.2:47808": [
            BacnetObjectReading(
                object_type="binaryOutput",
                object_instance=1,
                object_name="Fan",
                present_value="active",
                units=None,
            )
        ],
    }
    transport = _FakeBacnetTransport(announcements, readings_by_address)
    repo = _FakeDeviceRepository()

    result = await scan_bacnet(transport, repo)

    assert len(result) == 2
    assert len(repo.upsert_device_calls) == 2
    assert len(repo.upsert_candidate_calls) == 2
    expected_addresses = {
        format_device_address(101, "10.0.0.1:47808"),
        format_device_address(202, "10.0.0.2:47808"),
    }
    persisted_addresses = {call["address"] for call in repo.upsert_device_calls}
    assert persisted_addresses == expected_addresses
    for call in repo.upsert_device_calls:
        assert call["protocol"] == "bacnet"


@pytest.mark.asyncio
async def test_scan_bacnet_sin_ningun_i_am_retorna_lista_vacia_sin_tocar_repo():
    """RF-008 — sin I-Am, `[]` sin invocar el repositorio (200, no error)."""
    from services.device_scan_service import scan_bacnet

    transport = _FakeBacnetTransport(announcements=[])
    repo = _FakeDeviceRepository()

    result = await scan_bacnet(transport, repo)

    assert result == []
    assert repo.upsert_device_calls == []
    assert repo.upsert_candidate_calls == []


@pytest.mark.asyncio
async def test_scan_bacnet_timeout_de_un_dispositivo_no_aborta_el_resto():
    """RF-006 — 1 de 2 dispositivos lanza `BacnetReadTimeoutError`; el otro se
    persiste igual, sin abortar el escaneo completo."""
    from services.device_scan_service import scan_bacnet

    announcements = [
        BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808"),
        BacnetDeviceAnnouncement(instance_number=2, network_address="10.0.0.2:47808"),
    ]
    readings_by_address = {
        "10.0.0.2:47808": [
            BacnetObjectReading(
                object_type="analogInput",
                object_instance=1,
                object_name="Temp",
                present_value="20.0",
                units="degreesCelsius",
            )
        ]
    }
    transport = _FakeBacnetTransport(
        announcements,
        readings_by_address,
        timeout_addresses={"10.0.0.1:47808"},
    )
    repo = _FakeDeviceRepository()

    result = await scan_bacnet(transport, repo)

    # Ambos dispositivos quedan persistidos (I-Am recibido, RF-002); solo el
    # que no respondió a la lectura se queda sin candidatos nuevos (RF-006).
    assert len(result) == 2
    assert len(repo.upsert_device_calls) == 2
    assert len(repo.upsert_candidate_calls) == 1
    assert repo.upsert_candidate_calls[0]["object_type"] == "analogInput"


@pytest.mark.asyncio
async def test_scan_bacnet_lectura_de_objetos_con_timeout_no_cuelga_la_respuesta_total():
    """RF-006, RNF-001 — un doble que tarda más que `READ_TIMEOUT_SECONDS` (2s)
    no debe colgar la respuesta total del escaneo."""
    from services.device_scan_service import scan_bacnet

    announcements = [
        BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808"),
    ]
    transport = _FakeBacnetTransport(
        announcements,
        timeout_addresses={"10.0.0.1:47808"},
        read_delay_seconds={"10.0.0.1:47808": 3.0},
    )
    repo = _FakeDeviceRepository()

    started_at = time.monotonic()
    result = await asyncio.wait_for(scan_bacnet(transport, repo), timeout=4.0)
    elapsed = time.monotonic() - started_at

    assert len(result) == 1
    assert elapsed < 3.5


@pytest.mark.asyncio
async def test_scan_bacnet_lee_objetos_en_paralelo_no_secuencial():
    """RNF-001 — las N llamadas a `read_device_objects` se solapan en el
    tiempo, no son estrictamente secuenciales."""
    from services.device_scan_service import scan_bacnet

    announcements = [
        BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808"),
        BacnetDeviceAnnouncement(instance_number=2, network_address="10.0.0.2:47808"),
    ]
    transport = _FakeBacnetTransport(
        announcements,
        read_delay_seconds={
            "10.0.0.1:47808": 0.2,
            "10.0.0.2:47808": 0.2,
        },
    )
    repo = _FakeDeviceRepository()

    started_at = time.monotonic()
    await scan_bacnet(transport, repo)
    elapsed = time.monotonic() - started_at

    # Secuencial habría tardado >= 0.4s; en paralelo, ~0.2s.
    assert elapsed < 0.35


@pytest.mark.asyncio
async def test_scan_bacnet_segundo_escaneo_actualiza_no_duplica():
    """RF-002 — un segundo escaneo del mismo dispositivo actualiza (mismo
    `(protocol, address)`), no duplica."""
    from services.device_scan_service import scan_bacnet

    announcements = [
        BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808"),
    ]
    transport = _FakeBacnetTransport(announcements)
    repo = _FakeDeviceRepository()

    first_result = await scan_bacnet(transport, repo)
    second_result = await scan_bacnet(transport, repo)

    assert len(repo.devices_by_key) == 1
    assert first_result[0].id == second_result[0].id


def test_scan_bacnet_nunca_importa_un_puerto_de_puntos_operables():
    """RF-007 — el sistema nunca promueve un candidato a una tabla de puntos
    operables (`SRV-ADR-012`): verificado por inspección de imports del
    módulo, no existe ningún `PointsRepositoryPort` referenciado."""
    import services.device_scan_service as module

    source_names = dir(module)
    assert not any("points" in name.lower() for name in source_names)
