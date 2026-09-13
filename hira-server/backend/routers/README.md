# routers

Adaptadores de entrada HTTP (FastAPI). `monitor.py::GET /health`, contrato en
`hira-server/docs/openapi.yaml` (Contract-First, `tasks.md` T-013/T-014/T-015).
Inyecta `DatabasePort`/`CachePort`/`NotificationPort` vía
`Depends(adapters.factory.*)` — nunca instancia un adaptador concreto directamente
(`SRV-ADR-017`).

`auth.py::POST /auth/login|refresh|logout` (`SRV-002-auth-rbac`, T-017/T-018,
RF-001/RF-002/RF-010/RF-011/RF-013/RF-014) — traduce HTTP a
`services/auth_service.py`, inyecta `UserRepositoryPort`/`CachePort` vía
`Depends(adapters.factory.*)`. `POST /auth/logout` no valida autenticación en el
router — la exige `AuthenticationMiddleware` (`core/middleware.py`, T-019/T-020),
que no incluye esta ruta en su *allowlist* público.
