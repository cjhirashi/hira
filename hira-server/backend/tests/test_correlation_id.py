"""`core/middleware.py::CorrelationIdMiddleware` — Correlation ID (RF-005, `spec.md`).

Verifica que el `trace_id` se propaga desde el header `X-Trace-ID` del request, o se
genera (`uuid4()`) si el cliente no lo envía; y que queda disponible en el mismo
`ContextVar` que usa `core/logger.py` (`trace_id_var`, sin duplicar) durante el
request — devuelto también en la respuesta vía `X-Trace-ID`.
"""
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.logger import trace_id_var
from core.middleware import TRACE_ID_HEADER, CorrelationIdMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)

    @app.get("/echo-trace-id")
    async def echo_trace_id():
        return {"trace_id": trace_id_var.get()}

    return app


def test_propagates_trace_id_from_request_header():
    client = TestClient(_build_app())

    response = client.get("/echo-trace-id", headers={TRACE_ID_HEADER: "abc-123"})

    assert response.status_code == 200
    assert response.headers[TRACE_ID_HEADER] == "abc-123"
    assert response.json()["trace_id"] == "abc-123"


def test_generates_trace_id_when_header_missing():
    client = TestClient(_build_app())

    response = client.get("/echo-trace-id")

    assert response.status_code == 200
    generated = response.headers[TRACE_ID_HEADER]
    uuid.UUID(generated)  # no debe lanzar — es un UUID válido
    assert response.json()["trace_id"] == generated


def test_trace_id_differs_between_requests_without_header():
    client = TestClient(_build_app())

    first = client.get("/echo-trace-id")
    second = client.get("/echo-trace-id")

    assert first.headers[TRACE_ID_HEADER] != second.headers[TRACE_ID_HEADER]


def test_trace_id_context_reset_after_request():
    """El `ContextVar` no debe filtrar el `trace_id` de un request fuera de él."""
    client = TestClient(_build_app())

    client.get("/echo-trace-id", headers={TRACE_ID_HEADER: "leaked-id"})

    assert trace_id_var.get() == "-"
