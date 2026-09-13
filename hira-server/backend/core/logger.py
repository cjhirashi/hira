"""Observabilidad — RF-004 (`spec.md`).

`get_logger(module)` retorna un `logging.Logger` que emite JSON estructurado a
stdout con las claves `timestamp, level, service, module, trace_id, message`.
Cero uso de la sentencia `print` — el módulo entero usa `logging`.

`trace_id_var` es el `ContextVar` que `core/middleware.py::CorrelationIdMiddleware`
(pendiente, batch posterior) fija por request; sin request en curso, el valor por
defecto es `"-"`.
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

SERVICE_NAME = "hira-server"
_LOGGER_PREFIX = "hira."

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class JSONFormatter(logging.Formatter):
    """Formatea cada `LogRecord` como una línea JSON (RF-004)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "module": record.name.removeprefix(_LOGGER_PREFIX),
            "trace_id": trace_id_var.get(),
            "message": record.getMessage(),
        }
        return json.dumps(payload, ensure_ascii=False)


def get_logger(module: str) -> logging.Logger:
    """Retorna un logger JSON para `module`, sin handlers duplicados."""
    logger = logging.getLogger(f"{_LOGGER_PREFIX}{module}")
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
