"""`core/modbus_address.py` — núcleo puro, sin I/O (`SRV-004-modbus-adapter`).

Contrato exacto ya fijado en `plan.md §2`/Registro de decisiones (no es una
decisión abierta de este batch): `format_modbus_address(host, port, unit_id)
-> str` construye `"<host>:<port>:<unit_id>"` (RF-002); valida `host` no
vacío/sólo espacios, `1 <= port <= 65535`, `0 <= unit_id <= 255`. **Sin**
`parse_modbus_address` — a diferencia de BACnet, ningún consumidor de esta
feature necesita descomponer la dirección (`plan.md §1`, Registro de
decisiones: "sin función inversa... sería anticipación").

Debe fallar antes de T-002 (`core/modbus_address.py` no existe todavía).
"""
import pytest

from core.modbus_address import format_modbus_address


def test_format_modbus_address_construye_host_puerto_unit_id():
    assert format_modbus_address("192.168.1.50", 502, 1) == "192.168.1.50:502:1"


def test_format_modbus_address_round_trip_con_varios_valores():
    casos = [
        ("127.0.0.1", 502, 0),
        ("10.0.0.5", 1502, 255),
        ("modbus-plc.local", 502, 247),
    ]
    for host, port, unit_id in casos:
        address = format_modbus_address(host, port, unit_id)
        assert address == f"{host}:{port}:{unit_id}"


def test_format_modbus_address_rechaza_host_vacio():
    with pytest.raises(ValueError):
        format_modbus_address("", 502, 1)


def test_format_modbus_address_rechaza_host_solo_espacios():
    with pytest.raises(ValueError):
        format_modbus_address("   ", 502, 1)


def test_format_modbus_address_rechaza_port_menor_a_1():
    with pytest.raises(ValueError):
        format_modbus_address("192.168.1.50", 0, 1)


def test_format_modbus_address_rechaza_port_mayor_a_65535():
    with pytest.raises(ValueError):
        format_modbus_address("192.168.1.50", 65536, 1)


def test_format_modbus_address_acepta_port_en_los_limites():
    assert format_modbus_address("192.168.1.50", 1, 0) == "192.168.1.50:1:0"
    assert format_modbus_address("192.168.1.50", 65535, 255) == "192.168.1.50:65535:255"


def test_format_modbus_address_rechaza_unit_id_negativo():
    with pytest.raises(ValueError):
        format_modbus_address("192.168.1.50", 502, -1)


def test_format_modbus_address_rechaza_unit_id_mayor_a_255():
    with pytest.raises(ValueError):
        format_modbus_address("192.168.1.50", 502, 256)
