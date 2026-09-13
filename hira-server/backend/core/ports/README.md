# core/ports

Interfaces abstractas (`typing.Protocol`) del patrón Hexagonal (`SRV-ADR-017`).
`services/` importa únicamente de aquí — nunca de `adapters/` directamente.

Puertos del Walking Skeleton (`AC-SRV-01`):

- `database_port.py` — `DatabasePort.ping()`.
- `cache_port.py` — `CachePort.ping()` (*liveness*) + `get`/`set`/`incr`/`expire`/
  `delete` (ampliado en `SRV-002-auth-rbac`, T-010/T-011 — cache real, no solo
  *liveness*; `RF-006, RF-007, RF-010, RF-011, RF-013, RF-014`).
- `notification_port.py` — `NotificationPort.ping()` / `.connect()`. `send()` queda
  explícitamente fuera de alcance de este sprint (`plan.md §7`) — sin consumidor real
  todavía.

Puertos de `SRV-002-auth-rbac`:

- `user_repository_port.py` — `UserRepositoryPort` (`get_by_email`, `get_by_id`,
  `update_role`) + `UserRecord` (dataclass). Repositorio de dominio de usuarios,
  distinto de `DatabasePort` (*liveness*-only, sin tocar su contrato) — decisión
  registrada en `plan.md §2`/Registro de decisiones (T-009). Sin test propio,
  igual que `database_port.py`.

Implementaciones concretas (`adapters/db/postgresql_adapter.py`,
`adapters/cache/redis_adapter.py`, `adapters/mqtt/mosquitto_adapter.py`,
`adapters/db/user_repository_adapter.py`) pendientes de batches posteriores de
`tasks.md` (T-019/T-020, T-022 para el Walking Skeleton; T-024/T-025 para
`UserRepositoryPort`).
