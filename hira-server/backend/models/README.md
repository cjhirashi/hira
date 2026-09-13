# models

Modelos de datos — SQLAlchemy **Core** (`Table`, no ORM declarativo), mismo estilo
que `adapters/db/postgresql_adapter.py`; una sola tabla no justifica
`declarative_base()`/`Session` (Anti-Abstraction, `plan.md §0` de `SRV-002-auth-rbac`).

- `user_model.py` — `users_table` (`SRV-002-auth-rbac`, T-023, `plan.md §3`):
  `id`/`email`/`password_hash`/`rol`/`scope`/`project_id`/`activo`/`created_at`/
  `updated_at`, con los `CHECK` de `rol`, `scope` y la combinación `scope`/
  `project_id`. `metadata` es el `target_metadata` de `../alembic/env.py`.

Migraciones: `../alembic/` (primer uso de Alembic en el repo, ver su README).
