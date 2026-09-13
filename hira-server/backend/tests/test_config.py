"""`core/config.py::Settings` — arranque validado.

Cubre RF-003 (`spec.md`): si falta una variable de entorno requerida, el sistema
rechaza el arranque con un error que nombra la variable faltante — sin arranque
parcial (la validación ocurre al construir `Settings()`, no en el primer acceso
perezoso a un campo). Sin `HIRA_DEPLOY_MODE` (`E-ADR-001`).
"""
import pytest
from pydantic import ValidationError

from core.config import Settings

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


def test_settings_loads_when_all_required_vars_present(monkeypatch):
    _set_env(monkeypatch)

    settings = Settings()

    assert settings.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert settings.redis_url == REQUIRED_ENV["REDIS_URL"]
    assert settings.mqtt_user == "hira"


@pytest.mark.parametrize("missing_var", sorted(REQUIRED_ENV))
def test_settings_missing_var_raises_naming_it(monkeypatch, missing_var):
    _set_env(monkeypatch, remove=[missing_var])

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    error_text = str(exc_info.value).lower()
    assert missing_var.lower() in error_text


def test_settings_rejects_partial_startup_no_default_for_required_fields(monkeypatch):
    """No debe existir arranque parcial: sin ninguna variable seteada, falla."""
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    error_text = str(exc_info.value).lower()
    for key in REQUIRED_ENV:
        assert key.lower() in error_text


def test_settings_has_no_deploy_mode_field():
    """`HIRA_DEPLOY_MODE` está retirado (`E-ADR-001`) — no debe existir como campo."""
    assert "deploy_mode" not in Settings.model_fields
    assert "hira_deploy_mode" not in Settings.model_fields
