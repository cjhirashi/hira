"""`format_device_address`/`parse_device_address` — única regla de negocio pura
de `SRV-003-bacnet-adapter` (`plan.md §2`, RF-002). Núcleo sin I/O.

`devices.address` combina el *instance number* BACnet y la dirección de red
(IP:puerto) en una sola columna `VARCHAR` (`spec.md §3`: "instance number +
IP:puerto"), con el formato fijo `"<instance_number>@<network_address>"` (p.
ej. `"1234@192.168.1.50:47808"`) — decisión ya cerrada en `plan.md §2`/Registro
de decisiones, no una elección abierta de este batch. `services/
device_scan_service.py` construye la dirección con `format_device_address`
antes de persistir (RF-002); `parse_device_address` es su inverso exacto, para
cuando un consumidor futuro necesite descomponerla sin volver a tocar el
escaneo.

`format_simulator_device_address` (`SRV-006-simuladores`, `plan.md §2`/
Registro de decisiones) es una **ampliación**, no un reemplazo: identidad
restart-safe de un simulador BACnet (`str(device_instance)`, sin `@`) —
distinta del formato de dispositivos reales de arriba. Ver el razonamiento
completo en `.harness/specs/SRV-006-simuladores/plan.md §2`, Registro de
decisiones: la identidad debe ser calculable solo a partir del cuerpo del
request (RF-007), sin depender del puerto UDP efímero que ocupa cada
instancia simulada.
"""

_SEPARATOR = "@"
_MIN_SIMULATOR_DEVICE_INSTANCE = 0
_MAX_SIMULATOR_DEVICE_INSTANCE = 4194303


def format_device_address(instance_number: int, network_address: str) -> str:
    """Construye `"<instance_number>@<network_address>"` (RF-002).

    Lanza `ValueError` si `instance_number < 0` o `network_address` está vacío
    (o sólo espacios en blanco).
    """
    if instance_number < 0:
        raise ValueError(
            f"instance_number debe ser >= 0, recibido: {instance_number!r}"
        )
    if not network_address or not network_address.strip():
        raise ValueError("network_address no puede estar vacío")
    return f"{instance_number}{_SEPARATOR}{network_address}"


def parse_device_address(address: str) -> tuple[int, str]:
    """Inverso exacto de `format_device_address` (RF-002).

    Lanza `ValueError` si `address` no tiene el formato
    `"<instance_number>@<network_address>"`, si `instance_number` no es un
    entero válido (o es negativo), o si `network_address` queda vacío.
    """
    if _SEPARATOR not in address:
        raise ValueError(
            f"Dirección BACnet mal formada (falta '{_SEPARATOR}'): {address!r}"
        )
    raw_instance_number, network_address = address.split(_SEPARATOR, 1)
    try:
        instance_number = int(raw_instance_number)
    except ValueError as exc:
        raise ValueError(
            f"instance_number no es un entero válido: {raw_instance_number!r}"
        ) from exc
    if instance_number < 0:
        raise ValueError(
            f"instance_number debe ser >= 0, recibido: {instance_number!r}"
        )
    if not network_address or not network_address.strip():
        raise ValueError("network_address no puede estar vacío")
    return instance_number, network_address


def format_simulator_device_address(device_instance: int) -> str:
    """Identidad restart-safe de un simulador BACnet (`SRV-006-simuladores`,
    RF-001, RF-007): retorna `str(device_instance)`, sin `@` — distinta del
    formato `"<instance>@<network>"` de dispositivos reales (`SRV-003`).

    Lanza `ValueError` si `device_instance` está fuera de
    `[0, 4194303]` (rango real de *instance number* BACnet).
    """
    if not (
        _MIN_SIMULATOR_DEVICE_INSTANCE
        <= device_instance
        <= _MAX_SIMULATOR_DEVICE_INSTANCE
    ):
        raise ValueError(
            "device_instance debe estar entre "
            f"{_MIN_SIMULATOR_DEVICE_INSTANCE} y "
            f"{_MAX_SIMULATOR_DEVICE_INSTANCE}, recibido: {device_instance!r}"
        )
    return str(device_instance)
