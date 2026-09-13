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
DATABASE_URL="$DATABASE_URL" alembic upgrade head   # aplica 0001_create_users_table (SRV-002-auth-rbac, T-023)
python3 -m pytest -m integration -v

cd ..
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
rm -f .env mosquitto/password_file
```

## Archivos (T-019..T-023, T-024/T-025, T-027)

- `test_adapters.py` — `PostgreSQLAdapter.ping()` y `RedisAdapter.ping()` contra
  Postgres/Redis reales (RF-002, T-019/T-020); `MosquittoAdapter.connect()` con
  credencial inválida contra el broker real, verifica backoff fijo (1s/2s/4s, 4
  intentos totales) sin loop ciego (RF-008, T-021/T-022).
- `test_mqtt_security.py` — cliente MQTT externo (`paho-mqtt` directo, sin pasar
  por el adaptador) sin credenciales, rechazado por el broker real (RF-006,
  `VUL-SRV-001`, T-023).
- `test_user_repository_adapter.py` (`SRV-002-auth-rbac`, T-024/T-025) —
  `PostgreSQLUserRepository.get_by_email/get_by_id/update_role` contra la tabla
  `users` real (requiere `alembic upgrade head` aplicado antes); `email`
  duplicado rechazado por `UNIQUE`; combinaciones inválidas de `scope`/
  `project_id` y `rol` rechazadas por los `CHECK` (RF-001, RF-002, RF-006,
  RF-007, RF-012).
- `test_auth_security.py` (`SRV-002-auth-rbac`, T-027) — seguridad end-to-end
  con Postgres+Redis reales, migración aplicada y el seed (`../../scripts/
  seed_admin_user.py`) corrido antes: fuerza bruta real (RF-014), revocación
  real (RF-010/RF-013), bcrypt+JWT reales de punta a punta (login→acceso
  protegido→refresh→logout), forma RFC 9457 exacta.
