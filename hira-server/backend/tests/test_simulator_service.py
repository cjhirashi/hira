"""`services/simulator_service.py` — coordinación de arranque/detención de
simuladores (`SRV-006-simuladores`, `plan.md §2`).

Dobles (`Protocol` fakes) de `BacnetSimulatorPort`/`ModbusSimulatorPort`/
`MqttPublisherPort`/`DeviceRepositoryPort` — sin BAC0/pymodbus/paho-mqtt/
Postgres reales (`plan.md §5`: "unit + dobles"). `SimulatorRegistryService`
**real**, no doble — es puro, sin I/O (`plan.md §5`).

Camino BACnet (T-007): arranca, persiste device+candidatos, registra; RF-006
(dispositivo real → 409 antes de `transport.start`; ya corriendo → 409 antes
de `transport.start`); RF-007 (reanudación: `existing.id` reutilizado, sin
segundo `upsert_device` con `is_simulator` distinto); limpieza defensiva
(`upsert_device` lanza → `transport.stop(token)` invocado antes de propagar).
Debe fallar antes de T-008 (`services/simulator_service.py` no existe
todavía).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from core.errors import ProblemDetailError
from core.modbus_address import format_modbus_address
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec
from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec
from core.ports.modbus_transport_port import ModbusRegisterType
from core.ports.mqtt_publisher_port import MqttInvalidPublishError
from services.simulator_registry_service import RunningSimulator, SimulatorRegistryService


# ── Dobles compartidos ───────────────────────────────────────────────────────


class _FakeBacnetSimulatorPort:
    """`BacnetSimulatorPort` in-memory — controla el token/error de `start()`
    y registra cada invocación para verificar orden (RF-006)."""

    def __init__(self, token: str = "bacnet-token-1", start_error: Exception | None = None) -> None:
        self.token = token
        self.start_error = start_error
        self.start_calls: list[dict] = []
        self.stop_calls: list[str] = []

    async def start(self, *, device_instance: int, objects: list[BacnetSimulatedObjectSpec]) -> str:
        self.start_calls.append({"device_instance": device_instance, "objects": objects})
        if self.start_error is not None:
            raise self.start_error
        return self.token

    async def stop(self, token: str) -> None:
        self.stop_calls.append(token)


class _AlwaysFailsBacnetSimulatorPort:
    """Falla el test si `start`/`stop` se invocan — usado para verificar que
    RF-006 rechaza antes de arrancar ningún proceso."""

    async def start(self, **kwargs):
        raise AssertionError("start no debía invocarse (RF-006)")

    async def stop(self, token: str) -> None:
        raise AssertionError("stop no debía invocarse")


@dataclass
class _FakeDeviceRepository:
    """`DeviceRepositoryPort` in-memory — registra invocaciones para
    aserciones; `fail_upsert_device` simula un fallo de persistencia tras un
    `transport.start()` exitoso (limpieza defensiva)."""

    devices_by_key: dict[tuple[str, str], DeviceRecord] = field(default_factory=dict)
    candidates_by_device: dict[str, list[DeviceCandidateRecord]] = field(default_factory=dict)
    upsert_device_calls: list[dict] = field(default_factory=list)
    upsert_candidate_calls: list[dict] = field(default_factory=list)
    get_device_by_address_calls: list[tuple[str, str]] = field(default_factory=list)
    fail_upsert_device: bool = False

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        if self.fail_upsert_device:
            raise RuntimeError("fallo simulado de persistencia (limpieza defensiva)")
        self.upsert_device_calls.append(
            {"name": name, "protocol": protocol, "address": address, "is_simulator": is_simulator}
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

    async def get_device_by_address(self, protocol: str, address: str) -> DeviceRecord | None:
        self.get_device_by_address_calls.append((protocol, address))
        return self.devices_by_key.get((protocol, address))

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
                "present_value": present_value,
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

    async def list_candidates_for_device(self, device_id: str) -> list[DeviceCandidateRecord]:
        return list(self.candidates_by_device.get(device_id, []))


class _AlwaysFailsDeviceRepository:
    """Falla el test si se invoca — usado para verificar que RF-006/RF-015
    rechazan antes de tocar el repositorio."""

    async def upsert_device(self, **kwargs):
        raise AssertionError("upsert_device no debía invocarse")

    async def list_devices(self):
        raise AssertionError("list_devices no debía invocarse")

    async def get_device(self, device_id: str):
        raise AssertionError("get_device no debía invocarse")

    async def get_device_by_address(self, protocol: str, address: str):
        raise AssertionError("get_device_by_address no debía invocarse")

    async def upsert_candidate(self, **kwargs):
        raise AssertionError("upsert_candidate no debía invocarse")

    async def list_candidates_for_device(self, device_id: str):
        raise AssertionError("list_candidates_for_device no debía invocarse")


class _FakeModbusSimulatorPort:
    """`ModbusSimulatorPort` in-memory — mismo criterio que
    `_FakeBacnetSimulatorPort`."""

    def __init__(self, token: str = "modbus-token-1", start_error: Exception | None = None) -> None:
        self.token = token
        self.start_error = start_error
        self.start_calls: list[dict] = []
        self.stop_calls: list[str] = []

    async def start(
        self, *, host: str, port: int, unit_id: int, registers: list[ModbusSimulatedRegisterSpec]
    ) -> str:
        self.start_calls.append({"host": host, "port": port, "unit_id": unit_id, "registers": registers})
        if self.start_error is not None:
            raise self.start_error
        return self.token

    async def stop(self, token: str) -> None:
        self.stop_calls.append(token)


class _AlwaysFailsModbusSimulatorPort:
    async def start(self, **kwargs):
        raise AssertionError("start no debía invocarse (RF-006)")

    async def stop(self, token: str) -> None:
        raise AssertionError("stop no debía invocarse")


class _FakeMqttPublisherPort:
    """`MqttPublisherPort` in-memory — `start_error` puede ser
    `MqttInvalidPublishError` (RF-014) para simular el rechazo de la
    librería."""

    def __init__(self, token: str = "mqtt-token-1", start_error: Exception | None = None) -> None:
        self.token = token
        self.start_error = start_error
        self.start_calls: list[dict] = []
        self.stop_calls: list[str] = []

    async def start(self, *, topic: str, payload: str, interval_seconds: float) -> str:
        self.start_calls.append({"topic": topic, "payload": payload, "interval_seconds": interval_seconds})
        if self.start_error is not None:
            raise self.start_error
        return self.token

    async def stop(self, token: str) -> None:
        self.stop_calls.append(token)


class _AlwaysFailsMqttPublisherPort:
    async def start(self, **kwargs):
        raise AssertionError("start no debía invocarse")

    async def stop(self, token: str) -> None:
        raise AssertionError("stop no debía invocarse")


def _existing_device(protocol: str, address: str, *, is_simulator: bool, device_id: str | None = None) -> DeviceRecord:
    now = datetime.now(timezone.utc)
    return DeviceRecord(
        id=device_id or str(uuid4()),
        name=f"{protocol} {address}",
        protocol=protocol,
        address=address,
        is_simulator=is_simulator,
        last_seen_at=now,
        created_at=now,
        updated_at=now,
    )


# ── start_bacnet_simulator (T-007/T-008) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_start_bacnet_simulator_camino_feliz_arranca_persiste_y_registra():
    """RF-001 — arranca el transporte, persiste device+candidatos, registra
    en `SimulatorRegistryService`."""
    from services.simulator_service import start_bacnet_simulator

    transport = _FakeBacnetSimulatorPort()
    repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()
    objects = [
        BacnetSimulatedObjectSpec(object_type="analog-value", object_instance=1, present_value="42.0")
    ]

    entry = await start_bacnet_simulator(
        device_instance=999123, objects=objects, transport=transport, device_repo=repo, registry=registry
    )

    assert entry.protocol == "bacnet"
    assert entry.address == "999123"
    assert entry.token == transport.token
    assert len(transport.start_calls) == 1
    assert transport.start_calls[0]["device_instance"] == 999123
    assert len(repo.upsert_device_calls) == 1
    assert repo.upsert_device_calls[0]["is_simulator"] is True
    assert repo.upsert_device_calls[0]["address"] == "999123"
    assert len(repo.upsert_candidate_calls) == 1
    assert registry.is_running(entry.device_id) is True
    assert registry.get(entry.device_id) == entry


@pytest.mark.asyncio
async def test_start_bacnet_simulator_rechaza_409_si_direccion_es_dispositivo_real():
    """RF-006 — `get_device_by_address` retorna `is_simulator=False` → 409
    `simulator-address-conflict`, sin invocar `transport.start`."""
    from services.simulator_service import start_bacnet_simulator

    transport = _AlwaysFailsBacnetSimulatorPort()
    repo = _FakeDeviceRepository()
    repo.devices_by_key[("bacnet", "999123")] = _existing_device("bacnet", "999123", is_simulator=False)
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_bacnet_simulator(
            device_instance=999123, objects=[], transport=transport, device_repo=repo, registry=registry
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-address-conflict"


@pytest.mark.asyncio
async def test_start_bacnet_simulator_rechaza_409_si_ya_esta_corriendo():
    """RF-006 — la dirección ya tiene un simulador en ejecución (en el
    registro) → 409 `simulator-already-running`, sin invocar
    `transport.start`."""
    from services.simulator_service import start_bacnet_simulator

    transport = _AlwaysFailsBacnetSimulatorPort()
    repo = _FakeDeviceRepository()
    existing = _existing_device("bacnet", "999123", is_simulator=True)
    repo.devices_by_key[("bacnet", "999123")] = existing
    registry = SimulatorRegistryService()
    registry.register(
        RunningSimulator(
            device_id=existing.id,
            protocol="bacnet",
            address="999123",
            token="already-running-token",
            started_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_bacnet_simulator(
            device_instance=999123, objects=[], transport=transport, device_repo=repo, registry=registry
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-already-running"


@pytest.mark.asyncio
async def test_start_bacnet_simulator_reanuda_mismo_device_id_sin_duplicar():
    """RF-007 — la dirección ya es un simulador registrado pero no
    corriendo (tras un reinicio): reanuda, reutilizando el mismo
    `device_id`, sin crear un dispositivo duplicado."""
    from services.simulator_service import start_bacnet_simulator

    transport = _FakeBacnetSimulatorPort()
    repo = _FakeDeviceRepository()
    existing = _existing_device("bacnet", "999123", is_simulator=True)
    repo.devices_by_key[("bacnet", "999123")] = existing
    registry = SimulatorRegistryService()  # nace vacío — nadie lo tiene corriendo

    entry = await start_bacnet_simulator(
        device_instance=999123, objects=[], transport=transport, device_repo=repo, registry=registry
    )

    assert entry.device_id == existing.id
    assert len(repo.devices_by_key) == 1
    assert len(transport.start_calls) == 1


@pytest.mark.asyncio
async def test_start_bacnet_simulator_limpieza_defensiva_detiene_transporte_si_persistencia_falla():
    """Limpieza defensiva — `upsert_device` lanza tras `transport.start()`
    exitoso: `transport.stop(token)` se invoca antes de propagar la
    excepción original."""
    from services.simulator_service import start_bacnet_simulator

    transport = _FakeBacnetSimulatorPort(token="orphan-token")
    repo = _FakeDeviceRepository(fail_upsert_device=True)
    registry = SimulatorRegistryService()

    with pytest.raises(RuntimeError):
        await start_bacnet_simulator(
            device_instance=999123, objects=[], transport=transport, device_repo=repo, registry=registry
        )

    assert transport.stop_calls == ["orphan-token"]
    assert registry.list_running() == []


@pytest.mark.asyncio
async def test_start_bacnet_simulator_rechaza_device_instance_fuera_de_rango():
    """RF-001/RF-007 — `format_simulator_device_address` propaga el
    `ValueError` de rango, sin invocar `transport`/`device_repo`."""
    from services.simulator_service import start_bacnet_simulator

    transport = _AlwaysFailsBacnetSimulatorPort()
    repo = _AlwaysFailsDeviceRepository()
    registry = SimulatorRegistryService()

    with pytest.raises(ValueError):
        await start_bacnet_simulator(
            device_instance=-1, objects=[], transport=transport, device_repo=repo, registry=registry
        )


# ── start_modbus_simulator (T-009/T-010) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_start_modbus_simulator_camino_feliz_arranca_persiste_y_registra():
    """RF-002 — arranca el transporte, persiste device+candidatos, registra."""
    from services.simulator_service import start_modbus_simulator

    transport = _FakeModbusSimulatorPort()
    repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()
    registers = [
        ModbusSimulatedRegisterSpec(register_type=ModbusRegisterType.HOLDING_REGISTER, address=0, value=100)
    ]

    entry = await start_modbus_simulator(
        host="192.168.1.50", port=502, unit_id=1, registers=registers,
        transport=transport, device_repo=repo, registry=registry,
    )

    expected_address = format_modbus_address("192.168.1.50", 502, 1)
    assert entry.protocol == "modbus"
    assert entry.address == expected_address
    assert len(transport.start_calls) == 1
    assert len(repo.upsert_device_calls) == 1
    assert repo.upsert_device_calls[0]["is_simulator"] is True
    assert len(repo.upsert_candidate_calls) == 1
    assert repo.upsert_candidate_calls[0]["object_type"] == "holding_register"
    assert registry.is_running(entry.device_id) is True


@pytest.mark.asyncio
async def test_start_modbus_simulator_rechaza_409_si_direccion_es_dispositivo_real():
    """RF-006 — dispositivo real en la misma dirección → 409, sin invocar
    `transport.start`."""
    from services.simulator_service import start_modbus_simulator

    transport = _AlwaysFailsModbusSimulatorPort()
    repo = _FakeDeviceRepository()
    address = format_modbus_address("192.168.1.50", 502, 1)
    repo.devices_by_key[("modbus", address)] = _existing_device("modbus", address, is_simulator=False)
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_modbus_simulator(
            host="192.168.1.50", port=502, unit_id=1, registers=[],
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-address-conflict"


@pytest.mark.asyncio
async def test_start_modbus_simulator_rechaza_409_si_ya_esta_corriendo():
    """RF-006 — ya hay un simulador Modbus corriendo en esa dirección → 409,
    sin invocar `transport.start`."""
    from services.simulator_service import start_modbus_simulator

    transport = _AlwaysFailsModbusSimulatorPort()
    repo = _FakeDeviceRepository()
    address = format_modbus_address("192.168.1.50", 502, 1)
    existing = _existing_device("modbus", address, is_simulator=True)
    repo.devices_by_key[("modbus", address)] = existing
    registry = SimulatorRegistryService()
    registry.register(
        RunningSimulator(
            device_id=existing.id, protocol="modbus", address=address,
            token="already-running-token", started_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_modbus_simulator(
            host="192.168.1.50", port=502, unit_id=1, registers=[],
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-already-running"


@pytest.mark.asyncio
async def test_start_modbus_simulator_reanuda_mismo_device_id_sin_duplicar():
    """RF-007 — simulador Modbus registrado pero no corriendo: reanuda,
    reutilizando el mismo `device_id`."""
    from services.simulator_service import start_modbus_simulator

    transport = _FakeModbusSimulatorPort()
    repo = _FakeDeviceRepository()
    address = format_modbus_address("192.168.1.50", 502, 1)
    existing = _existing_device("modbus", address, is_simulator=True)
    repo.devices_by_key[("modbus", address)] = existing
    registry = SimulatorRegistryService()

    entry = await start_modbus_simulator(
        host="192.168.1.50", port=502, unit_id=1, registers=[],
        transport=transport, device_repo=repo, registry=registry,
    )

    assert entry.device_id == existing.id
    assert len(repo.devices_by_key) == 1


@pytest.mark.asyncio
async def test_start_modbus_simulator_limpieza_defensiva_detiene_transporte_si_persistencia_falla():
    """Limpieza defensiva — `upsert_device` lanza tras `transport.start()`
    exitoso: `transport.stop(token)` invocado antes de propagar."""
    from services.simulator_service import start_modbus_simulator

    transport = _FakeModbusSimulatorPort(token="orphan-modbus-token")
    repo = _FakeDeviceRepository(fail_upsert_device=True)
    registry = SimulatorRegistryService()

    with pytest.raises(RuntimeError):
        await start_modbus_simulator(
            host="192.168.1.50", port=502, unit_id=1, registers=[],
            transport=transport, device_repo=repo, registry=registry,
        )

    assert transport.stop_calls == ["orphan-modbus-token"]
    assert registry.list_running() == []


# ── start_mqtt_simulator (T-011/T-012) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_start_mqtt_simulator_camino_feliz_arranca_persiste_y_registra():
    """RF-003 — arranca el publicador, persiste device (sin candidatos —
    MQTT no tiene "puntos" en esta feature), registra."""
    from services.simulator_service import start_mqtt_simulator

    transport = _FakeMqttPublisherPort()
    repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()

    entry = await start_mqtt_simulator(
        topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=1.0,
        transport=transport, device_repo=repo, registry=registry,
    )

    assert entry.protocol == "mqtt"
    assert entry.address == "edificio/piso1/ahu1/temp"
    assert len(transport.start_calls) == 1
    assert len(repo.upsert_device_calls) == 1
    assert repo.upsert_device_calls[0]["is_simulator"] is True
    assert repo.upsert_candidate_calls == []
    assert registry.is_running(entry.device_id) is True


@pytest.mark.asyncio
async def test_start_mqtt_simulator_rechaza_409_si_direccion_es_dispositivo_real():
    """RF-006 — dispositivo real en el mismo topic → 409, sin invocar
    `transport.start`."""
    from services.simulator_service import start_mqtt_simulator

    transport = _AlwaysFailsMqttPublisherPort()
    repo = _FakeDeviceRepository()
    repo.devices_by_key[("mqtt", "edificio/piso1/ahu1/temp")] = _existing_device(
        "mqtt", "edificio/piso1/ahu1/temp", is_simulator=False
    )
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_mqtt_simulator(
            topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=1.0,
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-address-conflict"


@pytest.mark.asyncio
async def test_start_mqtt_simulator_rechaza_409_si_ya_esta_corriendo():
    """RF-006 — ya hay un publicador corriendo en ese topic → 409, sin
    invocar `transport.start`."""
    from services.simulator_service import start_mqtt_simulator

    transport = _AlwaysFailsMqttPublisherPort()
    repo = _FakeDeviceRepository()
    existing = _existing_device("mqtt", "edificio/piso1/ahu1/temp", is_simulator=True)
    repo.devices_by_key[("mqtt", "edificio/piso1/ahu1/temp")] = existing
    registry = SimulatorRegistryService()
    registry.register(
        RunningSimulator(
            device_id=existing.id, protocol="mqtt", address="edificio/piso1/ahu1/temp",
            token="already-running-token", started_at=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_mqtt_simulator(
            topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=1.0,
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 409
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-already-running"


@pytest.mark.asyncio
async def test_start_mqtt_simulator_reanuda_mismo_device_id_sin_duplicar():
    """RF-007 — publicador registrado pero no corriendo: reanuda, mismo
    `device_id`."""
    from services.simulator_service import start_mqtt_simulator

    transport = _FakeMqttPublisherPort()
    repo = _FakeDeviceRepository()
    existing = _existing_device("mqtt", "edificio/piso1/ahu1/temp", is_simulator=True)
    repo.devices_by_key[("mqtt", "edificio/piso1/ahu1/temp")] = existing
    registry = SimulatorRegistryService()

    entry = await start_mqtt_simulator(
        topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=1.0,
        transport=transport, device_repo=repo, registry=registry,
    )

    assert entry.device_id == existing.id
    assert len(repo.devices_by_key) == 1


@pytest.mark.asyncio
async def test_start_mqtt_simulator_rf014_publish_invalido_400_antes_de_persistir():
    """RF-014 — el doble de `MqttPublisherPort` lanza
    `MqttInvalidPublishError` en `start()`: `start_mqtt_simulator` la
    traduce a `ProblemDetailError(400, .../mqtt-invalid-publish)`, **sin**
    invocar `upsert_device` (el chequeo de conflicto RF-006, una lectura,
    sí ocurre antes — solo la escritura queda excluida)."""
    from services.simulator_service import start_mqtt_simulator

    transport = _FakeMqttPublisherPort(start_error=MqttInvalidPublishError("Invalid topic."))
    repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_mqtt_simulator(
            topic="edificio/#", payload="21.5", interval_seconds=1.0,
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 400
    assert exc_info.value.type_ == "https://hira.dev/errors/mqtt-invalid-publish"
    assert repo.upsert_device_calls == []


@pytest.mark.asyncio
async def test_start_mqtt_simulator_rf015_interval_no_positivo_400_sin_tocar_nada():
    """RF-015 — `interval_seconds <= 0` → 400, **antes** de tocar el
    registro o arrancar nada (dobles que fallan el test si se invocan)."""
    from services.simulator_service import start_mqtt_simulator

    transport = _AlwaysFailsMqttPublisherPort()
    repo = _AlwaysFailsDeviceRepository()
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_mqtt_simulator(
            topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=0,
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 400
    assert exc_info.value.type_ == "https://hira.dev/errors/mqtt-invalid-interval"
    assert registry.list_running() == []


@pytest.mark.asyncio
async def test_start_mqtt_simulator_rf015_interval_negativo_400():
    from services.simulator_service import start_mqtt_simulator

    transport = _AlwaysFailsMqttPublisherPort()
    repo = _AlwaysFailsDeviceRepository()
    registry = SimulatorRegistryService()

    with pytest.raises(ProblemDetailError) as exc_info:
        await start_mqtt_simulator(
            topic="edificio/piso1/ahu1/temp", payload="21.5", interval_seconds=-1,
            transport=transport, device_repo=repo, registry=registry,
        )

    assert exc_info.value.status == 400
    assert exc_info.value.type_ == "https://hira.dev/errors/mqtt-invalid-interval"


# ── stop_simulator (T-013/T-014) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_stop_simulator_despacha_al_puerto_correcto_y_desregistra():
    """RF-009 — `device_id` en el registro (`protocol='modbus'`): despacha
    al `modbus_transport` correcto (no a `bacnet_transport`/`mqtt_transport`,
    dobles que fallan si se invocan) y desregistra, sin tocar
    `devices`/candidatos (inspección: `stop_simulator` no importa ningún
    método de borrado — verificado en el propio módulo)."""
    from services.simulator_service import stop_simulator

    registry = SimulatorRegistryService()
    entry = RunningSimulator(
        device_id="dev-1", protocol="modbus", address="192.168.1.50:502:1",
        token="modbus-token-1", started_at=datetime.now(timezone.utc),
    )
    registry.register(entry)

    bacnet_transport = _AlwaysFailsBacnetSimulatorPort()
    modbus_transport = _FakeModbusSimulatorPort(token="modbus-token-1")
    mqtt_transport = _AlwaysFailsMqttPublisherPort()

    await stop_simulator(
        device_id="dev-1", registry=registry,
        bacnet_transport=bacnet_transport, modbus_transport=modbus_transport, mqtt_transport=mqtt_transport,
    )

    assert modbus_transport.stop_calls == ["modbus-token-1"]
    assert registry.get("dev-1") is None
    assert registry.is_running("dev-1") is False


@pytest.mark.asyncio
async def test_stop_simulator_despacha_bacnet_y_mqtt_tambien():
    """RF-009 — mismos casos para `bacnet` y `mqtt` (los 3 protocolos)."""
    from services.simulator_service import stop_simulator

    registry = SimulatorRegistryService()
    registry.register(
        RunningSimulator(
            device_id="dev-bacnet", protocol="bacnet", address="999123",
            token="bacnet-token", started_at=datetime.now(timezone.utc),
        )
    )
    registry.register(
        RunningSimulator(
            device_id="dev-mqtt", protocol="mqtt", address="edificio/piso1/ahu1/temp",
            token="mqtt-token", started_at=datetime.now(timezone.utc),
        )
    )
    bacnet_transport = _FakeBacnetSimulatorPort(token="bacnet-token")
    modbus_transport = _AlwaysFailsModbusSimulatorPort()
    mqtt_transport = _FakeMqttPublisherPort(token="mqtt-token")

    await stop_simulator(
        device_id="dev-bacnet", registry=registry,
        bacnet_transport=bacnet_transport, modbus_transport=modbus_transport, mqtt_transport=mqtt_transport,
    )
    await stop_simulator(
        device_id="dev-mqtt", registry=registry,
        bacnet_transport=bacnet_transport, modbus_transport=modbus_transport, mqtt_transport=mqtt_transport,
    )

    assert bacnet_transport.stop_calls == ["bacnet-token"]
    assert mqtt_transport.stop_calls == ["mqtt-token"]
    assert registry.list_running() == []


@pytest.mark.asyncio
async def test_stop_simulator_device_id_ausente_404():
    """RF-012 — `device_id` sin simulador actualmente en ejecución (no
    existe en el registro) → 404 `simulator-not-running`, sin invocar
    ningún transporte."""
    from services.simulator_service import stop_simulator

    registry = SimulatorRegistryService()
    bacnet_transport = _AlwaysFailsBacnetSimulatorPort()
    modbus_transport = _AlwaysFailsModbusSimulatorPort()
    mqtt_transport = _AlwaysFailsMqttPublisherPort()

    with pytest.raises(ProblemDetailError) as exc_info:
        await stop_simulator(
            device_id="no-existe", registry=registry,
            bacnet_transport=bacnet_transport, modbus_transport=modbus_transport, mqtt_transport=mqtt_transport,
        )

    assert exc_info.value.status == 404
    assert exc_info.value.type_ == "https://hira.dev/errors/simulator-not-running"


def test_stop_simulator_nunca_importa_un_metodo_de_borrado_de_devices():
    """RF-009, RF-011 — inspección de imports del módulo: ningún nombre
    relacionado con "delete"/"remove" de `devices`/candidatos — `RF-009`
    (no borra el dispositivo) y `RF-011` (sin mecanismo para quitar
    `is_simulator`) se cumplen por omisión de diseño."""
    import services.simulator_service as module

    source_names = dir(module)
    assert not any("delete" in name.lower() for name in source_names)
    assert not any("remove" in name.lower() for name in source_names)


def test_start_simulators_solo_invocan_upsert_device_con_is_simulator_true():
    """RF-011 — inspección del código fuente: los 3 `start_*_simulator`
    llaman `upsert_device(..., is_simulator=True)` — nunca invocan
    `upsert_device` con `is_simulator=False` (la única aparición literal de
    ese texto en el módulo es prosa de docstring, no una llamada real)."""
    import inspect
    import re

    import services.simulator_service as module

    source = inspect.getsource(module)
    assert re.search(r"upsert_device\([^)]*is_simulator=False", source) is None
    assert source.count("is_simulator=True,") == 3
