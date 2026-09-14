"""Integración real — `PostgreSQLDeviceRepository` contra Postgres real
(`SRV-003-bacnet-adapter`, T-015/T-016, `plan.md §5`/§6 paso 11).

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres
    cd backend && DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:5432/hiradb \
        alembic upgrade head   # aplica 0001 y 0002

Mismo patrón que `tests/integration/test_user_repository_adapter.py`: variable
`TEST_DATABASE_URL` con default apuntando a `localhost` vía los puertos
publicados por `docker-compose.dev.yml`. Cada test trunca `devices`/
`device_points_candidates` antes de correr (aislamiento).

Cubre: `upsert_device`/`list_devices`/`get_device`/`upsert_candidate`/
`list_candidates_for_device` (RF-002, RF-004, RF-005, RF-009); un segundo
`upsert_device` con el mismo `(protocol, address)` actualiza (`last_seen_at`),
no duplica — mismo criterio para `upsert_candidate` por `(device_id,
object_type, object_instance)`.
"""
import os

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from adapters.db.device_repository_adapter import PostgreSQLDeviceRepository
from models.device_model import device_points_candidates_table, devices_table

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)


async def _reset_tables() -> None:
    """Trunca `device_points_candidates`/`devices` antes de cada test — el
    orden respeta la FK (candidatos primero)."""
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(device_points_candidates_table.delete())
            await connection.execute(devices_table.delete())
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
async def _clean_tables():
    await _reset_tables()
    yield
    await _reset_tables()


@pytest.fixture
async def repository():
    repo = PostgreSQLDeviceRepository(DATABASE_URL)
    yield repo
    await repo.close()


@pytest.mark.asyncio
async def test_upsert_device_creates_new_device(repository):
    """RF-002 — `upsert_device` crea un dispositivo nuevo con `last_seen_at`."""
    device = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )

    assert device.id
    assert device.name == "BACnet 1234"
    assert device.protocol == "bacnet"
    assert device.address == "1234@192.168.1.50:47808"
    assert device.is_simulator is False
    assert device.last_seen_at is not None


@pytest.mark.asyncio
async def test_upsert_device_same_protocol_address_updates_not_duplicates(repository):
    """RF-002 — un segundo escaneo del mismo `(protocol, address)` actualiza
    (refresca `last_seen_at`), no duplica."""
    first = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )
    second = await repository.upsert_device(
        name="BACnet 1234 (renamed)",
        protocol="bacnet",
        address="1234@192.168.1.50:47808",
    )

    assert second.id == first.id
    assert second.name == "BACnet 1234 (renamed)"

    devices = await repository.list_devices()
    assert len(devices) == 1


@pytest.mark.asyncio
async def test_list_devices_reflects_persisted_devices(repository):
    """RF-004."""
    await repository.upsert_device(
        name="BACnet 1", protocol="bacnet", address="1@10.0.0.1:47808"
    )
    await repository.upsert_device(
        name="BACnet 2", protocol="bacnet", address="2@10.0.0.2:47808"
    )

    devices = await repository.list_devices()

    assert {d.address for d in devices} == {"1@10.0.0.1:47808", "2@10.0.0.2:47808"}


@pytest.mark.asyncio
async def test_get_device_returns_none_if_not_found(repository):
    """RF-009 — `None` si no existe (el router responde 404)."""
    import uuid

    result = await repository.get_device(str(uuid.uuid4()))

    assert result is None


@pytest.mark.asyncio
async def test_get_device_returns_the_persisted_device(repository):
    device = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )

    fetched = await repository.get_device(device.id)

    assert fetched is not None
    assert fetched.id == device.id
    assert fetched.address == device.address


@pytest.mark.asyncio
async def test_upsert_candidate_creates_and_lists(repository):
    """RF-002, RF-005."""
    device = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )

    candidate = await repository.upsert_candidate(
        device_id=device.id,
        object_type="analog-value",
        object_instance=1,
        object_name="Zone Temperature",
        present_value="21.5",
        units="degrees-celsius",
    )

    assert candidate.device_id == device.id
    assert candidate.object_type == "analog-value"
    assert candidate.object_instance == 1

    candidates = await repository.list_candidates_for_device(device.id)
    assert len(candidates) == 1
    assert candidates[0].id == candidate.id


@pytest.mark.asyncio
async def test_upsert_candidate_same_key_updates_not_duplicates(repository):
    """RF-002 — un segundo escaneo del mismo `(device_id, object_type,
    object_instance)` actualiza `present_value`/`updated_at`, no duplica."""
    device = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )

    first = await repository.upsert_candidate(
        device_id=device.id,
        object_type="analog-value",
        object_instance=1,
        object_name="Zone Temperature",
        present_value="21.5",
        units="degrees-celsius",
    )
    second = await repository.upsert_candidate(
        device_id=device.id,
        object_type="analog-value",
        object_instance=1,
        object_name="Zone Temperature",
        present_value="22.0",
        units="degrees-celsius",
    )

    assert second.id == first.id
    assert second.present_value == "22.0"

    candidates = await repository.list_candidates_for_device(device.id)
    assert len(candidates) == 1


@pytest.mark.asyncio
async def test_list_candidates_for_device_empty_when_none(repository):
    device = await repository.upsert_device(
        name="BACnet 1234", protocol="bacnet", address="1234@192.168.1.50:47808"
    )

    candidates = await repository.list_candidates_for_device(device.id)

    assert candidates == []
