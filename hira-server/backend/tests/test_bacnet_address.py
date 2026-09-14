"""`core/bacnet_address.py` — núcleo puro, sin I/O (`SRV-003-bacnet-adapter`,
ampliado en `SRV-006-simuladores`).

Contrato exacto ya fijado en `plan.md §2` (no es una decisión abierta de este
batch): `format_device_address(instance_number, network_address) -> str`
construye `"<instance_number>@<network_address>"`; `parse_device_address(address)
-> tuple[int, str]` es su inverso exacto. Ambas validan (RF-002): rechazan
`instance_number < 0` y `network_address` vacío/sólo espacios.

`format_simulator_device_address(device_instance) -> str` (`SRV-006`,
`plan.md §2`/Registro de decisiones) retorna `str(device_instance)` —
identidad restart-safe de un simulador BACnet, **distinta** del formato
`"<instance>@<network>"` de dispositivos reales — valida `0 <= device_instance
<= 4194303` (RF-001, RF-007). Debe fallar antes de T-002 (`core/
bacnet_address.py::format_simulator_device_address` no existe todavía).
"""
import pytest

from core.bacnet_address import (
    format_device_address,
    format_simulator_device_address,
    parse_device_address,
)


def test_format_device_address_construye_instance_arroba_network():
    assert (
        format_device_address(1234, "192.168.1.50:47808")
        == "1234@192.168.1.50:47808"
    )


def test_parse_device_address_es_el_inverso_exacto_de_format():
    address = format_device_address(999, "10.0.0.5:47808")

    instance_number, network_address = parse_device_address(address)

    assert instance_number == 999
    assert network_address == "10.0.0.5:47808"


def test_format_luego_parse_round_trip_con_varios_valores():
    casos = [
        (0, "127.0.0.1:47808"),
        (4194302, "192.168.100.200:47809"),
    ]
    for instance_number, network_address in casos:
        address = format_device_address(instance_number, network_address)
        assert parse_device_address(address) == (instance_number, network_address)


def test_format_rechaza_instance_number_negativo():
    with pytest.raises(ValueError):
        format_device_address(-1, "192.168.1.50:47808")


def test_format_rechaza_network_address_vacio():
    with pytest.raises(ValueError):
        format_device_address(1234, "")


def test_format_rechaza_network_address_solo_espacios():
    with pytest.raises(ValueError):
        format_device_address(1234, "   ")


def test_parse_rechaza_direccion_sin_separador_arroba():
    with pytest.raises(ValueError):
        parse_device_address("1234-192.168.1.50:47808")


def test_parse_rechaza_instance_number_no_entero():
    with pytest.raises(ValueError):
        parse_device_address("no-es-un-numero@192.168.1.50:47808")


def test_parse_rechaza_network_address_vacio_tras_arroba():
    with pytest.raises(ValueError):
        parse_device_address("1234@")


def test_parse_rechaza_instance_number_negativo():
    with pytest.raises(ValueError):
        parse_device_address("-1@192.168.1.50:47808")


# ── format_simulator_device_address (SRV-006-simuladores) ───────────────────


def test_format_simulator_device_address_retorna_str_del_instance_exacto():
    """RF-001, RF-007 — identidad restart-safe: `str(device_instance)`, sin
    `@`, distinta del formato de dispositivos reales."""
    assert format_simulator_device_address(999123) == "999123"


def test_format_simulator_device_address_no_incluye_separador_arroba():
    address = format_simulator_device_address(1234)
    assert "@" not in address


def test_format_simulator_device_address_acepta_limite_inferior_cero():
    assert format_simulator_device_address(0) == "0"


def test_format_simulator_device_address_acepta_limite_superior_4194303():
    assert format_simulator_device_address(4194303) == "4194303"


def test_format_simulator_device_address_rechaza_negativo():
    with pytest.raises(ValueError):
        format_simulator_device_address(-1)


def test_format_simulator_device_address_rechaza_mayor_a_4194303():
    with pytest.raises(ValueError):
        format_simulator_device_address(4194304)
