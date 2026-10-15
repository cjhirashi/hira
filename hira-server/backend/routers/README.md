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

`simulators.py::POST /simulators/{bacnet,modbus,mqtt}|GET /simulators|
DELETE /simulators/{device_id}` (`SRV-006-simuladores`, T-017,
RF-001/RF-002/RF-003/RF-004/RF-005/RF-006/RF-007/RF-009/RF-010/RF-012/
RF-014/RF-015) — **router nuevo, separado de `devices.py`** (`plan.md §2`
Registro de decisiones: RBAC mixto — `POST`/`DELETE` solo Admin
(`require_role("admin")`, RF-004), `GET` Admin+Operador
(`require_role("admin","operador")`, RF-005) — por eso **sin** `dependencies=`
a nivel de `APIRouter`, cada ruta aplica su propio `Depends(require_role(...))`.
Inyecta los 3 puertos de simulador + `DeviceRepositoryPort` vía
`Depends(adapters.factory.*)` y `SimulatorRegistryService` vía
`Depends(services.simulator_registry_service.get_simulator_registry)` —
nunca instancia ningún adaptador concreto (`SRV-ADR-017`). Delega la lógica
a `services/simulator_service.py`. `ProblemDetailError` (400/403/404/409)
propaga sin captura explícita — el `exception_handler` de `main.py` la
traduce. `DELETE` responde `204` sin cuerpo (`Response(status_code=204)`).
