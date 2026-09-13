"""Núcleo — regla de agregación de salud. Sin I/O, sin mocks.

Cubre RF-002 (`spec.md`): status = "ok" si postgres, redis y mosquitto están ok,
"degraded" si al menos uno falla. 8 combinaciones de 3 booleanos.
"""
import pytest

from services.health_service import aggregate_status


@pytest.mark.parametrize(
    "postgres_ok, redis_ok, mosquitto_ok, expected",
    [
        (True, True, True, "ok"),
        (True, True, False, "degraded"),
        (True, False, True, "degraded"),
        (True, False, False, "degraded"),
        (False, True, True, "degraded"),
        (False, True, False, "degraded"),
        (False, False, True, "degraded"),
        (False, False, False, "degraded"),
    ],
)
def test_aggregate_status(postgres_ok, redis_ok, mosquitto_ok, expected):
    result = aggregate_status(
        {
            "postgres": postgres_ok,
            "redis": redis_ok,
            "mosquitto": mosquitto_ok,
        }
    )
    assert result == expected
