"""E2E real — `POST /devices/scan/bacnet` → `GET /devices` → `GET /devices/
{id}/candidates` (`SRV-003-bacnet-adapter`, T-017, `plan.md §5`/§6 paso 12).

Recorrido completo con infraestructura real: una instancia real de
`BAC0.lite()` actúa de "dispositivo" (2 objetos BACnet reales, igual que
`tests/integration/test_bac0_adapter.py`); la app real de `main.py` usa un
`adapters/bacnet/bac0_adapter.py::BAC0Adapter` real (Who-Is unicast dirigido a
esa dirección, mismo criterio que `test_bac0_adapter.py` — evita depender de
broadcast UDP en el entorno de test) y un `adapters/db/
device_repository_adapter.py::PostgreSQLDeviceRepository` real contra Postgres
(requiere `alembic upgrade head` con la migración `0002` aplicada) vía
`app.dependency_overrides` — mismo patrón de inyección que
`tests/test_devices_router.py`, sustituyendo los dobles in-memory de ese test
por los adaptadores reales de esta feature.

Cliente HTTP: `httpx.AsyncClient(transport=ASGITransport(app=app))`, **no**
`fastapi.testclient.TestClient` — `TestClient` ejecuta la app ASGI en un hilo
propio con su propio *event loop* (vía el *portal* de `anyio`), y los objetos
`asyncio` internos de `BAC0`/`bacpypes3` (transportes UDP, futuros) quedan
atados al loop en el que se crearon; cruzarlos entre loops distintos falla en
tiempo real con `ValueError: The future belongs to a different loop...`
(verificado con ejecución real al escribir este test). `ASGITransport` corre
la app dentro del mismo *loop* async del test (`pytest-asyncio`), igual que
las instancias `BAC0` — sin cruce de *loops*.

`UserRepositoryPort`/`CachePort` (autenticación) se mantienen como dobles
in-memory — no son objeto de esta feature y ya están verificados de punta a
punta en `tests/integration/test_auth_security.py` (`SRV-002-auth-rbac`);
repetirlos aquí duplicaría cobertura sin aportar señal nueva sobre BACnet/
Postgres, que es lo que este test mide.

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres
    cd backend && DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:5432/hiradb \
        alembic upgrade head   # aplica 0001 y 0002

RNF-001 se mide con evidencia real de tiempo (ver aserción al final) — con
Who-Is unicast dirigido, el escaneo resuelve tan pronto llega el I-Am (no
espera la ventana completa de 3s de un broadcast sin respondientes); esta
medición cubre "el escaneo no cuelga ni tarda desproporcionadamente cuando el
dispositivo responde", no el caso de broadcast completo sin nadie que
responda (ya cubierto por RF-008 en `tests/test_device_scan_service.py`/
`tests/test_devices_router.py`).
"""
import asyncio
import os
import time
from unittest.mock import AsyncMock

import httpx
import pytest
from bacpypes3.local.analog import AnalogValueObject
from bacpypes3.local.binary import BinaryValueObject

import core.middleware as middleware_module
import main as main_module
from adapters.bacnet.bac0_adapter import BAC0Adapter
from adapters.db.device_repository_adapter import PostgreSQLDeviceRepository
from adapters.factory import (
    get_bacnet_transport_port,
    get_cache_port,
    get_device_repository_port,
    get_user_repository_port,
)
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.ports.user_repository_port import UserRecord
from core.security.passwords import hash_password
from main import app
from models.device_model import device_points_candidates_table, devices_table

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


class _FakeCache:
    """`CachePort` in-memory — autenticación no es objeto de este test
    (ver docstring del módulo)."""

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
    """`UserRepositoryPort` in-memory — mismo doble que
    `tests/test_devices_router.py`."""

    def __init__(self, users: list[UserRecord]) -> None:
        self._by_email = {u.email: u for u in users}
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        pass


async def _reset_device_tables() -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(device_points_candidates_table.delete())
            await connection.execute(devices_table.delete())
    finally:
        await engine.dispose()


async def _make_simulated_device(port: int):
    """"Dispositivo" BACnet real con 2 objetos — infraestructura de test."""
    import BAC0

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
    await asyncio.sleep(0.3)
    return device


@pytest.mark.asyncio
async def test_scan_bacnet_e2e_real_bac0_and_postgres(monkeypatch):
    """RF-001, RF-002, RF-004, RF-005, RF-008, RF-009, RNF-001 — recorrido
    completo con `BAC0Adapter`/`PostgreSQLDeviceRepository` reales."""
    await _reset_device_tables()

    device = await _make_simulated_device(47950)
    bacnet_adapter = BAC0Adapter(
        ip="127.0.0.1", port=47951, target_address="127.0.0.1:47950"
    )
    device_repo = PostgreSQLDeviceRepository(DATABASE_URL)

    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

    user = UserRecord(
        id="user-1",
        email="admin@hira.dev",
        password_hash=hash_password("Correcto123!"),
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    user_repo = _FakeUserRepository([user])
    cache = _FakeCache()

    app.dependency_overrides[get_user_repository_port] = lambda: user_repo
    app.dependency_overrides[get_cache_port] = lambda: cache
    app.dependency_overrides[get_bacnet_transport_port] = lambda: bacnet_adapter
    app.dependency_overrides[get_device_repository_port] = lambda: device_repo
    monkeypatch.setattr(middleware_module, "get_user_repository_port", lambda: user_repo)
    monkeypatch.setattr(middleware_module, "get_cache_port", lambda: cache)
    monkeypatch.setattr(main_module, "get_cache_port", lambda: cache)

    try:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            login_response = await client.post(
                "/auth/login",
                json={"email": user.email, "password": "Correcto123!"},
            )
            assert login_response.status_code == 200
            access_token = login_response.json()["access_token"]
            client.headers.update({"Authorization": f"Bearer {access_token}"})

            start = time.monotonic()
            scan_response = await client.post("/devices/scan/bacnet")
            elapsed = time.monotonic() - start

            assert scan_response.status_code == 200
            scanned = scan_response.json()
            assert len(scanned) == 1
            assert scanned[0]["protocol"] == "bacnet"
            assert scanned[0]["is_simulator"] is False
            device_id = scanned[0]["id"]

            # RNF-001 — Who-Is unicast dirigido resuelve al primer I-Am; no
            # cuelga ni se acerca a la ventana completa de 3s de un broadcast
            # sin respondientes (ver docstring del módulo).
            print(f"\nRNF-001 evidencia real: escaneo completo (Who-Is unicast + lectura de 2 objetos) tardó {elapsed:.3f}s")
            assert elapsed < 3.0, f"escaneo tardó {elapsed:.2f}s (RNF-001)"

            devices_response = await client.get("/devices")
            assert devices_response.status_code == 200
            listed = devices_response.json()
            assert len(listed) == 1
            assert listed[0]["id"] == device_id

            candidates_response = await client.get(f"/devices/{device_id}/candidates")
            assert candidates_response.status_code == 200
            candidates = candidates_response.json()
            by_type = {c["object_type"]: c for c in candidates}
            assert set(by_type) == {"analog-value", "binary-value"}
            assert by_type["analog-value"]["object_name"] == "Zone Temperature"
            assert by_type["analog-value"]["present_value"] == "21.5"
            assert by_type["binary-value"]["present_value"] == "active"

            # RF-009 — `id` inexistente responde 404 `device-not-found`.
            missing_response = await client.get(
                "/devices/00000000-0000-0000-0000-000000000000/candidates"
            )
            assert missing_response.status_code == 404
            assert (
                missing_response.json()["type"]
                == "https://hira.dev/errors/device-not-found"
            )
    finally:
        app.dependency_overrides.clear()
        await bacnet_adapter.disconnect()
        await device.disconnect()
        await device_repo.close()
        await _reset_device_tables()
