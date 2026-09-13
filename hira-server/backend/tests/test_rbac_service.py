"""`services/rbac_service.py::resolve_permissions/invalidate_permissions_cache/
update_user_role` — coordinación (`plan.md §2`, RF-006, RF-007).

Dobles (`Protocol` fakes) de `UserRepositoryPort`/`CachePort`, in-memory — sin
Postgres/Redis reales (esos llegan en T-024/T-025).
"""
import json
from dataclasses import replace

import pytest

from core.errors import ProblemDetailError
from core.ports.user_repository_port import UserRecord
from services.rbac_service import (
    RBAC_CACHE_TTL_SECONDS,
    invalidate_permissions_cache,
    resolve_permissions,
    update_user_role,
)


class _FakeCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._store[key] = value
        if ttl_seconds is not None:
            self.ttls[key] = ttl_seconds

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def expire(self, key: str, ttl_seconds: int) -> None:
        self.ttls[key] = ttl_seconds

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self.ttls.pop(key, None)


class _FakeUserRepository:
    def __init__(self, users: list[UserRecord]) -> None:
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        raise AssertionError("get_by_email no debería invocarse desde rbac_service")

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        user = self._by_id[user_id]
        self._by_id[user_id] = replace(user, rol=new_role)


class _ExplodingUserRepository:
    """Lanza si se invoca — usado para probar que un *cache-hit* NO toca el
    repositorio (RF-007)."""

    async def get_by_email(self, email: str) -> UserRecord | None:
        raise AssertionError("no debería invocarse en un cache-hit")

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        raise AssertionError("no debería invocarse en un cache-hit")

    async def update_role(self, user_id: str, new_role: str) -> None:
        raise AssertionError("no debería invocarse en un cache-hit")


def _make_user(**overrides) -> UserRecord:
    defaults = dict(
        id="user-1",
        email="admin@hira.dev",
        password_hash="irrelevante-para-rbac",
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    defaults.update(overrides)
    return UserRecord(**defaults)


@pytest.mark.asyncio
async def test_resolve_permissions_cache_miss_consulta_y_repuebla():
    """RF-007 — *cache-miss*: consulta `users_repo`, repuebla `rbac:{user_id}`
    con TTL de 7 días."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    result = await resolve_permissions(user.id, repo, cache)

    assert result.user_id == user.id
    assert result.rol == "admin"
    assert result.scope == "global"
    assert result.project_id is None
    cached_raw = await cache.get(f"rbac:{user.id}")
    assert cached_raw is not None
    assert json.loads(cached_raw)["rol"] == "admin"
    assert cache.ttls[f"rbac:{user.id}"] == RBAC_CACHE_TTL_SECONDS


@pytest.mark.asyncio
async def test_resolve_permissions_cache_hit_no_toca_el_repositorio():
    """RF-007 — *cache-hit*: no consulta `users_repo` en absoluto."""
    cache = _FakeCache()
    await cache.set(
        "rbac:user-1",
        json.dumps(
            {"rol": "operador", "scope": "project", "project_id": "proj-1", "activo": True}
        ),
    )
    exploding_repo = _ExplodingUserRepository()

    result = await resolve_permissions("user-1", exploding_repo, cache)

    assert result.user_id == "user-1"
    assert result.rol == "operador"
    assert result.scope == "project"
    assert result.project_id == "proj-1"


@pytest.mark.asyncio
async def test_resolve_permissions_usuario_no_encontrado_401_token_invalid():
    """RF-007 — usuario no encontrado (revocación efectiva) → 401 `token-invalid`."""
    repo = _FakeUserRepository([])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await resolve_permissions("no-existe", repo, cache)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-invalid"


@pytest.mark.asyncio
async def test_resolve_permissions_usuario_desactivado_401_token_invalid():
    """RF-007 — usuario desactivado → 401 `token-invalid` (revocación efectiva)."""
    user = _make_user(activo=False)
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await resolve_permissions(user.id, repo, cache)

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-invalid"


@pytest.mark.asyncio
async def test_invalidate_permissions_cache_borra_la_entrada():
    """RF-006 — `DEL rbac:{user_id}`."""
    cache = _FakeCache()
    await cache.set("rbac:user-1", json.dumps({"rol": "admin"}))

    await invalidate_permissions_cache("user-1", cache)

    assert await cache.get("rbac:user-1") is None


@pytest.mark.asyncio
async def test_update_user_role_actualiza_y_luego_invalida_cache():
    """RF-006 — actualiza el rol en `users_repo` y **luego** invalida el caché,
    en ese orden (verificado por el estado final: el próximo `resolve_permissions`
    hace *cache-miss* y ve el rol nuevo)."""
    user = _make_user(rol="visor")
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    await resolve_permissions(user.id, repo, cache)  # puebla el cache con "visor"

    await update_user_role(user.id, "admin", repo, cache)

    assert await cache.get(f"rbac:{user.id}") is None  # invalidado
    result = await resolve_permissions(user.id, repo, cache)  # cache-miss, releído
    assert result.rol == "admin"


@pytest.mark.asyncio
async def test_update_user_role_orden_update_antes_que_invalidate():
    """RF-006 — si `update_role` fallara, la caché NO debe invalidarse (orden
    correcto: actualizar primero, invalidar después, no al revés)."""
    calls: list[str] = []

    class _FailingUpdateRepository:
        async def get_by_email(self, email: str):
            raise AssertionError

        async def get_by_id(self, user_id: str):
            raise AssertionError

        async def update_role(self, user_id: str, new_role: str) -> None:
            calls.append("update_role")
            raise RuntimeError("fallo simulado de BD")

    class _RecordingCache(_FakeCache):
        async def delete(self, key: str) -> None:
            calls.append("delete")
            await super().delete(key)

    with pytest.raises(RuntimeError):
        await update_user_role(
            "user-1", "admin", _FailingUpdateRepository(), _RecordingCache()
        )

    assert calls == ["update_role"]  # nunca llegó a invalidar
