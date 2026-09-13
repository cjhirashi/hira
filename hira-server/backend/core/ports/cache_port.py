"""`CachePort` — interfaz abstracta de cache (`Protocol`, `SRV-ADR-017`).

`services/` importa este contrato, nunca una librería concreta (`redis.asyncio`...).
La implementación real (`adapters/cache/redis_adapter.py`) implementa tanto el
contrato de *liveness* de `SRV-001` (`ping()`) como el de cache real ampliado en
`SRV-002-auth-rbac` (T-010/T-011, `plan.md §2`, Nota de ampliación de
`CachePort`/`RedisAdapter`): `get`/`set`/`incr`/`expire`/`delete`, usados por
`services/auth_service.py` (RF-001, RF-002, RF-010, RF-011, RF-013, RF-014) y
`services/rbac_service.py` (RF-006, RF-007).

Segunda ampliación (T-032/T-033, `plan.md §10`, resolución de RNF-001):
`publish(channel, message)`/`subscribe(channel) -> AsyncIterator[str]` —
`services/rbac_service.py::update_user_role`/`run_invalidation_subscriber` los
usan para propagar la invalidación de `LocalPermissionsCache` (caché en memoria
del proceso) a otros procesos/réplicas del backend, sin depender de un puerto
nuevo (Registro de decisiones de `plan.md`: Pub/Sub es acceso a Redis, mismo
propósito del puerto).
"""
from typing import AsyncIterator, Protocol, runtime_checkable


@runtime_checkable
class CachePort(Protocol):
    """Contrato de *liveness* (RF-002, `SRV-001`) + cache real (`SRV-002-auth-rbac`)
    + pub/sub de invalidación (RNF-001, `plan.md §10`)."""

    async def ping(self) -> bool:
        """Retorna `True` si el backend de cache responde correctamente."""
        ...

    async def get(self, key: str) -> str | None:
        """Retorna el valor de `key`, o `None` si no existe."""
        ...

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        """Escribe `key`/`value`; si `ttl_seconds` se da, expira tras ese tiempo."""
        ...

    async def incr(self, key: str) -> int:
        """Incrementa `key` en 1 (créala en 0 si no existe) y retorna el nuevo valor."""
        ...

    async def expire(self, key: str, ttl_seconds: int) -> None:
        """Fija (o reemplaza) el TTL de `key`."""
        ...

    async def delete(self, key: str) -> None:
        """Elimina `key`. Idempotente — no falla si `key` no existe."""
        ...

    async def publish(self, channel: str, message: str) -> None:
        """Publica `message` en `channel` — entregado *best-effort* a quien esté
        suscrito en ese momento (sin persistencia si nadie escucha)."""
        ...

    def subscribe(self, channel: str) -> AsyncIterator[str]:
        """Retorna un iterador asíncrono de los mensajes publicados en `channel`
        (`async for mensaje in cache.subscribe(...)`). No se `await`ea — la
        implementación real es un generador asíncrono (`yield` por mensaje)."""
        ...
