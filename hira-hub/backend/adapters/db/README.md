# adapters/db

`postgres_adapter.py::PostgresAdapter` — implementa `DatabasePort` contra
PostgreSQL (`SELECT 1`, SQLAlchemy 2.x async + `asyncpg`) — RF-002. Verificado
en `tests/integration/test_adapters.py` contra el contenedor `postgres` real
del compose (`@pytest.mark.integration`).
