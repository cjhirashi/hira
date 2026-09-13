# schemas

Modelos Pydantic de request/response.

- `health.py` — `HealthResponse`, payload de respuesta de `GET /health`,
  traducción exacta de `hira-server/docs/openapi.yaml#/paths/~1health`
  (Contract-First, `SRV-001-walking-skeleton`).
- `errors.py` — `ProblemDetail` (`type`, `title`, `status`, `detail`), sobre de
  error RFC 9457 común a los 3 productos (`SRV-002-auth-rbac`, `E-ADR-003`).
  Traduce `core.errors.ProblemDetailError` a la respuesta HTTP (exception handler
  de un batch posterior, `plan.md §2`).
