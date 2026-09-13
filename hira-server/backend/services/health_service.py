"""Núcleo de negocio + coordinación del Walking Skeleton — salud agregada.

`aggregate_status` es lógica pura, sin I/O (RF-002, `spec.md §4`). `get_health` es la
coordinación (RF-002, RF-005, RF-007): llama a los 3 puertos en paralelo, cada uno
envuelto en `asyncio.wait_for(timeout=2)` (RNF-002) — una excepción o timeout se
captura y marca ese servicio como `error` sin propagarse (RF-007) — y agrega el
`trace_id` vigente en el `ContextVar` de `core/logger.py` (RF-005).

`services/` solo importa de `core/ports/` — nunca una librería concreta de
infraestructura (`SRV-ADR-017`).
"""
import asyncio
from typing import Literal

from core.logger import get_logger, trace_id_var
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from core.ports.notification_port import NotificationPort

HealthStatus = Literal["ok", "degraded"]
ServiceStatus = Literal["ok", "error"]

VERSION = "0.1.0"
PING_TIMEOUT_SECONDS = 2.0

_logger = get_logger("services.health_service")


def aggregate_status(results: dict[str, bool]) -> HealthStatus:
    """RF-002 — agrega el estado booleano de los servicios de infraestructura.

    Retorna "ok" si todos los valores de `results` son verdaderos (los tres
    servicios responden correctamente); "degraded" si al menos uno falla.
    """
    if all(results.values()):
        return "ok"
    return "degraded"


async def _ping_with_timeout(name: str, ping_coro) -> bool:
    """Envuelve un `ping()` con timeout de 2s (RNF-002); nunca propaga (RF-007)."""
    try:
        return bool(await asyncio.wait_for(ping_coro, timeout=PING_TIMEOUT_SECONDS))
    except Exception:  # noqa: BLE001 — cualquier fallo del puerto se degrada, no se propaga
        _logger.error("chequeo de salud falló para %s", name)
        return False


async def get_health(
    database: DatabasePort,
    cache: CachePort,
    notification: NotificationPort,
) -> dict:
    """RF-002, RF-005, RF-007 — arma el payload agregado de `GET /health`.

    Llama a los 3 puertos en paralelo; ninguno puede colgar la respuesta más allá
    de `PING_TIMEOUT_SECONDS` (RNF-002).
    """
    names = ("postgres", "redis", "mosquitto")
    checks = (database.ping(), cache.ping(), notification.ping())

    results_list = await asyncio.gather(
        *(_ping_with_timeout(name, coro) for name, coro in zip(names, checks))
    )
    results = dict(zip(names, results_list))

    services: dict[str, ServiceStatus] = {
        name: ("ok" if ok else "error") for name, ok in results.items()
    }

    return {
        "status": aggregate_status(results),
        "services": services,
        "version": VERSION,
        "trace_id": trace_id_var.get(),
    }
