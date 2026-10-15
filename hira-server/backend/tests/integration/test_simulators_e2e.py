"""E2E real — simuladores BACnet/Modbus/MQTT de punta a punta
(`SRV-006-simuladores`, T-026, `plan.md §5` fila "Sistema (e2e)").

La app real de `main.py` con los **adaptadores reales** de esta feature
(`BacnetSimulatorAdapter`, `ModbusSimulatorAdapter`, `MqttPublisherAdapter`),
`PostgreSQLDeviceRepository` real y un `SimulatorRegistryService` nuevo por
test, inyectados vía `app.dependency_overrides`. Cada simulador arrancado por
HTTP se confirma con un **cliente real** de su protocolo (BAC0, pymodbus,
paho-mqtt). Autenticación con dobles in-memory, mismo criterio que
`tests/integration/test_devices_scan_e2e.py` (ya verificada de punta a punta
en `SRV-002`).

Cliente HTTP: `httpx.AsyncClient(transport=ASGITransport(app=app))` — la app
corre en el mismo *event loop* que los objetos `asyncio` de BAC0/pymodbus
(ver docstring de `test_devices_scan_e2e.py`).

Requiere Postgres (migración `0002`) y Mosquitto del compose levantados.
"""
import asyncio
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass
from unittest.mock import AsyncMock

import BAC0
import httpx
import paho.mqtt.client as mqtt
import pytest
from pymodbus.client import AsyncModbusTcpClient

import core.middleware as middleware_module
import main as main_module
from adapters.bacnet.bacnet_simulator_adapter import BacnetSimulatorAdapter
from adapters.db.device_repository_adapter import PostgreSQLDeviceRepository
from adapters.factory import (
    get_bacnet_simulator_port,
    get_cache_port,
    get_device_repository_port,
    get_modbus_simulator_port,
    get_modbus_transport_port,
    get_mqtt_publisher_port,
    get_user_repository_port,
)
from adapters.modbus.modbus_simulator_adapter import ModbusSimulatorAdapter
from adapters.modbus.pymodbus_adapter import PymodbusAdapter
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from adapters.mqtt.mqtt_publisher_adapter import MqttPublisherAdapter
from core.ports.user_repository_port import UserRecord
from core.security.passwords import hash_password
from main import app
from models.device_model import device_points_candidates_table, devices_table
from services.simulator_registry_service import SimulatorRegistryService, get_simulator_registry

logging.getLogger("pymodbus").setLevel(logging.WARNING)

# Credenciales reales del Mosquitto, capturadas antes de que `REQUIRED_ENV`
# las sobreescriba (mismo criterio que `test_devices_scan_e2e.py`).
_REAL_MQTT_HOST = os.environ.get("TEST_MQTT_HOST", "localhost")
_REAL_MQTT_PORT = int(os.environ.get("TEST_MQTT_PORT", "1883"))
_REAL_MQTT_USER = os.environ.get("MQTT_USER", "hira")
_REAL_MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "changeme")

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)

REQUIRED_ENV = {
    "DATABASE_URL": DATABASE_URL,
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}

_IP = "127.0.0.1"
_PASSWORD = "Correcto123!"


class _FakeCache:
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
        try:
            while True:
                await asyncio.sleep(3600)
                yield "unreachable"  # pragma: no cover
        except asyncio.CancelledError:
            raise


class _FakeUserRepository:
    def __init__(self, users: list[UserRecord]) -> None:
        self._by_email = {u.email: u for u in users}
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        pass


def _user(rol: str) -> UserRecord:
    return UserRecord(
        id=f"user-{rol}",
        email=f"{rol}@hira.dev",
        password_hash=hash_password(_PASSWORD),
        rol=rol,
        scope="global",
        project_id=None,
        activo=True,
    )


async def _reset_device_tables() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(device_points_candidates_table.delete())
            await connection.execute(devices_table.delete())
    finally:
        await engine.dispose()


@dataclass
class _Harness:
    client: httpx.AsyncClient
    tokens: dict[str, str]
    bacnet: BacnetSimulatorAdapter
    modbus: ModbusSimulatorAdapter
    mqtt: MqttPublisherAdapter
    device_repo: PostgreSQLDeviceRepository

    def as_role(self, rol: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.tokens[rol]}"}

    def use_new_registry(self) -> SimulatorRegistryService:
        """Equivalente verificable de un reinicio del proceso (RF-013): el
        registro en memoria nace vacío."""
        registry = SimulatorRegistryService()
        app.dependency_overrides[get_simulator_registry] = lambda: registry
        return registry


@pytest.fixture
async def harness(monkeypatch):
    await _reset_device_tables()
    bacnet = BacnetSimulatorAdapter(ip=_IP, port_range_start=48500)
    modbus = ModbusSimulatorAdapter()
    mqtt_publisher = MqttPublisherAdapter(
        host=_REAL_MQTT_HOST,
        port=_REAL_MQTT_PORT,
        user=_REAL_MQTT_USER,
        password=_REAL_MQTT_PASSWORD,
    )
    device_repo = PostgreSQLDeviceRepository(DATABASE_URL)
    registry = SimulatorRegistryService()

    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

    users = [_user("admin"), _user("operador"), _user("visor")]
    user_repo = _FakeUserRepository(users)
    cache = _FakeCache()
    app.dependency_overrides[get_user_repository_port] = lambda: user_repo
    app.dependency_overrides[get_cache_port] = lambda: cache
    app.dependency_overrides[get_bacnet_simulator_port] = lambda: bacnet
    app.dependency_overrides[get_modbus_simulator_port] = lambda: modbus
    app.dependency_overrides[get_mqtt_publisher_port] = lambda: mqtt_publisher
    app.dependency_overrides[get_modbus_transport_port] = PymodbusAdapter
    app.dependency_overrides[get_device_repository_port] = lambda: device_repo
    app.dependency_overrides[get_simulator_registry] = lambda: registry
    monkeypatch.setattr(middleware_module, "get_user_repository_port", lambda: user_repo)
    monkeypatch.setattr(middleware_module, "get_cache_port", lambda: cache)
    monkeypatch.setattr(main_module, "get_cache_port", lambda: cache)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        tokens = {}
        for user in users:
            response = await client.post(
                "/auth/login", json={"email": user.email, "password": _PASSWORD}
            )
            assert response.status_code == 200
            tokens[user.rol] = response.json()["access_token"]
        try:
            yield _Harness(client, tokens, bacnet, modbus, mqtt_publisher, device_repo)
        finally:
            app.dependency_overrides.clear()
            running = (
                (bacnet, bacnet._instances),  # noqa: SLF001
                (modbus, modbus._servers),  # noqa: SLF001
                (mqtt_publisher, mqtt_publisher._publishers),  # noqa: SLF001
            )
            for adapter, tokens in running:
                for token in list(tokens):
                    await adapter.stop(token)
            await device_repo.close()
            await _reset_device_tables()


async def _devices_by_address(harness: _Harness, protocol: str) -> dict[str, dict]:
    response = await harness.client.get("/devices", headers=harness.as_role("admin"))
    assert response.status_code == 200
    return {d["address"]: d for d in response.json() if d["protocol"] == protocol}


@pytest.mark.asyncio
async def test_bacnet_simulator_full_lifecycle(harness):
    """RF-001, RF-006, RF-007, RF-009, RF-010 — arrancar por HTTP → I-Am y
    `presentValue` reales → listado en `/simulators` y `/devices` → 409 si ya
    corre → `DELETE` → deja de responder pero el dispositivo y sus candidatos
    siguen → rearrancar reutiliza el mismo `device_id`."""
    admin = harness.as_role("admin")
    body = {
        "device_instance": 999123,
        "objects": [
            {"object_type": "analog-value", "object_instance": 1, "present_value": "42.0"}
        ],
    }
    client_bacnet = BAC0.lite(ip=_IP, port=48599, ping=False)
    try:
        start = await harness.client.post("/simulators/bacnet", json=body, headers=admin)
        assert start.status_code == 201
        simulator = start.json()
        assert simulator["address"] == "999123"
        device_id = simulator["device_id"]

        iams = await client_bacnet.who_is(address=f"{_IP}:48500", timeout=3)
        assert [int(iam.iAmDeviceIdentifier[1]) for iam in iams] == [999123]
        assert await client_bacnet.read(f"{_IP}:48500 analogValue 1 presentValue") == 42.0

        running = await harness.client.get("/simulators", headers=admin)
        assert [s["device_id"] for s in running.json()] == [device_id]
        device = (await _devices_by_address(harness, "bacnet"))["999123"]
        assert device["id"] == device_id
        assert device["is_simulator"] is True
        candidates = await harness.client.get(f"/devices/{device_id}/candidates", headers=admin)
        assert [(c["object_type"], c["present_value"]) for c in candidates.json()] == [
            ("analog-value", "42.0")
        ]

        duplicate = await harness.client.post("/simulators/bacnet", json=body, headers=admin)
        assert duplicate.status_code == 409
        assert duplicate.json()["type"] == "https://hira.dev/errors/simulator-already-running"

        stop = await harness.client.delete(f"/simulators/{device_id}", headers=admin)
        assert stop.status_code == 204
        assert (await harness.client.get("/simulators", headers=admin)).json() == []
        assert await client_bacnet.who_is(address=f"{_IP}:48500", timeout=1) == []
        assert (await _devices_by_address(harness, "bacnet"))["999123"]["id"] == device_id
        candidates = await harness.client.get(f"/devices/{device_id}/candidates", headers=admin)
        assert len(candidates.json()) == 1

        await asyncio.sleep(0.3)
        resumed = await harness.client.post("/simulators/bacnet", json=body, headers=admin)
        assert resumed.status_code == 201
        assert resumed.json()["device_id"] == device_id
        assert len(await _devices_by_address(harness, "bacnet")) == 1
    finally:
        await client_bacnet.disconnect()


@pytest.mark.asyncio
async def test_modbus_simulator_survives_real_scan_and_rejects_real_address(harness):
    """RF-002, RF-006, RF-008 — un cliente Modbus real lee el valor cargado;
    un escaneo real (`POST /devices/scan/modbus`) sobre la misma dirección NO
    revierte `is_simulator`; una dirección ya ocupada por un dispositivo real
    responde 409 sin arrancar nada."""
    admin = harness.as_role("admin")
    start = await harness.client.post(
        "/simulators/modbus",
        json={
            "host": _IP,
            "port": 15800,
            "unit_id": 1,
            "holding_registers": [{"address": 0, "value": 42}],
        },
        headers=admin,
    )
    assert start.status_code == 201
    device_id = start.json()["device_id"]

    modbus_client = AsyncModbusTcpClient(_IP, port=15800, timeout=1.0, retries=0)
    await modbus_client.connect()
    try:
        assert (await modbus_client.read_holding_registers(0, count=1, device_id=1)).registers == [42]
    finally:
        modbus_client.close()

    scan = await harness.client.post(
        "/devices/scan/modbus",
        json={"host": _IP, "port": 15800, "unit_id": 1, "holding_registers": {"start": 0, "count": 1}},
        headers=admin,
    )
    assert scan.status_code == 200
    assert [c["present_value"] for c in scan.json()] == ["42"]
    device = (await _devices_by_address(harness, "modbus"))[f"{_IP}:15800:1"]
    assert device["id"] == device_id
    assert device["is_simulator"] is True

    await harness.device_repo.upsert_device(
        name="PLC real", protocol="modbus", address=f"{_IP}:15801:1", is_simulator=False
    )
    conflict = await harness.client.post(
        "/simulators/modbus",
        json={"host": _IP, "port": 15801, "unit_id": 1},
        headers=admin,
    )
    assert conflict.status_code == 409
    assert conflict.json()["type"] == "https://hira.dev/errors/simulator-address-conflict"
    probe = AsyncModbusTcpClient(_IP, port=15801, timeout=1.0, retries=0)
    try:
        assert await probe.connect() is False
    finally:
        probe.close()


def _subscribe(topic: str) -> tuple[mqtt.Client, list[str]]:
    received: list[str] = []
    subscribed = threading.Event()
    client = mqtt.Client(
        client_id=f"test-e2e-sub-{uuid.uuid4().hex[:8]}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    )
    client.username_pw_set(_REAL_MQTT_USER, _REAL_MQTT_PASSWORD)
    client.on_connect = lambda c, *_: c.subscribe(topic, qos=1)
    client.on_subscribe = lambda *_: subscribed.set()
    client.on_message = lambda c, u, message: received.append(message.payload.decode())
    client.connect(_REAL_MQTT_HOST, _REAL_MQTT_PORT, keepalive=10)
    client.loop_start()
    assert subscribed.wait(timeout=5.0)
    return client, received


@pytest.mark.asyncio
async def test_mqtt_simulator_publishes_and_validates_input(harness):
    """RF-003, RF-009, RF-014, RF-015 — el publicador arrancado por HTTP llega
    a un suscriptor real; tras `DELETE` deja de publicar; topic con wildcard
    e intervalo ≤ 0 responden 400 RFC 9457 sin crear dispositivos."""
    admin = harness.as_role("admin")
    topic = f"hira/e2e-sim/{uuid.uuid4().hex[:8]}/temp"
    subscriber, received = _subscribe(topic)
    try:
        start = await harness.client.post(
            "/simulators/mqtt",
            json={"topic": topic, "payload": "21.5", "interval_seconds": 0.5},
            headers=admin,
        )
        assert start.status_code == 201
        device_id = start.json()["device_id"]
        await asyncio.sleep(1.8)
        assert len(received) >= 3
        assert set(received) == {"21.5"}
        assert (await _devices_by_address(harness, "mqtt"))[topic]["is_simulator"] is True

        stop = await harness.client.delete(f"/simulators/{device_id}", headers=admin)
        assert stop.status_code == 204
        count_at_stop = len(received)
        await asyncio.sleep(1.0)
        assert len(received) == count_at_stop
    finally:
        subscriber.disconnect()
        subscriber.loop_stop()

    wildcard = await harness.client.post(
        "/simulators/mqtt",
        json={"topic": "hira/e2e-sim/#", "payload": "x", "interval_seconds": 1.0},
        headers=admin,
    )
    assert wildcard.status_code == 400
    assert wildcard.json()["type"] == "https://hira.dev/errors/mqtt-invalid-publish"
    interval = await harness.client.post(
        "/simulators/mqtt",
        json={"topic": "hira/e2e-sim/x", "payload": "x", "interval_seconds": 0},
        headers=admin,
    )
    assert interval.status_code == 400
    assert interval.json()["type"] == "https://hira.dev/errors/mqtt-invalid-interval"
    assert set(await _devices_by_address(harness, "mqtt")) == {topic}


@pytest.mark.asyncio
async def test_rbac_and_unknown_simulator(harness):
    """RF-004, RF-005, RF-012 — Operador/Visor no arrancan ni detienen;
    Operador sí lista, Visor no; detener un `device_id` sin simulador en
    ejecución responde 404."""
    operador = harness.as_role("operador")
    visor = harness.as_role("visor")
    body = {"device_instance": 4242}

    assert (await harness.client.post("/simulators/bacnet", json=body, headers=operador)).status_code == 403
    assert (await harness.client.post("/simulators/bacnet", json=body, headers=visor)).status_code == 403
    assert (await harness.client.get("/simulators", headers=operador)).status_code == 200
    assert (await harness.client.get("/simulators", headers=visor)).status_code == 403
    assert (await harness.client.delete(f"/simulators/{uuid.uuid4()}", headers=operador)).status_code == 403

    missing = await harness.client.delete(f"/simulators/{uuid.uuid4()}", headers=harness.as_role("admin"))
    assert missing.status_code == 404
    assert missing.json()["type"] == "https://hira.dev/errors/simulator-not-running"
    assert await _devices_by_address(harness, "bacnet") == {}


@pytest.mark.asyncio
async def test_restart_empties_running_list_and_keeps_devices(harness):
    """RF-007, RF-013 — tras un "reinicio" (proceso del simulador detenido y
    registro en memoria nuevo) `GET /simulators` queda vacío, `GET /devices`
    conserva la fila, y volver a arrancar la misma identidad reutiliza el
    mismo `device_id`."""
    admin = harness.as_role("admin")
    body = {"host": _IP, "port": 15802, "unit_id": 2}
    first = await harness.client.post("/simulators/modbus", json=body, headers=admin)
    assert first.status_code == 201
    device_id = first.json()["device_id"]

    for token in list(harness.modbus._servers):  # noqa: SLF001 — muerte del proceso
        await harness.modbus.stop(token)
    harness.use_new_registry()

    assert (await harness.client.get("/simulators", headers=admin)).json() == []
    assert (await _devices_by_address(harness, "modbus"))[f"{_IP}:15802:2"]["id"] == device_id

    resumed = await harness.client.post("/simulators/modbus", json=body, headers=admin)
    assert resumed.status_code == 201
    assert resumed.json()["device_id"] == device_id
    assert len(await _devices_by_address(harness, "modbus")) == 1


@pytest.mark.asyncio
async def test_api_keeps_responding_while_simulators_run(harness):
    """RNF-001 — con un simulador de cada protocolo en ejecución, `/health`,
    `/devices` y `/simulators` siguen respondiendo con normalidad (evidencia
    de tiempo real impresa)."""
    admin = harness.as_role("admin")
    started = [
        await harness.client.post("/simulators/bacnet", json={"device_instance": 5001}, headers=admin),
        await harness.client.post(
            "/simulators/modbus", json={"host": _IP, "port": 15803, "unit_id": 1}, headers=admin
        ),
        await harness.client.post(
            "/simulators/mqtt",
            json={"topic": f"hira/e2e-sim/{uuid.uuid4().hex[:8]}", "payload": "x", "interval_seconds": 0.2},
            headers=admin,
        ),
    ]
    assert [r.status_code for r in started] == [201, 201, 201]

    timings = {}
    for path in ("/health", "/devices", "/simulators"):
        begin = time.monotonic()
        response = await harness.client.get(path, headers=admin)
        timings[path] = time.monotonic() - begin
        assert response.status_code == 200, path
    print(f"\nRNF-001 evidencia real con 3 simuladores en ejecución: {timings}")
    assert all(elapsed < 1.0 for elapsed in timings.values()), timings
    assert len((await harness.client.get("/simulators", headers=admin)).json()) == 3
