# tests/integration

Pruebas de integración contra los contenedores reales del compose (Postgres, Redis,
Mosquitto) — `@pytest.mark.integration`, requieren `docker compose up` previo.

## Cómo correrlas

```bash
cd hira-server
cp .env.example .env   # o valores propios; nunca commitear .env
set -a && source .env && set +a
./mosquitto/generate_password_file.sh
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis mosquitto

cd backend
python3 -m pytest -m integration -v

cd ..
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
rm -f .env mosquitto/password_file
```

## Archivos (T-019..T-023)

- `test_adapters.py` — `PostgreSQLAdapter.ping()` y `RedisAdapter.ping()` contra
  Postgres/Redis reales (RF-002, T-019/T-020); `MosquittoAdapter.connect()` con
  credencial inválida contra el broker real, verifica backoff fijo (1s/2s/4s, 4
  intentos totales) sin loop ciego (RF-008, T-021/T-022).
- `test_mqtt_security.py` — cliente MQTT externo (`paho-mqtt` directo, sin pasar
  por el adaptador) sin credenciales, rechazado por el broker real (RF-006,
  `VUL-SRV-001`, T-023).
