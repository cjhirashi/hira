"""`main.py::lifespan` — arranque validado (RF-003, `spec.md`).

Wiring de `Settings()` en el `lifespan` de FastAPI: si falta una variable de entorno
requerida, `pydantic.ValidationError` se captura, se loguea en JSON (`level: error`)
nombrando el/los campo(s) faltante(s) vía `core/logger.py`, y el arranque se aborta
(`sys.exit(1)`) — nunca arranque parcial (`plan.md §2`, `tasks.md` T-012).
"""
import json

import pytest

from main import app, lifespan

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hira:hira@postgres:5432/hiradb",
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}


def _set_env(monkeypatch, remove=None):
    remove = remove or []
    for key, value in REQUIRED_ENV.items():
        if key in remove:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.mark.asyncio
async def test_lifespan_starts_when_all_required_vars_present(monkeypatch):
    _set_env(monkeypatch)

    async with lifespan(app):
        pass  # no debe abortar ni lanzar


@pytest.mark.asyncio
async def test_lifespan_aborts_with_json_error_when_var_missing(monkeypatch, capsys):
    _set_env(monkeypatch, remove=["MQTT_PASSWORD"])

    with pytest.raises(SystemExit) as exc_info:
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line]
    record = json.loads(lines[-1])
    assert record["level"] == "ERROR"
    assert "mqtt_password" in record["message"].lower()


@pytest.mark.asyncio
async def test_lifespan_no_partial_startup_names_all_missing_vars(monkeypatch, capsys):
    """RF-003: sin arranque parcial — nombra TODAS las variables faltantes, no solo una."""
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(SystemExit):
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip().splitlines()[-1])
    assert record["level"] == "ERROR"
    for key in REQUIRED_ENV:
        assert key.lower() in record["message"].lower()
