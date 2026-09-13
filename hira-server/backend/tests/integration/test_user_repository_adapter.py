"""Integración real — `PostgreSQLUserRepository` contra Postgres real
(`SRV-002-auth-rbac`, T-024/T-025, `plan.md §5`/§6 paso 14).

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres
    cd backend && DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:5432/hiradb \
        alembic upgrade head

Mismo patrón que `test_adapters.py`: variables `TEST_*` con default apuntando a
`localhost` vía los puertos publicados por `docker-compose.dev.yml`. Cada test
trunca la tabla `users` antes de correr (aislamiento — no depende del orden ni
dejan filas de un test anterior).

Cubre: `get_by_email`/`get_by_id`/`update_role` (RF-001, RF-002, RF-006, RF-007,
RF-012); `email` duplicado rechazado por `UNIQUE` (`ck`/`uq_users_email`);
combinaciones inválidas de `scope`/`project_id` rechazadas por
`ck_users_scope_project_id`.
"""
import os
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from models.user_model import users_table

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)


async def _reset_users_table() -> None:
    """Trunca `users` antes de cada test — aislamiento entre tests."""
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(users_table.delete())
    finally:
        await engine.dispose()


async def _insert_user(
    *,
    email: str = "admin@hira.dev",
    password_hash: str = "$2b$12$abcdefghijklmnopqrstuv",
    rol: str = "admin",
    scope: str = "global",
    project_id: str | None = None,
    activo: bool = True,
) -> str:
    """Inserta una fila directamente vía `users_table` (sin pasar por el
    repositorio — el `Protocol` no expone un método de creación, `spec.md §2`).
    Retorna el `id` insertado como `str`."""
    user_id = uuid.uuid4()
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                users_table.insert().values(
                    id=user_id,
                    email=email,
                    password_hash=password_hash,
                    rol=rol,
                    scope=scope,
                    project_id=project_id,
                    activo=activo,
                )
            )
    finally:
        await engine.dispose()
    return str(user_id)


@pytest.fixture(autouse=True)
async def _clean_table():
    await _reset_users_table()
    yield
    await _reset_users_table()


@pytest.mark.asyncio
async def test_get_by_email_returns_matching_user_record():
    """RF-001, RF-002 — `get_by_email` contra Postgres real."""
    from adapters.db.user_repository_adapter import PostgreSQLUserRepository

    user_id = await _insert_user(email="visor@hira.dev", rol="visor", scope="global")
    repo = PostgreSQLUserRepository(DATABASE_URL)
    try:
        record = await repo.get_by_email("visor@hira.dev")
        assert record is not None
        assert record.id == user_id
        assert record.email == "visor@hira.dev"
        assert record.rol == "visor"
        assert record.scope == "global"
        assert record.project_id is None
        assert record.activo is True
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_get_by_email_returns_none_when_not_found():
    from adapters.db.user_repository_adapter import PostgreSQLUserRepository

    repo = PostgreSQLUserRepository(DATABASE_URL)
    try:
        assert await repo.get_by_email("no-existe@hira.dev") is None
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_get_by_id_returns_matching_user_record():
    """RF-007 — `get_by_id` contra Postgres real (cache-miss de `resolve_permissions`)."""
    from adapters.db.user_repository_adapter import PostgreSQLUserRepository

    project_id = str(uuid.uuid4())
    user_id = await _insert_user(
        email="operador@hira.dev",
        rol="operador",
        scope="project",
        project_id=project_id,
    )
    repo = PostgreSQLUserRepository(DATABASE_URL)
    try:
        record = await repo.get_by_id(user_id)
        assert record is not None
        assert record.email == "operador@hira.dev"
        assert record.rol == "operador"
        assert record.scope == "project"
        assert record.project_id == project_id
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found():
    from adapters.db.user_repository_adapter import PostgreSQLUserRepository

    repo = PostgreSQLUserRepository(DATABASE_URL)
    try:
        assert await repo.get_by_id(str(uuid.uuid4())) is None
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_update_role_persists_new_role():
    """RF-006 — `update_role` contra Postgres real; `services/rbac_service.py::
    update_user_role` invoca esto y luego invalida el cache (fuera de este test,
    ya cubierto con dobles en `tests/test_rbac_service.py`)."""
    from adapters.db.user_repository_adapter import PostgreSQLUserRepository

    user_id = await _insert_user(email="promovido@hira.dev", rol="visor", scope="global")
    repo = PostgreSQLUserRepository(DATABASE_URL)
    try:
        await repo.update_role(user_id, "operador")
        record = await repo.get_by_id(user_id)
        assert record is not None
        assert record.rol == "operador"
    finally:
        await repo.close()


@pytest.mark.asyncio
async def test_duplicate_email_rejected_by_unique_constraint():
    """`uq_users_email` — `email` duplicado rechazado por Postgres real."""
    await _insert_user(email="duplicado@hira.dev")
    with pytest.raises(IntegrityError):
        await _insert_user(email="duplicado@hira.dev")


@pytest.mark.asyncio
async def test_scope_global_with_project_id_rejected_by_check_constraint():
    """`ck_users_scope_project_id` — `scope=global` con `project_id` no nulo."""
    with pytest.raises(IntegrityError):
        await _insert_user(scope="global", project_id=str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_scope_project_without_project_id_rejected_by_check_constraint():
    """`ck_users_scope_project_id` — `scope=project` sin `project_id`."""
    with pytest.raises(IntegrityError):
        await _insert_user(scope="project", project_id=None)


@pytest.mark.asyncio
async def test_invalid_rol_rejected_by_check_constraint():
    """`ck_users_rol` — `rol` fuera de {admin, operador, visor}."""
    with pytest.raises(IntegrityError):
        await _insert_user(rol="superadmin")
