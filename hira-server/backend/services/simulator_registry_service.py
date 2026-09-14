"""`services/simulator_registry_service.py` — estado en memoria del proceso de
los simuladores actualmente en ejecución (`SRV-006-simuladores`, `plan.md §2`).

**No es un puerto** (mismo criterio ya registrado en
`services/rbac_service.py::LocalPermissionsCache`, `SRV-002-auth-rbac`): no
habla con ningún sistema externo, es una estructura de datos interna
(`dict[device_id, RunningSimulator]`). `spec.md §3` ya decidió que el estado
"en ejecución" vive en memoria del proceso de Hira Server, no en `devices` —
un reinicio del proceso lo vacía sin código adicional (RF-013).

Vive en su propio archivo (no inline en `services/simulator_service.py`, a
diferencia de `LocalPermissionsCache` en `rbac_service.py`) porque las 3
funciones de arranque (una por protocolo) más `stop_simulator`/`GET
/simulators` convergen sobre el **mismo** registro — un componente
compartido, no propiedad de una sola función (`plan.md §2`, Registro de
decisiones).
"""
from dataclasses import dataclass
from datetime import datetime

import asyncio


@dataclass(frozen=True)
class RunningSimulator:
    """Una entrada del registro en memoria (RF-010): un simulador actualmente
    en ejecución. `token` es el identificador opaco que retorna
    `BacnetSimulatorPort.start()`/`ModbusSimulatorPort.start()`/
    `MqttPublisherPort.start()` (`plan.md §2`) — se pasa de vuelta a `stop()`
    del mismo puerto."""

    device_id: str
    protocol: str
    address: str
    token: str
    started_at: datetime


class SimulatorRegistryService:
    """`dict[device_id, RunningSimulator]` + `asyncio.Lock` **público**
    (`self.lock`) — usado por `services/simulator_service.py` para envolver
    la sección crítica completa "verificar conflicto (RF-006) → arrancar el
    proceso real → registrar", no solo la mutación del `dict` (`plan.md §2`,
    Registro de decisiones: un único lock global, no uno por `device_id`).

    Métodos síncronos (sin `await` propio) — las mutaciones del `dict` no
    necesitan ser `async`; el `Lock` protege la *secuencia* de operaciones de
    quien lo usa, no cada método individual."""

    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self._running: dict[str, RunningSimulator] = {}

    def get(self, device_id: str) -> RunningSimulator | None:
        return self._running.get(device_id)

    def is_running(self, device_id: str) -> bool:
        return device_id in self._running

    def register(self, entry: RunningSimulator) -> None:
        self._running[entry.device_id] = entry

    def unregister(self, device_id: str) -> None:
        """Idempotente — no falla si `device_id` no está registrado."""
        self._running.pop(device_id, None)

    def list_running(self) -> list[RunningSimulator]:
        return list(self._running.values())


# Singleton de módulo (`plan.md §2`), inyectado vía `Depends()` en
# `routers/simulators.py` — mismo mecanismo de FastAPI que los puertos reales
# de `adapters/factory.py`, aunque este objeto vive en `services/`, no en
# `adapters/` (no es infraestructura intercambiable).
_default_registry = SimulatorRegistryService()


def get_simulator_registry() -> SimulatorRegistryService:
    return _default_registry
