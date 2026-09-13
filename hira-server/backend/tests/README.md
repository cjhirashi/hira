# tests

Pruebas unitarias y de coordinación (sin contenedores — corren con `pytest` local).
Un test por cada `AC-*`/`RF-*` que la tarea de `tasks.md` deja verificable; cada test
cita la ancla que cubre.

- `test_health_policy.py` — `aggregate_status`, 8 combinaciones de 3 booleanos (RF-002).
- `test_config.py` — `Settings`, variable de entorno faltante nombrada en el error
  (RF-003).
- `test_logger.py` — log JSON con `timestamp, level, service, module, trace_id,
  message`, cero `print()` (RF-004).

`tests/integration/` — pruebas contra contenedores reales (`@pytest.mark.integration`),
fuera del alcance de este batch.
