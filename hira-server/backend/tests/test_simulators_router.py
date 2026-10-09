"""`routers/simulators.py` — `POST /simulators/{bacnet,modbus,mqtt}`,
`GET /simulators`, `DELETE /simulators/{device_id}` (adaptador de entrada
HTTP, `SRV-006-simuladores`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1simulators~1bacnet`
(+ `~1simulators~1modbus`, `~1simulators~1mqtt`, `~1simulators`,
`~1simulators~1{device_id}`) — verifica el *shape* exacto de
201/200/204/400/403/404/409, incluyendo el sobre RFC 9457 en los errores.

Golpea la app real de `main.py` vía `TestClient` (mismo patrón que
`tests/test_devices_router.py`), sustituyendo `UserRepositoryPort`/`CachePort`
por dobles in-memory vía `app.dependency_overrides` — un login real emite el
JWT que autentica cada llamada. `BacnetSimulatorPort`/`ModbusSimulatorPort`/
`MqttPublisherPort`/`DeviceRepositoryPort`/`SimulatorRegistryService`
(`adapters/factory.py::get_bacnet_simulator_port/get_modbus_simulator_port/
get_mqtt_publisher_port/get_device_repository_port`,
`services/simulator_registry_service.py::get_simulator_registry`) también se
sustituyen por dobles/instancias propias de este archivo — una
`SimulatorRegistryService()` **nueva** por test (evita fugas de estado del
singleton de módulo entre tests).

Debe fallar hasta que `routers/simulators.py`/`schemas/simulators.py`/
`adapters/factory.py::get_bacnet_simulator_port/get_modbus_simulator_port/
get_mqtt_publisher_port` existan (T-017) — `routers/simulators.py` no existe
todavía en este punto de la secuencia (T-016 antes de T-017).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import core.middleware as middleware_module
import main as main_module
from adapters.factory import get_cache_port, get_user_repository_port
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec
from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec
from core.ports.mqtt_publisher_port import MqttInvalidPublishError
from core.ports.user_repository_port import UserRecord
from core.security.passwords import hash_password
from main import app
from services.simulator_registry_service import RunningSimulator, SimulatorRegistryService
from unittest.mock import AsyncMock

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hira:hira@postgres:5432/hiradb",
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}


class _FakeCache:
    """`CachePort` in-memory — mismo doble que `tests/test_devices_router.py`."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._store[key] = value

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def expire(self, key: str, ttl_seconds: int) -> None:
        pass

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def publish(self, channel: str, message: str) -> None:
        pass

    async def subscribe(self, channel: str):
        import asyncio

        try:
            while True:
                await asyncio.sleep(3600)
                yield "unreachable"  # pragma: no cover
        except asyncio.CancelledError:
            raise


class _FakeUserRepository:
    """`UserRepositoryPort` in-memory — mismo doble que `tests/test_devices_router.py`."""

    def __init__(self, users: list[UserRecord]) -> None:
        self._by_email = {u.email: u for u in users}
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        pass


def _make_user(**overrides) -> UserRecord:
    defaults = dict(
        id="user-1",
        email="admin@hira.dev",
        password_hash=hash_password("Correcto123!"),
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    defaults.update(overrides)
    return UserRecord(**defaults)


class _FakeBacnetSimulatorPort:
    """`BacnetSimulatorPort` in-memory."""

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


class _FakeModbusSimulatorPort:
    """`ModbusSimulatorPort` in-memory."""

    def __init__(self, token: str = "modbus-token-1", start_error: Exception | None = None) -> None:
        self.token = token
        self.start_error = start_error
        self.start_calls: list[dict] = []
        self.stop_calls: list[str] = []

    async def start(
        self, *, host: str, port: int, unit_id: int, registers: list[ModbusSimulatedRegisterSpec]
    ) -> str:
        self.start_calls.append(
            {"host": host, "port": port, "unit_id": unit_id, "registers": registers}
        )
        if self.start_error is not None:
            raise self.start_error
        return self.token

    async def stop(self, token: str) -> None:
        self.stop_calls.append(token)


class _FakeMqttPublisherPort:
    """`MqttPublisherPort` in-memory."""

    def __init__(self, token: str = "mqtt-token-1", start_error: Exception | None = None) -> None:
        self.token = token
        self.start_error = start_error
        self.start_calls: list[dict] = []
        self.stop_calls: list[str] = []

    async def start(self, *, topic: str, payload: str, interval_seconds: float) -> str:
        self.start_calls.append(
            {"topic": topic, "payload": payload, "interval_seconds": interval_seconds}
        )
        if self.start_error is not None:
            raise self.start_error
        return self.token

    async def stop(self, token: str) -> None:
        self.stop_calls.append(token)


@dataclass
class _FakeDeviceRepository:
    """`DeviceRepositoryPort` in-memory — mismo criterio de
    `tests/test_devices_router.py::_FakeDeviceRepository`, ampliado con
    `get_device_by_address` (RF-006/RF-007)."""

    devices_by_key: dict[tuple[str, str], DeviceRecord] = field(default_factory=dict)
    candidates_by_device: dict[str, list[DeviceCandidateRecord]] = field(default_factory=dict)

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
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


@pytest.fixture
def make_client(monkeypatch):
    """Factory de `TestClient` parametrizable por usuario/dobles de los 3
    puertos de simulador + repositorio + registro — cada test elige su rol y
    sus dobles."""

    def _make(
        *,
        user: UserRecord,
        bacnet_transport: _FakeBacnetSimulatorPort | None = None,
        modbus_transport: _FakeModbusSimulatorPort | None = None,
        mqtt_transport: _FakeMqttPublisherPort | None = None,
        device_repo: _FakeDeviceRepository | None = None,
        registry: SimulatorRegistryService | None = None,
    ) -> TestClient:
        for key, value in REQUIRED_ENV.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

        user_repo = _FakeUserRepository([user])
        cache = _FakeCache()
        bacnet_transport = bacnet_transport or _FakeBacnetSimulatorPort()
        modbus_transport = modbus_transport or _FakeModbusSimulatorPort()
        mqtt_transport = mqtt_transport or _FakeMqttPublisherPort()
        device_repo = device_repo or _FakeDeviceRepository()
        registry = registry or SimulatorRegistryService()

        from adapters.factory import (
            get_bacnet_simulator_port,
            get_device_repository_port,
            get_modbus_simulator_port,
            get_mqtt_publisher_port,
        )
        from services.simulator_registry_service import get_simulator_registry

        app.dependency_overrides[get_user_repository_port] = lambda: user_repo
        app.dependency_overrides[get_cache_port] = lambda: cache
        app.dependency_overrides[get_bacnet_simulator_port] = lambda: bacnet_transport
        app.dependency_overrides[get_modbus_simulator_port] = lambda: modbus_transport
        app.dependency_overrides[get_mqtt_publisher_port] = lambda: mqtt_transport
        app.dependency_overrides[get_device_repository_port] = lambda: device_repo
        app.dependency_overrides[get_simulator_registry] = lambda: registry
        monkeypatch.setattr(middleware_module, "get_user_repository_port", lambda: user_repo)
        monkeypatch.setattr(middleware_module, "get_cache_port", lambda: cache)
        monkeypatch.setattr(main_module, "get_cache_port", lambda: cache)

        test_client = TestClient(app)
        test_client.__enter__()

        login_response = test_client.post(
            "/auth/login", json={"email": user.email, "password": "Correcto123!"}
        )
        access_token = login_response.json()["access_token"]
        test_client.headers.update({"Authorization": f"Bearer {access_token}"})
        return test_client

    yield _make
    app.dependency_overrides.clear()


# ── POST /simulators/bacnet ─────────────────────────────────────────────────


def test_start_bacnet_simulator_admin_201(make_client):
    """RF-001 — Admin arranca un simulador BACnet, 201 con `SimulatorOut`."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/simulators/bacnet",
        json={
            "device_instance": 999123,
            "objects": [
                {"object_type": "analog-value", "object_instance": 1, "present_value": "42.0"}
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"device_id", "protocol", "address", "started_at"}
    assert body["protocol"] == "bacnet"
    assert body["address"] == "999123"


def test_start_bacnet_simulator_operador_403(make_client):
    """RF-004 — Operador no puede arrancar simuladores."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.post("/simulators/bacnet", json={"device_instance": 1})

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/insufficient-role"
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_start_bacnet_simulator_visor_403(make_client):
    """RF-004 — Visor no puede arrancar simuladores."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.post("/simulators/bacnet", json={"device_instance": 1})

    assert response.status_code == 403


def test_start_bacnet_simulator_direccion_real_409(make_client):
    """RF-006 — la dirección ya corresponde a un dispositivo real
    (`is_simulator=false`) → 409, sin arrancar ningún proceso."""
    device_repo = _FakeDeviceRepository()
    bacnet_transport = _FakeBacnetSimulatorPort()
    client = make_client(
        user=_make_user(rol="admin"), device_repo=device_repo, bacnet_transport=bacnet_transport
    )
    import asyncio

    asyncio.run(
        device_repo.upsert_device(
            name="BACnet real", protocol="bacnet", address="999123", is_simulator=False
        )
    )

    response = client.post("/simulators/bacnet", json={"device_instance": 999123})

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-address-conflict"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert bacnet_transport.start_calls == []


def test_start_bacnet_simulator_ya_en_ejecucion_409(make_client):
    """RF-006 — la dirección ya tiene un simulador en ejecución → 409."""
    device_repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()
    bacnet_transport = _FakeBacnetSimulatorPort()
    client = make_client(
        user=_make_user(rol="admin"),
        device_repo=device_repo,
        registry=registry,
        bacnet_transport=bacnet_transport,
    )
    import asyncio

    device = asyncio.run(
        device_repo.upsert_device(
            name="Simulador BACnet", protocol="bacnet", address="999123", is_simulator=True
        )
    )
    registry.register(
        RunningSimulator(
            device_id=device.id,
            protocol="bacnet",
            address="999123",
            token="already-running-token",
            started_at=datetime.now(timezone.utc),
        )
    )

    response = client.post("/simulators/bacnet", json={"device_instance": 999123})

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-already-running"
    assert bacnet_transport.start_calls == []


def test_start_bacnet_simulator_body_invalido_422(make_client):
    """Defensa en profundidad de forma: `device_instance` fuera de rango es
    rechazado por FastAPI/Pydantic (`Field(le=4194303)`)."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post("/simulators/bacnet", json={"device_instance": 5000000})

    assert response.status_code == 422


def test_start_bacnet_simulator_object_type_invalido_422(make_client):
    """`object_type` fuera del `Literal` de 6 valores → 422 (`plan.md §1`,
    Registro de decisiones: no es un RF de negocio, es forma)."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/simulators/bacnet",
        json={
            "device_instance": 1,
            "objects": [{"object_type": "schedule", "object_instance": 1, "present_value": "x"}],
        },
    )

    assert response.status_code == 422


# ── POST /simulators/modbus ─────────────────────────────────────────────────


def test_start_modbus_simulator_admin_201(make_client):
    """RF-002 — Admin arranca un simulador Modbus, 201 con `SimulatorOut`."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/simulators/modbus",
        json={
            "host": "127.0.0.1",
            "port": 15020,
            "unit_id": 1,
            "holding_registers": [{"address": 0, "value": 42}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["protocol"] == "modbus"
    assert body["address"] == "127.0.0.1:15020:1"


def test_start_modbus_simulator_operador_403(make_client):
    """RF-004."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.post(
        "/simulators/modbus", json={"host": "127.0.0.1", "port": 15020, "unit_id": 1}
    )

    assert response.status_code == 403


def test_start_modbus_simulator_visor_403(make_client):
    """RF-004 — Visor no puede arrancar simuladores Modbus."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.post(
        "/simulators/modbus", json={"host": "127.0.0.1", "port": 15020, "unit_id": 1}
    )

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


def test_start_modbus_simulator_direccion_real_409(make_client):
    """RF-006 — la dirección Modbus ya corresponde a un dispositivo real → 409,
    sin arrancar ningún proceso."""
    device_repo = _FakeDeviceRepository()
    modbus_transport = _FakeModbusSimulatorPort()
    client = make_client(
        user=_make_user(rol="admin"), device_repo=device_repo, modbus_transport=modbus_transport
    )
    import asyncio

    asyncio.run(
        device_repo.upsert_device(
            name="PLC real", protocol="modbus", address="127.0.0.1:15020:1", is_simulator=False
        )
    )

    response = client.post(
        "/simulators/modbus", json={"host": "127.0.0.1", "port": 15020, "unit_id": 1}
    )

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-address-conflict"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert modbus_transport.start_calls == []


def test_start_modbus_simulator_ya_en_ejecucion_409(make_client):
    """RF-006 — la dirección Modbus ya tiene un simulador en ejecución → 409."""
    device_repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()
    modbus_transport = _FakeModbusSimulatorPort()
    client = make_client(
        user=_make_user(rol="admin"),
        device_repo=device_repo,
        registry=registry,
        modbus_transport=modbus_transport,
    )
    import asyncio

    device = asyncio.run(
        device_repo.upsert_device(
            name="Simulador Modbus",
            protocol="modbus",
            address="127.0.0.1:15020:1",
            is_simulator=True,
        )
    )
    registry.register(
        RunningSimulator(
            device_id=device.id,
            protocol="modbus",
            address="127.0.0.1:15020:1",
            token="already-running-token",
            started_at=datetime.now(timezone.utc),
        )
    )

    response = client.post(
        "/simulators/modbus", json={"host": "127.0.0.1", "port": 15020, "unit_id": 1}
    )

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-already-running"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert modbus_transport.start_calls == []


# ── POST /simulators/mqtt ───────────────────────────────────────────────────


def test_start_mqtt_simulator_admin_201(make_client):
    """RF-003 — Admin arranca un publicador MQTT, 201 con `SimulatorOut`."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "edificio/piso1/ahu1/temp", "payload": "21.5", "interval_seconds": 1.0},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["protocol"] == "mqtt"
    assert body["address"] == "edificio/piso1/ahu1/temp"


def test_start_mqtt_simulator_operador_403(make_client):
    """RF-004."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "a/b", "payload": "x", "interval_seconds": 1.0},
    )

    assert response.status_code == 403


def test_start_mqtt_simulator_visor_403(make_client):
    """RF-004 — Visor no puede arrancar publicadores MQTT."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "a/b", "payload": "x", "interval_seconds": 1.0},
    )

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


def test_start_mqtt_simulator_direccion_real_409(make_client):
    """RF-006 — el topic ya corresponde a un dispositivo real → 409, sin
    arrancar el publicador."""
    device_repo = _FakeDeviceRepository()
    mqtt_transport = _FakeMqttPublisherPort()
    client = make_client(
        user=_make_user(rol="admin"), device_repo=device_repo, mqtt_transport=mqtt_transport
    )
    import asyncio

    asyncio.run(
        device_repo.upsert_device(
            name="Sensor MQTT real", protocol="mqtt", address="a/b", is_simulator=False
        )
    )

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "a/b", "payload": "x", "interval_seconds": 1.0},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-address-conflict"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert mqtt_transport.start_calls == []


def test_start_mqtt_simulator_ya_en_ejecucion_409(make_client):
    """RF-006 — el topic ya tiene un publicador en ejecución → 409."""
    device_repo = _FakeDeviceRepository()
    registry = SimulatorRegistryService()
    mqtt_transport = _FakeMqttPublisherPort()
    client = make_client(
        user=_make_user(rol="admin"),
        device_repo=device_repo,
        registry=registry,
        mqtt_transport=mqtt_transport,
    )
    import asyncio

    device = asyncio.run(
        device_repo.upsert_device(
            name="Simulador MQTT a/b", protocol="mqtt", address="a/b", is_simulator=True
        )
    )
    registry.register(
        RunningSimulator(
            device_id=device.id,
            protocol="mqtt",
            address="a/b",
            token="already-running-token",
            started_at=datetime.now(timezone.utc),
        )
    )

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "a/b", "payload": "x", "interval_seconds": 1.0},
    )

    assert response.status_code == 409
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-already-running"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert mqtt_transport.start_calls == []


def test_start_mqtt_simulator_intervalo_invalido_400_rfc9457(make_client):
    """RF-015 — `interval_seconds <= 0` responde 400 RFC 9457, sin arrancar
    el publicador."""
    mqtt_transport = _FakeMqttPublisherPort()
    client = make_client(user=_make_user(rol="admin"), mqtt_transport=mqtt_transport)

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "a/b", "payload": "x", "interval_seconds": 0},
    )

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/mqtt-invalid-interval"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert mqtt_transport.start_calls == []


def test_start_mqtt_simulator_publish_invalido_400_rfc9457(make_client):
    """RF-014 — `topic`/`payload` rechazado por la librería al publicar
    responde 400 RFC 9457, sin escribir en `devices`."""
    mqtt_transport = _FakeMqttPublisherPort(
        start_error=MqttInvalidPublishError("Publish topic cannot contain wildcards.")
    )
    device_repo = _FakeDeviceRepository()
    client = make_client(
        user=_make_user(rol="admin"), mqtt_transport=mqtt_transport, device_repo=device_repo
    )

    response = client.post(
        "/simulators/mqtt",
        json={"topic": "edificio/#", "payload": "x", "interval_seconds": 1.0},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/mqtt-invalid-publish"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
    assert device_repo.devices_by_key == {}


# ── GET /simulators ─────────────────────────────────────────────────────────


def test_list_simulators_admin_200(make_client):
    """RF-010 — Admin lista únicamente los simuladores en ejecución."""
    registry = SimulatorRegistryService()
    entry = RunningSimulator(
        device_id=str(uuid4()),
        protocol="bacnet",
        address="999123",
        token="tok",
        started_at=datetime.now(timezone.utc),
    )
    registry.register(entry)
    client = make_client(user=_make_user(rol="admin"), registry=registry)

    response = client.get("/simulators")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["device_id"] == entry.device_id
    assert set(body[0].keys()) == {"device_id", "protocol", "address", "started_at"}


def test_list_simulators_operador_200(make_client):
    """RF-005 — Operador también puede listar (mismo criterio que `GET /devices`)."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.get("/simulators")

    assert response.status_code == 200
    assert response.json() == []


def test_list_simulators_visor_403(make_client):
    """RF-005 — Visor no puede listar simuladores."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.get("/simulators")

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


# ── DELETE /simulators/{device_id} ──────────────────────────────────────────


def test_stop_simulator_admin_204(make_client):
    """RF-009 — Admin detiene un simulador en ejecución, 204 sin cuerpo."""
    registry = SimulatorRegistryService()
    bacnet_transport = _FakeBacnetSimulatorPort()
    device_id = str(uuid4())
    registry.register(
        RunningSimulator(
            device_id=device_id,
            protocol="bacnet",
            address="999123",
            token="tok-1",
            started_at=datetime.now(timezone.utc),
        )
    )
    client = make_client(
        user=_make_user(rol="admin"), registry=registry, bacnet_transport=bacnet_transport
    )

    response = client.delete(f"/simulators/{device_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert bacnet_transport.stop_calls == ["tok-1"]
    assert registry.get(device_id) is None


def test_stop_simulator_operador_403(make_client):
    """RF-004."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.delete(f"/simulators/{uuid4()}")

    assert response.status_code == 403


def test_stop_simulator_visor_403(make_client):
    """RF-004 — Visor no puede detener simuladores."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.delete(f"/simulators/{uuid4()}")

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


def test_stop_simulator_no_encontrado_404_rfc9457(make_client):
    """RF-012 — `device_id` sin ningún simulador en ejecución responde 404
    RFC 9457."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.delete(f"/simulators/{uuid4()}")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/simulator-not-running"
    assert set(body.keys()) == {"type", "title", "status", "detail"}
