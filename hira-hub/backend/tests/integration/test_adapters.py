"""Integración real — Postgres/Redis (T-018/T-019, RF-002) contra los
contenedores reales del compose.

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-hub
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d \
        postgres redis

con un `.env` de prueba (no committeado) cuyas credenciales coincidan con las
variables `TEST_*` de abajo (por defecto, las mismas de `.env.example`,
apuntando a `localhost` vía los puertos publicados por
`docker-compose.dev.yml`).

Los adaptadores no dependen de `core.config.Settings` (que exige el set
completo de variables del backend) — reciben la cadena de conexión
directamente, así el test puede apuntar a `localhost` sin tener que simular
el entorno completo del contenedor `backend`.

**Corrección post-revisión:** los defaults de abajo (`TEST_REDIS_URL`/
`TEST_REDIS_PASSWORD`) deben ser la **misma fuente de verdad** que
`.env.example`/`docker-compose.yml` reales — antes, `TEST_REDIS_URL` traía
la password embebida (`redis://:changeme@...`), distinto de cómo
`RedisAdapter`/`adapters/factory.py` arman la conexión en producción
(`REDIS_URL` sin credenciales + `REDIS_PASSWORD` aparte). Ese desvío dejaba
pasar en verde un `RedisAdapter` que en producción real se conectaba sin
password y fallaba `PING` con `AuthenticationError` (`redis: error` falso en
`/health`). Ahora el test arma la llamada igual que `factory.py::
get_cache_port()`: URL sin credenciales + password explícita, ambas leídas
con los mismos valores de `.env.example`.

A diferencia de `hira-server`: sin Mosquitto — solo 2 adaptadores
(`HUB-ADR-01`).
"""
import os

import pytest

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hub:changeme@localhost:5432/hubdb"
)
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/0")
REDIS_PASSWORD = os.environ.get("TEST_REDIS_PASSWORD", "changeme")


@pytest.mark.asyncio
async def test_postgres_adapter_ping_against_real_container():
    """RF-002 — `DatabasePort.ping()` real: `SELECT 1` contra Postgres."""
    from adapters.db.postgres_adapter import PostgresAdapter

    adapter = PostgresAdapter(DATABASE_URL)
    try:
        assert await adapter.ping() is True
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_redis_adapter_ping_against_real_container():
    """RF-002 — `CachePort.ping()` real: comando `PING` contra Redis."""
    from adapters.cache.redis_adapter import RedisAdapter

    adapter = RedisAdapter(REDIS_URL, REDIS_PASSWORD)
    try:
        assert await adapter.ping() is True
    finally:
        await adapter.close()
