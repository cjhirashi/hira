"""Observabilidad — RF-004 (`spec.md`).

`get_logger(module)` retorna un `logging.Logger` que emite JSON estructurado a
stdout con las claves `timestamp, level, service, module, trace_id, message`.
Cero uso de la sentencia `print` — el módulo entero usa `logging`.

`trace_id_var` es el `ContextVar` que `core/middleware.py::CorrelationIdMiddleware`
(pendiente, batch T-011/T-012) fija por request; sin request en curso, el valor
por defecto es `"-"`.
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

SERVICE_NAME = "hira-hub"
_LOGGER_PREFIX = "hira."

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


class _DynamicStdoutHandler(logging.StreamHandler):
    """`StreamHandler` que resuelve `sys.stdout` en cada `emit`, no al crearse.

    `logging.StreamHandler(stream=sys.stdout)` fija la referencia al objeto vigente
    en el momento de la llamada. Como `get_logger` cachea el logger (y su handler)
    la primera vez que se pide un `module` dado, un logger creado en tiempo de
    import (p. ej. `core.logger.get_logger("main")` a nivel de módulo en
    `main.py`) queda atado al `sys.stdout` real del proceso — y un test que
    redirige `sys.stdout` después (`capsys`) nunca ve la salida. Esta subclase
    reemplaza `stream` por una propiedad para que cada log use el `sys.stdout`
    vigente, sin cambiar el formato ni el comportamiento en producción.
    """

    def __init__(self) -> None:
        super().__init__(stream=sys.stdout)

    @property
    def stream(self):  # type: ignore[override]
        return sys.stdout

    @stream.setter
    def stream(self, value) -> None:  # pragma: no cover - fijado por __init__ del padre
        pass


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
        handler = _DynamicStdoutHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
