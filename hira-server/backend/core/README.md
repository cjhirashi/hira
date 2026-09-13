# core

Núcleo transversal del backend — no depende de infraestructura concreta.

- `config.py` — `Settings` (Pydantic v2), arranque validado (RF-003): falta una
  variable de entorno requerida → error explícito nombrándola, sin arranque parcial.
- `logger.py` — `get_logger(module)`, logging JSON estructurado (`timestamp, level,
  service, module, trace_id, message`), cero `print()` (RF-004).
- `middleware.py` — `CorrelationIdMiddleware` (RF-005). Pendiente (fuera del alcance
  de este batch de tareas).
- `ports/` — interfaces abstractas (`Protocol`) que `services/` puede importar; `core/`
  nunca importa `adapters/`.
