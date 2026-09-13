"""Punto de entrada de la API de Hira Server (FastAPI) — RF-003, RF-005 (`spec.md`).

El `lifespan` valida `Settings()` al arrancar (RF-003): si falta una variable de
entorno requerida, `pydantic.ValidationError` se captura, se loguea en JSON
(`level: error`) nombrando el/los campo(s) faltante(s), y el proceso aborta con
`sys.exit(1)` — nunca arranque parcial.

El `lifespan` también invoca `MosquittoAdapter.connect()` (RF-006/RF-008,
`plan.md §7` Directiva de Pausa #2, `tasks.md` T-022 ampliada): a diferencia del
error de `Settings()`, un fallo de conexión a Mosquitto **no** aborta el
arranque — `connect()` ya agota su propio backoff fijo (1s/2s/4s) sin lanzar
excepción y sin loop ciego (RF-008); si tras eso sigue sin conectar, el proceso
arranca igual y `/health` refleja `mosquitto: error` en su primer chequeo vía
`ping()` (lazy retry, RF-007). Se obtiene la instancia vía
`adapters/factory.py::get_notification_port` — mismo punto de inyección que ya
usa `routers/monitor.py` vía `Depends` (`SRV-ADR-017`).

`CorrelationIdMiddleware` (RF-005) se registra aquí — todo request lleva un
`trace_id` propagado o generado (`core/middleware.py`).

`routers/monitor.py::GET /health` se registra aquí (RF-002, T-013..T-015).
"""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from adapters.factory import get_notification_port
from core.config import Settings
from core.logger import get_logger
from core.middleware import CorrelationIdMiddleware
from routers.monitor import router as monitor_router

_logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """RF-003 — valida `Settings()` al arrancar; aborta sin arranque parcial.
    RF-006/RF-008 — conecta Mosquitto con backoff; nunca bloquea el arranque."""
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

    try:
        await get_notification_port().connect()
    except Exception as exc:  # noqa: BLE001 — no bloquea el arranque (RF-008); `/health` refleja el estado (RF-007)
        _logger.error(
            "Conexión de arranque a Mosquitto falló tras el backoff; el arranque continúa: %s",
            exc,
        )

    yield


app = FastAPI(title="Hira Server", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(monitor_router)
