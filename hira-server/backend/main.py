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

`routers/auth.py::POST /auth/login|refresh|logout` (`SRV-002-auth-rbac`,
T-017/T-018) se registra aquí, junto con el exception handler de
`core.errors.ProblemDetailError` → `schemas.errors.ProblemDetail` (RFC 9457,
`media_type="application/problem+json"`, `plan.md §2`/§4).

`AuthenticationMiddleware` (T-019/T-020, RF-003/RF-007) se registra **antes** que
`CorrelationIdMiddleware` en el código de abajo — a propósito, no es un desliz:
Starlette envuelve el middleware añadido **último** como el más externo (se
ejecuta primero), así que para que el `trace_id` ya exista cuando
`AuthenticationMiddleware` procese (y eventualmente loguee) un fallo de
autenticación, `CorrelationIdMiddleware` debe ser el añadido en último lugar
(verificado empíricamente; ver nota de desviación en `tasks.md` T-020 — la
redacción de `plan.md §2`/§6 describe el resultado deseado, "el trace_id debe
existir antes", con el orden de líneas de código invertido al que lo logra).
"""
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from adapters.factory import get_notification_port
from core.config import Settings
from core.errors import ProblemDetailError
from core.logger import get_logger
from core.middleware import AuthenticationMiddleware, CorrelationIdMiddleware
from routers.auth import router as auth_router
from routers.monitor import router as monitor_router
from schemas.errors import ProblemDetail

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
# Orden de registro invertido a propósito respecto al orden de ejecución deseado
# — ver docstring del módulo (Starlette envuelve el último `add_middleware` como
# el más externo/primero en ejecutar).
app.add_middleware(AuthenticationMiddleware)
app.add_middleware(CorrelationIdMiddleware)
app.include_router(monitor_router)
app.include_router(auth_router)


@app.exception_handler(ProblemDetailError)
async def problem_detail_exception_handler(
    request: Request, exc: ProblemDetailError
) -> JSONResponse:
    """RFC 9457 (`E-ADR-003`) — traduce `ProblemDetailError` a la respuesta HTTP."""
    problem = ProblemDetail(
        type=exc.type_, title=exc.title, status=exc.status, detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status,
        content=problem.model_dump(),
        media_type="application/problem+json",
    )
