"""`services/device_scan_service.py::scan_bacnet`/`scan_modbus`/`scan_mqtt` —
coordinación, sin I/O real (`SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter`/
`SRV-005-mqtt-scanning`, `plan.md §2`).

Dobles (`Protocol` fakes) de `BacnetTransportPort`/`ModbusTransportPort`/
`MqttScanTransportPort`/`DeviceRepositoryPort` — sin BAC0/pymodbus/paho-mqtt/
Postgres reales (`plan.md §5`: "unit + dobles"). Los casos de `scan_mqtt`
(RF-001, RF-002, RF-004, RF-005, RF-006, RNF-001) deben fallar antes de T-005
(`services/device_scan_service.py::scan_mqtt` no existe todavía).
"""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from core.bacnet_address import format_device_address
from core.errors import ProblemDetailError
from core.modbus_address import format_modbus_address
from core.ports.bacnet_transport_port import (
    BacnetDeviceAnnouncement,
    BacnetObjectReading,
    BacnetReadTimeoutError,
)
from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord
from core.ports.modbus_transport_port import (
    ModbusReadFailure,
    ModbusRegisterReading,
    ModbusRegisterType,
)
from core.ports.mqtt_scan_transport_port import (
    MqttInvalidTopicPatternError,
    MqttTopicMessage,
)


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


class _FakeModbusTransport:
    """`ModbusTransportPort` in-memory — controla los resultados de
    `read_range` por `(register_type, start, count)`, registra cada llamada
    para verificar que RF-004 rechaza **antes** de invocar `transport`."""

    def __init__(
        self,
        results_by_range: dict[
            tuple[ModbusRegisterType, int, int],
            list[ModbusRegisterReading | ModbusReadFailure],
        ]
        | None = None,
    ) -> None:
        self._results_by_range = results_by_range or {}
        self.read_range_calls: list[dict] = []

    async def read_range(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        register_type: ModbusRegisterType,
        start: int,
        count: int,
        timeout_seconds: float,
    ) -> list[ModbusRegisterReading | ModbusReadFailure]:
        self.read_range_calls.append(
            {
                "host": host,
                "port": port,
                "unit_id": unit_id,
                "register_type": register_type,
                "start": start,
                "count": count,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self._results_by_range.get((register_type, start, count), [])


class _AlwaysFailsModbusTransport:
    """`ModbusTransportPort` que falla el test si `read_range` se invoca —
    usado para verificar que RF-004 rechaza antes de cualquier lectura."""

    async def read_range(self, **kwargs) -> list:
        raise AssertionError(
            "read_range no debía invocarse: el rango excede el límite (RF-004)"
        )


class _FakeMqttTransport:
    """`MqttScanTransportPort` in-memory — controla los mensajes retornados
    por `listen()` (o lanza `MqttInvalidTopicPatternError`) para cada test."""

    def __init__(
        self,
        messages: list[MqttTopicMessage] | None = None,
        invalid_pattern_error: Exception | None = None,
    ) -> None:
        self._messages = messages or []
        self._invalid_pattern_error = invalid_pattern_error
        self.listen_calls: list[dict] = []

    async def listen(
        self, topic_pattern: str, window_seconds: float
    ) -> list[MqttTopicMessage]:
        self.listen_calls.append(
            {"topic_pattern": topic_pattern, "window_seconds": window_seconds}
        )
        if self._invalid_pattern_error is not None:
            raise self._invalid_pattern_error
        return self._messages


class _AlwaysFailsModbusDeviceRepository:
    """`DeviceRepositoryPort` que falla el test si se invoca — usado para
    verificar que RF-004/RF-007 no tocan el repositorio."""

    async def upsert_device(self, **kwargs):
        raise AssertionError("upsert_device no debía invocarse")

    async def list_devices(self):
        raise AssertionError("list_devices no debía invocarse")

    async def get_device(self, device_id: str):
        raise AssertionError("get_device no debía invocarse")

    async def upsert_candidate(self, **kwargs):
        raise AssertionError("upsert_candidate no debía invocarse")

    async def list_candidates_for_device(self, device_id: str):
        raise AssertionError("list_candidates_for_device no debía invocarse")


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
    módulo, no existe ningún `PointsRepositoryPort` referenciado. Cubre tanto
    `scan_bacnet` como `scan_modbus`, mismo módulo (`SRV-006`, RF-006)."""
    import services.device_scan_service as module

    source_names = dir(module)
    assert not any("points" in name.lower() for name in source_names)


# ── scan_modbus (SRV-004-modbus-adapter) ────────────────────────────────────


@pytest.mark.asyncio
async def test_scan_modbus_camino_feliz_dos_tipos_persiste_device_y_candidatos():
    """RF-001, RF-002 — 2 tipos de registro con valores → 1 `upsert_device`
    (la primera vez que algo responde) + N `upsert_candidate`, retorna N
    candidatos."""
    from services.device_scan_service import scan_modbus

    results_by_range = {
        (ModbusRegisterType.HOLDING_REGISTER, 0, 2): [
            ModbusRegisterReading(
                register_type=ModbusRegisterType.HOLDING_REGISTER, address=0, value=100
            ),
            ModbusRegisterReading(
                register_type=ModbusRegisterType.HOLDING_REGISTER, address=1, value=200
            ),
        ],
        (ModbusRegisterType.COIL, 0, 1): [
            ModbusRegisterReading(
                register_type=ModbusRegisterType.COIL, address=0, value=True
            ),
        ],
    }
    transport = _FakeModbusTransport(results_by_range)
    repo = _FakeDeviceRepository()

    result = await scan_modbus(
        host="192.168.1.50",
        port=502,
        unit_id=1,
        ranges={
            ModbusRegisterType.HOLDING_REGISTER: (0, 2),
            ModbusRegisterType.COIL: (0, 1),
        },
        transport=transport,
        device_repo=repo,
    )

    assert len(result) == 3
    assert len(repo.upsert_device_calls) == 1
    assert repo.upsert_device_calls[0]["protocol"] == "modbus"
    assert repo.upsert_device_calls[0]["address"] == format_modbus_address(
        "192.168.1.50", 502, 1
    )
    assert len(repo.upsert_candidate_calls) == 3
    object_types = {call["object_type"] for call in repo.upsert_candidate_calls}
    assert object_types == {"holding_register", "coil"}


@pytest.mark.asyncio
async def test_scan_modbus_rango_mayor_a_125_rechaza_antes_de_leer_nada():
    """RF-004 — un rango > 125 direcciones se rechaza con `ProblemDetailError`
    (400, slug `modbus-range-too-large`) **antes** de invocar `transport`/
    `device_repo` (dobles que fallan el test si se llaman)."""
    from services.device_scan_service import scan_modbus

    transport = _AlwaysFailsModbusTransport()
    repo = _AlwaysFailsModbusDeviceRepository()

    with pytest.raises(ProblemDetailError) as exc_info:
        await scan_modbus(
            host="192.168.1.50",
            port=502,
            unit_id=1,
            ranges={ModbusRegisterType.HOLDING_REGISTER: (0, 126)},
            transport=transport,
            device_repo=repo,
        )

    assert exc_info.value.status == 400
    assert exc_info.value.type_ == "https://hira.dev/errors/modbus-range-too-large"


@pytest.mark.asyncio
async def test_scan_modbus_rango_de_125_exacto_no_rechaza():
    """RF-004 — el límite es inclusivo: 125 direcciones exactas no rechaza."""
    from services.device_scan_service import scan_modbus

    transport = _FakeModbusTransport(
        {(ModbusRegisterType.HOLDING_REGISTER, 0, 125): []}
    )
    repo = _FakeDeviceRepository()

    result = await scan_modbus(
        host="192.168.1.50",
        port=502,
        unit_id=1,
        ranges={ModbusRegisterType.HOLDING_REGISTER: (0, 125)},
        transport=transport,
        device_repo=repo,
    )

    assert result == []
    assert len(transport.read_range_calls) == 1


@pytest.mark.asyncio
async def test_scan_modbus_una_direccion_que_falla_no_aborta_las_demas():
    """RF-005 — una mezcla de `ModbusRegisterReading`/`ModbusReadFailure` en
    la misma lista: las direcciones fallidas se omiten (logueadas), las
    exitosas se persisten igual, sin abortar el resto del rango."""
    from services.device_scan_service import scan_modbus

    results_by_range = {
        (ModbusRegisterType.HOLDING_REGISTER, 0, 3): [
            ModbusRegisterReading(
                register_type=ModbusRegisterType.HOLDING_REGISTER, address=0, value=10
            ),
            ModbusReadFailure(
                register_type=ModbusRegisterType.HOLDING_REGISTER,
                address=1,
                reason="timeout",
            ),
            ModbusRegisterReading(
                register_type=ModbusRegisterType.HOLDING_REGISTER, address=2, value=30
            ),
        ],
    }
    transport = _FakeModbusTransport(results_by_range)
    repo = _FakeDeviceRepository()

    result = await scan_modbus(
        host="192.168.1.50",
        port=502,
        unit_id=1,
        ranges={ModbusRegisterType.HOLDING_REGISTER: (0, 3)},
        transport=transport,
        device_repo=repo,
    )

    assert len(result) == 2
    assert len(repo.upsert_candidate_calls) == 2
    persisted_instances = {
        call["object_instance"] for call in repo.upsert_candidate_calls
    }
    assert persisted_instances == {0, 2}
    assert len(repo.upsert_device_calls) == 1


@pytest.mark.asyncio
async def test_scan_modbus_sin_ninguna_respuesta_exitosa_no_crea_device():
    """RF-007 — sin ninguna dirección exitosa (todas `ModbusReadFailure`),
    `[]` sin invocar `upsert_device`/`upsert_candidate` (200, no es error)."""
    from services.device_scan_service import scan_modbus

    results_by_range = {
        (ModbusRegisterType.HOLDING_REGISTER, 0, 2): [
            ModbusReadFailure(
                register_type=ModbusRegisterType.HOLDING_REGISTER,
                address=0,
                reason="timeout",
            ),
            ModbusReadFailure(
                register_type=ModbusRegisterType.HOLDING_REGISTER,
                address=1,
                reason="timeout",
            ),
        ],
    }
    transport = _FakeModbusTransport(results_by_range)
    repo = _FakeDeviceRepository()

    result = await scan_modbus(
        host="192.168.1.50",
        port=502,
        unit_id=1,
        ranges={ModbusRegisterType.HOLDING_REGISTER: (0, 2)},
        transport=transport,
        device_repo=repo,
    )

    assert result == []
    assert repo.upsert_device_calls == []
    assert repo.upsert_candidate_calls == []


@pytest.mark.asyncio
async def test_scan_modbus_segundo_escaneo_actualiza_no_duplica():
    """RF-002 — un segundo escaneo del mismo dispositivo actualiza (mismo
    `(protocol, address)`), no duplica."""
    from services.device_scan_service import scan_modbus

    results_by_range = {
        (ModbusRegisterType.HOLDING_REGISTER, 0, 1): [
            ModbusRegisterReading(
                register_type=ModbusRegisterType.HOLDING_REGISTER, address=0, value=1
            ),
        ],
    }
    transport = _FakeModbusTransport(results_by_range)
    repo = _FakeDeviceRepository()
    kwargs = dict(
        host="192.168.1.50",
        port=502,
        unit_id=1,
        ranges={ModbusRegisterType.HOLDING_REGISTER: (0, 1)},
        transport=transport,
        device_repo=repo,
    )

    await scan_modbus(**kwargs)
    await scan_modbus(**kwargs)

    assert len(repo.devices_by_key) == 1


# ── scan_mqtt (SRV-005-mqtt-scanning) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_scan_mqtt_camino_feliz_dos_topics_persiste_device_y_candidatos():
    """RF-001, RF-002 — 3 mensajes en 2 topics distintos → 1 `upsert_device`
    + 2 `upsert_candidate` (candidatos separados por topic, clave `crc32`)."""
    from core.mqtt_topic_key import topic_instance_key
    from services.device_scan_service import scan_mqtt

    messages = [
        MqttTopicMessage(topic="edificio/piso1/ahu1/temp", payload="21.5"),
        MqttTopicMessage(topic="edificio/piso1/ahu2/humidity", payload="55"),
        MqttTopicMessage(topic="edificio/piso1/ahu1/temp", payload="21.7"),
    ]
    transport = _FakeMqttTransport(messages)
    repo = _FakeDeviceRepository()

    result = await scan_mqtt(
        topic_pattern="edificio/piso1/#", transport=transport, device_repo=repo
    )

    assert len(result) == 2
    assert len(repo.upsert_device_calls) == 1
    assert repo.upsert_device_calls[0]["protocol"] == "mqtt"
    assert repo.upsert_device_calls[0]["address"] == "edificio/piso1/#"

    assert len(repo.upsert_candidate_calls) == 2
    instances = {call["object_instance"] for call in repo.upsert_candidate_calls}
    assert instances == {
        topic_instance_key("edificio/piso1/ahu1/temp"),
        topic_instance_key("edificio/piso1/ahu2/humidity"),
    }
    for call in repo.upsert_candidate_calls:
        assert call["object_type"] == "mqtt_topic"


@pytest.mark.asyncio
async def test_scan_mqtt_mismo_topic_dos_veces_actualiza_no_duplica_ultimo_mensaje_gana():
    """`spec.md §2` — el mismo topic recibe 2 mensajes en la ventana: el
    candidato final lleva el `present_value` del **último** mensaje, sin
    duplicar filas (misma clave `crc32`, un solo `upsert_candidate` visible
    en el resultado por topic)."""
    from services.device_scan_service import scan_mqtt

    messages = [
        MqttTopicMessage(topic="edificio/piso1/ahu1/temp", payload="21.5"),
        MqttTopicMessage(topic="edificio/piso1/ahu1/temp", payload="22.0"),
    ]
    transport = _FakeMqttTransport(messages)
    repo = _FakeDeviceRepository()

    result = await scan_mqtt(
        topic_pattern="edificio/piso1/#", transport=transport, device_repo=repo
    )

    assert len(result) == 1
    assert result[0].present_value == "22.0"
    # El repositorio recibe una sola invocación de upsert_candidate para este
    # topic (deduplicado en services/, RF-002) — no dos.
    assert len(repo.upsert_candidate_calls) == 1


@pytest.mark.asyncio
async def test_scan_mqtt_patron_invalido_propaga_como_problem_detail_400_antes_de_tocar_repo():
    """RF-004 — el doble de `MqttScanTransportPort` lanza
    `MqttInvalidTopicPatternError`; `scan_mqtt` la traduce a
    `ProblemDetailError(400, .../mqtt-invalid-topic-pattern)` **antes** de
    invocar `device_repo` (doble que falla el test si se llama)."""
    from services.device_scan_service import scan_mqtt

    transport = _FakeMqttTransport(
        invalid_pattern_error=MqttInvalidTopicPatternError("Invalid subscription filter.")
    )
    repo = _AlwaysFailsModbusDeviceRepository()

    with pytest.raises(ProblemDetailError) as exc_info:
        await scan_mqtt(
            topic_pattern="edificio/#/piso1", transport=transport, device_repo=repo
        )

    assert exc_info.value.status == 400
    assert (
        exc_info.value.type_ == "https://hira.dev/errors/mqtt-invalid-topic-pattern"
    )


@pytest.mark.asyncio
async def test_scan_mqtt_sin_ningun_mensaje_retorna_lista_vacia_sin_crear_device():
    """RF-006 — sin ningún mensaje durante la ventana, `[]` sin invocar
    `upsert_device` (doble que falla el test si se llama) — sin `device`
    "fantasma"."""
    from services.device_scan_service import scan_mqtt

    transport = _FakeMqttTransport(messages=[])
    repo = _AlwaysFailsModbusDeviceRepository()

    result = await scan_mqtt(
        topic_pattern="edificio/piso1/#", transport=transport, device_repo=repo
    )

    assert result == []


@pytest.mark.asyncio
async def test_scan_mqtt_usa_ventana_de_3_segundos():
    """RF-001, RNF-001 — `listen()` se invoca con la ventana fija de 3s
    (`MQTT_SCAN_WINDOW_SECONDS`)."""
    from services.device_scan_service import MQTT_SCAN_WINDOW_SECONDS, scan_mqtt

    transport = _FakeMqttTransport(messages=[])
    repo = _FakeDeviceRepository()

    await scan_mqtt(
        topic_pattern="edificio/piso1/#", transport=transport, device_repo=repo
    )

    assert MQTT_SCAN_WINDOW_SECONDS == 3
    assert transport.listen_calls == [
        {"topic_pattern": "edificio/piso1/#", "window_seconds": MQTT_SCAN_WINDOW_SECONDS}
    ]
