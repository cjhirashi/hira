"""`routers/auth.py` — `POST /auth/login|refresh|logout` (adaptador de entrada HTTP).

Contrato: `hira-server/docs/openapi.yaml#/paths/~1auth~1login` (+ `~1auth~1refresh`,
`~1auth~1logout`) — verifica el *shape* exacto de 200/401/429, incluyendo el sobre
RFC 9457 (`ProblemDetail`, `Content-Type: application/problem+json`) en los errores.

Golpea la app real de `main.py` vía `TestClient` (mismo patrón que
`test_health_router.py`), sustituyendo `UserRepositoryPort`/`CachePort` por dobles
in-memory vía `app.dependency_overrides` (`adapters/factory.py::
get_user_repository_port/get_cache_port`) — sin contenedores reales (`plan.md §5`:
"unit + TestClient, sin contenedores"). `MosquittoAdapter.connect()` se sustituye
igual que en `test_health_router.py`, para que el `lifespan` no dependa de red real.

Debe fallar antes de T-018 (no existen `routers/auth.py` ni
`adapters/factory.py::get_user_repository_port`).

El `Authorization: Bearer <access_token>` en las llamadas a `/auth/logout` se
incluye desde este batch aunque `AuthenticationMiddleware` (T-019/T-020) todavía no
exista — es inofensivo hasta entonces y evita reescribir este test cuando el
middleware entre en vigor y `/auth/logout` empiece a exigirlo (`plan.md §2`: "SÍ
requiere el middleware").
"""
from dataclasses import replace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import core.middleware as middleware_module
from adapters.factory import get_cache_port, get_user_repository_port
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from core.ports.user_repository_port import UserRecord
from core.security.passwords import hash_password
from main import app
from services.auth_service import MAX_LOGIN_ATTEMPTS

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hira:hira@postgres:5432/hiradb",
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}


class _FakeCache:
    """`CachePort` in-memory — mismo doble que `tests/test_auth_service.py`."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None:
        self._store[key] = value

    async def incr(self, key: str) -> int:
        current = int(self._store.get(key, "0")) + 1
        self._store[key] = str(current)
        return current

    async def expire(self, key: str, ttl_seconds: int) -> None:
        pass

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class _FakeUserRepository:
    """`UserRepositoryPort` in-memory — mismo doble que `tests/test_auth_service.py`."""

    def __init__(self, users: list[UserRecord]) -> None:
        self._by_email = {u.email: u for u in users}
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return self._by_email.get(email)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        user = self._by_id[user_id]
        updated = replace(user, rol=new_role)
        self._by_id[user_id] = updated
        self._by_email[user.email] = updated


def _make_user(**overrides) -> UserRecord:
    defaults = dict(
        id="user-1",
        email="admin@hira.dev",
        password_hash=hash_password("Correcto123!"),
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    defaults.update(overrides)
    return UserRecord(**defaults)


@pytest.fixture
def client(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

    repo = _FakeUserRepository([_make_user()])
    cache = _FakeCache()
    app.dependency_overrides[get_user_repository_port] = lambda: repo
    app.dependency_overrides[get_cache_port] = lambda: cache
    # `AuthenticationMiddleware` (T-019/T-020) no participa del sistema de
    # `Depends()` de FastAPI — resuelve los puertos invocando directamente
    # `adapters.factory.*` (mismo patrón que `main.py::lifespan`). Para que
    # `/auth/logout` (protegido por el middleware) vea el **mismo** usuario/
    # refresh token que el router acaba de crear vía login, el middleware debe
    # resolver contra las mismas instancias `repo`/`cache` de este fixture, no
    # contra el `RedisAdapter`/`_InMemoryUserRepository` reales de `factory.py`.
    monkeypatch.setattr(middleware_module, "get_user_repository_port", lambda: repo)
    monkeypatch.setattr(middleware_module, "get_cache_port", lambda: cache)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_login_credenciales_validas_200_shape_del_contrato(client):
    response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "Correcto123!"}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "refresh_token", "token_type"}
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_credenciales_invalidas_401_rfc9457(client):
    response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "incorrecto"}
    )

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/invalid-credentials"
    assert body["status"] == 401
    assert set(body.keys()) == {"type", "title", "status", "detail"}


def test_login_email_inexistente_mismo_401_generico(client):
    response = client.post(
        "/auth/login", json={"email": "nadie@hira.dev", "password": "cualquiera"}
    )

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/invalid-credentials"


def test_login_sexto_intento_fallido_429_rfc9457(client):
    for _ in range(MAX_LOGIN_ATTEMPTS):
        client.post(
            "/auth/login", json={"email": "admin@hira.dev", "password": "incorrecto"}
        )

    response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "incorrecto"}
    )

    assert response.status_code == 429
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/rate-limited"
    assert body["status"] == 429


def test_refresh_token_valido_200_shape_del_contrato(client):
    login_response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "Correcto123!"}
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"


def test_refresh_token_revocado_401_rfc9457(client):
    login_response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "Correcto123!"}
    )
    tokens = login_response.json()
    client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    response = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-revoked"


def test_refresh_token_malformado_401_rfc9457(client):
    response = client.post(
        "/auth/refresh", json={"refresh_token": "token-basura-no-es-jwt"}
    )

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-invalid"


def test_logout_revoca_y_204_sin_contenido(client):
    login_response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "Correcto123!"}
    )
    tokens = login_response.json()

    response = client.post(
        "/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 204
    assert response.content == b""


def test_logout_es_idempotente_204(client):
    login_response = client.post(
        "/auth/login", json={"email": "admin@hira.dev", "password": "Correcto123!"}
    )
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    first = client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )
    second = client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers
    )

    assert first.status_code == 204
    assert second.status_code == 204
