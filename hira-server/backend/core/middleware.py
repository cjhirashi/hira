"""Correlation ID — RF-005 (`spec.md`).

`CorrelationIdMiddleware` lee `X-Trace-ID` del request entrante; si el cliente no lo
envía, genera uno con `uuid4()`. Lo fija en `core.logger.trace_id_var` — el mismo
`ContextVar` que `core/logger.py` ya usa para sus logs (no se duplica) — durante todo
el ciclo de vida del request, y lo devuelve en la respuesta vía el header
`X-Trace-ID`.
"""
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from core.logger import trace_id_var

TRACE_ID_HEADER = "X-Trace-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propaga/genera el `trace_id` por request (RF-005)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid4())
        token = trace_id_var.set(trace_id)
        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
