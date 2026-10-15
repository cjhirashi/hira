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

- `simulators.py` — `BacnetSimulatedObjectIn`, `StartBacnetSimulatorRequest`,
  `ModbusRegisterValueIn`, `StartModbusSimulatorRequest`,
  `StartMqttSimulatorRequest`, `SimulatorOut` (`SRV-006-simuladores`, T-017),
  traducción exacta de `hira-server/docs/openapi.yaml#/components/schemas`
  (Contract-First). `BacnetSimulatedObjectIn.object_type` usa un `Literal` de
  6 valores (`analog-value`, `analog-input`, `analog-output`, `binary-value`,
  `binary-input`, `binary-output`) — rechazo 422 estándar de Pydantic para
  cualquier otro valor (`plan.md §1`, Registro de decisiones: `spec.md` no
  define una rama de error de negocio para tipo no soportado).
  `StartMqttSimulatorRequest.interval_seconds` **sin** `Field(gt=0)` a propósito:
  RF-015 exige 400 RFC 9457, no el 422 genérico que produciría Pydantic (mismo
  criterio que `ModbusRangeIn.count`, `SRV-004`). `SimulatorOut` traduce
  `services/simulator_registry_service.py::RunningSimulator` a HTTP.
