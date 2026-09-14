"""Núcleo — regla de agregación de salud. Sin I/O, sin mocks.

Cubre RF-002 (`spec.md`): status = "ok" si postgres y redis están ok,
"degraded" si al menos uno falla. 4 combinaciones de 2 booleanos — a
diferencia de `hira-server` (3 servicios, 8 combinaciones), Hub no tiene
Mosquitto (`HUB-ADR-01`).
"""
import pytest

from services.health_service import aggregate_status


@pytest.mark.parametrize(
    "postgres_ok, redis_ok, expected",
    [
        (True, True, "ok"),
        (True, False, "degraded"),
        (False, True, "degraded"),
        (False, False, "degraded"),
    ],
)
def test_aggregate_status(postgres_ok, redis_ok, expected):
    result = aggregate_status(
        {
            "postgres": postgres_ok,
            "redis": redis_ok,
        }
    )
    assert result == expected
