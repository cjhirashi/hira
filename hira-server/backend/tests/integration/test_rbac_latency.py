"""RNF-001 — latencia agregada de `AuthenticationMiddleware` en *cache-hit*
(`SRV-002-auth-rbac`, T-028, `plan.md §9`: "Implementación de RNF-001").

**Método exacto:** dos apps FastAPI sintéticas idénticas, un único
`GET /bench` que retorna `{"ok": True}` sin tocar Postgres/Redis en el handler
— la única diferencia entre ambas es que una registra `AuthenticationMiddleware`
y la otra no. Se dispara el mismo número de requests **concurrentes**
(`asyncio.gather`, `httpx.AsyncClient` con `ASGITransport` — in-process, sin
red real, para no mezclar latencia de socket/Nginx con la del middleware) contra
cada app y se mide `time.perf_counter()` por request. El overhead atribuible al
middleware es `avg(app_con_auth) - avg(app_sin_auth)` — resta el costo base de
FastAPI/Starlette/ASGI, deja solo lo que añade `AuthenticationMiddleware`
(RF-003, RF-007: decodificar el JWT + `resolve_permissions` cache-first).

**Cache-hit real garantizado:** antes de medir, se siembra un usuario real en
Postgres (`PostgreSQLUserRepository`, misma tabla `users`) y se dispara un
request de *warm-up* que fuerza el *cache-miss* inicial (repuebla
`rbac:{user_id}` en Redis real, TTL 7 días) — todos los requests medidos después
son *cache-hit* (RF-007: "no consulta BD salvo cache-miss"), verificado además
contando las consultas a `UserRepositoryPort` con un espía.

Requiere Postgres+Redis reales (mismo compose que el resto de `tests/integration/`).
Evidencia de terminal: correr con `-s` para ver el resumen impreso (medias,
overhead, umbral).

**DIRECTIVA DE PAUSA (2026-09-13, T-028) — histórico, ver `plan.md §10` para el
diseño completo aprobado y T-040 para la re-medición real:** midiendo con este
mismo método (100 requests concurrentes, `asyncio.gather`, sin red real) un
`AuthenticationMiddleware` **completamente vacío** (`return await
call_next(request)`, sin JWT/Redis) ya agregaba **~20-40ms** de media a 100
concurrentes (vs. ~0.02-0.4ms sin middleware) — confirmado también con
`starlette.applications.Starlette` puro (sin FastAPI) y con una llamada ASGI
directa (sin `httpx`/`ASGITransport`) para descartar artefactos de medición.
Era el costo conocido de `starlette.middleware.base.BaseHTTPMiddleware` (spawn
de `anyio` *task group* + *memory stream* por request), escalando superlineal
con la concurrencia (n=10 → ~2ms, n=25 → ~8.6ms, n=100 → ~26ms ya sin ninguna
lógica propia). Una ronda de revisión posterior confirmó una **segunda causa
aditiva**: el round-trip real a Redis por request en *cache-hit* (~27-30ms a
100 concurrentes, independiente de la clase base). Carlos aprobó (2026-09-13)
la solución de raíz que ataca ambas a la vez: migrar `AuthenticationMiddleware`
a ASGI puro (T-038) + `LocalPermissionsCache` en memoria del proceso con
invalidación por pub/sub de Redis (T-032..T-035/T-037). Diseño completo:
`.harness/specs/SRV-002-auth-rbac/plan.md §10`.

**T-039 amplía este test** (con el diseño completo ya implementado) para
verificar, además de 0 consultas a `UserRepositoryPort`, **0 consultas a
`CachePort.get`** durante la medición — el *cache-hit* ahora es 100 % en
memoria (`LocalPermissionsCache`), ni siquiera toca Redis. El `xfail(strict=True)`
se mantiene hasta que **T-040** mida de verdad con el diseño completo (`method.md
§5`: no se asume el resultado de un rediseño sin medirlo).
"""
import asyncio
import os
import time
import uuid

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from adapters.cache.redis_adapter import RedisAdapter
from adapters.db.user_repository_adapter import PostgreSQLUserRepository
from core.middleware import AuthenticationMiddleware
from core.security.jwt import create_access_token
from models.user_model import users_table

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/0")
SECRET_KEY = "latency-benchmark-secret-key-32-chars"

CONCURRENT_REQUESTS = 100
MAX_MIDDLEWARE_OVERHEAD_MS = 5.0


class _CountingUserRepository:
    """Envuelve `PostgreSQLUserRepository` real, cuenta llamadas a
    `get_by_id` — usado para verificar que la medición corre en *cache-hit*
    puro (0 llamadas tras el *warm-up*)."""

    def __init__(self, inner: PostgreSQLUserRepository) -> None:
        self._inner = inner
        self.get_by_id_calls = 0

    async def get_by_email(self, email: str):
        return await self._inner.get_by_email(email)

    async def get_by_id(self, user_id: str):
        self.get_by_id_calls += 1
        return await self._inner.get_by_id(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        await self._inner.update_role(user_id, new_role)


class _CountingCachePort:
    """Envuelve `RedisAdapter` real, cuenta llamadas a `get` — usado para
    verificar que la medición corre 100 % en memoria (`LocalPermissionsCache`,
    T-035): 0 consultas a Redis tras el *warm-up* (T-039, `plan.md §10`)."""

    def __init__(self, inner: RedisAdapter) -> None:
        self._inner = inner
        self.get_calls = 0

    async def ping(self) -> bool:
        return await self._inner.ping()

    async def get(self, key: str) -> str | None:
        self.get_calls += 1
        return await self._inner.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        await self._inner.set(key, value, ttl_seconds=ttl_seconds)

    async def incr(self, key: str) -> int:
        return await self._inner.incr(key)

    async def expire(self, key: str, ttl_seconds: int) -> None:
        await self._inner.expire(key, ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._inner.delete(key)

    async def publish(self, channel: str, message: str) -> None:
        await self._inner.publish(channel, message)

    async def subscribe(self, channel: str):
        async for message in self._inner.subscribe(channel):
            yield message


async def _insert_user(email: str) -> str:
    user_id = uuid.uuid4()
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                users_table.insert().values(
                    id=user_id,
                    email=email,
                    password_hash="$2b$12$" + "a" * 53,
                    rol="admin",
                    scope="global",
                    project_id=None,
                    activo=True,
                )
            )
    finally:
        await engine.dispose()
    return str(user_id)


def _build_bench_app(*, with_auth: bool) -> FastAPI:
    app = FastAPI()
    if with_auth:
        app.add_middleware(AuthenticationMiddleware)

    @app.get("/bench")
    async def bench(request: Request):
        return {"ok": True}

    return app


async def _fire_concurrent_requests(app: FastAPI, headers: dict, count: int) -> list[float]:
    """Dispara `count` requests concurrentes contra `app` (in-process,
    `ASGITransport`) y retorna la latencia individual (ms) de cada una."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://bench") as client:

        async def _one_request() -> float:
            start = time.perf_counter()
            response = await client.get("/bench", headers=headers)
            elapsed_ms = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            return elapsed_ms

        return await asyncio.gather(*(_one_request() for _ in range(count)))


@pytest.mark.asyncio
async def test_middleware_rbac_agrega_menos_de_5ms_en_cache_hit():
    """RNF-001, `AC-SRV-02.6` — 100 requests concurrentes, cache-hit puro (100%
    en memoria desde T-035, sin tocar Redis ni Postgres).

    **T-040 (2026-09-13) — RESUELTO, medido de verdad, `xfail` retirado:** con
    el diseño completo (middleware ASGI puro T-038 + `LocalPermissionsCache`
    T-035, invalidación por pub/sub T-032/T-033/T-037) el overhead real medido
    es **~0.10-0.12ms** (3 corridas consecutivas: 0.118ms, 0.117ms, 0.111ms),
    muy por debajo del umbral de 5ms, con 0 consultas a `UserRepositoryPort` y
    0 consultas a `CachePort.get` durante la medición (evidencia completa,
    `plan.md §10`)."""
    email = f"latency-{uuid.uuid4().hex}@hira.dev"
    user_id = await _insert_user(email)

    real_repo = PostgreSQLUserRepository(DATABASE_URL)
    counting_repo = _CountingUserRepository(real_repo)
    real_cache = RedisAdapter(REDIS_URL)
    counting_cache = _CountingCachePort(real_cache)

    import core.middleware as middleware_module

    original_get_repo = middleware_module.get_user_repository_port
    original_get_cache = middleware_module.get_cache_port
    middleware_module.get_user_repository_port = lambda: counting_repo
    middleware_module.get_cache_port = lambda: counting_cache

    try:
        access_token = create_access_token(
            user_id=user_id,
            rol="admin",
            scope="global",
            project_id=None,
            secret_key=SECRET_KEY,
        )
        # `AuthenticationMiddleware` lee `Settings().secret_key` — se sustituye
        # `Settings` para no depender de las variables de entorno completas del
        # backend en este benchmark aislado.
        original_settings = middleware_module.Settings
        middleware_module.Settings = lambda: type(
            "S", (), {"secret_key": SECRET_KEY}
        )()

        headers = {"Authorization": f"Bearer {access_token}"}
        app_with_auth = _build_bench_app(with_auth=True)
        app_without_auth = _build_bench_app(with_auth=False)

        # Warm-up 1/2: 1 request fuerza el cache-miss inicial (repuebla
        # `rbac:{user_id}` en Redis Y en `LocalPermissionsCache`) — no se mide,
        # y no debe repetirse en la medición.
        await _fire_concurrent_requests(app_with_auth, headers, 1)
        assert counting_repo.get_by_id_calls == 1, (
            "el warm-up debió consultar UserRepositoryPort exactamente una vez "
            "(cache-miss inicial)"
        )
        assert counting_cache.get_calls == 1, (
            "el warm-up debió consultar Redis (CachePort.get) exactamente una "
            "vez (cache-miss local + Redis inicial, repuebla ambos niveles)"
        )

        # Warm-up 2/2: una ronda de `CONCURRENT_REQUESTS` concurrentes,
        # descartada — establece de antemano el *pool* de conexiones TCP que
        # la ronda medida necesitará (a Redis ya no debería hacer falta,
        # LocalPermissionsCache ya está caliente desde el warm-up 1/2, pero se
        # mantiene por la parte sin middleware / artefactos de conexión HTTP).
        # Sin este paso, la primera ráfaga de 100 conexiones concurrentes
        # nuevas domina la medición con el costo de *handshake* de socket
        # (artefacto del entorno de test, no del código del middleware — en
        # producción el pool ya está caliente tras el tráfico inicial, no se
        # recrea en cada ráfaga).
        await _fire_concurrent_requests(app_with_auth, headers, CONCURRENT_REQUESTS)
        await _fire_concurrent_requests(app_without_auth, {}, CONCURRENT_REQUESTS)
        assert counting_cache.get_calls == 1, (
            "el warm-up 2/2 (100 requests) no debió tocar Redis — "
            "LocalPermissionsCache ya estaba caliente desde el warm-up 1/2"
        )

        latencies_with_auth = await _fire_concurrent_requests(
            app_with_auth, headers, CONCURRENT_REQUESTS
        )
        assert counting_repo.get_by_id_calls == 1, (
            "los 100 requests medidos debieron ser 100% cache-hit — 0 consultas "
            "adicionales a UserRepositoryPort (RF-007)"
        )
        assert counting_cache.get_calls == 1, (
            "los 100 requests medidos debieron resolverse 100% EN MEMORIA "
            "(LocalPermissionsCache) — 0 consultas adicionales a CachePort.get "
            "(RNF-001, T-035)"
        )

        latencies_without_auth = await _fire_concurrent_requests(
            app_without_auth, {}, CONCURRENT_REQUESTS
        )

        avg_with_auth = sum(latencies_with_auth) / len(latencies_with_auth)
        avg_without_auth = sum(latencies_without_auth) / len(latencies_without_auth)
        overhead_ms = avg_with_auth - avg_without_auth

        print(
            "\n--- RNF-001: latencia de AuthenticationMiddleware (cache-hit) ---\n"
            f"Requests concurrentes: {CONCURRENT_REQUESTS}\n"
            f"Media CON middleware:    {avg_with_auth:.3f} ms\n"
            f"Media SIN middleware:    {avg_without_auth:.3f} ms\n"
            f"Overhead del middleware: {overhead_ms:.3f} ms "
            f"(umbral: < {MAX_MIDDLEWARE_OVERHEAD_MS} ms)\n"
            f"Consultas a UserRepositoryPort durante la medición: "
            f"{counting_repo.get_by_id_calls - 1} (esperado: 0, cache-hit puro)\n"
            f"Consultas a CachePort.get (Redis) durante la medición: "
            f"{counting_cache.get_calls - 1} (esperado: 0, 100% en memoria)\n"
            "-------------------------------------------------------------------"
        )

        assert overhead_ms < MAX_MIDDLEWARE_OVERHEAD_MS, (
            f"el middleware agregó {overhead_ms:.3f} ms en promedio, "
            f"por encima del umbral de {MAX_MIDDLEWARE_OVERHEAD_MS} ms (RNF-001)"
        )
    finally:
        middleware_module.get_user_repository_port = original_get_repo
        middleware_module.get_cache_port = original_get_cache
        middleware_module.Settings = original_settings
        await real_repo.close()
        await real_cache.close()
