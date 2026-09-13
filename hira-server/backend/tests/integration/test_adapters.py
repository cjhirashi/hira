"""Integración real — Postgres/Redis (T-019/T-020, RF-002) y backoff de Mosquitto
(T-021/T-022, RF-008) contra los contenedores reales del compose.

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d \
        postgres redis mosquitto

con un `.env` de prueba (no committeado) cuyas credenciales coincidan con las
variables `TEST_*` de abajo (por defecto, las mismas de `.env.example`, apuntando
a `localhost` vía los puertos publicados por `docker-compose.dev.yml`).

Los adaptadores no dependen de `core.config.Settings` (que exige el set completo
de variables del backend) — reciben la cadena de conexión/host directamente, así
el test puede apuntar a `localhost` sin tener que simular el entorno completo del
contenedor `backend`.
"""
import os
import time

import pytest

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/0")
MQTT_HOST = os.environ.get("TEST_MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("TEST_MQTT_PORT", "1883"))
MQTT_USER = os.environ.get("TEST_MQTT_USER", "hira")


@pytest.mark.asyncio
async def test_postgresql_adapter_ping_against_real_container():
    """RF-002 — `DatabasePort.ping()` real: `SELECT 1` contra Postgres/TimescaleDB."""
    from adapters.db.postgresql_adapter import PostgreSQLAdapter

    adapter = PostgreSQLAdapter(DATABASE_URL)
    try:
        assert await adapter.ping() is True
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_redis_adapter_ping_against_real_container():
    """RF-002 — `CachePort.ping()` real: comando `PING` contra Redis."""
    from adapters.cache.redis_adapter import RedisAdapter

    adapter = RedisAdapter(REDIS_URL)
    try:
        assert await adapter.ping() is True
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_mosquitto_adapter_connect_with_invalid_credentials_gives_up_with_fixed_backoff(
    caplog,
):
    """RF-008 — credencial inválida contra el broker real: `connect()` no reintenta
    indefinidamente. Backoff fijo (1s -> 2s -> 4s, 3 reintentos tras el intento
    inicial = 4 intentos totales) y luego se rinde sin lanzar excepción. Se
    verifica el tiempo total (~7s, nunca un loop ciego) y que cada fallo se
    registra en `level: error`.
    """
    import logging

    from adapters.mqtt.mosquitto_adapter import MosquittoAdapter

    adapter = MosquittoAdapter(
        host=MQTT_HOST,
        port=MQTT_PORT,
        user=MQTT_USER,
        password="credencial-invalida-a-proposito",
    )

    with caplog.at_level(logging.ERROR, logger="hira.adapters.mqtt.mosquitto_adapter"):
        start = time.monotonic()
        await adapter.connect()
        elapsed = time.monotonic() - start

    assert adapter.is_connected is False
    # 1s + 2s + 4s = 7s de espera acumulada; margen para el propio round-trip MQTT.
    assert 6.5 <= elapsed < 20.0, f"tiempo de backoff inesperado: {elapsed}s (se esperaba ~7s)"

    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 4, (
        f"se esperaban 4 fallos registrados (1 intento inicial + 3 reintentos), "
        f"se registraron {len(error_records)}"
    )
