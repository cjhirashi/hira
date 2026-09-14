"""`routers/devices.py` — `POST /devices/scan/bacnet`, `POST /devices/scan/
modbus`, `GET /devices`, `GET /devices/{id}/candidates` (adaptador de entrada
HTTP, `SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1bacnet`
(+ `~1devices~1scan~1modbus`, `~1devices`, `~1devices~1{id}~1candidates`) —
verifica el *shape* exacto de 200/400/403/404, incluyendo el sobre RFC 9457
en los errores.

Golpea la app real de `main.py` vía `TestClient` (mismo patrón que
`test_auth_router.py`), sustituyendo `UserRepositoryPort`/`CachePort` por
dobles in-memory vía `app.dependency_overrides` — un login real emite el JWT
que autentica cada llamada (los endpoints están fuera de `PUBLIC_ALLOWLIST`,
`core/middleware.py`). `BacnetTransportPort`/`ModbusTransportPort`/
`DeviceRepositoryPort` (`adapters/factory.py::get_bacnet_transport_port/
get_modbus_transport_port/get_device_repository_port`) también se sustituyen
por dobles in-memory propios de este archivo, controlando exactamente qué
devuelve el escaneo.

Los casos de `POST /devices/scan/modbus` (`SRV-004-modbus-adapter`) deben
fallar antes de T-008 (no existen el endpoint en `routers/devices.py` ni
`adapters/factory.py::get_modbus_transport_port`).
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import core.middleware as middleware_module
import main as main_module
from adapters.factory import get_cache_port, get_user_repository_port
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.ports.bacnet_transport_port import (
    BacnetDeviceAnnouncement,
    BacnetObjectReading,
)
from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord
from core.ports.modbus_transport_port import (
    ModbusReadFailure,
    ModbusRegisterReading,
    ModbusRegisterType,
)
from core.ports.user_repository_port import UserRecord
from core.security.passwords import hash_password
from main import app

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
    """`CachePort` in-memory — mismo doble que `tests/test_auth_router.py`."""

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
    """`UserRepositoryPort` in-memory — mismo doble que `tests/test_auth_router.py`."""

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


class _FakeBacnetTransport:
    """`BacnetTransportPort` in-memory — controla los anuncios del escaneo."""

    def __init__(
        self,
        announcements: list[BacnetDeviceAnnouncement] | None = None,
        readings_by_address: dict[str, list[BacnetObjectReading]] | None = None,
    ) -> None:
        self._announcements = announcements or []
        self._readings_by_address = readings_by_address or {}

    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        return self._announcements

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        return self._readings_by_address.get(network_address, [])


@dataclass
class _FakeDeviceRepository:
    """`DeviceRepositoryPort` in-memory — mismo criterio de
    `tests/test_device_scan_service.py::_FakeDeviceRepository`."""

    devices_by_key: dict[tuple[str, str], DeviceRecord] = field(default_factory=dict)
    candidates_by_device: dict[str, list[DeviceCandidateRecord]] = field(
        default_factory=dict
    )

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

    async def list_candidates_for_device(
        self, device_id: str
    ) -> list[DeviceCandidateRecord]:
        return list(self.candidates_by_device.get(device_id, []))


class _FakeModbusTransport:
    """`ModbusTransportPort` in-memory — controla los resultados de
    `read_range` por `(register_type, start, count)` para cada test."""

    def __init__(
        self,
        results_by_range: dict[
            tuple[ModbusRegisterType, int, int],
            list[ModbusRegisterReading | ModbusReadFailure],
        ]
        | None = None,
    ) -> None:
        self._results_by_range = results_by_range or {}

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
        return self._results_by_range.get((register_type, start, count), [])


@pytest.fixture
def make_client(monkeypatch):
    """Factory de `TestClient` parametrizable por usuario/dobles de puertos
    BACnet/Modbus — cada test elige su rol y su transporte/repositorio."""

    def _make(
        *,
        user: UserRecord,
        transport: _FakeBacnetTransport | None = None,
        modbus_transport: _FakeModbusTransport | None = None,
        device_repo: _FakeDeviceRepository | None = None,
    ) -> TestClient:
        for key, value in REQUIRED_ENV.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

        user_repo = _FakeUserRepository([user])
        cache = _FakeCache()
        transport = transport or _FakeBacnetTransport()
        modbus_transport = modbus_transport or _FakeModbusTransport()
        device_repo = device_repo or _FakeDeviceRepository()

        from adapters.factory import (
            get_bacnet_transport_port,
            get_device_repository_port,
            get_modbus_transport_port,
        )

        app.dependency_overrides[get_user_repository_port] = lambda: user_repo
        app.dependency_overrides[get_cache_port] = lambda: cache
        app.dependency_overrides[get_bacnet_transport_port] = lambda: transport
        app.dependency_overrides[get_modbus_transport_port] = lambda: modbus_transport
        app.dependency_overrides[get_device_repository_port] = lambda: device_repo
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


def test_scan_bacnet_admin_200_lista_dispositivos_del_escaneo(make_client):
    """RF-001, RF-002 — Admin dispara el escaneo, 200 con los dispositivos tocados."""
    transport = _FakeBacnetTransport(
        announcements=[
            BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808")
        ],
        readings_by_address={
            "10.0.0.1:47808": [
                BacnetObjectReading(
                    object_type="analogInput",
                    object_instance=1,
                    object_name="Temp",
                    present_value="21.5",
                    units="degreesCelsius",
                )
            ]
        },
    )
    client = make_client(user=_make_user(rol="admin"), transport=transport)

    response = client.post("/devices/scan/bacnet")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    device = body[0]
    assert set(device.keys()) == {
        "id",
        "name",
        "protocol",
        "address",
        "is_simulator",
        "last_seen_at",
    }
    assert device["protocol"] == "bacnet"
    assert device["is_simulator"] is False


def test_scan_bacnet_sin_i_am_200_lista_vacia(make_client):
    """RF-008 — sin ningún I-Am, 200 con lista vacía (no es un error)."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.post("/devices/scan/bacnet")

    assert response.status_code == 200
    assert response.json() == []


def test_scan_bacnet_visor_403_rfc9457(make_client):
    """RF-003 — Visor no puede disparar el escaneo."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.post("/devices/scan/bacnet")

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/insufficient-role"
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_list_devices_admin_200(make_client):
    """RF-004 — Admin lista los dispositivos persistidos."""
    device_repo = _FakeDeviceRepository()
    client = make_client(user=_make_user(rol="admin"), device_repo=device_repo)
    client.post("/devices/scan/bacnet")  # sin anuncios: repo queda vacío

    response = client.get("/devices")

    assert response.status_code == 200
    assert response.json() == []


def test_list_devices_visor_403(make_client):
    """RF-003 — Visor no puede listar dispositivos."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.get("/devices")

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


def test_list_candidates_de_device_existente_200(make_client):
    """RF-005 — lista los candidatos de un dispositivo ya escaneado."""
    transport = _FakeBacnetTransport(
        announcements=[
            BacnetDeviceAnnouncement(instance_number=1, network_address="10.0.0.1:47808")
        ],
        readings_by_address={
            "10.0.0.1:47808": [
                BacnetObjectReading(
                    object_type="analogInput",
                    object_instance=1,
                    object_name="Temp",
                    present_value="21.5",
                    units="degreesCelsius",
                )
            ]
        },
    )
    client = make_client(user=_make_user(rol="operador"), transport=transport)
    scan_response = client.post("/devices/scan/bacnet")
    device_id = scan_response.json()[0]["id"]

    response = client.get(f"/devices/{device_id}/candidates")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    candidate = body[0]
    assert set(candidate.keys()) == {
        "id",
        "object_type",
        "object_instance",
        "object_name",
        "present_value",
        "units",
        "discovered_at",
        "updated_at",
    }
    assert candidate["object_type"] == "analogInput"
    assert candidate["present_value"] == "21.5"


def test_list_candidates_de_device_inexistente_404_rfc9457(make_client):
    """RF-009 — `id` inexistente responde 404 `device-not-found`."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.get(f"/devices/{uuid4()}/candidates")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/device-not-found"
    assert body["status"] == 404
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_list_candidates_visor_403(make_client):
    """RF-003 — Visor no puede listar candidatos, ni siquiera de un id inexistente."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.get(f"/devices/{uuid4()}/candidates")

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


# ── POST /devices/scan/modbus (SRV-004-modbus-adapter) ──────────────────────


def test_scan_modbus_admin_200_lista_candidatos_del_escaneo(make_client):
    """RF-001, RF-002 — Admin dispara el escaneo, 200 con los candidatos
    nuevos (contrato exacto de `openapi.yaml`)."""
    modbus_transport = _FakeModbusTransport(
        {
            (ModbusRegisterType.HOLDING_REGISTER, 0, 2): [
                ModbusRegisterReading(
                    register_type=ModbusRegisterType.HOLDING_REGISTER,
                    address=0,
                    value=42,
                ),
                ModbusRegisterReading(
                    register_type=ModbusRegisterType.HOLDING_REGISTER,
                    address=1,
                    value=43,
                ),
            ]
        }
    )
    client = make_client(user=_make_user(rol="admin"), modbus_transport=modbus_transport)

    response = client.post(
        "/devices/scan/modbus",
        json={
            "host": "192.168.1.50",
            "port": 502,
            "unit_id": 1,
            "holding_registers": {"start": 0, "count": 2},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    candidate = body[0]
    assert set(candidate.keys()) == {
        "id",
        "object_type",
        "object_instance",
        "object_name",
        "present_value",
        "units",
        "discovered_at",
        "updated_at",
    }
    assert candidate["object_type"] == "holding_register"


def test_scan_modbus_sin_ninguna_respuesta_200_lista_vacia(make_client):
    """RF-007 — sin ninguna dirección exitosa, 200 con lista vacía (no es error)."""
    client = make_client(user=_make_user(rol="operador"))

    response = client.post(
        "/devices/scan/modbus",
        json={
            "host": "192.168.1.50",
            "port": 502,
            "unit_id": 1,
            "coils": {"start": 0, "count": 1},
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_scan_modbus_visor_403_rfc9457(make_client):
    """RF-003 — Visor no puede disparar el escaneo."""
    client = make_client(user=_make_user(rol="visor"))

    response = client.post(
        "/devices/scan/modbus",
        json={"host": "192.168.1.50", "port": 502, "unit_id": 1},
    )

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/insufficient-role"
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_scan_modbus_rango_mayor_a_125_400_rfc9457(make_client):
    """RF-004 — rango > 125 direcciones responde 400 con el sobre RFC 9457 y
    el slug `modbus-range-too-large`.

    `ModbusRangeIn.count` **no** lleva `Field(le=125)`: si lo llevara,
    Pydantic/FastAPI interceptaría la solicitud con un 422 genérico (sin
    sobre RFC 9457) **antes** de que `scan_modbus` pudiera ejecutar la
    validación de negocio — RF-004 exige explícitamente 400, no 422. El
    `maximum: 125` de `openapi.yaml#/ModbusRegisterRange` es documentación
    del contrato para clientes/tooling; la validación real y única que
    determina la respuesta HTTP es la de `services/device_scan_service.py::
    scan_modbus` (`plan.md §4`: "no se depende únicamente del schema")."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/devices/scan/modbus",
        json={
            "host": "192.168.1.50",
            "port": 502,
            "unit_id": 1,
            "holding_registers": {"start": 0, "count": 126},
        },
    )

    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/modbus-range-too-large"
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_scan_modbus_body_invalido_422(make_client):
    """Defensa en profundidad de forma (`ModbusRangeIn`/schema): un `port`
    fuera de rango es rechazado por FastAPI/Pydantic antes de llegar al
    servicio."""
    client = make_client(user=_make_user(rol="admin"))

    response = client.post(
        "/devices/scan/modbus",
        json={"host": "192.168.1.50", "port": 70000, "unit_id": 1},
    )

    assert response.status_code == 422
