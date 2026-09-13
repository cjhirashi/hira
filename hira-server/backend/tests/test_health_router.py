"""`GET /health` — adaptador de entrada HTTP (RF-002, `spec.md §3`).

Golpea la app real de `main.py` (con su `lifespan`, RF-003) vía `TestClient` y
verifica el shape exacto pactado en `hira-server/docs/openapi.yaml#/paths/~1health`:
`status`, `services.{postgres,redis,mosquitto}`, `version`, `trace_id`, siempre
HTTP 200 (decisión cerrada en `spec.md §3`/§6 — sin sobre RFC 9457 en este endpoint
de monitoreo). Debe fallar antes de T-015 (no existe `routers/monitor.py` todavía).

Desde T-037 (`plan.md §10`, resolución de RNF-001), `lifespan` también arranca
`run_invalidation_subscriber(get_cache_port())` como tarea de fondo — sin
sustituirla, esa tarea intentaría un `SUBSCRIBE` real contra el host `redis` (solo
resoluble dentro de la red de docker), lo que rompería el *shutdown* de
`TestClient` fuera de ese entorno. Se sustituye únicamente `main.get_cache_port`
(la referencia que usa `lifespan`) por un doble sin red — el `Depends(get_cache_port)`
de `routers/monitor.py` (importado de `adapters.factory`, una referencia distinta)
sigue intacto: `/health` continúa ejercitando el `RedisAdapter` real tal como antes.
"""
import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import main as main_module
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from main import app


class _NoNetworkSubscribeCache:
    """Doble mínimo de `CachePort` — solo `subscribe`, nunca toca la red. Usado
    exclusivamente para que `main.py::lifespan` no dependa de Redis real en
    este test (no sustituye el `CachePort` real que usa `/health`)."""

    async def subscribe(self, channel: str):
        try:
            while True:
                await asyncio.sleep(3600)
                yield "unreachable"  # pragma: no cover
        except asyncio.CancelledError:
            raise

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
    # Este test es zona `test-adaptador-entrada` (contrato HTTP del router) — no
    # depende de red real ni del backoff de Mosquitto (1s/2s/4s, ya probado de
    # forma aislada en `tests/integration/test_adapters.py`). Mismo patrón que
    # `test_main_lifespan.py`: se sustituye `connect()` para que el `lifespan`
    # real que dispara `TestClient(app)` no intente resolver el host "mosquitto"
    # fuera de la red de docker.
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))
    monkeypatch.setattr(main_module, "get_cache_port", lambda: _NoNetworkSubscribeCache())
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
