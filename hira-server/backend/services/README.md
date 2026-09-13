# services

Lógica de negocio / casos de uso. Importa solo de `core/ports/`, nunca de `adapters/`
directamente (regla de oro `SRV-ADR-017`).

- `health_service.py::aggregate_status(results: dict[str, bool]) -> Literal["ok",
  "degraded"]` — núcleo puro, sin I/O (RF-002). "ok" si los tres servicios están `ok`,
  "degraded" si al menos uno falla.
- `health_service.py::get_health()` — coordinación (RF-002, RF-005, RF-007), pendiente
  de un batch posterior (requiere `core/ports/` implementados).
