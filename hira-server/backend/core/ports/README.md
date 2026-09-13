# core/ports

Interfaces abstractas (`typing.Protocol`) del patrón Hexagonal (`SRV-ADR-017`).
`services/` importa únicamente de aquí — nunca de `adapters/` directamente.

Puertos del Walking Skeleton (`AC-SRV-01`):

- `database_port.py` — `DatabasePort.ping()`.
- `cache_port.py` — `CachePort.ping()`.
- `notification_port.py` — `NotificationPort.ping()` / `.connect()`. `send()` queda
  explícitamente fuera de alcance de este sprint (`plan.md §7`) — sin consumidor real
  todavía.

Implementaciones concretas (`adapters/db/postgresql_adapter.py`,
`adapters/cache/redis_adapter.py`, `adapters/mqtt/mosquitto_adapter.py`) pendientes de
un batch posterior de `tasks.md` (T-019/T-020, T-022).
