# core

Núcleo transversal del backend — no depende de infraestructura concreta.

- `config.py` — `Settings` (Pydantic v2), arranque validado (RF-003): falta una
  variable de entorno requerida → error explícito nombrándola, sin arranque parcial.
- `logger.py` — `get_logger(module)`, logging JSON estructurado (`timestamp, level,
  service, module, trace_id, message`), cero `print()` (RF-004).
- `middleware.py` — `CorrelationIdMiddleware` (RF-005): lee `X-Trace-ID` del request o
  genera un `uuid4()`, lo fija en `logger.trace_id_var` durante el request y lo
  devuelve en la respuesta.
- `ports/` — interfaces abstractas (`Protocol`) que `services/` puede importar; `core/`
  nunca importa `adapters/`.
- `errors.py` — `ProblemDetailError(status, type_, title, detail)`, excepción del
  sobre de error RFC 9457 (`SRV-002-auth-rbac`, `plan.md §2`/`§4`, `E-ADR-003`).
  Sin I/O; el catálogo concreto de slugs se consume en `services/`/routers de
  batches posteriores.
- `security/` — núcleo de autenticación/RBAC de 3 roles fijos
  (`SRV-002-auth-rbac`), ver `core/security/README.md`. Sin I/O.
