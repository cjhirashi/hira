# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `E-ADR-002`).
`factory.py` es el **único** punto de selección de la implementación concreta —
`services/` y `routers/` nunca instancian un adaptador directamente. Un solo
perfil de despliegue (cloud single-tenant).

- `factory.py` — nació en T-015 con 2 placeholders in-memory (siempre `ok`,
  sin I/O real); T-018/T-019 reemplazó el **cuerpo** (no la firma) para
  instanciar los adaptadores reales de abajo.
- `db/` — `DatabasePort` contra PostgreSQL (`postgres_adapter.py`, `SELECT 1`,
  SQLAlchemy 2.x async + `asyncpg`).
- `cache/` — `CachePort` contra Redis (`redis_adapter.py`, `redis.asyncio`,
  comando `PING`).
