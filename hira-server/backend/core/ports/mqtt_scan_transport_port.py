"""`MqttScanTransportPort` — interfaz abstracta del transporte MQTT de
escaneo (`Protocol`, `SRV-ADR-017`), `SRV-005-mqtt-scanning` (`plan.md §2`).

`services/device_scan_service.py` importa este contrato y sus value objects,
nunca `paho-mqtt` directamente (overlay de `hira-server/CLAUDE.md`: "si un
módulo de `services/` importa... `paho`... viola la arquitectura"). La
implementación real (`adapters/mqtt/mqtt_scan_adapter.py::MqttScanAdapter`)
llega en un batch posterior de `tasks.md` (T-009/T-010) — fuera de alcance
aquí. Sin test propio, igual que `bacnet_transport_port.py`/
`modbus_transport_port.py`/`device_repository_port.py`: es una interfaz, no
lógica.

Un único método (`listen`) cubre suscripción + acumulación de mensajes
durante la ventana — MQTT es push-based, no hay una operación de "leer"
análoga a BACnet/Modbus (Anti-Abstraction, `plan.md §0`/Registro de
decisiones). `MqttInvalidTopicPatternError` se modela como excepción de
dominio (mismo criterio que `BacnetReadTimeoutError`, `SRV-003`) — a
diferencia de `ModbusReadFailure` (`SRV-004`, valor de retorno): un patrón
de suscripción inválido es una única evaluación por invocación completa del
escaneo, no un elemento de una colección que se puede seguir procesando.
"""
from dataclasses import dataclass
from typing import Protocol


class MqttInvalidTopicPatternError(Exception):
    """`topic_pattern` rechazado por la librería MQTT al suscribirse (RF-004).
    Señal de dominio, no la excepción cruda de `paho-mqtt` — mismo criterio
    que `BacnetReadTimeoutError` (`SRV-003`)."""


@dataclass(frozen=True)
class MqttTopicMessage:
    """Un mensaje recibido en un topic real durante la ventana de escucha
    (RF-001, RF-002). `payload` ya decodificado a texto por el adaptador
    (`plan.md §1`, Registro de decisiones)."""

    topic: str
    payload: str


class MqttScanTransportPort(Protocol):
    async def listen(
        self, topic_pattern: str, window_seconds: float
    ) -> list[MqttTopicMessage]:
        """Se suscribe a `topic_pattern` (wildcard MQTT, p. ej.
        `edificio/piso1/#`) y acumula todos los mensajes recibidos durante
        `window_seconds` (RF-001), en el orden en que llegaron — puede haber
        varios mensajes del mismo topic; la deduplicación es responsabilidad
        de quien llama (`services/device_scan_service.py::scan_mqtt`, RF-002).
        Lista vacía si ningún mensaje llega (RF-006).

        Lanza `MqttInvalidTopicPatternError` si `topic_pattern` es
        sintácticamente inválido (RF-004) — la validación ocurre al
        suscribirse, **antes** de esperar la ventana completa (verificado
        con ejecución real, `plan.md §5`)."""
        ...
