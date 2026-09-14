# routers

Adaptadores de entrada HTTP (FastAPI).

- `monitor.py::GET /health` (RF-002) — contrato en `hira-hub/docs/openapi.yaml`
  (Contract-First, `tasks.md` T-013). Inyecta `DatabasePort`/`CachePort` vía
  `Depends(adapters.factory.*)` — nunca instancia un adaptador concreto
  directamente (`E-ADR-002`). Sin auth (UptimeRobot depende de esto).
