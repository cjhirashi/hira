# adapters/db

Implementa `DatabasePort` contra PostgreSQL/TimescaleDB (`postgresql_adapter.py`,
`SELECT 1`, SQLAlchemy 2.x async + `asyncpg`). Pendiente — requiere el contenedor
`postgres` del compose (`tasks.md` T-019/T-020, fuera de este batch).
