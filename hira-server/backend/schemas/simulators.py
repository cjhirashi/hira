"""Request/response Pydantic de `POST /simulators/{bacnet,modbus,mqtt}`,
`GET /simulators`, `DELETE /simulators/{device_id}` (`SRV-006-simuladores`).

Traducción exacta de `hira-server/docs/openapi.yaml#/components/schemas`
(Contract-First, escrito antes que este módulo) — no se introduce ningún
campo que el contrato no declare.

`object_type` de `BacnetSimulatedObjectIn` usa un `Literal` de 6 valores —
rechazo 422 estándar de Pydantic/FastAPI para cualquier otro valor, **no**
un 400 RFC 9457 (`plan.md §1`, Registro de decisiones: `spec.md` no define
una rama de error de negocio para "tipo de objeto no soportado").

`StartMqttSimulatorRequest.interval_seconds` **no** lleva `Field(gt=0)` a
propósito — RF-015 exige 400 con el sobre RFC 9457, no el 422 genérico que
produciría FastAPI/Pydantic si se rechazara a nivel de schema antes de
llegar a `services/simulator_service.py::start_mqtt_simulator` (mismo
criterio que `ScanModbusRequest`/`ModbusRangeIn.count`, `SRV-004`).
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BacnetSimulatedObjectIn(BaseModel):
    """Un objeto BACnet inicial del simulador (RF-001) — traduce
    `openapi.yaml#/components/schemas/BacnetSimulatedObjectIn`."""

    object_type: Literal[
        "analog-value",
        "analog-input",
        "analog-output",
        "binary-value",
        "binary-input",
        "binary-output",
    ]
    object_instance: int = Field(ge=0)
    present_value: str


class StartBacnetSimulatorRequest(BaseModel):
    """Body de `POST /simulators/bacnet` (RF-001)."""

    device_instance: int = Field(ge=0, le=4194303)
    objects: list[BacnetSimulatedObjectIn] = Field(default_factory=list)


class ModbusRegisterValueIn(BaseModel):
    """Un registro inicial del simulador Modbus (RF-002) — traduce
    `openapi.yaml#/components/schemas/ModbusRegisterValueIn`."""

    address: int = Field(ge=0)
    value: bool | int


class StartModbusSimulatorRequest(BaseModel):
    """Body de `POST /simulators/modbus` (RF-002)."""

    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    unit_id: int = Field(ge=0, le=255)
    coils: list[ModbusRegisterValueIn] = Field(default_factory=list)
    discrete_inputs: list[ModbusRegisterValueIn] = Field(default_factory=list)
    holding_registers: list[ModbusRegisterValueIn] = Field(default_factory=list)
    input_registers: list[ModbusRegisterValueIn] = Field(default_factory=list)


class StartMqttSimulatorRequest(BaseModel):
    """Body de `POST /simulators/mqtt` (RF-003) — `topic` concreto (sin
    wildcard), a diferencia de `topic_pattern` de `ScanMqttRequest`
    (`SRV-005`). `interval_seconds` deliberadamente sin `Field(gt=0)` (ver
    docstring del módulo): la validación de negocio de RF-015 (400 RFC 9457)
    la hace `services/simulator_service.py::start_mqtt_simulator`."""

    topic: str = Field(min_length=1)
    payload: str
    interval_seconds: float


class SimulatorOut(BaseModel):
    """Simulador en ejecución (RF-001, RF-002, RF-003, RF-010) — traduce
    `services/simulator_registry_service.py::RunningSimulator`."""

    device_id: str
    protocol: str
    address: str
    started_at: datetime
