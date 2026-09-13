# routers

Adaptadores de entrada HTTP (FastAPI). Único router de este sprint: `monitor.py::GET
/health`, contrato en `hira-server/docs/openapi.yaml` (Contract-First, `tasks.md`
T-013/T-014/T-015). Inyecta `DatabasePort`/`CachePort`/`NotificationPort` vía
`Depends(adapters.factory.*)` — nunca instancia un adaptador concreto directamente
(`SRV-ADR-017`).
