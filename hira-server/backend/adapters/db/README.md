# adapters/db

Implementa `DatabasePort` contra PostgreSQL/TimescaleDB (`postgresql_adapter.py`,
`SELECT 1`, SQLAlchemy 2.x async + `asyncpg`) — `tasks.md` T-019/T-020, RF-002.
Verificado con `tests/integration/test_adapters.py` contra el contenedor `postgres`
real del compose.
