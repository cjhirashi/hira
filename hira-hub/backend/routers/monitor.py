"""`GET /health` — adaptador de entrada HTTP (RF-002).

Contrato: `hira-hub/docs/openapi.yaml#/paths/~1health` (Contract-First,
`tasks.md` T-013, escrito antes que este router). Siempre HTTP 200 — el
detalle de cada servicio va en el body (decisión cerrada en `spec.md
§3`/§6). Sin auth (UptimeRobot depende de esto).

Los 2 puertos se inyectan vía `adapters/factory.py` (`E-ADR-002`): este router
nunca instancia un adaptador concreto directamente, solo declara su
dependencia del `Protocol` (`core/ports/`). En este sprint el factory
devuelve implementaciones in-memory (T-019 las reemplaza por las reales; ver
`adapters/factory.py`).
"""
from fastapi import APIRouter, Depends

from adapters.factory import get_cache_port, get_database_port
from core.ports.cache_port import CachePort
from core.ports.database_port import DatabasePort
from schemas.health import HealthResponse
from services.health_service import get_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    database: DatabasePort = Depends(get_database_port),
    cache: CachePort = Depends(get_cache_port),
) -> HealthResponse:
    """RF-002 — expone `services/health_service.py::get_health` vía HTTP."""
    payload = await get_health(database, cache)
    return HealthResponse(**payload)
