# alembic

Migraciones de esquema — primer uso de Alembic en el repo (`SRV-002-auth-rbac`,
T-023, `plan.md §3`). Plantilla **async** (`env.py`), reutiliza `asyncpg` (ya en
`requirements.txt`, mismo driver que `adapters/db/postgresql_adapter.py`) — sin
añadir un driver síncrono nuevo solo para migrar.

- `env.py` — `target_metadata` = `models/user_model.py::metadata`. La URL de
  conexión se toma de la variable de entorno `DATABASE_URL` (nunca de un valor
  commiteado en `../alembic.ini`).
- `versions/0001_create_users_table.py` — escrita a mano (no autogenerada): crea
  la tabla `users` con sus `CHECK` (`rol`, `scope`, combinación `scope`/
  `project_id`).

## Cómo aplicar la migración

```bash
cd hira-server/backend
export DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:5432/hiradb
alembic upgrade head
```

En producción (dentro del compose): `docker compose exec backend alembic upgrade
head` — paso operativo explícito, **no** se ejecuta automáticamente en el
arranque del contenedor (evita condiciones de carrera con múltiples réplicas;
ver `../README.md`).
