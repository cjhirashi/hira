"""`core/middleware.py::CorrelationIdMiddleware` — Correlation ID (RF-005,
`spec.md`) + wiring de `Settings()` en el `lifespan` de `main.py` (RF-003).

Primera parte: verifica que el `trace_id` se propaga desde el header
`X-Trace-ID` del request, o se genera (`uuid4()`) si el cliente no lo envía;
disponible en el mismo `ContextVar` que usa `core/logger.py` (`trace_id_var`,
sin duplicar) durante el request — devuelto también en la respuesta vía
`X-Trace-ID`.

Segunda parte (T-011, `tasks.md`): `main.py::lifespan` — primer punto donde
`main.py` existe. Si falta una variable de entorno requerida,
`pydantic.ValidationError` se captura, se loguea en JSON (`level: error`)
nombrando el/los campo(s) faltante(s) vía `core/logger.py`, y el arranque se
aborta (`sys.exit(1)`) — nunca arranque parcial. Sin adaptadores/factory
todavía en este batch (T-001..T-012) — el `lifespan` de este sprint solo
valida `Settings()`, sin conexión a Postgres/Redis (eso llega con
`adapters/factory.py`, T-015+).
"""
import json
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.logger import trace_id_var
from core.middleware import TRACE_ID_HEADER, CorrelationIdMiddleware

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hub:hub@postgres:5432/hubdb",
    "POSTGRES_USER": "hub",
    "POSTGRES_PASSWORD": "s3cret",
    "POSTGRES_DB": "hubdb",
    "REDIS_URL": "redis://redis:6379/0",
    "REDIS_PASSWORD": "r3dispass",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "INFO",
}


def _set_env(monkeypatch, remove=None):
    remove = remove or []
    for key, value in REQUIRED_ENV.items():
        if key in remove:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


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


# --- Wiring de `Settings()` en el `lifespan` de `main.py` (RF-003) ---


@pytest.mark.asyncio
async def test_lifespan_starts_when_all_required_vars_present(monkeypatch):
    _set_env(monkeypatch)

    from main import app, lifespan

    async with lifespan(app):
        pass  # no debe abortar ni lanzar


@pytest.mark.asyncio
async def test_lifespan_aborts_with_json_error_when_var_missing(monkeypatch, capsys):
    _set_env(monkeypatch, remove=["REDIS_PASSWORD"])

    from main import app, lifespan

    with pytest.raises(SystemExit) as exc_info:
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line]
    record = json.loads(lines[-1])
    assert record["level"] == "ERROR"
    assert "redis_password" in record["message"].lower()


@pytest.mark.asyncio
async def test_lifespan_no_partial_startup_names_all_missing_vars(monkeypatch, capsys):
    """RF-003: sin arranque parcial — nombra TODAS las variables faltantes, no solo una."""
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    from main import app, lifespan

    with pytest.raises(SystemExit):
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip().splitlines()[-1])
    assert record["level"] == "ERROR"
    for key in REQUIRED_ENV:
        assert key.lower() in record["message"].lower()
