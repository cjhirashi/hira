# adapters/db

Implementará `DatabasePort` contra PostgreSQL (`postgres_adapter.py`, `SELECT
1`, SQLAlchemy 2.x async + `asyncpg`) — `tasks.md` T-018/T-019, RF-002. Vacío en
este batch (T-001..T-012); se verificará con `tests/integration/
test_adapters.py` contra el contenedor `postgres` real del compose.
