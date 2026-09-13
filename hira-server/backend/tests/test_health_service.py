"""`services/health_service.py::get_health` — coordinación (RF-002, RF-005, RF-007).

Usa dobles (`Protocol` fakes) de `DatabasePort`/`CachePort`/`NotificationPort`
definidos aquí mismo — no son adaptadores reales (esos llegan en T-019/T-020, fuera
de alcance de este batch). Verifica:

- RF-007/RNF-002: un servicio que tarda más de 2s no cuelga la respuesta agregada —
  se marca `error` al vencer el timeout.
- RF-002: usa `aggregate_status` ya existente (`status` agregado correcto).
- RF-005: el `trace_id` vigente en el `ContextVar` de `core/logger.py` se refleja en
  el payload.
"""
import asyncio
import time

import pytest

from core.logger import trace_id_var
from services.health_service import get_health


class _FastOkPort:
    """Responde de inmediato con éxito."""

    async def ping(self) -> bool:
        return True


class _SlowPort:
    """Tarda más que el timeout de 2s (RNF-002) — nunca debe colgar la respuesta."""

    async def ping(self) -> bool:
        await asyncio.sleep(5)
        return True


class _FailingPort:
    """Lanza una excepción — no debe propagarse, se marca `error` (RF-007)."""

    async def ping(self) -> bool:
        raise ConnectionError("conexión rechazada")


class _NotificationFastOk:
    async def ping(self) -> bool:
        return True

    async def connect(self) -> None:
        return None


@pytest.mark.asyncio
async def test_get_health_all_ok_aggregates_status_ok():
    result = await get_health(_FastOkPort(), _FastOkPort(), _NotificationFastOk())

    assert result["status"] == "ok"
    assert result["services"] == {"postgres": "ok", "redis": "ok", "mosquitto": "ok"}
    assert result["version"]


@pytest.mark.asyncio
async def test_get_health_timeout_does_not_hang_response():
    """RF-007/RNF-002: `_SlowPort` tarda 5s; la respuesta debe llegar en ~2s, no 5s."""
    start = time.monotonic()

    result = await get_health(_SlowPort(), _FastOkPort(), _NotificationFastOk())

    elapsed = time.monotonic() - start

    assert elapsed < 3.0, f"la respuesta tardó {elapsed}s — el timeout de 2s no aplicó"
    assert result["services"]["postgres"] == "error"
    assert result["services"]["redis"] == "ok"
    assert result["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_health_exception_marks_service_error_without_propagating():
    """RF-007: una excepción de un puerto no debe propagarse fuera de `get_health`."""
    result = await get_health(_FailingPort(), _FastOkPort(), _NotificationFastOk())

    assert result["services"]["postgres"] == "error"
    assert result["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_health_notification_error_marks_mosquitto_error():
    class _NotificationFailing:
        async def ping(self) -> bool:
            raise TimeoutError("mqtt no responde")

        async def connect(self) -> None:
            return None

    result = await get_health(_FastOkPort(), _FastOkPort(), _NotificationFailing())

    assert result["services"]["mosquitto"] == "error"
    assert result["status"] == "degraded"


@pytest.mark.asyncio
async def test_get_health_includes_trace_id_from_context():
    """RF-005: `get_health` agrega el `trace_id` vigente del `ContextVar` de logger."""
    token = trace_id_var.set("trace-xyz-789")
    try:
        result = await get_health(_FastOkPort(), _FastOkPort(), _NotificationFastOk())
    finally:
        trace_id_var.reset(token)

    assert result["trace_id"] == "trace-xyz-789"


@pytest.mark.asyncio
async def test_get_health_defaults_trace_id_when_no_context():
    result = await get_health(_FastOkPort(), _FastOkPort(), _NotificationFastOk())

    assert result["trace_id"] == "-"
