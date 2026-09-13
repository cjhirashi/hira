"""`CachePort` — interfaz abstracta de cache (`Protocol`, `SRV-ADR-017`).

`services/` importa este contrato, nunca una librería concreta (`redis.asyncio`...).
La implementación real (`adapters/cache/redis_adapter.py`, comando `PING`) llega en
un batch posterior de `tasks.md` (T-019/T-020) — fuera de alcance aquí.
"""
from typing import Protocol


class CachePort(Protocol):
    """Contrato mínimo de *liveness* contra el backend de cache (RF-002)."""

    async def ping(self) -> bool:
        """Retorna `True` si el backend de cache responde correctamente."""
        ...
