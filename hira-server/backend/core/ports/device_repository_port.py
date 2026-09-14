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

Ampliado en `SRV-006-simuladores` (`plan.md §2`): `get_device_by_address`
(nuevo, RF-006/RF-007 — lectura puntual, "find-or-reject" antes de cualquier
escritura, por el índice único `(protocol, address)` ya existente). La
implementación real de este método nuevo, y la corrección de `upsert_device`
(RF-008, garantía documentada en su docstring), llegan en un batch posterior
(`tasks.md` T-018/T-019) — fuera de alcance de este batch, que solo amplía el
`Protocol`.
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
        refrescando `last_seen_at` (RF-002).

        Garantía RF-008 (`SRV-006-simuladores`): una vez que una fila tiene
        `is_simulator=true`, ninguna llamada posterior con
        `is_simulator=false` la revierte — `is_simulator` solo se apaga por
        un mecanismo explícito que esta versión del contrato no expone
        (RF-011). Esto protege el flujo de escaneo real
        (`scan_bacnet`/`scan_modbus`/`scan_mqtt`, que siempre pasan
        `is_simulator=False` literal) sobre una fila que ya es un simulador
        registrado."""
        ...

    async def list_devices(self) -> list[DeviceRecord]:
        """RF-004."""
        ...

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        """RF-009 — `None` si no existe (el router responde 404)."""
        ...

    async def get_device_by_address(
        self, protocol: str, address: str
    ) -> DeviceRecord | None:
        """`SRV-006-simuladores`, RF-006/RF-007 — lectura puntual por el
        índice único `(protocol, address)` ya existente (`SRV-003`). `None`
        si no existe. Usado como "find-or-reject" **antes** de cualquier
        `upsert_device`, para rechazar con 409 sin escribir nada cuando la
        dirección ya corresponde a un dispositivo real o a un simulador ya
        en ejecución (RF-006), y para reanudar el mismo `device_id` de un
        simulador previamente registrado pero no en ejecución (RF-007)."""
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
