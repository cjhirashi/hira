# tests/integration

Pruebas de integración contra los contenedores reales del compose (Postgres,
Redis — sin Mosquitto, `HUB-ADR-01`) — `@pytest.mark.integration`, requieren
`docker compose up` previo.

Vacío en este batch (T-001..T-012): `test_adapters.py` nace en un batch
posterior (`tasks.md` T-018), una vez exista `hira-hub/docker-compose.yml`
(T-016/T-017).
