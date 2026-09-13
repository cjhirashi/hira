# scripts

Scripts standalone del backend, fuera del ciclo HTTP normal (`main.py`).

- `seed_admin_user.py` (`SRV-002-auth-rbac`, T-026) — único mecanismo de
  creación de usuarios de este sprint (`spec.md §2`: sin CRUD). Idempotente: si
  `SEED_ADMIN_EMAIL` ya existe en `users`, no falla ni sobreescribe. Lee
  `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` (`.env.example`, sin valores reales),
  hashea con `core/security/passwords.py::hash_password` (bcrypt factor 12)
  antes de insertar — el password en claro nunca se persiste. Usuario sembrado:
  `rol=admin`, `scope=global`, `project_id=None`.

  Uso (dentro del contenedor `backend`, `.env` real ya cargado):

  ```bash
  docker compose exec backend python -m scripts.seed_admin_user
  ```

  Requiere que la migración `0001_create_users_table` ya esté aplicada
  (`../alembic/README.md`).
