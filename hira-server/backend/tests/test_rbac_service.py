"""`services/rbac_service.py::resolve_permissions/invalidate_permissions_cache/
update_user_role` — coordinación (`plan.md §2`, RF-006, RF-007).

Dobles (`Protocol` fakes) de `UserRepositoryPort`/`CachePort`, in-memory — sin
Postgres/Redis reales (esos llegan en T-024/T-025).

Ampliado en T-034 (`plan.md §10`, resolución de RNF-001):
`LocalPermissionsCache` (caché en memoria del proceso, delante de Redis) — *hit*
en memoria evita Redis y BD; *miss* local + *hit* Redis repuebla el local sin
tocar BD; TTL local expira (reloj inyectable, sin `sleep` real) y vuelve a
consultar Redis; invalidación cruzada entre "2 procesos" simulada con 2
instancias de `LocalPermissionsCache` + un doble de `CachePort` respaldado por
`asyncio.Queue` (`plan.md §5`).
"""
import asyncio
import contextlib
import json
from dataclasses import replace

import pytest

from core.errors import ProblemDetailError
from core.ports.user_repository_port import UserRecord
from services.rbac_service import (
    LOCAL_CACHE_TTL_SECONDS,
    RBAC_CACHE_TTL_SECONDS,
    AuthenticatedUser,
    LocalPermissionsCache,
    invalidate_permissions_cache,
    resolve_permissions,
    run_invalidation_subscriber,
    update_user_role,
)


class _FakeCache:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.published: list[tuple[str, str]] = []

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

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))

    async def subscribe(self, channel: str):
        # Nunca produce mensajes por sí solo — los tests que necesitan pub/sub
        # real (simulado) usan `_QueuePubSubCache` en su lugar.
        return
        yield  # pragma: no cover


class _QueuePubSubCache(_FakeCache):
    """Doble de `CachePort` cuyo `publish`/`subscribe` está respaldado por un
    `asyncio.Queue` en memoria — simula el canal Pub/Sub de Redis sin un Redis
    real (`plan.md §5`)."""

    def __init__(self) -> None:
        super().__init__()
        self._channels: dict[str, list[asyncio.Queue]] = {}

    async def publish(self, channel: str, message: str) -> None:
        self.published.append((channel, message))
        for queue in self._channels.get(channel, []):
            await queue.put(message)

    async def subscribe(self, channel: str):
        queue: asyncio.Queue = asyncio.Queue()
        self._channels.setdefault(channel, []).append(queue)
        while True:
            message = await queue.get()
            yield message


class _ExplodingCache:
    """Lanza si se invoca cualquier método de I/O — usado para probar que un
    *hit* en `LocalPermissionsCache` NO toca Redis en absoluto (RNF-001)."""

    async def ping(self) -> bool:
        raise AssertionError("no debería invocarse en un hit local")

    async def get(self, key: str) -> str | None:
        raise AssertionError("no debería invocarse en un hit local")

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        raise AssertionError("no debería invocarse en un hit local")

    async def incr(self, key: str) -> int:
        raise AssertionError("no debería invocarse en un hit local")

    async def expire(self, key: str, ttl_seconds: int) -> None:
        raise AssertionError("no debería invocarse en un hit local")

    async def delete(self, key: str) -> None:
        raise AssertionError("no debería invocarse en un hit local")

    async def publish(self, channel: str, message: str) -> None:
        raise AssertionError("no debería invocarse en un hit local")

    async def subscribe(self, channel: str):
        raise AssertionError("no debería invocarse en un hit local")
        yield  # pragma: no cover


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
    """Lanza si se invoca — usado para probar que un *cache-hit* (Redis o local)
    NO toca el repositorio (RF-007)."""

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
    """RF-007 — *cache-miss* (local y Redis): consulta `users_repo`, repuebla
    `rbac:{user_id}` con TTL de 7 días y el `LocalPermissionsCache`."""
    user = _make_user()
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    local_cache = LocalPermissionsCache()

    result = await resolve_permissions(user.id, repo, cache, local_cache=local_cache)

    assert result.user_id == user.id
    assert result.rol == "admin"
    assert result.scope == "global"
    assert result.project_id is None
    cached_raw = await cache.get(f"rbac:{user.id}")
    assert cached_raw is not None
    assert json.loads(cached_raw)["rol"] == "admin"
    assert cache.ttls[f"rbac:{user.id}"] == RBAC_CACHE_TTL_SECONDS
    local_hit = local_cache.get(user.id)
    assert local_hit is not None
    assert local_hit.rol == "admin"


@pytest.mark.asyncio
async def test_resolve_permissions_cache_hit_redis_no_toca_el_repositorio():
    """RF-007 — *miss* local + *hit* Redis: no consulta `users_repo`, repuebla
    el `LocalPermissionsCache`."""
    cache = _FakeCache()
    await cache.set(
        "rbac:user-1",
        json.dumps(
            {"rol": "operador", "scope": "project", "project_id": "proj-1", "activo": True}
        ),
    )
    local_cache = LocalPermissionsCache()
    exploding_repo = _ExplodingUserRepository()

    result = await resolve_permissions(
        "user-1", exploding_repo, cache, local_cache=local_cache
    )

    assert result.user_id == "user-1"
    assert result.rol == "operador"
    assert result.scope == "project"
    assert result.project_id == "proj-1"
    local_hit = local_cache.get("user-1")
    assert local_hit is not None
    assert local_hit.rol == "operador"


@pytest.mark.asyncio
async def test_resolve_permissions_usuario_no_encontrado_401_token_invalid():
    """RF-007 — usuario no encontrado (revocación efectiva) → 401 `token-invalid`."""
    repo = _FakeUserRepository([])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await resolve_permissions("no-existe", repo, cache, local_cache=LocalPermissionsCache())

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-invalid"


@pytest.mark.asyncio
async def test_resolve_permissions_usuario_desactivado_401_token_invalid():
    """RF-007 — usuario desactivado → 401 `token-invalid` (revocación efectiva)."""
    user = _make_user(activo=False)
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    with pytest.raises(ProblemDetailError) as exc_info:
        await resolve_permissions(user.id, repo, cache, local_cache=LocalPermissionsCache())

    assert exc_info.value.status == 401
    assert exc_info.value.type_ == "https://hira.dev/errors/token-invalid"


@pytest.mark.asyncio
async def test_invalidate_permissions_cache_borra_la_entrada():
    """RF-006 — `DEL rbac:{user_id}`."""
    cache = _FakeCache()
    await cache.set("rbac:user-1", json.dumps({"rol": "admin"}))

    await invalidate_permissions_cache("user-1", cache, local_cache=LocalPermissionsCache())

    assert await cache.get("rbac:user-1") is None


@pytest.mark.asyncio
async def test_update_user_role_actualiza_y_luego_invalida_cache():
    """RF-006 — actualiza el rol en `users_repo` y **luego** invalida el caché,
    en ese orden (verificado por el estado final: el próximo `resolve_permissions`
    hace *cache-miss* y ve el rol nuevo)."""
    user = _make_user(rol="visor")
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    local_cache = LocalPermissionsCache()
    await resolve_permissions(user.id, repo, cache, local_cache=local_cache)  # puebla con "visor"

    await update_user_role(user.id, "admin", repo, cache, local_cache=local_cache)

    assert await cache.get(f"rbac:{user.id}") is None  # invalidado en Redis
    assert local_cache.get(user.id) is None  # invalidado en memoria
    result = await resolve_permissions(user.id, repo, cache, local_cache=local_cache)
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
            "user-1",
            "admin",
            _FailingUpdateRepository(),
            _RecordingCache(),
            local_cache=LocalPermissionsCache(),
        )

    assert calls == ["update_role"]  # nunca llegó a invalidar


# ─── T-034 (`plan.md §10`, RNF-001) — LocalPermissionsCache ────────────────


@pytest.mark.asyncio
async def test_local_cache_hit_no_llama_a_redis_ni_a_bd():
    """RNF-001 — con `LocalPermissionsCache` ya caliente, `resolve_permissions`
    no toca `CachePort` (doble que lanza si se invoca) ni `UserRepositoryPort`."""
    local_cache = LocalPermissionsCache()
    seeded = AuthenticatedUser(
        user_id="user-1", rol="admin", scope="global", project_id=None, activo=True
    )
    local_cache.set("user-1", seeded)

    result = await resolve_permissions(
        "user-1", _ExplodingUserRepository(), _ExplodingCache(), local_cache=local_cache
    )

    assert result == seeded


@pytest.mark.asyncio
async def test_local_cache_ttl_expira_y_vuelve_a_consultar_redis():
    """RNF-001 — tras `LOCAL_CACHE_TTL_SECONDS`, el hit local expira y
    `resolve_permissions` vuelve a Redis (reloj inyectable, sin `sleep` real)."""
    fake_time = {"now": 1_000.0}
    local_cache = LocalPermissionsCache(clock=lambda: fake_time["now"])
    user = _make_user(rol="operador")
    repo = _FakeUserRepository([user])
    cache = _FakeCache()

    await resolve_permissions(user.id, repo, cache, local_cache=local_cache)
    assert local_cache.get(user.id) is not None

    fake_time["now"] += LOCAL_CACHE_TTL_SECONDS + 1
    assert local_cache.get(user.id) is None  # expiró, sin sleep real

    # Redis sigue teniendo la entrada — la BD no debe tocarse de nuevo.
    result = await resolve_permissions(
        user.id, _ExplodingUserRepository(), cache, local_cache=local_cache
    )

    assert result.rol == "operador"
    assert local_cache.get(user.id) is not None  # repoblado


@pytest.mark.asyncio
async def test_update_user_role_invalida_local_redis_y_publica():
    """RF-006, RNF-001 — `update_user_role` invalida su `LocalPermissionsCache`,
    Redis, y publica en `rbac:invalidations`."""
    user = _make_user(rol="visor")
    repo = _FakeUserRepository([user])
    cache = _FakeCache()
    local_cache = LocalPermissionsCache()
    await resolve_permissions(user.id, repo, cache, local_cache=local_cache)

    await update_user_role(user.id, "admin", repo, cache, local_cache=local_cache)

    assert local_cache.get(user.id) is None
    assert await cache.get(f"rbac:{user.id}") is None
    assert cache.published == [("rbac:invalidations", user.id)]


@pytest.mark.asyncio
async def test_invalidacion_cruzada_entre_dos_procesos_via_pubsub():
    """RF-006, RNF-001 — simula 2 procesos backend con 2 instancias de
    `LocalPermissionsCache` (`local_cache_a`, `local_cache_b`) y un doble de
    `CachePort` respaldado por `asyncio.Queue` (`plan.md §5`): `update_user_role`
    invalida `local_cache_a` síncronamente y publica; `run_invalidation_subscriber`
    corriendo contra `local_cache_b` consume el mensaje y lo invalida también."""
    user = _make_user(rol="visor")
    repo = _FakeUserRepository([user])
    cache = _QueuePubSubCache()
    local_cache_a = LocalPermissionsCache()
    local_cache_b = LocalPermissionsCache()

    # Ambos "procesos" calientan su caché local con el mismo usuario.
    await resolve_permissions(user.id, repo, cache, local_cache=local_cache_a)
    await resolve_permissions(user.id, repo, cache, local_cache=local_cache_b)
    assert local_cache_a.get(user.id) is not None
    assert local_cache_b.get(user.id) is not None

    subscriber_task = asyncio.create_task(
        run_invalidation_subscriber(cache, local_cache=local_cache_b)
    )
    try:
        # Deja que el suscriptor de fondo llegue a registrarse en el canal
        # simulado (`queue.get()`) antes de publicar — sin este punto de
        # cesión, `publish()` podría ejecutarse antes de que la tarea arranque
        # (ninguna otra `await` en el camino de `update_user_role` cede el
        # control real al loop) y el mensaje se perdería (no hay backlog en
        # `_QueuePubSubCache`, igual que Redis Pub/Sub real).
        await asyncio.sleep(0.05)

        await update_user_role(user.id, "admin", repo, cache, local_cache=local_cache_a)

        # Mismo proceso: invalidación síncrona, sin esperar el pub/sub.
        assert local_cache_a.get(user.id) is None

        # Otro "proceso": converge al consumir el mensaje del canal simulado.
        async def _wait_local_cache_b_invalidated() -> None:
            while local_cache_b.get(user.id) is not None:
                await asyncio.sleep(0.01)

        await asyncio.wait_for(_wait_local_cache_b_invalidated(), timeout=1.0)
        assert local_cache_b.get(user.id) is None
    finally:
        subscriber_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await subscriber_task


@pytest.mark.asyncio
async def test_run_invalidation_subscriber_no_traga_cancelacion():
    """`run_invalidation_subscriber` debe salir limpio ante `CancelledError` (no
    debe tragarse la cancelación) — el `lifespan` depende de esto (T-036/T-037)."""
    cache = _QueuePubSubCache()
    local_cache = LocalPermissionsCache()

    task = asyncio.create_task(run_invalidation_subscriber(cache, local_cache=local_cache))
    await asyncio.sleep(0.05)  # deja que la tarea llegue a esperar en la cola

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
