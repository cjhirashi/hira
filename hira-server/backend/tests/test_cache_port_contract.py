"""`core/ports/cache_port.py::CachePort` — contrato ampliado (T-010/T-011,
`plan.md §2`, Nota de ampliación de `CachePort`/`RedisAdapter`).

`SRV-001` solo definía `ping()` (*liveness*). Este test verifica, con dobles
(`Protocol` fakes) — sin tocar Redis real — que `CachePort` es ahora
`@runtime_checkable` y exige `get`/`set`/`incr`/`expire`/`delete` además de
`ping()`. Debe fallar antes de ampliar el `Protocol` (T-010), pasar después
(T-011).
"""
import pytest

from core.ports.cache_port import CachePort


class _FullCacheDouble:
    """Implementa el contrato ampliado completo (`ping` + las 5 operaciones nuevas)."""

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


class _LivenessOnlyDouble:
    """Solo implementa `ping()` — el contrato de `SRV-001`, ya insuficiente."""

    async def ping(self) -> bool:
        return True


def test_cache_port_es_runtime_checkable():
    """El `Protocol` debe declararse `@runtime_checkable` para poder verificarlo
    estructuralmente con `isinstance` (T-011)."""
    assert getattr(CachePort, "_is_runtime_protocol", False) is True


def test_cache_port_exige_get_set_incr_expire_delete():
    """Un doble que implementa el contrato ampliado completo SÍ satisface `CachePort`."""
    assert isinstance(_FullCacheDouble(), CachePort)


def test_cache_port_rechaza_un_doble_solo_liveness():
    """Un doble que solo tiene `ping()` (contrato viejo de `SRV-001`) YA NO basta —
    demuestra que el `Protocol` ampliado exige más superficie que antes."""
    assert not isinstance(_LivenessOnlyDouble(), CachePort)


@pytest.mark.parametrize(
    "method_name", ["ping", "get", "set", "incr", "expire", "delete"]
)
def test_cache_port_declara_cada_metodo(method_name):
    """Cada método del contrato ampliado existe como atributo del `Protocol`."""
    assert hasattr(CachePort, method_name)
