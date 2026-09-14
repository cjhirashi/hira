# tests/integration

Pruebas de integración contra los contenedores reales del compose (Postgres,
Redis — sin Mosquitto, `HUB-ADR-01`) — `@pytest.mark.integration`, requieren
`docker compose up` previo.

- `test_adapters.py` — `PostgresAdapter.ping()`/`RedisAdapter.ping()` contra
  `postgres`/`redis` reales (RF-002). Ejecutar:

  ```bash
  cd hira-hub
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
  cd backend
  TEST_DATABASE_URL=postgresql+asyncpg://hub:changeme@localhost:5432/hubdb \
  TEST_REDIS_URL=redis://:changeme@localhost:6379/0 \
  pytest -m integration
  ```
