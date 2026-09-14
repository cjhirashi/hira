"""`POST /devices/scan/bacnet`, `GET /devices`, `GET /devices/{id}/candidates`
— adaptador de entrada HTTP (`SRV-003-bacnet-adapter`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1bacnet`
(+ `~1devices`, `~1devices~1{id}~1candidates`), escrito antes que este router
(`tasks.md` T-007, Contract-First).

Inyecta `BacnetTransportPort`/`DeviceRepositoryPort` vía
`Depends(adapters.factory.*)` — nunca instancia un adaptador concreto
(`SRV-ADR-017`), mismo patrón que `routers/auth.py`/`routers/monitor.py`.
Protegidos con `require_role("admin", "operador")` (RF-003, reusa
`core/security/dependencies.py` de `SRV-002-auth-rbac`, sin reimplementarlo).
Delega la lógica de escaneo a `services/device_scan_service.py::scan_bacnet`.
"""
from fastapi import APIRouter, Depends

from adapters.factory import get_bacnet_transport_port, get_device_repository_port
from core.errors import ProblemDetailError
from core.ports.bacnet_transport_port import BacnetTransportPort
from core.ports.device_repository_port import DeviceRepositoryPort
from core.security.dependencies import require_role
from schemas.devices import DeviceCandidateOut, DeviceOut
from services.device_scan_service import scan_bacnet

_ERRORS_BASE_URL = "https://hira.dev/errors"

router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    dependencies=[Depends(require_role("admin", "operador"))],
)


@router.post("/scan/bacnet", response_model=list[DeviceOut])
async def scan_bacnet_devices(
    transport: BacnetTransportPort = Depends(get_bacnet_transport_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
) -> list[DeviceOut]:
    """RF-001, RF-002, RF-006, RF-008 — expone
    `services/device_scan_service.py::scan_bacnet` vía HTTP."""
    devices = await scan_bacnet(transport, device_repo)
    return [DeviceOut(**device.__dict__) for device in devices]


@router.get("", response_model=list[DeviceOut])
async def list_devices(
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
) -> list[DeviceOut]:
    """RF-004 — lista los dispositivos persistidos."""
    devices = await device_repo.list_devices()
    return [DeviceOut(**device.__dict__) for device in devices]


@router.get("/{id}/candidates", response_model=list[DeviceCandidateOut])
async def list_device_candidates(
    id: str,
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
) -> list[DeviceCandidateOut]:
    """RF-005, RF-009 — lista los puntos crudos candidatos de un dispositivo;
    404 `device-not-found` si `id` no existe."""
    device = await device_repo.get_device(id)
    if device is None:
        raise ProblemDetailError(
            status=404,
            type_=f"{_ERRORS_BASE_URL}/device-not-found",
            title="Dispositivo no encontrado",
            detail=f"No existe un dispositivo con id '{id}'.",
        )
    candidates = await device_repo.list_candidates_for_device(id)
    return [DeviceCandidateOut(**candidate.__dict__) for candidate in candidates]
