"""`alembic/env.py` — plantilla async (`SRV-002-auth-rbac`, T-023, `plan.md §3`).

Reutiliza `asyncpg` (ya en `requirements.txt`, mismo driver que
`adapters/db/postgresql_adapter.py`) — sin añadir un driver síncrono nuevo solo
para migrar. `target_metadata` = `models/user_model.py::metadata` (SQLAlchemy
Core `Table`, no ORM declarativo).

La URL de conexión se toma de la variable de entorno `DATABASE_URL` (mismo
formato `postgresql+asyncpg://...` que `core/config.py::Settings.database_url`)
en vez de un valor commiteado en `alembic.ini` — nunca un secreto en un
artefacto versionado. Se usa `os.environ` directo, no `Settings()`: `Settings()`
exige el set completo de variables del backend (Redis, MQTT, `SECRET_KEY`...),
que no son necesarias para migrar el esquema.
"""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from models.user_model import metadata as user_model_metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# `models/user_model.py::metadata` — primera (y única, en este sprint) tabla de
# negocio del producto (`users`).
target_metadata = user_model_metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Crea un `AsyncEngine` y asocia una conexión con el contexto de Alembic."""

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
