"""`MqttPublisherPort` — interfaz abstracta del publicador MQTT
(`Protocol`, `SRV-ADR-017`), `SRV-006-simuladores` (`plan.md §2`).

`services/simulator_service.py` importa este contrato, nunca `paho-mqtt`
directamente (overlay de `hira-server/CLAUDE.md`). La implementación real
(`adapters/mqtt/mqtt_publisher_adapter.py::MqttPublisherAdapter`) llega en un
batch posterior de `tasks.md` (T-024/T-025) — fuera de alcance aquí. Sin test
propio, igual que `mqtt_scan_transport_port.py`/`device_repository_port.py`:
es una interfaz, no lógica.

**Puerto nuevo, distinto de `MqttScanTransportPort`** (`SRV-005`, suscribe +
acumula durante una ventana de 3s y desconecta) — este puerto modela un
publicador con ciclo de vida indefinido, hasta `DELETE` (`plan.md §2`,
Registro de decisiones).
"""
from typing import Protocol


class MqttInvalidPublishError(Exception):
    """`topic`/`payload` rechazado por la librería MQTT al publicar
    (RF-014) — señal de dominio, no la excepción cruda de `paho-mqtt` (mismo
    criterio que `MqttInvalidTopicPatternError`, `SRV-005`)."""


class MqttPublisherPort(Protocol):
    async def start(self, *, topic: str, payload: str, interval_seconds: float) -> str:
        """Arranca un publicador MQTT real (RF-003) que publica `payload` en
        `topic` cada `interval_seconds` segundos, en un bucle de fondo
        (RNF-001, `plan.md §5`). Lanza `MqttInvalidPublishError` si
        `topic`/`payload` es rechazado por la librería al intentar el primer
        publish (RF-014) — **antes** de arrancar el bucle periódico. Retorna
        un token opaco."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene el publicador identificado por `token` (RF-009)."""
        ...
