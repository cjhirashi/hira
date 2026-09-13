# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `SRV-ADR-017`).
`factory.py` (pendiente, batch posterior) instancia explícitamente cada adaptador —
un solo perfil de despliegue, sin `HIRA_DEPLOY_MODE` (`E-ADR-001`).

- `db/` — `postgresql_adapter.py` implementa `DatabasePort` (PostgreSQL/TimescaleDB).
- `cache/` — `redis_adapter.py` implementa `CachePort`.
- `mqtt/` — `mosquitto_adapter.py` implementa `NotificationPort`.

Todo lo anterior requiere contenedores reales levantados — fuera del alcance de este
batch de tareas (`tasks.md` T-019 en adelante).
