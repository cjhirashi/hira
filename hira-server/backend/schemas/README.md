# schemas

Modelos Pydantic de request/response.

- `health.py` — `HealthResponse`, payload de respuesta de `GET /health`,
  traducción exacta de `hira-server/docs/openapi.yaml#/paths/~1health`
  (Contract-First, `SRV-001-walking-skeleton`).
- `errors.py` — `ProblemDetail` (`type`, `title`, `status`, `detail`), sobre de
  error RFC 9457 común a los 3 productos (`SRV-002-auth-rbac`, `E-ADR-003`).
  Traduce `core.errors.ProblemDetailError` a la respuesta HTTP — exception
  handler registrado en `main.py` (T-017/T-018).
- `auth.py` — `LoginRequest`, `TokenResponse`, `RefreshRequest`,
  `AccessTokenResponse` (`SRV-002-auth-rbac`, T-017/T-018), traducción exacta de
  `hira-server/docs/openapi.yaml#/components/schemas` para
  `POST /auth/login|refresh|logout`.
- `devices.py` — `DeviceOut`, `DeviceCandidateOut` (`SRV-003-bacnet-adapter`,
  T-008/T-009), traducción exacta de
  `hira-server/docs/openapi.yaml#/components/schemas` para
  `POST /devices/scan/bacnet|GET /devices|GET /devices/{id}/candidates`.
