"""`ModbusTransportPort` — interfaz abstracta del transporte Modbus TCP
(`Protocol`, `SRV-ADR-017`), `SRV-004-modbus-adapter` (`plan.md §2`).

`services/device_scan_service.py` importa este contrato y sus value objects,
nunca `pymodbus` directamente (overlay de `hira-server/CLAUDE.md`: "si un
módulo de `services/` importa... `pymodbus`... viola la arquitectura"). La
implementación real (`adapters/modbus/pymodbus_adapter.py::PymodbusAdapter`)
llega en un batch posterior de `tasks.md` (T-009/T-010) — fuera de alcance
aquí. Sin test propio, igual que `bacnet_transport_port.py`/
`device_repository_port.py`: es una interfaz, no lógica.

Un único método (`read_range`) cubre los 4 tipos de registro — la única
diferencia real entre ellos es qué método de `pymodbus` invoca el adaptador
internamente; el contrato de dominio es idéntico en los 4 casos
(Anti-Abstraction, `plan.md §0`/Registro de decisiones).

Los fallos de dirección (`ModbusReadFailure`) son **valor de retorno**, no
excepción — a diferencia de `BacnetReadTimeoutError` de BACnet. En un
escaneo de rango Modbus, "no responde" es el resultado esperado para la
mayoría de direcciones (`plan.md §1`/Registro de decisiones) — usar
excepciones para el caso común de control de flujo es un antipatrón.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ModbusRegisterType(str, Enum):
    """Los 4 tipos de registro Modbus soportados (`spec.md §2`). El valor de
    cada miembro es el `object_type` persistido en `device_points_candidates`
    (`spec.md §3`)."""

    COIL = "coil"
    DISCRETE_INPUT = "discrete_input"
    HOLDING_REGISTER = "holding_register"
    INPUT_REGISTER = "input_register"


@dataclass(frozen=True)
class ModbusRegisterReading:
    """Una dirección que respondió dentro del timeout (RF-001, RF-002)."""

    register_type: ModbusRegisterType
    address: int
    value: bool | int  # bool para coil/discrete_input, int (0-65535) para holding/input registers


@dataclass(frozen=True)
class ModbusReadFailure:
    """Una dirección que no respondió — timeout o excepción Modbus (RF-005).

    No es una excepción de Python (`raise`): en un escaneo de rango, "no
    responde" es el resultado esperado para la mayoría de direcciones — se
    modela como dato, no como control de flujo (`plan.md §1`, Registro de
    decisiones)."""

    register_type: ModbusRegisterType
    address: int
    reason: str  # mensaje de diagnóstico, para el log de `services/`


class ModbusTransportPort(Protocol):
    """Contrato del transporte Modbus TCP (RF-001, RF-002, RF-005, RF-008)."""

    async def read_range(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        register_type: ModbusRegisterType,
        start: int,
        count: int,
        timeout_seconds: float,
    ) -> list[ModbusRegisterReading | ModbusReadFailure]:
        """Abre una conexión TCP a `host:port` (una sola vez, reutilizada
        para las `count` direcciones de este rango — RNF-001) y lee, una
        dirección a la vez (RF-001; nunca en batch, para que una dirección
        fallida no aborte las demás), cada dirección de `start` a
        `start + count - 1` del `register_type` indicado, con `unit_id`
        como Modbus device id. Cada dirección se resuelve a
        `ModbusRegisterReading` (éxito) o `ModbusReadFailure` (timeout o
        excepción Modbus dentro de `timeout_seconds` — RF-005). La lista
        retornada tiene siempre `count` elementos, uno por dirección, en
        orden ascendente."""
        ...
