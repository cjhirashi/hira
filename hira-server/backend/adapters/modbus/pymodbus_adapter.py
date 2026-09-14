"""`PymodbusAdapter` — implementación real de `ModbusTransportPort` vía
`pymodbus` (`SRV-004-modbus-adapter`, T-009/T-010, `plan.md §2`).

Solo `adapters/modbus/*` importa `pymodbus` — `services/` sigue importando
únicamente `core/ports/modbus_transport_port.py` (`SRV-ADR-017`).

Notas de implementación (verificadas con ejecución real contra
`pymodbus==3.15.0`, `plan.md §5` nota de investigación — re-verificadas en
esta sesión, ver evidencia en el reporte de tarea):
- `AsyncModbusTcpClient(host, port=port, timeout=timeout_seconds, retries=0)`
  — `retries=0` es imprescindible para que el timeout real de una dirección
  sin respuesta sea `timeout_seconds` (≈1.002s medido) y no lo multiplique
  por reintentos (valor por defecto de `pymodbus`, `retries=3`, produciría
  ~4s — violaría RF-008).
- Una sola conexión TCP por llamada a `read_range` (`client.connect()` una
  vez), reutilizada para las `count` direcciones del rango (RNF-001) — cada
  dirección se lee individualmente (`count=1` por lectura), nunca en batch,
  para que una dirección fallida no aborte las demás (RF-001).
- Una dirección fuera del rango configurado en el dispositivo, o un
  `unit_id`/`device_id` no reconocido, responde con un `ExceptionResponse`
  real del servidor (`result.isError() == True`) — no una excepción de
  Python ni un timeout. Se trata igual que cualquier otro fallo de lectura
  (`ModbusReadFailure`), sin caso especial.
- Una dirección que no responde (servidor caído/silencioso) lanza
  `ModbusException` (`ModbusIOException` en la práctica) — capturada por
  dirección, no aborta el resto del rango (RF-005).
- `read_coils`/`read_discrete_inputs` devuelven `.bits` (lista de `bool`);
  `read_holding_registers`/`read_input_registers` devuelven `.registers`
  (lista de `int`, 0-65535) — se toma el primer elemento de cada lectura de
  `count=1`.
"""
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ModbusPDU

from core.logger import get_logger
from core.ports.modbus_transport_port import (
    ModbusReadFailure,
    ModbusRegisterReading,
    ModbusRegisterType,
)

_logger = get_logger("pymodbus_adapter")

# Mapea cada `ModbusRegisterType` al nombre del método real de
# `AsyncModbusTcpClient` que lo lee (Anti-Abstraction: un solo método de
# puerto, `read_range`, despacha internamente al método de `pymodbus`
# correcto — `plan.md §1`, Registro de decisiones).
_READ_METHOD_NAME = {
    ModbusRegisterType.COIL: "read_coils",
    ModbusRegisterType.DISCRETE_INPUT: "read_discrete_inputs",
    ModbusRegisterType.HOLDING_REGISTER: "read_holding_registers",
    ModbusRegisterType.INPUT_REGISTER: "read_input_registers",
}

# `coil`/`discrete_input` exponen `.bits` (bool); `holding_register`/
# `input_register` exponen `.registers` (int, 0-65535).
_BIT_TYPES = frozenset({ModbusRegisterType.COIL, ModbusRegisterType.DISCRETE_INPUT})


class PymodbusAdapter:
    """Implementa `ModbusTransportPort` con la librería `pymodbus` real."""

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
        client = AsyncModbusTcpClient(
            host, port=port, timeout=timeout_seconds, retries=0
        )
        try:
            await client.connect()
            if not client.connected:
                return [
                    ModbusReadFailure(
                        register_type=register_type,
                        address=start + offset,
                        reason=f"No se pudo conectar a {host}:{port}",
                    )
                    for offset in range(count)
                ]

            read_method = getattr(client, _READ_METHOD_NAME[register_type])
            results: list[ModbusRegisterReading | ModbusReadFailure] = []
            for offset in range(count):
                address = start + offset
                results.append(
                    await self._read_one(
                        read_method, register_type, address, unit_id
                    )
                )
            return results
        finally:
            client.close()

    async def _read_one(
        self,
        read_method,
        register_type: ModbusRegisterType,
        address: int,
        unit_id: int,
    ) -> ModbusRegisterReading | ModbusReadFailure:
        try:
            response: ModbusPDU = await read_method(
                address=address, count=1, device_id=unit_id
            )
        except ModbusException as exc:
            _logger.warning(
                "Fallo leyendo %s:%s (unit_id=%s): %s",
                register_type.value,
                address,
                unit_id,
                exc,
            )
            return ModbusReadFailure(
                register_type=register_type, address=address, reason=str(exc)
            )

        if response.isError():
            _logger.warning(
                "Excepción Modbus leyendo %s:%s (unit_id=%s): %s",
                register_type.value,
                address,
                unit_id,
                response,
            )
            return ModbusReadFailure(
                register_type=register_type, address=address, reason=str(response)
            )

        if register_type in _BIT_TYPES:
            value: bool | int = bool(response.bits[0])
        else:
            value = int(response.registers[0])

        return ModbusRegisterReading(
            register_type=register_type, address=address, value=value
        )
