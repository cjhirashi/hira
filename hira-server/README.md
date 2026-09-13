# hira-server

Núcleo SCADA de Hira — **local / on-premise, con instalador** (Docker Compose).
Se reimplementa desde cero bajo el harness SDD-Anchored.

- Instrucciones de trabajo: [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) (generados).
- Especificación: [`../docs/hira-server/spec/`](../docs/hira-server/spec/).
- Decisiones: [`../docs/hira-server/decisions/`](../docs/hira-server/decisions/).
- Feature activa: [`../.harness/specs/SRV-001-walking-skeleton/`](../.harness/specs/SRV-001-walking-skeleton/).
- Contratos con Hub y Studio: [`../docs/contracts/`](../docs/contracts/).
- Sprint legacy (pre-reestructuración del arnés, superseded): [`../docs/planning/SPRINT.md`](../docs/planning/SPRINT.md).

> El código de la implementación previa está en la rama `legacy/hira-server-snapshot`
> (ver [`../docs/legacy/README.md`](../docs/legacy/README.md)).

Arranca por `SRV-001-walking-skeleton` (Walking Skeleton).

## Operación — migraciones (Alembic)

Las migraciones de base de datos **no se ejecutan automáticamente** al arrancar el
contenedor `backend` (evita condiciones de carrera si en el futuro hay más de una
réplica). Aplícalas a mano, **antes de levantar tráfico**:

```bash
docker compose exec backend alembic upgrade head
```
