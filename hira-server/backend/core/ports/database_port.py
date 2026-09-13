"""`DatabasePort` — interfaz abstracta de persistencia (`Protocol`, `SRV-ADR-017`).

`services/` importa este contrato, nunca una librería concreta (`asyncpg`,
`sqlalchemy`...). La implementación real (`adapters/db/postgresql_adapter.py`,
`SELECT 1`) llega en un batch posterior de `tasks.md` (T-019/T-020) — fuera de
alcance aquí.
"""
from typing import Protocol


class DatabasePort(Protocol):
    """Contrato mínimo de *liveness* contra el backend de persistencia (RF-002)."""

    async def ping(self) -> bool:
        """Retorna `True` si el backend de datos responde correctamente."""
        ...
