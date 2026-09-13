"""`RedisAdapter` — implementación real de `CachePort` (RF-002, T-019/T-020;
ampliado en `SRV-002-auth-rbac`, T-010/T-011, `plan.md §2`; T-032/T-033,
`plan.md §10`, resolución de RNF-001).

Usa `redis.asyncio` (cliente async oficial de `redis-py`). `ping()` ejecuta el
comando `PING`; el timeout de 2s (RNF-002) lo aplica quien llama
(`services/health_service.py::_ping_with_timeout`, `asyncio.wait_for`) — este
adaptador no impone uno propio. Los métodos de cache real (`get`/`set`/`incr`/
`expire`/`delete`) sirven a `services/auth_service.py` (RF-001, RF-002, RF-010,
RF-011, RF-013, RF-014) y `services/rbac_service.py` (RF-006, RF-007).
`publish`/`subscribe` (T-032/T-033) usan `client.publish(...)`/`client.pubsub()`
reales — sirven a `services/rbac_service.py::update_user_role`/
`run_invalidation_subscriber` (RNF-001).

Solo `adapters/*` puede importar `redis` — `services/` sigue importando únicamente
`core/ports/cache_port.py` (`SRV-ADR-017`).
"""
from typing import AsyncIterator

import redis.asyncio as redis


class RedisAdapter:
    """Implementa `CachePort` contra un Redis real."""

    def __init__(self, redis_url: str) -> None:
        self._client: redis.Redis = redis.from_url(redis_url)

    async def ping(self) -> bool:
        """RF-002 — comando `PING` real contra Redis."""
        return bool(await self._client.ping())

    async def get(self, key: str) -> str | None:
        """`GET key` — decodificado a `str` (el cliente se crea sin
        `decode_responses`, se decodifica aquí para no filtrar `bytes` a `services/`)."""
        value = await self._client.get(key)
        return value.decode("utf-8") if value is not None else None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """`SET key value [EX ttl_seconds]`."""
        await self._client.set(key, value, ex=ttl_seconds)

    async def incr(self, key: str) -> int:
        """`INCR key` — Redis la crea en 0 y la incrementa si no existía."""
        return int(await self._client.incr(key))

    async def expire(self, key: str, ttl_seconds: int) -> None:
        """`EXPIRE key ttl_seconds`."""
        await self._client.expire(key, ttl_seconds)

    async def delete(self, key: str) -> None:
        """`DEL key` — idempotente, `redis-py` no falla si `key` no existe."""
        await self._client.delete(key)

    async def publish(self, channel: str, message: str) -> None:
        """`PUBLISH channel message` — *best-effort*, sin persistencia si nadie
        está suscrito en el momento de publicar (RNF-001, `plan.md §10`)."""
        await self._client.publish(channel, message)

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        """`SUBSCRIBE channel` real vía `client.pubsub()`/`listen()` — generador
        asíncrono, no se `await`ea (se consume con `async for`). Se desuscribe y
        cierra el `pubsub` propio al salir (normal o por cancelación)."""
        pubsub = self._client.pubsub()
        await pubsub.subscribe(channel)
        try:
            async for item in pubsub.listen():
                if item["type"] != "message":
                    continue
                data = item["data"]
                yield data.decode("utf-8") if isinstance(data, bytes) else data
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    async def close(self) -> None:
        """Cierra la conexión — usado en tests de integración y shutdown."""
        await self._client.aclose()
