# backend

API de Hira Server (FastAPI). Arquitectura Hexagonal — `core/ports/` define las
interfaces, `adapters/` las implementa, `services/` orquesta usando solo `core/ports/`
(nunca importa `adapters/` directamente). Ver `SRV-ADR-017`.

Feature activa: `.harness/specs/SRV-001-walking-skeleton/` (Walking Skeleton — `AC-SRV-01`).

## Subcarpetas

- `core/` — configuración, logger, middleware, puertos (`core/ports/`).
- `adapters/` — implementaciones concretas (PostgreSQL, Redis, Mosquitto).
- `routers/` — adaptadores de entrada HTTP (FastAPI).
- `models/` — modelos ORM (SQLAlchemy). Vacío en este sprint (sin esquema de negocio).
- `schemas/` — modelos Pydantic de request/response.
- `services/` — casos de uso / lógica de coordinación.
- `workers/` — tareas en segundo plano (Celery). Vacío en este sprint.
- `websocket/` — gestión de conexiones WebSocket. Vacío en este sprint.
- `tests/` — pruebas unitarias y de coordinación; `tests/integration/` — contra
  contenedores reales.

## Tests

```bash
cd hira-server/backend
pytest
```

`pytest.ini` fija `pythonpath = .` — los tests importan con rutas relativas a esta
carpeta (p. ej. `from services.health_service import aggregate_status`).
