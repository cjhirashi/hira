"""Punto de entrada de la API de Hira Server (FastAPI) — RF-003, RF-005 (`spec.md`).

El `lifespan` valida `Settings()` al arrancar (RF-003): si falta una variable de
entorno requerida, `pydantic.ValidationError` se captura, se loguea en JSON
(`level: error`) nombrando el/los campo(s) faltante(s), y el proceso aborta con
`sys.exit(1)` — nunca arranque parcial.

`CorrelationIdMiddleware` (RF-005) se registra aquí — todo request lleva un
`trace_id` propagado o generado (`core/middleware.py`).

`routers/monitor.py::GET /health` se registra aquí (RF-002, T-013..T-015).
"""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from core.config import Settings
from core.logger import get_logger
from core.middleware import CorrelationIdMiddleware
from routers.monitor import router as monitor_router

_logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """RF-003 — valida `Settings()` al arrancar; aborta sin arranque parcial."""
    try:
        Settings()
    except ValidationError as exc:
        missing_fields = ", ".join(
            ".".join(str(part) for part in error["loc"]) for error in exc.errors()
        )
        _logger.error(
            "Arranque abortado: variable(s) de entorno faltante(s): %s",
            missing_fields or str(exc),
        )
        sys.exit(1)
    yield


app = FastAPI(title="Hira Server", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(monitor_router)
