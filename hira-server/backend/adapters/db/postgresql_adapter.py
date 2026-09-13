"""`PostgreSQLAdapter` — implementación real de `DatabasePort` (RF-002, T-019/T-020).

Motor async de SQLAlchemy 2.x + `asyncpg` como driver, coherente con el formato
`postgresql+asyncpg://...` ya fijado en `.env.example`/`core/config.py::Settings`.
`ping()` ejecuta `SELECT 1`; el timeout de 2s (RNF-002) lo aplica quien llama
(`services/health_service.py::_ping_with_timeout`, `asyncio.wait_for`) — este
adaptador no impone uno propio.

Solo `adapters/*` puede importar `sqlalchemy`/`asyncpg` — `services/` sigue
importando únicamente `core/ports/database_port.py` (`SRV-ADR-017`).
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class PostgreSQLAdapter:
    """Implementa `DatabasePort` contra un PostgreSQL/TimescaleDB real."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, pool_pre_ping=True)

    async def ping(self) -> bool:
        """RF-002 — `SELECT 1` real contra Postgres."""
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True

    async def close(self) -> None:
        """Libera el pool de conexiones — usado en tests de integración y shutdown."""
        await self._engine.dispose()
