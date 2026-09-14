"""`RedisAdapter`/`adapters/factory.py::get_cache_port` — wiring de la
password (RF-002).

Corrección post-revisión: el Redis del compose exige password
(`--requirepass ${REDIS_PASSWORD}`, `docker-compose.yml`), pero
`RedisAdapter` construía el cliente solo con `redis_url`
(`redis://redis:6379/0`, sin credenciales) y nunca leía
`Settings().redis_password` — campo con validación en `Settings` pero sin
consumidor real. Resultado: `PING` fallaba con `AuthenticationError` contra
un Redis real y sano, y `GET /health` reportaba `redis: error` (falso
negativo, viola RF-002).

Este test no depende de un contenedor real (a diferencia de
`tests/integration/test_adapters.py`) — verifica en aislamiento que la
password efectivamente viaja hasta `redis.asyncio.from_url`, así una
regresión de wiring se detecta sin Docker.
"""
from unittest.mock import patch

import pytest


def test_redis_adapter_passes_password_to_client():
    """RF-002 — `RedisAdapter` combina `redis_url` + `redis_password` reales."""
    from adapters.cache.redis_adapter import RedisAdapter

    with patch("adapters.cache.redis_adapter.redis.from_url") as mock_from_url:
        RedisAdapter("redis://redis:6379/0", "s3cret-pass")

    mock_from_url.assert_called_once_with(
        "redis://redis:6379/0", password="s3cret-pass"
    )


def test_factory_get_cache_port_reads_password_from_settings(monkeypatch):
    """RF-002 — `get_cache_port()` no deja `Settings().redis_password` sin
    consumidor: debe llegar hasta el `RedisAdapter` real."""
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://hub:hub@postgres:5432/hubdb")
    monkeypatch.setenv("POSTGRES_USER", "hub")
    monkeypatch.setenv("POSTGRES_PASSWORD", "hub")
    monkeypatch.setenv("POSTGRES_DB", "hubdb")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("REDIS_PASSWORD", "factory-pass")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("LOG_LEVEL", "INFO")

    import adapters.factory as factory

    factory._cache_port = None
    try:
        with patch("adapters.cache.redis_adapter.redis.from_url") as mock_from_url:
            factory.get_cache_port()

        mock_from_url.assert_called_once_with(
            "redis://redis:6379/0", password="factory-pass"
        )
    finally:
        factory._cache_port = None
