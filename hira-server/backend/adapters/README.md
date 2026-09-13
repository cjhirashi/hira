# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `SRV-ADR-017`).
`factory.py` es el **único** punto de selección de la implementación concreta —
`services/` y `routers/` nunca instancian un adaptador directamente. Un solo perfil
de despliegue, sin `HIRA_DEPLOY_MODE` (`E-ADR-001`).

- `factory.py` — nació en T-015 con placeholders **in-memory** (siempre `ok`),
  coherentes con los `Protocol` de `core/ports/`. T-019/T-020 reemplazó el
  **cuerpo** de sus 3 funciones para instanciar los adaptadores reales de abajo
  (singleton perezoso por proceso); la firma no cambió, `routers/monitor.py` no
  se tocó en ese batch.
- `db/` — `postgresql_adapter.py` implementa `DatabasePort` (PostgreSQL/TimescaleDB,
  SQLAlchemy 2.x async + `asyncpg`, `SELECT 1`).
- `cache/` — `redis_adapter.py` implementa `CachePort` (`redis.asyncio`, `PING`).
- `mqtt/` — `mosquitto_adapter.py` implementa `NotificationPort` (`paho-mqtt`,
  backoff fijo 1s/2s/4s sin loop ciego en `connect()` — RF-008).

Los tres adaptadores concretos de arriba están verificados con
`tests/integration/test_adapters.py` y `tests/integration/test_mqtt_security.py`
contra los contenedores reales del compose (`tasks.md` T-019..T-023).
