"""`format_modbus_address` — única regla de negocio pura de
`SRV-004-modbus-adapter` (`plan.md §2`, RF-002). Núcleo sin I/O.

`devices.address` para Modbus combina `host`, `port` y `unit_id` en una sola
columna `VARCHAR` (`spec.md §3`), con el formato fijo
`"<host>:<port>:<unit_id>"` (p. ej. `"192.168.1.50:502:1"`) — decisión ya
cerrada en `plan.md §2`/Registro de decisiones, no una elección abierta de
este batch. `services/device_scan_service.py::scan_modbus` construye la
dirección con esta función antes de persistir (RF-002).

**Sin `parse_modbus_address`** (inversa) — a diferencia de BACnet, ningún
consumidor de esta feature necesita descomponer la dirección (`plan.md §2`,
Registro de decisiones: añadirla "por si acaso" sería anticipación, Art. 10).
"""

_MIN_PORT = 1
_MAX_PORT = 65535
_MIN_UNIT_ID = 0
_MAX_UNIT_ID = 255


def format_modbus_address(host: str, port: int, unit_id: int) -> str:
    """Construye `"<host>:<port>:<unit_id>"` (RF-002).

    Lanza `ValueError` si `host` está vacío (o sólo espacios en blanco), si
    `port` no está en `[1, 65535]`, o si `unit_id` no está en `[0, 255]`
    (límite real de `pymodbus.simulator.SimDevice.id`, `plan.md §2`).
    """
    if not host or not host.strip():
        raise ValueError("host no puede estar vacío")
    if not (_MIN_PORT <= port <= _MAX_PORT):
        raise ValueError(
            f"port debe estar entre {_MIN_PORT} y {_MAX_PORT}, recibido: {port!r}"
        )
    if not (_MIN_UNIT_ID <= unit_id <= _MAX_UNIT_ID):
        raise ValueError(
            f"unit_id debe estar entre {_MIN_UNIT_ID} y {_MAX_UNIT_ID}, "
            f"recibido: {unit_id!r}"
        )
    return f"{host}:{port}:{unit_id}"
