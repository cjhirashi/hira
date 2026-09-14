"""`core/mqtt_topic_key.py` — núcleo puro, sin I/O (`SRV-005-mqtt-scanning`).

Contrato exacto ya fijado en `plan.md §2`/Registro de decisiones (no es una
decisión abierta de este batch): `topic_instance_key(topic: str) -> int`
resuelve el conflicto de esquema entre `object_instance` (`INTEGER`, columna
compartida con BACnet/Modbus, `SRV-003`) y el topic real de MQTT (texto) —
`zlib.crc32(topic.encode("utf-8")) & 0x7FFFFFFF`: determinista (mismo topic →
misma clave, requisito de RF-002 "actualiza si ya existía, no duplica"),
siempre `>= 0` y `<= 2147483647` (cabe en `INTEGER` de Postgres). Rechaza
topic vacío.

Debe fallar antes de T-002 (`core/mqtt_topic_key.py` no existe todavía).
"""
import pytest

from core.mqtt_topic_key import topic_instance_key


def test_topic_instance_key_es_determinista_mismo_topic_misma_clave():
    """RF-002 — el mismo topic, invocado 2 veces, produce siempre la misma
    clave (requisito de "actualiza si ya existía, no duplica")."""
    topic = "edificio/piso1/ahu1/temp"

    first = topic_instance_key(topic)
    second = topic_instance_key(topic)

    assert first == second


def test_topic_instance_key_topics_distintos_producen_claves_distintas():
    """RF-002 — caso normal: topics distintos producen claves distintas
    (no es una garantía criptográfica, `crc32` de 32 bits — pero para este
    conjunto pequeño de topics de ejemplo no debe colisionar)."""
    topics = [
        "edificio/piso1/ahu1/temp",
        "edificio/piso1/ahu2/humidity",
        "edificio/piso2/ahu1/temp",
    ]

    keys = {topic_instance_key(topic) for topic in topics}

    assert len(keys) == len(topics)


def test_topic_instance_key_produce_enteros_no_negativos_que_caben_en_integer():
    """Cabe en la columna `INTEGER` (`device_points_candidates.object_instance`,
    `SRV-003`, no se toca): siempre `>= 0` y `<= 2147483647`."""
    topics = [
        "edificio/piso1/ahu1/temp",
        "a",
        "edificio/" + "x" * 200,
    ]

    for topic in topics:
        key = topic_instance_key(topic)
        assert 0 <= key <= 2147483647


def test_topic_instance_key_rechaza_topic_vacio():
    with pytest.raises(ValueError):
        topic_instance_key("")
