# services

Lógica de negocio / casos de uso. Importa solo de `core/ports/` — nunca de
`adapters/` directamente ni de FastAPI (regla de oro `E-ADR-002`).

- `health_service.py::aggregate_status(results: dict[str, bool]) -> Literal["ok",
  "degraded"]` — núcleo puro, sin I/O (RF-002). "ok" si Postgres y Redis están
  `ok` (2 servicios, 4 combinaciones — a diferencia de `hira-server`, sin
  Mosquitto); "degraded" si al menos uno falla.
- `health_service.py::get_health(database, cache)` — coordinación (RF-002,
  RF-005, RF-007): llama a los 2 puertos en paralelo, cada uno con
  `asyncio.wait_for(timeout=2)` (RNF-002); excepción o timeout → ese servicio
  queda `error` sin colgar la respuesta; agrega el `trace_id` vigente del
  `ContextVar` de `core/logger.py`. Recibe los puertos por parámetro — no
  instancia adaptadores (`adapters/factory.py` los inyecta, pendiente de un
  batch posterior).
