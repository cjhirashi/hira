# core

Núcleo transversal del backend — no depende de infraestructura concreta.

- `config.py` — `Settings` (Pydantic v2), arranque validado (RF-003): falta una
  variable de entorno requerida → error explícito nombrándola, sin arranque
  parcial. Variables de este sprint: `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`,
  `REDIS_PASSWORD`, `ENVIRONMENT`, `LOG_LEVEL` — **sin** `SECRET_KEY` ni
  `ADMIN_PASSWORD_HASH` (`VUL-HUB-03`, Panel Admin es H1, sin consumidor real
  todavía).
- `logger.py` — `get_logger(module)`, logging JSON estructurado (`timestamp,
  level, service, module, trace_id, message`), cero `print()` (RF-004).
- `middleware.py` — `CorrelationIdMiddleware` (RF-005): lee `X-Trace-ID` del
  request o genera un `uuid4()`, lo fija en `logger.trace_id_var` durante el
  request y lo devuelve en la respuesta.
- `ports/` — interfaces abstractas (`Protocol`) que `services/` puede importar;
  `core/` nunca importa `adapters/`.
