"""`DeviceRepositoryPort` — interfaz abstracta del repositorio de dominio de
dispositivos/candidatos (`Protocol`, `SRV-ADR-017`), `SRV-003-bacnet-adapter`
(`plan.md §2`, Registro de decisiones: puerto nuevo, no se fuerza en
`DatabasePort` que es *liveness*-only, ni en `UserRepositoryPort` que es un
dominio distinto — mismo criterio ya registrado en `SRV-002-auth-rbac/plan.md`).

`services/device_scan_service.py` y `routers/devices.py` importan este
contrato, nunca `sqlalchemy`/`asyncpg` directamente. La implementación real
(`adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository`) llega
en un batch posterior de `tasks.md` (T-015/T-016) — fuera de alcance aquí. Sin
test propio, igual que `database_port.py`/`user_repository_port.py`: es una
interfaz, no lógica.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class DeviceRecord:
    """Registro de un dispositivo tal como lo expone el repositorio de dominio.

    `protocol` ∈ {"bacnet", "modbus", "mqtt"} — solo `"bacnet"` usado en esta
    feature. `address` es `"<instance_number>@<network_address>"`
    (`core/bacnet_address.py`)."""

    id: str
    name: str
    protocol: str
    address: str
    is_simulator: bool
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DeviceCandidateRecord:
    """Un punto crudo candidato descubierto de un dispositivo (`SRV-ADR-012` —
    nunca promovido automáticamente a una tabla de puntos operables)."""

    id: str
    device_id: str
    object_type: str
    object_instance: int
    object_name: str | None
    present_value: str | None
    units: str | None
    discovered_at: datetime
    updated_at: datetime


class DeviceRepositoryPort(Protocol):
    """Contrato del repositorio de dominio de dispositivos y candidatos
    (RF-002, RF-004, RF-005, RF-009)."""

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        """Crea o actualiza (único por `(protocol, address)`) un dispositivo,
        refrescando `last_seen_at` (RF-002)."""
        ...

    async def list_devices(self) -> list[DeviceRecord]:
        """RF-004."""
        ...

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        """RF-009 — `None` si no existe (el router responde 404)."""
        ...

    async def upsert_candidate(
        self,
        *,
        device_id: str,
        object_type: str,
        object_instance: int,
        object_name: str | None,
        present_value: str | None,
        units: str | None,
    ) -> DeviceCandidateRecord:
        """Único por `(device_id, object_type, object_instance)` — actualiza
        `present_value`/`updated_at` si ya existía, no duplica (RF-002)."""
        ...

    async def list_candidates_for_device(
        self, device_id: str
    ) -> list[DeviceCandidateRecord]:
        """RF-005."""
        ...
