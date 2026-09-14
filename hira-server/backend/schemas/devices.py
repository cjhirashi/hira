"""Response Pydantic de `GET /devices|/devices/{id}/candidates` y
`POST /devices/scan/bacnet` (`SRV-003-bacnet-adapter`).

Traducción exacta de `hira-server/docs/openapi.yaml#/components/schemas`
(Contract-First, `tasks.md` T-007, escrito antes que este módulo) — no se
introduce ningún campo que el contrato no declare.
"""
from datetime import datetime

from pydantic import BaseModel


class DeviceOut(BaseModel):
    """Dispositivo persistido (RF-004) — traduce
    `core.ports.device_repository_port.DeviceRecord`."""

    id: str
    name: str
    protocol: str
    address: str
    is_simulator: bool
    last_seen_at: datetime | None


class DeviceCandidateOut(BaseModel):
    """Punto crudo candidato de un dispositivo (RF-005) — traduce
    `core.ports.device_repository_port.DeviceCandidateRecord`."""

    id: str
    object_type: str
    object_instance: int
    object_name: str | None
    present_value: str | None
    units: str | None
    discovered_at: datetime
    updated_at: datetime
