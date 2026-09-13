"""Núcleo de negocio del Walking Skeleton — regla de agregación de salud.

Sin I/O: `aggregate_status` es lógica pura (RF-002, `spec.md §4`). La coordinación
real (`get_health`, que llama a los 3 puertos con timeout) llega en un batch
posterior de `tasks.md` (T-008..T-010), cuando existan `core/ports/`.
"""
from typing import Literal

HealthStatus = Literal["ok", "degraded"]


def aggregate_status(results: dict[str, bool]) -> HealthStatus:
    """RF-002 — agrega el estado booleano de los servicios de infraestructura.

    Retorna "ok" si todos los valores de `results` son verdaderos (los tres
    servicios responden correctamente); "degraded" si al menos uno falla.
    """
    if all(results.values()):
        return "ok"
    return "degraded"
