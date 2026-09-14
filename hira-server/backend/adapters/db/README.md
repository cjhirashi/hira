# adapters/db

Implementa `DatabasePort` contra PostgreSQL/TimescaleDB (`postgresql_adapter.py`,
`SELECT 1`, SQLAlchemy 2.x async + `asyncpg`) — `tasks.md` T-019/T-020, RF-002.
Verificado con `tests/integration/test_adapters.py` contra el contenedor `postgres`
real del compose.

`user_repository_adapter.py::PostgreSQLUserRepository` (`SRV-002-auth-rbac`,
T-024/T-025) implementa `UserRepositoryPort` (`get_by_email`/`get_by_id`/
`update_role`) contra la tabla `users` (`models/user_model.py`) — mismo estilo
SQLAlchemy Core (`select`/`update`, `AsyncEngine` propio), sin ORM declarativo.
Verificado con `tests/integration/test_user_repository_adapter.py` (requiere
`alembic upgrade head` aplicado) — RF-001, RF-002, RF-006, RF-007, RF-012.

`device_repository_adapter.py::PostgreSQLDeviceRepository`
(`SRV-003-bacnet-adapter`, T-015/T-016) implementa `DeviceRepositoryPort`
(`upsert_device`/`list_devices`/`get_device`/`upsert_candidate`/
`list_candidates_for_device`) contra `devices`/`device_points_candidates`
(`models/device_model.py`) — `INSERT ... ON CONFLICT DO UPDATE` nativo de
PostgreSQL para los `upsert_*` (único por `(protocol, address)`/`(device_id,
object_type, object_instance)`, un segundo escaneo actualiza, no duplica).
Verificado con `tests/integration/test_device_repository_adapter.py` (requiere
`alembic upgrade head` con la migración `0002` aplicada) — RF-002, RF-004,
RF-005, RF-009.
