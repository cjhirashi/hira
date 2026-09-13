# adapters

Implementaciones concretas de los `core/ports/` (patrón Hexagonal, `SRV-ADR-017`).
`factory.py` es el **único** punto de selección de la implementación concreta —
`services/` y `routers/` nunca instancian un adaptador directamente. Un solo perfil
de despliegue, sin `HIRA_DEPLOY_MODE` (`E-ADR-001`).

- `factory.py` — implementado en T-015 con placeholders **in-memory** (siempre
  `ok`), coherentes con los `Protocol` de `core/ports/`. T-020 reemplaza el cuerpo
  de sus funciones para instanciar los adaptadores reales de abajo; la firma no
  cambia, así que `routers/monitor.py` no se toca en ese batch.
- `db/` — `postgresql_adapter.py` implementará `DatabasePort` (PostgreSQL/TimescaleDB).
- `cache/` — `redis_adapter.py` implementará `CachePort`.
- `mqtt/` — `mosquitto_adapter.py` implementará `NotificationPort`.

Los tres adaptadores concretos de arriba requieren contenedores reales levantados —
fuera del alcance de este batch de tareas (`tasks.md` T-019 en adelante).
