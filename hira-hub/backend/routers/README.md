# routers

Adaptadores de entrada HTTP (FastAPI). `monitor.py::GET /health`, contrato en
`hira-hub/docs/openapi.yaml` (Contract-First) — nace en un batch posterior
(`tasks.md` T-014/T-015), fuera de alcance de este batch (T-001..T-012).
Inyectará `DatabasePort`/`CachePort` vía `Depends(adapters.factory.*)` — nunca
instanciará un adaptador concreto directamente (`E-ADR-002`).
