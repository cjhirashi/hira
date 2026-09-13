# tests

Pruebas unitarias y de coordinación (sin contenedores — corren con `pytest` local).
Un test por cada `AC-*`/`RF-*` que la tarea de `tasks.md` deja verificable; cada test
cita la ancla que cubre.

- `test_health_policy.py` — `aggregate_status`, 8 combinaciones de 3 booleanos (RF-002).
- `test_config.py` — `Settings`, variable de entorno faltante nombrada en el error
  (RF-003).
- `test_logger.py` — log JSON con `timestamp, level, service, module, trace_id,
  message`, cero `print()` (RF-004).
- `test_health_service.py` — `get_health` con dobles (`Protocol` fakes) de
  `DatabasePort`/`CachePort`/`NotificationPort`: timeout de 2s no cuelga la respuesta
  (RF-007/RNF-002), agrega `trace_id` (RF-005), usa `aggregate_status` (RF-002).
- `test_correlation_id.py` — `CorrelationIdMiddleware`: propaga `X-Trace-ID` o genera
  `uuid4()`, lo fija en el `ContextVar` de `core/logger.py` (RF-005).
- `test_main_lifespan.py` — `main.py::lifespan`: `ValidationError` de `Settings()` →
  log JSON `level: error` nombrando el/los campo(s) faltante(s) + `sys.exit(1)`, sin
  arranque parcial (RF-003).

`asyncio_mode = auto` (`pytest.ini`) — los tests `async def` no necesitan el marcador
`@pytest.mark.asyncio` explícito, aunque algunos lo declaran por claridad.

`tests/integration/` — pruebas contra contenedores reales (`@pytest.mark.integration`),
fuera del alcance de este batch.
