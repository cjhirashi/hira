"""`BAC0Adapter` — implementación real de `BacnetTransportPort` vía `BAC0`/
`bacpypes3` (`SRV-003-bacnet-adapter`, T-013/T-014, `plan.md §2`).

Solo `adapters/bacnet/*` importa `BAC0`/`bacpypes3` — `services/` sigue
importando únicamente `core/ports/bacnet_transport_port.py` (`SRV-ADR-017`).

Notas de implementación (resuelven la "duda abierta" de `plan.md §5`, spike
real contra `BAC0==2026.7.25`/`bacpypes3==0.0.106`, evidencia de ejecución en
`tests/integration/test_bac0_adapter.py`):
- `bacnet.who_is(address=..., timeout=...)` retorna una lista de
  `bacpypes3.apdu.IAmRequest` (`.pduSource` → dirección de red,
  `.iAmDeviceIdentifier` → tupla `("device", instance_number)`). Con
  `address` fijo (unicast) resuelve tan pronto llega el primer I-Am que
  coincide, sin esperar el `timeout` completo; con `address=None`
  (producción, RF-001) es un broadcast real.
- Cada `who_is()` deja el dispositivo en el `device_info_cache` interno de
  `bacpypes3` (incluye `device_instance`) — `read_device_objects` lo reutiliza
  para no requerir el número de instancia como parámetro (la firma de
  `BacnetTransportPort.read_device_objects` solo recibe `network_address`,
  `plan.md §2`). Si el caché está frío (uso aislado del adaptador sin un
  `who_is` unicast previo a esa dirección — no ocurre en
  `services/device_scan_service.py::scan_bacnet`, que siempre llama
  `who_is()` antes) se resuelve con un `who_is` unicast propio.
- `bacnet.read()` (lectura de una sola propiedad) maneja con gracia una
  propiedad ausente en un objeto que no la tiene (p. ej. `units` en un objeto
  binario retorna `EngineeringUnits("noUnits")` en vez de lanzar, verificado
  con ejecución real) — `bacnet.readMultiple()` en cambio **no** lo hace de
  forma consistente (un `TypeError` interno de `BAC0` si una sola propiedad
  del lote falla en un objeto que no la soporta, verificado con ejecución
  real) — por eso se usa `read()` por propiedad, no `readMultiple()` por
  objeto (Anti-Abstraction: corrección antes que la optimización de menos
  *round-trips*; RNF-001 ya se resuelve con paralelismo entre dispositivos en
  `services/device_scan_service.py`, no dentro de la lectura de un solo
  dispositivo).
- Los objetos `device` (el propio dispositivo) y `network-port` no tienen
  `presentValue` (verificado con ejecución real, `UnknownPropertyError`) — no
  son "puntos" en el sentido de RF-002, se excluyen de los candidatos.
  Cualquier otro objeto que falle al leer sus propiedades se omite (con log,
  no aborta la lectura completa del dispositivo) — no es el timeout de RF-006
  (ese se maneja aparte, en el nivel del dispositivo completo), es una
  propiedad puntual no soportada por ese objeto/dispositivo.
"""
import asyncio
from typing import Any

import BAC0
from bacpypes3.pdu import Address

from core.logger import get_logger
from core.ports.bacnet_transport_port import (
    BacnetDeviceAnnouncement,
    BacnetObjectReading,
    BacnetReadTimeoutError,
)

_logger = get_logger("bac0_adapter")

# El objeto `device` (el dispositivo en sí) y `network-port` no son "puntos"
# BACnet (no tienen `presentValue`) — no se persisten como candidatos (RF-002).
_NON_POINT_OBJECT_TYPES = frozenset({"device", "network-port"})

_UNITS_NONE_VALUES = frozenset({"no-units", "noUnits"})


class BAC0Adapter:
    """Implementa `BacnetTransportPort` con la librería `BAC0` real."""

    def __init__(
        self,
        *,
        ip: str | None = None,
        port: int | None = None,
        target_address: str | None = None,
    ) -> None:
        """`ip`/`port`: interfaz local (`None` → `BAC0` autodetecta, `plan.md
        §1`). `target_address`: **solo para tests de integración** — dirige el
        Who-Is a una dirección unicast específica en vez de broadcast, para no
        depender de que el broadcast UDP atraviese la red/namespace del
        entorno de test (`plan.md §5`). En producción se deja `None`
        (broadcast real, RF-001) — no forma parte de `BacnetTransportPort`."""
        self._bacnet = BAC0.lite(ip=ip, port=port, ping=False)
        self._target_address = target_address

    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        iams = await self._bacnet.who_is(
            address=self._target_address, timeout=timeout_seconds
        )
        return [
            BacnetDeviceAnnouncement(
                instance_number=int(iam.iAmDeviceIdentifier[1]),
                network_address=str(iam.pduSource),
            )
            for iam in iams
        ]

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        try:
            return await asyncio.wait_for(
                self._read_device_objects(network_address, timeout_seconds),
                timeout_seconds,
            )
        except asyncio.TimeoutError as exc:
            raise BacnetReadTimeoutError(
                f"Timeout leyendo objetos de {network_address} "
                f"({timeout_seconds}s, RF-006/RF-010)"
            ) from exc

    async def disconnect(self) -> None:
        """Libera el socket UDP local — usado en tests de integración y
        shutdown (mismo criterio que `PostgreSQLUserRepository.close()`)."""
        await self._bacnet.disconnect()

    async def _read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        instance_number = await self._resolve_device_instance(
            network_address, timeout_seconds
        )
        object_list = await self._bacnet.read(
            f"{network_address} device:{instance_number} objectList"
        )

        readings: list[BacnetObjectReading] = []
        for object_type, object_instance in object_list:
            type_name = str(object_type)
            if type_name in _NON_POINT_OBJECT_TYPES:
                continue
            reading = await self._read_one_object(
                network_address, type_name, int(object_instance)
            )
            if reading is not None:
                readings.append(reading)
        return readings

    async def _resolve_device_instance(
        self, network_address: str, timeout_seconds: float
    ) -> int:
        device_info_cache = self._bacnet.this_application.app.device_info_cache
        device_info = await device_info_cache.get_device_info(Address(network_address))
        if device_info is not None:
            return device_info.device_instance

        iams = await self._bacnet.who_is(address=network_address, timeout=timeout_seconds)
        if not iams:
            raise BacnetReadTimeoutError(
                f"No se pudo resolver el número de instancia de {network_address}"
            )
        return int(iams[0].iAmDeviceIdentifier[1])

    async def _read_one_object(
        self, network_address: str, object_type: str, object_instance: int
    ) -> BacnetObjectReading | None:
        try:
            object_name = await self._read_property(
                network_address, object_type, object_instance, "objectName"
            )
            present_value = await self._read_property(
                network_address, object_type, object_instance, "presentValue"
            )
            units = await self._read_property(
                network_address, object_type, object_instance, "units"
            )
        except Exception as exc:  # noqa: BLE001 — objeto puntual no soportado, no aborta el dispositivo
            _logger.warning(
                "No se pudo leer %s:%s de %s: %s",
                object_type,
                object_instance,
                network_address,
                exc,
            )
            return None

        return BacnetObjectReading(
            object_type=object_type,
            object_instance=object_instance,
            object_name=None if object_name is None else str(object_name),
            present_value=None if present_value is None else str(present_value),
            units=_normalize_units(units),
        )

    async def _read_property(
        self,
        network_address: str,
        object_type: str,
        object_instance: int,
        property_name: str,
    ) -> Any:
        return await self._bacnet.read(
            f"{network_address} {object_type} {object_instance} {property_name}"
        )


def _normalize_units(units: Any) -> str | None:
    """`None` si el objeto no soporta `units` (BAC0 retorna `noUnits`/`no-units`
    en vez de lanzar, ver docstring del módulo) — evita persistir un valor de
    "sin unidades" como si fuera una unidad real."""
    if units is None:
        return None
    text = str(units)
    return None if text in _UNITS_NONE_VALUES else text
