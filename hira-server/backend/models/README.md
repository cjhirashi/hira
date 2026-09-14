# models

Modelos de datos — SQLAlchemy **Core** (`Table`, no ORM declarativo), mismo estilo
que `adapters/db/postgresql_adapter.py`; una sola tabla no justifica
`declarative_base()`/`Session` (Anti-Abstraction, `plan.md §0` de `SRV-002-auth-rbac`).

- `base.py` — `metadata` compartida (`SRV-003-bacnet-adapter`, T-010, `plan.md
  §3`/§7): único `MetaData()` del producto, importado por `user_model.py` y
  `device_model.py` — es el `target_metadata` de `../alembic/env.py`.
- `user_model.py` — `users_table` (`SRV-002-auth-rbac`, T-023, `plan.md §3`):
  `id`/`email`/`password_hash`/`rol`/`scope`/`project_id`/`activo`/`created_at`/
  `updated_at`, con los `CHECK` de `rol`, `scope` y la combinación `scope`/
  `project_id`.
- `device_model.py` — `devices_table`/`device_points_candidates_table`
  (`SRV-003-bacnet-adapter`, T-011, `plan.md §3`): dispositivos descubiertos
  (`UNIQUE(protocol, address)`) y sus puntos crudos candidatos (`UNIQUE
  (device_id, object_type, object_instance)`, FK a `devices` `ON DELETE
  CASCADE`) — nunca promovidos a una tabla de puntos operables (`SRV-ADR-012`).

Migraciones: `../alembic/` (primer uso de Alembic en el repo, ver su README).
