"""`POST /simulators/{bacnet,modbus,mqtt}`, `GET /simulators`,
`DELETE /simulators/{device_id}` — adaptador de entrada HTTP
(`SRV-006-simuladores`).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1simulators~1bacnet`
(+ `~1simulators~1modbus`, `~1simulators~1mqtt`, `~1simulators`,
`~1simulators~1{device_id}`), escrito antes que este router (Contract-First).

**Router nuevo, separado de `routers/devices.py`** (`plan.md §2`, Registro de
decisiones): RBAC mixto — `POST`/`DELETE` solo Admin (`require_role("admin")`,
RF-004), `GET` Admin+Operador (`require_role("admin", "operador")`, RF-005) —
por eso **sin** `dependencies=` a nivel de router, cada ruta aplica el suyo.

Inyecta `BacnetSimulatorPort`/`ModbusSimulatorPort`/`MqttPublisherPort`/
`DeviceRepositoryPort` vía `Depends(adapters.factory.*)` y
`SimulatorRegistryService` vía `Depends(services.simulator_registry_service.
get_simulator_registry)` — nunca instancia un adaptador concreto
(`SRV-ADR-017`). Delega la lógica a `services/simulator_service.py`.
`ProblemDetailError` (400/403/404/409) propaga sin captura explícita — el
`exception_handler` de `main.py` la traduce a HTTP.
"""
from fastapi import APIRouter, Depends, Response

from adapters.factory import (
    get_bacnet_simulator_port,
    get_device_repository_port,
    get_modbus_simulator_port,
    get_mqtt_publisher_port,
)
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec, BacnetSimulatorPort
from core.ports.device_repository_port import DeviceRepositoryPort
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec, ModbusSimulatorPort
from core.ports.modbus_transport_port import ModbusRegisterType
from core.ports.mqtt_publisher_port import MqttPublisherPort
from core.security.dependencies import require_role
from schemas.simulators import (
    SimulatorOut,
    StartBacnetSimulatorRequest,
    StartModbusSimulatorRequest,
    StartMqttSimulatorRequest,
)
from services.simulator_registry_service import RunningSimulator, SimulatorRegistryService, get_simulator_registry
from services.simulator_service import (
    start_bacnet_simulator,
    start_modbus_simulator,
    start_mqtt_simulator,
    stop_simulator,
)

router = APIRouter(prefix="/simulators", tags=["simulators"])


def _to_out(entry: RunningSimulator) -> SimulatorOut:
    return SimulatorOut(
        device_id=entry.device_id,
        protocol=entry.protocol,
        address=entry.address,
        started_at=entry.started_at,
    )


@router.post("/bacnet", response_model=SimulatorOut, status_code=201)
async def start_bacnet_simulator_endpoint(
    body: StartBacnetSimulatorRequest,
    _: None = Depends(require_role("admin")),
    transport: BacnetSimulatorPort = Depends(get_bacnet_simulator_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
    registry: SimulatorRegistryService = Depends(get_simulator_registry),
) -> SimulatorOut:
    """RF-001, RF-004, RF-006, RF-007 — expone
    `services/simulator_service.py::start_bacnet_simulator` vía HTTP."""
    objects = [
        BacnetSimulatedObjectSpec(
            object_type=obj.object_type,
            object_instance=obj.object_instance,
            present_value=obj.present_value,
        )
        for obj in body.objects
    ]
    entry = await start_bacnet_simulator(
        device_instance=body.device_instance,
        objects=objects,
        transport=transport,
        device_repo=device_repo,
        registry=registry,
    )
    return _to_out(entry)


@router.post("/modbus", response_model=SimulatorOut, status_code=201)
async def start_modbus_simulator_endpoint(
    body: StartModbusSimulatorRequest,
    _: None = Depends(require_role("admin")),
    transport: ModbusSimulatorPort = Depends(get_modbus_simulator_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
    registry: SimulatorRegistryService = Depends(get_simulator_registry),
) -> SimulatorOut:
    """RF-002, RF-004, RF-006, RF-007 — expone
    `services/simulator_service.py::start_modbus_simulator` vía HTTP."""
    registers: list[ModbusSimulatedRegisterSpec] = []
    for register_type, values in (
        (ModbusRegisterType.COIL, body.coils),
        (ModbusRegisterType.DISCRETE_INPUT, body.discrete_inputs),
        (ModbusRegisterType.HOLDING_REGISTER, body.holding_registers),
        (ModbusRegisterType.INPUT_REGISTER, body.input_registers),
    ):
        for value in values:
            registers.append(
                ModbusSimulatedRegisterSpec(
                    register_type=register_type, address=value.address, value=value.value
                )
            )

    entry = await start_modbus_simulator(
        host=body.host,
        port=body.port,
        unit_id=body.unit_id,
        registers=registers,
        transport=transport,
        device_repo=device_repo,
        registry=registry,
    )
    return _to_out(entry)


@router.post("/mqtt", response_model=SimulatorOut, status_code=201)
async def start_mqtt_simulator_endpoint(
    body: StartMqttSimulatorRequest,
    _: None = Depends(require_role("admin")),
    transport: MqttPublisherPort = Depends(get_mqtt_publisher_port),
    device_repo: DeviceRepositoryPort = Depends(get_device_repository_port),
    registry: SimulatorRegistryService = Depends(get_simulator_registry),
) -> SimulatorOut:
    """RF-003, RF-004, RF-006, RF-007, RF-014, RF-015 — expone
    `services/simulator_service.py::start_mqtt_simulator` vía HTTP."""
    entry = await start_mqtt_simulator(
        topic=body.topic,
        payload=body.payload,
        interval_seconds=body.interval_seconds,
        transport=transport,
        device_repo=device_repo,
        registry=registry,
    )
    return _to_out(entry)


@router.get("", response_model=list[SimulatorOut])
async def list_simulators_endpoint(
    _: None = Depends(require_role("admin", "operador")),
    registry: SimulatorRegistryService = Depends(get_simulator_registry),
) -> list[SimulatorOut]:
    """RF-005, RF-010 — lista los simuladores actualmente en ejecución
    (lectura directa del registro, mismo criterio que
    `routers/devices.py::list_devices`)."""
    return [_to_out(entry) for entry in registry.list_running()]


@router.delete("/{device_id}", status_code=204)
async def stop_simulator_endpoint(
    device_id: str,
    _: None = Depends(require_role("admin")),
    bacnet_transport: BacnetSimulatorPort = Depends(get_bacnet_simulator_port),
    modbus_transport: ModbusSimulatorPort = Depends(get_modbus_simulator_port),
    mqtt_transport: MqttPublisherPort = Depends(get_mqtt_publisher_port),
    registry: SimulatorRegistryService = Depends(get_simulator_registry),
) -> Response:
    """RF-004, RF-009, RF-012 — expone
    `services/simulator_service.py::stop_simulator` vía HTTP. `204` sin
    cuerpo."""
    await stop_simulator(
        device_id=device_id,
        registry=registry,
        bacnet_transport=bacnet_transport,
        modbus_transport=modbus_transport,
        mqtt_transport=mqtt_transport,
    )
    return Response(status_code=204)
