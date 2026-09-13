"""`core/ports/cache_port.py::CachePort` — contrato ampliado (T-010/T-011,
`plan.md §2`, Nota de ampliación de `CachePort`/`RedisAdapter`; segunda
ampliación T-032/T-033, `plan.md §10`, resolución de RNF-001).

`SRV-001` solo definía `ping()` (*liveness*). Este test verifica, con dobles
(`Protocol` fakes) — sin tocar Redis real — que `CachePort` es ahora
`@runtime_checkable` y exige `get`/`set`/`incr`/`expire`/`delete` además de
`ping()`. Debe fallar antes de ampliar el `Protocol` (T-010), pasar después
(T-011).

T-032 amplía de nuevo: el contrato ahora también exige `publish(channel,
message)`/`subscribe(channel) -> AsyncIterator[str]` — necesarios para que
`services/rbac_service.py::update_user_role` propague la invalidación de su
caché en memoria a otros procesos/réplicas (`plan.md §10`). Debe fallar antes
de T-033, pasar después.
"""
from typing import AsyncIterator

import pytest

from core.ports.cache_port import CachePort


class _FullCacheDouble:
    """Implementa el contrato ampliado completo (`ping` + las 5 operaciones de
    T-010/T-011 + `publish`/`subscribe` de T-032)."""

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        return None

    async def incr(self, key: str) -> int:
        return 1

    async def expire(self, key: str, ttl_seconds: int) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None

    async def publish(self, channel: str, message: str) -> None:
        return None

    async def subscribe(self, channel: str) -> AsyncIterator[str]:
        return
        yield  # pragma: no cover - nunca alcanzado, solo fija la forma de generador async


class _LivenessOnlyDouble:
    """Solo implementa `ping()` — el contrato de `SRV-001`, ya insuficiente."""

    async def ping(self) -> bool:
        return True


class _CacheSinPubSubDouble:
    """Implementa el contrato de T-010/T-011 (`get/set/incr/expire/delete`) pero
    NO `publish`/`subscribe` — el contrato ampliado de T-032 ya no basta con esto."""

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return None

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        return None

    async def incr(self, key: str) -> int:
        return 1

    async def expire(self, key: str, ttl_seconds: int) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None


def test_cache_port_es_runtime_checkable():
    """El `Protocol` debe declararse `@runtime_checkable` para poder verificarlo
    estructuralmente con `isinstance` (T-011)."""
    assert getattr(CachePort, "_is_runtime_protocol", False) is True


def test_cache_port_exige_get_set_incr_expire_delete_publish_subscribe():
    """Un doble que implementa el contrato ampliado completo (incluido pub/sub)
    SÍ satisface `CachePort`."""
    assert isinstance(_FullCacheDouble(), CachePort)


def test_cache_port_rechaza_un_doble_solo_liveness():
    """Un doble que solo tiene `ping()` (contrato viejo de `SRV-001`) YA NO basta —
    demuestra que el `Protocol` ampliado exige más superficie que antes."""
    assert not isinstance(_LivenessOnlyDouble(), CachePort)


def test_cache_port_rechaza_un_doble_sin_publish_subscribe():
    """Un doble con el contrato de T-010/T-011 pero sin `publish`/`subscribe`
    (la ampliación de T-032) ya no satisface `CachePort`."""
    assert not isinstance(_CacheSinPubSubDouble(), CachePort)


@pytest.mark.parametrize(
    "method_name",
    ["ping", "get", "set", "incr", "expire", "delete", "publish", "subscribe"],
)
def test_cache_port_declara_cada_metodo(method_name):
    """Cada método del contrato ampliado existe como atributo del `Protocol`."""
    assert hasattr(CachePort, method_name)
