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

`devices.py::POST /devices/scan/bacnet|GET /devices|GET /devices/{id}/
candidates` (`SRV-003-bacnet-adapter`, T-008/T-009, RF-001/RF-002/RF-003/
RF-004/RF-005/RF-008/RF-009) — traduce HTTP a
`services/device_scan_service.py::scan_bacnet`, inyecta
`BacnetTransportPort`/`DeviceRepositoryPort` vía `Depends(adapters.factory.*)`.
Los 3 endpoints comparten `dependencies=[Depends(require_role("admin",
"operador"))]` a nivel de `APIRouter` (RF-003) — Visor recibe 403
`insufficient-role`. `GET /devices/{id}/candidates` responde 404
`device-not-found` (RFC 9457) si `id` no existe (RF-009).
