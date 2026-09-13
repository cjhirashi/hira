"""Seguridad end-to-end — Postgres+Redis reales (`SRV-002-auth-rbac`, T-027,
`plan.md §5`/§6 paso 16).

Requiere, antes de correr esta suite (`pytest -m integration`):

    cd hira-server
    docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
    cd backend && DATABASE_URL=postgresql+asyncpg://hira:changeme@localhost:5432/hiradb \
        alembic upgrade head

App sintética propia (`_build_app()`, mismo patrón que
`tests/test_authentication_middleware.py::_build_app`): `AuthenticationMiddleware`
real + `routers/auth.py` real + un `GET /test-protected` sintético — sin tocar
`main.py`/`routers/monitor.py` (no se necesita Mosquitto real para este batch,
`spec.md`/`plan.md` de esta feature no lo exigen). `UserRepositoryPort`/`CachePort`
**no** se sustituyen por dobles — se resuelven vía `adapters/factory.py::
get_user_repository_port/get_cache_port` reales (`PostgreSQLUserRepository`/
`RedisAdapter` contra los contenedores del compose), igual que en producción.

Cubre: fuerza bruta real (RF-014, 6º intento → 429); revocación real (RF-010/
RF-013, logout → refresh con ese token → 401); bcrypt+JWT reales de punta a
punta (RF-001, RF-002, RF-011, RF-012 — login → acceso a `/test-protected` →
refresh → logout); forma RFC 9457 exacta en cada 401/429 (`E-ADR-003`).
"""
import os

import pytest
import redis.asyncio as redis_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine

import adapters.factory as factory_module
from core.errors import ProblemDetailError
from core.middleware import AuthenticationMiddleware
from models.user_model import users_table
from routers.auth import router as auth_router
from schemas.errors import ProblemDetail
from scripts.seed_admin_user import seed_admin_user
from services.auth_service import MAX_LOGIN_ATTEMPTS

pytestmark = pytest.mark.integration

DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://hira:changeme@localhost:5432/hiradb"
)
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/0")

REQUIRED_ENV = {
    "DATABASE_URL": DATABASE_URL,
    "REDIS_URL": REDIS_URL,
    # Sin Mosquitto real en este batch — `_build_app()` no registra
    # `routers/monitor.py` ni el `lifespan` de `main.py`, así que estos 2
    # valores solo necesitan estar *presentes* para que `Settings()` no
    # rechace el arranque (RF-003) — nunca se usan para conectar de verdad.
    "MQTT_BROKER_HOST": "unused",
    "MQTT_USER": "unused",
    "MQTT_PASSWORD": "unused",
    "SECRET_KEY": "e2e-secret-key-min-32-caracteres-reales",
    "CORS_ORIGINS": "http://localhost:5173",
}

SEED_EMAIL = "seed-e2e@hira.dev"
SEED_PASSWORD = "Sup3rSeguraDeVerdad!2026"


def _build_app() -> FastAPI:
    """App sintética: `AuthenticationMiddleware` + `routers/auth.py` reales
    (`adapters/factory.py` sin sustituir) + una ruta protegida de prueba."""
    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)
    app.include_router(auth_router)

    @app.exception_handler(ProblemDetailError)
    async def _problem_detail_handler(
        request: Request, exc: ProblemDetailError
    ) -> JSONResponse:
        problem = ProblemDetail(
            type=exc.type_, title=exc.title, status=exc.status, detail=exc.detail
        )
        return JSONResponse(
            status_code=exc.status,
            content=problem.model_dump(),
            media_type="application/problem+json",
        )

    @app.get("/test-protected")
    async def test_protected(request: Request):
        user = request.state.user
        return {"user_id": user.user_id, "rol": user.rol}

    return app


async def _reset_real_infra() -> None:
    """Trunca `users` (Postgres) y limpia Redis — aislamiento entre tests."""
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.begin() as connection:
            await connection.execute(users_table.delete())
    finally:
        await engine.dispose()

    redis_client = redis_asyncio.from_url(REDIS_URL)
    try:
        await redis_client.flushdb()
    finally:
        await redis_client.aclose()


@pytest.fixture(autouse=True)
def _fresh_factory_singletons():
    """`adapters/factory.py` cachea sus puertos a nivel de proceso — diseño
    correcto en producción (un solo `event loop` de por vida del proceso
    `uvicorn`). `pytest-asyncio` crea un `event loop` **nuevo por test
    function** (`asyncio_mode = auto`, scope por defecto); reusar una conexión
    de Redis/Postgres atada a un loop ya cerrado revienta con `RuntimeError:
    Event loop is closed`. Se resetean los singletons antes de cada test para
    que `get_cache_port()`/`get_user_repository_port()` los recreen ligados al
    loop vigente — no cambia la lógica de negocio bajo prueba, es un artefacto
    del test runner, no de producción."""
    factory_module._database_port = None
    factory_module._cache_port = None
    factory_module._notification_port = None
    factory_module._user_repository_port = None
    yield


@pytest.fixture(autouse=True)
async def _clean_infra():
    """Trunca `users`/limpia Redis **antes** de cada test — aislamiento entre
    tests. `client` (abajo) declara una dependencia explícita sobre este
    fixture para garantizar el orden (los `autouse` sin dependencia declarada
    no tienen orden garantizado frente a otros fixtures del mismo scope)."""
    await _reset_real_infra()
    yield
    await _reset_real_infra()


@pytest.fixture
async def client(monkeypatch, _clean_infra):
    """`TestClient` sobre `_build_app()` + admin de prueba ya sembrado (RF-012,
    script real de T-026, bcrypt real) — env real (`DATABASE_URL`/`REDIS_URL`
    apuntando a los contenedores del compose). Depende de `_clean_infra` para
    sembrar sobre una tabla ya truncada."""
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SEED_ADMIN_EMAIL", SEED_EMAIL)
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", SEED_PASSWORD)

    exit_code = await seed_admin_user()
    assert exit_code == 0, "el seed debió crear al admin de prueba (idempotente)"

    with TestClient(_build_app()) as test_client:
        yield test_client


def test_seed_es_real_y_bcrypt_real_end_to_end(client):
    """RF-012 — el password sembrado nunca queda en claro; `verify_password`
    (bcrypt real) es lo único que permite el login (sin este test, un futuro
    cambio a un hash no-bcrypt pasaría desapercibido)."""
    wrong = client.post(
        "/auth/login", json={"email": SEED_EMAIL, "password": "password-incorrecto"}
    )
    assert wrong.status_code == 401

    right = client.post(
        "/auth/login", json={"email": SEED_EMAIL, "password": SEED_PASSWORD}
    )
    assert right.status_code == 200


def test_fuerza_bruta_real_sexto_intento_429(client):
    """RF-014 — contador real en Redis; 6º intento fallido → 429 RFC 9457."""
    for _ in range(MAX_LOGIN_ATTEMPTS):
        response = client.post(
            "/auth/login", json={"email": SEED_EMAIL, "password": "incorrecto"}
        )
        assert response.status_code == 401

    sixth = client.post(
        "/auth/login", json={"email": SEED_EMAIL, "password": "incorrecto"}
    )

    assert sixth.status_code == 429
    assert sixth.headers["content-type"] == "application/problem+json"
    body = sixth.json()
    assert body["type"] == "https://hira.dev/errors/rate-limited"
    assert body["status"] == 429
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_revocacion_real_logout_luego_refresh_401(client):
    """RF-010, RF-013 — logout revoca de verdad en Redis; el mismo refresh
    token ya no sirve."""
    login = client.post(
        "/auth/login", json={"email": SEED_EMAIL, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200
    tokens = login.json()

    logout = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout.status_code == 204

    refresh = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401
    body = refresh.json()
    assert body["type"] == "https://hira.dev/errors/token-revoked"
    assert body["status"] == 401
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_flujo_completo_login_acceso_protegido_refresh_logout(client):
    """Bcrypt+JWT reales de punta a punta — login → acceso a ruta protegida →
    refresh → logout (RF-001, RF-002, RF-011, RF-012)."""
    login = client.post(
        "/auth/login", json={"email": SEED_EMAIL, "password": SEED_PASSWORD}
    )
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"

    protected = client.get(
        "/test-protected",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert protected.status_code == 200
    assert protected.json()["rol"] == "admin"

    refresh = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 200
    new_access_token = refresh.json()["access_token"]
    # Nota: no se compara `new_access_token != tokens["access_token"]` con
    # desigualdad de string — si login y refresh caen en el mismo segundo
    # (`iat`/`exp` con resolución de segundos), el payload JWT es idéntico y la
    # firma también lo es determinísticamente; eso es correcto, no un bug. La
    # prueba real de que el refresh emitió un token *utilizable* es que
    # `/test-protected` responde 200 con él, abajo.

    protected_again = client.get(
        "/test-protected",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert protected_again.status_code == 200

    logout = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert logout.status_code == 204


def test_ruta_protegida_sin_token_401_rfc9457_exacto(client):
    response = client.get("/test-protected")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/token-missing"
    assert body["status"] == 401
    assert set(body.keys()) == {"type", "title", "status", "detail"}
