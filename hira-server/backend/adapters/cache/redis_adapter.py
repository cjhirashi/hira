"""`RedisAdapter` — implementación real de `CachePort` (RF-002, T-019/T-020).

Usa `redis.asyncio` (cliente async oficial de `redis-py`). `ping()` ejecuta el
comando `PING`; el timeout de 2s (RNF-002) lo aplica quien llama
(`services/health_service.py::_ping_with_timeout`, `asyncio.wait_for`) — este
adaptador no impone uno propio.

Solo `adapters/*` puede importar `redis` — `services/` sigue importando únicamente
`core/ports/cache_port.py` (`SRV-ADR-017`).
"""
import redis.asyncio as redis


class RedisAdapter:
    """Implementa `CachePort` contra un Redis real."""

    def __init__(self, redis_url: str) -> None:
        self._client: redis.Redis = redis.from_url(redis_url)

    async def ping(self) -> bool:
        """RF-002 — comando `PING` real contra Redis."""
        return bool(await self._client.ping())

    async def close(self) -> None:
        """Cierra la conexión — usado en tests de integración y shutdown."""
        await self._client.aclose()
