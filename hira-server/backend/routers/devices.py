"""`POST /devices/scan/bacnet`, `POST /devices/scan/modbus`,
`POST /devices/scan/mqtt`, `GET /devices`, `GET /devices/{id}/candidates` —
adaptador de entrada HTTP (`SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter`/
`SRV-005-mqtt-scanning`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1bacnet`
(+ `~1devices~1scan~1modbus`, `~1devices~1scan~1mqtt`, `~1devices`,
`~1devices~1{id}~1candidates`), escrito antes que este router (Contract-First).

Inyecta `BacnetTransportPort`/`ModbusTransportPort`/`MqttScanTransportPort`/
`DeviceRepositoryPort` vía `Depends(adapters.factory.*)` — nunca instancia un
adaptador concreto (`SRV-ADR-017`), mismo patrón que
`routers/auth.py`/`routers/monitor.py`. Protegidos con
`require_role("admin", "operador")` (RF-003, reusa
`core/security/dependencies.py` de `SRV-002-auth-rbac`, sin reimplementarlo).
Delega la lógica de escaneo a `services/device_scan_service.py::scan_bacnet`/
`scan_modbus`/`scan_mqtt`.
"""
from fastapi import APIRouter, Depends

from adapters.factory import (
    get_bacnet_transport_port,
    get_device_repository_port,
    get_modbus_transport_port,
    get_mqtt_scan_transport_port,
)
from core.errors import ProblemDetailError
from core.ports.bacnet_transport_port import BacnetTransportPort
from core.ports.device_repository_port import DeviceRepositoryPort
from core.ports.modbus_transport_port import ModbusRegisterType, ModbusTransportPort
from core.ports.mqtt_scan_transport_port import MqttScanTransportPort
from core.security.dependencies import require_role
from schemas.devices import DeviceCandidateOut, DeviceOut, ScanModbusRequest, ScanMqttRequest
from services.device_scan_service import scan_bacnet, scan_modbus, scan_mqtt

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


@router.post("/scan/modbus", response_model=list[DeviceCandidateOut])
async def scan_modbus_devices(
    body: ScanModbusRequest,
    transport: ModbusTransportPort = Depends(get_modbus_transport_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
) -> list[DeviceCandidateOut]:
    """RF-001, RF-002, RF-004, RF-005, RF-007 — expone
    `services/device_scan_service.py::scan_modbus` vía HTTP. Un tipo de
    registro sin rango en el body no se escanea (`spec.md §3`).
    `ProblemDetailError` (400, RF-004) propaga sin captura explícita — el
    `exception_handler` de `main.py` la traduce a HTTP."""
    ranges: dict[ModbusRegisterType, tuple[int, int]] = {}
    if body.coils is not None:
        ranges[ModbusRegisterType.COIL] = (body.coils.start, body.coils.count)
    if body.discrete_inputs is not None:
        ranges[ModbusRegisterType.DISCRETE_INPUT] = (
            body.discrete_inputs.start,
            body.discrete_inputs.count,
        )
    if body.holding_registers is not None:
        ranges[ModbusRegisterType.HOLDING_REGISTER] = (
            body.holding_registers.start,
            body.holding_registers.count,
        )
    if body.input_registers is not None:
        ranges[ModbusRegisterType.INPUT_REGISTER] = (
            body.input_registers.start,
            body.input_registers.count,
        )

    candidates = await scan_modbus(
        host=body.host,
        port=body.port,
        unit_id=body.unit_id,
        ranges=ranges,
        transport=transport,
        device_repo=device_repo,
    )
    return [DeviceCandidateOut(**candidate.__dict__) for candidate in candidates]


@router.post("/scan/mqtt", response_model=list[DeviceCandidateOut])
async def scan_mqtt_devices(
    body: ScanMqttRequest,
    transport: MqttScanTransportPort = Depends(get_mqtt_scan_transport_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
) -> list[DeviceCandidateOut]:
    """RF-001, RF-002, RF-004, RF-006 — expone
    `services/device_scan_service.py::scan_mqtt` vía HTTP. `ProblemDetailError`
    (400, RF-004) propaga sin captura explícita — el `exception_handler` de
    `main.py` la traduce a HTTP."""
    candidates = await scan_mqtt(
        topic_pattern=body.topic_pattern,
        transport=transport,
        device_repo=device_repo,
    )
    return [DeviceCandidateOut(**candidate.__dict__) for candidate in candidates]


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
