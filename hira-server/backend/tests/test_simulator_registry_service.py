"""`services/simulator_registry_service.py` — estado en memoria de los
simuladores en ejecución (`SRV-006-simuladores`, `plan.md §2`).

Sin mocks (Art. 3, `plan.md §5`): estructura de datos pura en memoria, prueba
su propia serialización con corutinas reales (`asyncio.gather`) contra
`SimulatorRegistryService.lock`. Debe fallar antes de T-004 (`services/
simulator_registry_service.py` no existe todavía).
"""
import asyncio
from datetime import datetime, timezone

import pytest

from services.simulator_registry_service import (
    RunningSimulator,
    SimulatorRegistryService,
    get_simulator_registry,
)


def _make_entry(device_id: str = "dev-1", protocol: str = "bacnet") -> RunningSimulator:
    return RunningSimulator(
        device_id=device_id,
        protocol=protocol,
        address="999123",
        token="token-1",
        started_at=datetime.now(timezone.utc),
    )


def test_register_get_is_running():
    """RF-010 — tras `register`, `get`/`is_running` reflejan la entrada."""
    registry = SimulatorRegistryService()
    entry = _make_entry()

    assert registry.get(entry.device_id) is None
    assert registry.is_running(entry.device_id) is False

    registry.register(entry)

    assert registry.get(entry.device_id) == entry
    assert registry.is_running(entry.device_id) is True


def test_unregister_es_idempotente():
    """RF-009 — `unregister` de una entrada existente la elimina; de una
    entrada ausente no falla (idempotente)."""
    registry = SimulatorRegistryService()
    entry = _make_entry()
    registry.register(entry)

    registry.unregister(entry.device_id)

    assert registry.get(entry.device_id) is None
    assert registry.is_running(entry.device_id) is False
    # Segunda vez, sin la entrada — no debe lanzar.
    registry.unregister(entry.device_id)


def test_list_running_lista_solo_lo_registrado():
    """RF-010 — `GET /simulators` lista únicamente lo actualmente registrado."""
    registry = SimulatorRegistryService()
    entry_bacnet = _make_entry(device_id="dev-1", protocol="bacnet")
    entry_modbus = _make_entry(device_id="dev-2", protocol="modbus")
    registry.register(entry_bacnet)
    registry.register(entry_modbus)

    assert set(registry.list_running()) == {entry_bacnet, entry_modbus}

    registry.unregister(entry_bacnet.device_id)

    assert registry.list_running() == [entry_modbus]


def test_una_instancia_nueva_siempre_nace_vacia():
    """RF-013 (equivalente verificable) — un `SimulatorRegistryService()`
    nuevo siempre nace vacío, como si el proceso se hubiera reiniciado."""
    registry = SimulatorRegistryService()

    assert registry.list_running() == []


def test_get_simulator_registry_es_un_singleton_de_modulo():
    """`plan.md §2` — `get_simulator_registry()` retorna siempre la misma
    instancia dentro del proceso."""
    first = get_simulator_registry()
    second = get_simulator_registry()

    assert first is second


@pytest.mark.asyncio
async def test_lock_serializa_dos_corutinas_reales():
    """`plan.md §5` — 2 corutinas reales que intentan `async with
    registry.lock` a la vez: una espera a que la otra libere. Verificado con
    orden de ejecución real (`asyncio.gather`), sin mocks."""
    registry = SimulatorRegistryService()
    order: list[str] = []

    async def _hold_lock(label: str, hold_seconds: float) -> None:
        async with registry.lock:
            order.append(f"{label}-start")
            await asyncio.sleep(hold_seconds)
            order.append(f"{label}-end")

    await asyncio.gather(_hold_lock("first", 0.05), _hold_lock("second", 0.0))

    # Si el lock serializa correctamente, "first" empieza y termina antes de
    # que "second" pueda empezar — nunca se intercalan.
    assert order == ["first-start", "first-end", "second-start", "second-end"]
