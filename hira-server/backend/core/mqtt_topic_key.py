"""`topic_instance_key` — única regla de negocio pura nueva de
`SRV-005-mqtt-scanning` (`plan.md §2`, RF-002). Núcleo sin I/O.

Resuelve el conflicto real entre `spec.md §2` (MQTT: `object_instance` = el
topic real, un string) y el esquema ya `verified` de
`device_points_candidates.object_instance` (`INTEGER NOT NULL`, columna
**compartida** con BACnet/Modbus, `SRV-003-bacnet-adapter`, `plan.md §2`
Registro de decisiones — no se toca). `zlib.crc32` de 32 bits sobre el
universo de topics reales de un proyecto de automatización de edificios
(cientos, no millones, por `device`) tiene una probabilidad de colisión
despreciable para este caso de uso — **no** es un identificador
criptográfico, es una clave de deduplicación determinista dentro del alcance
de un solo `device` (patrón de suscripción).

`services/device_scan_service.py::scan_mqtt` usa esta función para construir
`object_instance` antes de persistir (RF-002); `object_name` (`String(255)`)
lleva el topic real completo como texto.
"""
import zlib


def topic_instance_key(topic: str) -> int:
    """Construye una clave entera determinista de `topic` (RF-002): el mismo
    topic siempre produce la misma clave (requisito de "actualiza si ya
    existía, no duplica" en escaneos repetidos del mismo patrón).

    `zlib.crc32(topic.encode("utf-8")) & 0x7FFFFFFF` — siempre `>= 0` y
    `<= 2147483647` (cabe en el `INTEGER` de Postgres de
    `device_points_candidates.object_instance`).

    Lanza `ValueError` si `topic` está vacío (o sólo espacios en blanco).
    """
    if not topic or not topic.strip():
        raise ValueError("topic no puede estar vacío")
    return zlib.crc32(topic.encode("utf-8")) & 0x7FFFFFFF
