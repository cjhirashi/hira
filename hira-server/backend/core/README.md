# core

Núcleo transversal del backend — no depende de infraestructura concreta.

- `config.py` — `Settings` (Pydantic v2), arranque validado (RF-003): falta una
  variable de entorno requerida → error explícito nombrándola, sin arranque parcial.
- `logger.py` — `get_logger(module)`, logging JSON estructurado (`timestamp, level,
  service, module, trace_id, message`), cero `print()` (RF-004).
- `middleware.py` — `CorrelationIdMiddleware` (RF-005): lee `X-Trace-ID` del request o
  genera un `uuid4()`, lo fija en `logger.trace_id_var` durante el request y lo
  devuelve en la respuesta. `AuthenticationMiddleware` (`SRV-002-auth-rbac`,
  T-019/T-020, RF-003/RF-007): exige `Authorization: Bearer <token>` fuera de
  `PUBLIC_ALLOWLIST` (`/health`, `/auth/login`, `/auth/refresh`, `/docs`,
  `/openapi.json`, `/redoc`), decodifica el access token y resuelve
  `request.state.user` vía `services/rbac_service.py::resolve_permissions`;
  cualquier 401 se retorna como `JSONResponse` RFC 9457 directamente (no depende
  del exception handler de FastAPI). Registrado en `main.py` **antes** que
  `CorrelationIdMiddleware` en el código — Starlette envuelve el último
  `add_middleware` como el más externo/primero en ejecutar, así que ese orden de
  líneas es el que logra que el `trace_id` exista antes de que Auth procese un
  fallo (ver docstring de `core/middleware.py` y de `main.py`).
- `ports/` — interfaces abstractas (`Protocol`) que `services/` puede importar; `core/`
  nunca importa `adapters/`.
- `errors.py` — `ProblemDetailError(status, type_, title, detail)`, excepción del
  sobre de error RFC 9457 (`SRV-002-auth-rbac`, `plan.md §2`/`§4`, `E-ADR-003`).
  Sin I/O; el catálogo concreto de slugs se consume en `services/`/routers de
  batches posteriores.
- `security/` — núcleo de autenticación/RBAC de 3 roles fijos
  (`SRV-002-auth-rbac`), ver `core/security/README.md`. Sin I/O.
