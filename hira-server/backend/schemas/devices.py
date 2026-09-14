"""Response/request Pydantic de `GET /devices|/devices/{id}/candidates`,
`POST /devices/scan/bacnet` (`SRV-003-bacnet-adapter`) y
`POST /devices/scan/modbus` (`SRV-004-modbus-adapter`).

Traducción exacta de `hira-server/docs/openapi.yaml#/components/schemas`
(Contract-First, escrito antes que este módulo) — no se introduce ningún
campo que el contrato no declare.

`ModbusRangeIn.count` **no** lleva `Field(le=125)` a propósito — ver
docstring de `ScanModbusRequest` abajo: RF-004 exige 400 con el sobre RFC
9457, no el 422 genérico que produciría FastAPI/Pydantic si el rango se
rechazara a nivel de schema antes de llegar a
`services/device_scan_service.py::scan_modbus`.
"""
from datetime import datetime

from pydantic import BaseModel, Field


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


class ModbusRangeIn(BaseModel):
    """Rango de direcciones a sondear para un tipo de registro Modbus
    (`SRV-004-modbus-adapter`) — traduce
    `openapi.yaml#/components/schemas/ModbusRegisterRange`.

    `count` deliberadamente sin `Field(le=125)` (ver docstring del módulo):
    la validación de negocio de RF-004 (400 RFC 9457) la hace
    `services/device_scan_service.py::scan_modbus`, no este schema."""

    start: int = Field(ge=0)
    count: int = Field(ge=1)


class ScanModbusRequest(BaseModel):
    """Body de `POST /devices/scan/modbus` (RF-001) — un tipo de registro sin
    rango no se escanea (`spec.md §3`)."""

    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    unit_id: int = Field(ge=0, le=255)
    coils: ModbusRangeIn | None = None
    discrete_inputs: ModbusRangeIn | None = None
    holding_registers: ModbusRangeIn | None = None
    input_registers: ModbusRangeIn | None = None
