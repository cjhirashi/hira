"""`services/simulator_service.py` — coordinación de arranque/detención de
simuladores de dispositivos (`SRV-006-simuladores`, `plan.md §2`).

Implementa **RF-001, RF-002, RF-003, RF-006, RF-007, RF-009, RF-011, RF-012,
RF-014, RF-015, RNF-001**.

Solo importa de `core/ports/`, `core/bacnet_address.py`,
`core/modbus_address.py`, `core/errors.py`, `core/logger.py`, y
`services/simulator_registry_service.py` (estado en memoria, no un puerto) —
nunca de `adapters/` ni de FastAPI (`SRV-ADR-017`). Recibe los puertos por
parámetro (`adapters/factory.py` los inyecta desde `routers/simulators.py`).

RF-011 ("sin mecanismo para quitar `is_simulator`") se cumple por **omisión
de diseño**: ningún `upsert_device` de este módulo pasa `is_simulator=False`
— los 3 `start_*_simulator` solo llaman `upsert_device(...,
is_simulator=True)`. RF-009 ("no elimina el dispositivo ni sus candidatos")
también por omisión: `stop_simulator` no importa ni referencia ningún método
de borrado (no existe en `DeviceRepositoryPort`).
"""
from datetime import datetime, timezone

from core.bacnet_address import format_simulator_device_address
from core.errors import ProblemDetailError
from core.logger import get_logger
from core.modbus_address import format_modbus_address
from core.ports.bacnet_simulator_port import BacnetSimulatedObjectSpec, BacnetSimulatorPort
from core.ports.device_repository_port import DeviceRecord, DeviceRepositoryPort
from core.ports.modbus_simulator_port import ModbusSimulatedRegisterSpec, ModbusSimulatorPort
from core.ports.mqtt_publisher_port import MqttInvalidPublishError, MqttPublisherPort
from services.simulator_registry_service import RunningSimulator, SimulatorRegistryService

_ERRORS_BASE_URL = "https://hira.dev/errors"

_logger = get_logger("simulator_service")


def _address_conflict_error(address: str) -> ProblemDetailError:
    """RF-006 — la dirección ya corresponde a un dispositivo real."""
    return ProblemDetailError(
        status=409,
        type_=f"{_ERRORS_BASE_URL}/simulator-address-conflict",
        title="Dirección ya registrada",
        detail=f"La dirección '{address}' ya corresponde a un dispositivo real.",
    )


def _already_running_error(address: str) -> ProblemDetailError:
    """RF-006 — la dirección ya tiene un simulador en ejecución."""
    return ProblemDetailError(
        status=409,
        type_=f"{_ERRORS_BASE_URL}/simulator-already-running",
        title="Simulador ya en ejecución",
        detail=f"Ya hay un simulador en ejecución en la dirección '{address}'.",
    )


def _not_running_error(device_id: str) -> ProblemDetailError:
    """RF-012 — cubre los 3 sub-casos de una sola vez: no existe, es
    `is_simulator=false`, o ya está detenido — ninguno está en el registro."""
    return ProblemDetailError(
        status=404,
        type_=f"{_ERRORS_BASE_URL}/simulator-not-running",
        title="Simulador no encontrado",
        detail=f"No hay ningún simulador en ejecución con device_id '{device_id}'.",
    )


def _invalid_publish_error(topic: str, exc: Exception) -> ProblemDetailError:
    """RF-014."""
    return ProblemDetailError(
        status=400,
        type_=f"{_ERRORS_BASE_URL}/mqtt-invalid-publish",
        title="Publicación MQTT inválida",
        detail=f"El topic/payload para '{topic}' fue rechazado al publicar: {exc}",
    )


def _invalid_interval_error(interval_seconds: float) -> ProblemDetailError:
    """RF-015."""
    return ProblemDetailError(
        status=400,
        type_=f"{_ERRORS_BASE_URL}/mqtt-invalid-interval",
        title="Intervalo inválido",
        detail=f"interval_seconds debe ser > 0, recibido: {interval_seconds!r}.",
    )


async def _check_conflict(
    protocol: str, address: str, device_repo: DeviceRepositoryPort, registry: SimulatorRegistryService
) -> DeviceRecord | None:
    """RF-006/RF-007 — "find-or-reject": lee `device_repo` por
    `(protocol, address)` **antes** de arrancar ningún proceso. Rechaza con
    409 si la dirección ya es un dispositivo real (`is_simulator=false`) o
    si ya tiene un simulador en ejecución en el registro. Retorna el
    `DeviceRecord` existente (o `None`) para que el llamador sepa si está
    reanudando (RF-007)."""
    existing = await device_repo.get_device_by_address(protocol, address)
    if existing is not None and not existing.is_simulator:
        raise _address_conflict_error(address)
    if existing is not None and registry.is_running(existing.id):
        raise _already_running_error(address)
    return existing


async def start_bacnet_simulator(
    *,
    device_instance: int,
    objects: list[BacnetSimulatedObjectSpec],
    transport: BacnetSimulatorPort,
    device_repo: DeviceRepositoryPort,
    registry: SimulatorRegistryService,
) -> RunningSimulator:
    """RF-001, RF-006, RF-007, RNF-001."""
    address = format_simulator_device_address(device_instance)
    async with registry.lock:
        await _check_conflict("bacnet", address, device_repo, registry)

        token = await transport.start(device_instance=device_instance, objects=objects)
        try:
            device = await device_repo.upsert_device(
                name=f"Simulador BACnet {device_instance}",
                protocol="bacnet",
                address=address,
                is_simulator=True,
            )
            for obj in objects:
                await device_repo.upsert_candidate(
                    device_id=device.id,
                    object_type=obj.object_type,
                    object_instance=obj.object_instance,
                    object_name=None,
                    present_value=obj.present_value,
                    units=None,
                )
        except Exception:
            _logger.warning(
                "Limpieza defensiva: deteniendo simulador BACnet device_instance=%s "
                "tras fallo de persistencia",
                device_instance,
            )
            await transport.stop(token)
            raise

        entry = RunningSimulator(
            device_id=device.id,
            protocol="bacnet",
            address=address,
            token=token,
            started_at=datetime.now(timezone.utc),
        )
        registry.register(entry)
        return entry


async def start_modbus_simulator(
    *,
    host: str,
    port: int,
    unit_id: int,
    registers: list[ModbusSimulatedRegisterSpec],
    transport: ModbusSimulatorPort,
    device_repo: DeviceRepositoryPort,
    registry: SimulatorRegistryService,
) -> RunningSimulator:
    """RF-002, RF-006, RF-007, RNF-001."""
    address = format_modbus_address(host, port, unit_id)
    async with registry.lock:
        await _check_conflict("modbus", address, device_repo, registry)

        token = await transport.start(host=host, port=port, unit_id=unit_id, registers=registers)
        try:
            device = await device_repo.upsert_device(
                name=f"Simulador Modbus {address}",
                protocol="modbus",
                address=address,
                is_simulator=True,
            )
            for spec in registers:
                await device_repo.upsert_candidate(
                    device_id=device.id,
                    object_type=spec.register_type.value,
                    object_instance=spec.address,
                    object_name=None,
                    present_value=str(spec.value),
                    units=None,
                )
        except Exception:
            _logger.warning(
                "Limpieza defensiva: deteniendo simulador Modbus address=%s "
                "tras fallo de persistencia",
                address,
            )
            await transport.stop(token)
            raise

        entry = RunningSimulator(
            device_id=device.id,
            protocol="modbus",
            address=address,
            token=token,
            started_at=datetime.now(timezone.utc),
        )
        registry.register(entry)
        return entry


async def start_mqtt_simulator(
    *,
    topic: str,
    payload: str,
    interval_seconds: float,
    transport: MqttPublisherPort,
    device_repo: DeviceRepositoryPort,
    registry: SimulatorRegistryService,
) -> RunningSimulator:
    """RF-003, RF-006, RF-007, RF-014, RF-015, RNF-001."""
    if interval_seconds <= 0:
        raise _invalid_interval_error(interval_seconds)

    async with registry.lock:
        await _check_conflict("mqtt", topic, device_repo, registry)

        try:
            token = await transport.start(topic=topic, payload=payload, interval_seconds=interval_seconds)
        except MqttInvalidPublishError as exc:
            raise _invalid_publish_error(topic, exc) from exc

        try:
            device = await device_repo.upsert_device(
                name=f"Simulador MQTT {topic}",
                protocol="mqtt",
                address=topic,
                is_simulator=True,
            )
        except Exception:
            _logger.warning(
                "Limpieza defensiva: deteniendo simulador MQTT topic=%s "
                "tras fallo de persistencia",
                topic,
            )
            await transport.stop(token)
            raise

        entry = RunningSimulator(
            device_id=device.id,
            protocol="mqtt",
            address=topic,
            token=token,
            started_at=datetime.now(timezone.utc),
        )
        registry.register(entry)
        return entry


async def stop_simulator(
    *,
    device_id: str,
    registry: SimulatorRegistryService,
    bacnet_transport: BacnetSimulatorPort,
    modbus_transport: ModbusSimulatorPort,
    mqtt_transport: MqttPublisherPort,
) -> None:
    """RF-009, RF-012 — despacha al puerto correcto según `entry.protocol`.

    `registry.get(device_id) is None` cubre los 3 sub-casos de RF-012 de una
    sola vez (no existe, es `is_simulator=false`, o ya está detenido —
    ninguno está en el registro)."""
    async with registry.lock:
        entry = registry.get(device_id)
        if entry is None:
            raise _not_running_error(device_id)

        transport_by_protocol = {
            "bacnet": bacnet_transport,
            "modbus": modbus_transport,
            "mqtt": mqtt_transport,
        }
        transport = transport_by_protocol[entry.protocol]
        await transport.stop(entry.token)
        registry.unregister(device_id)
