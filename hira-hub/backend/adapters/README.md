# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `E-ADR-002`).
`factory.py` es el **único** punto de selección de la implementación concreta —
`services/` y `routers/` nunca instancian un adaptador directamente. Un solo
perfil de despliegue (cloud single-tenant).

Vacío en este batch (T-001..T-012): `factory.py` nace en un batch posterior
(`tasks.md` T-015) con 2 funciones placeholder in-memory, antes de que existan
los adaptadores reales de abajo.

- `db/` — implementará `DatabasePort` contra PostgreSQL (`postgres_adapter.py`,
  `SELECT 1`, SQLAlchemy 2.x async + `asyncpg`) — T-018/T-019.
- `cache/` — implementará `CachePort` contra Redis (`redis_adapter.py`,
  `redis.asyncio`, comando `PING`) — T-018/T-019.
