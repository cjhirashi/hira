"""`core/config.py::Settings` — arranque validado.

Cubre RF-003 (`spec.md`): si falta una variable de entorno requerida, el
sistema rechaza el arranque con un error que nombra la variable faltante —
sin arranque parcial (la validación ocurre al construir `Settings()`, no en
el primer acceso perezoso a un campo).

Variables de este sprint: `DATABASE_URL`, `POSTGRES_*`, `REDIS_URL`,
`REDIS_PASSWORD`, `ENVIRONMENT`, `LOG_LEVEL`. Confirma explícitamente que
`SECRET_KEY`/`ADMIN_PASSWORD_HASH` (`VUL-HUB-03`, Panel Admin es H1) **no**
son campos requeridos en este sprint (`spec.md §2`, `plan.md §2`).
"""
import pytest
from pydantic import ValidationError

from core.config import Settings

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


def test_settings_loads_when_all_required_vars_present(monkeypatch):
    _set_env(monkeypatch)

    settings = Settings()

    assert settings.database_url == REQUIRED_ENV["DATABASE_URL"]
    assert settings.redis_url == REQUIRED_ENV["REDIS_URL"]
    assert settings.postgres_user == "hub"


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


def test_settings_has_no_secret_key_or_admin_password_hash_fields():
    """`SECRET_KEY`/`ADMIN_PASSWORD_HASH` NO son campos requeridos en este
    sprint (`VUL-HUB-03`, Panel Admin es H1, sin consumidor real todavía)."""
    assert "secret_key" not in Settings.model_fields
    assert "admin_password_hash" not in Settings.model_fields
