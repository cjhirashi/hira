"""`NotificationPort` — interfaz abstracta de notificaciones MQTT (`Protocol`,
`SRV-ADR-017`).

`services/` importa este contrato, nunca `paho-mqtt` directamente. La implementación
real (`adapters/mqtt/mosquitto_adapter.py`) llega en un batch posterior de
`tasks.md` (T-019/T-020, T-022) — fuera de alcance aquí.

`send()` **no se declara todavía** — no hay ningún caso de uso real que lo necesite
en este sprint (regla de oro Art. 10, `plan.md §7`); se añade cuando exista un
consumidor concreto.
"""
from typing import Protocol


class NotificationPort(Protocol):
    """Contrato mínimo de *liveness* y conexión de arranque (RF-002, RF-006, RF-008)."""

    async def ping(self) -> bool:
        """Retorna `True` si la conexión MQTT responde correctamente."""
        ...

    async def connect(self) -> None:
        """Establece la conexión de arranque con credencial propia (RF-006/RF-008)."""
        ...
