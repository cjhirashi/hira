# backend

API de Hira Hub (FastAPI). Arquitectura Hexagonal — `core/ports/` define las
interfaces, `adapters/` las implementa, `services/` orquesta usando solo
`core/ports/` (nunca importa `adapters/` directamente). Ver `E-ADR-002`
(supersede `HUB-ADR-05`, "arquitectura directa").

Feature activa: `.harness/specs/HUB-001-walking-skeleton/` (Walking Skeleton).
A diferencia de `hira-server`: **sin Mosquitto** — solo Postgres + Redis + Nginx
(`HUB-ADR-01`), 2 puertos de infraestructura (`DatabasePort`, `CachePort`).

`main.py` — punto de entrada FastAPI. El `lifespan` valida `Settings()` al
arrancar (RF-003: `ValidationError` → log JSON `level: error` + `sys.exit(1)`,
sin arranque parcial). Registra `CorrelationIdMiddleware` (`core/middleware.py`,
RF-005) y el router `routers/monitor.py::GET /health` (RF-002).

## Subcarpetas

- `core/` — configuración, logger, middleware, puertos (`core/ports/`).
- `adapters/` — implementaciones concretas (PostgreSQL, Redis).
- `routers/` — adaptadores de entrada HTTP (FastAPI).
- `models/` — modelos ORM. Vacío en este sprint (sin esquema de negocio —
  licencias/crash-reports/versiones llegan con H1/H2/H3).
- `schemas/` — modelos Pydantic de request/response.
- `services/` — casos de uso / lógica de coordinación.
- `tests/` — pruebas unitarias y de coordinación; `tests/integration/` — contra
  contenedores reales.

## Tests

```bash
cd hira-hub/backend
pytest
```

`pytest.ini` fija `pythonpath = .` — los tests importan con rutas relativas a
esta carpeta (p. ej. `from services.health_service import aggregate_status`).
