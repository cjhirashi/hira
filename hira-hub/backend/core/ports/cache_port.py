"""`CachePort` — interfaz abstracta de cache (`Protocol`, `E-ADR-002`).

`services/` importa este contrato, nunca una librería concreta
(`redis.asyncio`...). La implementación real (`adapters/cache/redis_adapter.py`)
llega en un batch posterior de `tasks.md` (T-018/T-019) — fuera de alcance
aquí.

Sin métodos de negocio (`get`/`set`/`incr`/`expire`/`delete`) todavía —
ningún caso de uso de este sprint los necesita (Constitución Art. 10, no
anticipar). Se amplían cuando exista un caso de uso real que los consuma
(H1/H2: rate-limiting de `/api/licenses/validate`).
"""
from typing import Protocol


class CachePort(Protocol):
    """Contrato mínimo de *liveness* contra el backend de cache (RF-002)."""

    async def ping(self) -> bool:
        """Retorna `True` si el backend de cache responde correctamente."""
        ...
