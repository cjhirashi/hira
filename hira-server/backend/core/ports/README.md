# core/ports

Interfaces abstractas (`typing.Protocol`) del patrón Hexagonal (`SRV-ADR-017`).
`services/` importa únicamente de aquí — nunca de `adapters/` directamente.

Puertos previstos para el Walking Skeleton (`AC-SRV-01`, pendientes de implementación
en un batch posterior de `tasks.md`):

- `database_port.py` — `DatabasePort.ping()`.
- `cache_port.py` — `CachePort.ping()`.
- `notification_port.py` — `NotificationPort.ping()` / `.connect()`.
