"""Response model de `GET /health` — payload exacto del contrato (RF-002).

`hira-hub/docs/openapi.yaml#/paths/~1health` es la fuente de verdad
(Contract-First, `tasks.md` T-013); este módulo solo la traduce a Pydantic para
que FastAPI valide/serialice la respuesta. A diferencia de `hira-server`: sin
Mosquitto — solo 2 servicios (`HUB-ADR-01`).
"""
from typing import Literal

from pydantic import BaseModel

ServiceStatus = Literal["ok", "error"]
HealthStatus = Literal["ok", "degraded"]


class ServicesStatus(BaseModel):
    """Estado individual de cada dependencia de infraestructura (RF-002)."""

    postgres: ServiceStatus
    redis: ServiceStatus


class HealthResponse(BaseModel):
    """Payload exacto de `GET /health` (`spec.md §3`)."""

    status: HealthStatus
    services: ServicesStatus
    version: str
    trace_id: str
