"""`BacnetTransportPort` — interfaz abstracta del transporte BACnet/IP
(`Protocol`, `SRV-ADR-017`), `SRV-003-bacnet-adapter` (`plan.md §2`).

`services/device_scan_service.py` importa este contrato y sus value objects,
nunca `BAC0`/`bacpypes3` directamente (overlay de `hira-server/CLAUDE.md`: "si
un módulo de `services/` importa... `BAC0`... viola la arquitectura"). La
implementación real (`adapters/bacnet/bac0_adapter.py::BAC0Adapter`) llega en
un batch posterior de `tasks.md` (T-013/T-014) — fuera de alcance aquí. Sin
test propio, igual que `database_port.py`/`user_repository_port.py`: es una
interfaz, no lógica.
"""
from dataclasses import dataclass
from typing import Protocol


class BacnetReadTimeoutError(Exception):
    """El dispositivo no respondió a la lectura de objetos dentro del timeout
    (RF-006, RF-010). Sin I/O — es una señal de dominio, no una excepción de
    red cruda de BAC0/bacpypes3."""


@dataclass(frozen=True)
class BacnetDeviceAnnouncement:
    """Un dispositivo que respondió I-Am durante un Who-Is (RF-001, RF-002)."""

    instance_number: int
    network_address: str  # dirección de red BACnet tal como la expone BAC0 (p. ej. "192.168.1.50:47808")


@dataclass(frozen=True)
class BacnetObjectReading:
    """Un objeto BACnet leído de un dispositivo (RF-002)."""

    object_type: str  # p. ej. "analogInput", "binaryOutput"
    object_instance: int
    object_name: str | None
    present_value: str | None  # serializado a texto — `plan.md §0`/§2, Anti-Abstraction
    units: str | None


class BacnetTransportPort(Protocol):
    """Contrato del transporte BACnet/IP (RF-001, RF-002, RF-006, RF-010)."""

    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        """Emite un Who-Is (broadcast en producción) y retorna los I-Am
        recibidos dentro de `timeout_seconds` (RF-001). Lista vacía si nadie
        responde (RF-008)."""
        ...

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        """Lee la lista de objetos del dispositivo en `network_address`
        (RF-002). Lanza `BacnetReadTimeoutError` si no responde dentro de
        `timeout_seconds` (RF-006, RF-010)."""
        ...
