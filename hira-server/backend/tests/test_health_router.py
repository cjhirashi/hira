"""`GET /health` — adaptador de entrada HTTP (RF-002, `spec.md §3`).

Golpea la app real de `main.py` (con su `lifespan`, RF-003) vía `TestClient` y
verifica el shape exacto pactado en `hira-server/docs/openapi.yaml#/paths/~1health`:
`status`, `services.{postgres,redis,mosquitto}`, `version`, `trace_id`, siempre
HTTP 200 (decisión cerrada en `spec.md §3`/§6 — sin sobre RFC 9457 en este endpoint
de monitoreo). Debe fallar antes de T-015 (no existe `routers/monitor.py` todavía).
"""
import pytest
from fastapi.testclient import TestClient

from main import app

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hira:hira@postgres:5432/hiradb",
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}


@pytest.fixture
def client(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    with TestClient(app) as test_client:
        yield test_client


def test_health_returns_200_with_contract_shape(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ok", "degraded")
    assert set(body["services"].keys()) == {"postgres", "redis", "mosquitto"}
    for value in body["services"].values():
        assert value in ("ok", "error")
    assert isinstance(body["version"], str) and body["version"]
    assert isinstance(body["trace_id"], str) and body["trace_id"]


def test_health_reflects_correlation_id_header(client):
    """RF-005: el `trace_id` del body coincide con el `X-Trace-ID` propagado."""
    response = client.get("/health", headers={"X-Trace-ID": "trace-router-test"})

    assert response.status_code == 200
    assert response.json()["trace_id"] == "trace-router-test"
    assert response.headers["X-Trace-ID"] == "trace-router-test"
