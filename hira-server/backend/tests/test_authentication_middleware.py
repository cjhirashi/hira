"""`core/middleware.py::AuthenticationMiddleware` — RF-003, RF-007 (`plan.md §2`).

Verifica: token ausente/inválido/expirado en una ruta protegida → 401 con la
forma RFC 9457 exacta; una ruta del *allowlist* público no exige token;
`request.state.user` (`AuthenticatedUser`) queda disponible en una ruta protegida
tras un access token válido; una ruta fuera del *allowlist* (p. ej. `/auth/logout`)
sí exige el middleware.

App de prueba construida en este mismo archivo (mismo patrón que
`test_correlation_id.py::_build_app`) — no toca `main.py` ni routers de
producción. Los puertos que el middleware resuelve internamente
(`adapters/factory.py::get_user_repository_port/get_cache_port`, invocados
directamente sin `Depends()` — mismo patrón que `main.py::lifespan` con
`get_notification_port()`) se sustituyen por dobles in-memory vía `monkeypatch`
sobre los nombres importados dentro de `core.middleware`. `Settings()` también se
sustituye — el módulo no necesita las variables de entorno reales del backend.

Debe fallar antes de T-020 (`AuthenticationMiddleware` no existe todavía).
"""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

import core.middleware as middleware_module
from core.middleware import PUBLIC_ALLOWLIST, AuthenticationMiddleware
from core.ports.user_repository_port import UserRecord
from core.security import jwt as jwt_module
from services.rbac_service import AuthenticatedUser

SECRET_KEY = "test-secret-key"


class _FakeCache:
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
    def __init__(self, users: list[UserRecord]) -> None:
        self._by_id = {u.id: u for u in users}

    async def get_by_email(self, email: str) -> UserRecord | None:
        return next((u for u in self._by_id.values() if u.email == email), None)

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    async def update_role(self, user_id: str, new_role: str) -> None:
        pass


def _make_user(**overrides) -> UserRecord:
    defaults = dict(
        id="user-1",
        email="admin@hira.dev",
        password_hash="x",
        rol="admin",
        scope="global",
        project_id=None,
        activo=True,
    )
    defaults.update(overrides)
    return UserRecord(**defaults)


class _FakeSettings:
    secret_key = SECRET_KEY


def _access_token(
    user_id: str = "user-1", rol: str = "admin", scope: str = "global", project_id=None
) -> str:
    return jwt_module.create_access_token(user_id, rol, scope, project_id, SECRET_KEY)


def _build_app(monkeypatch, users: list[UserRecord] | None = None) -> TestClient:
    repo = _FakeUserRepository(users if users is not None else [_make_user()])
    cache = _FakeCache()
    monkeypatch.setattr(middleware_module, "get_user_repository_port", lambda: repo)
    monkeypatch.setattr(middleware_module, "get_cache_port", lambda: cache)
    monkeypatch.setattr(middleware_module, "Settings", _FakeSettings)

    app = FastAPI()
    app.add_middleware(AuthenticationMiddleware)

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.post("/auth/login")
    async def auth_login():
        return {"ok": True}

    @app.get("/protected")
    async def protected(request: Request):
        user: AuthenticatedUser = request.state.user
        return {"user_id": user.user_id, "rol": user.rol}

    return TestClient(app)


@pytest.fixture
def client(monkeypatch) -> TestClient:
    return _build_app(monkeypatch)


def test_allowlist_contiene_las_rutas_publicas_esperadas():
    assert PUBLIC_ALLOWLIST == {
        "/health",
        "/auth/login",
        "/auth/refresh",
        "/docs",
        "/openapi.json",
        "/redoc",
    }


def test_ruta_allowlist_get_health_no_exige_token(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_ruta_allowlist_auth_login_no_exige_token(client):
    response = client.post("/auth/login")

    assert response.status_code == 200


def test_ruta_fuera_de_allowlist_sin_token_401_token_missing(client):
    response = client.get("/protected")

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/token-missing"
    assert body["status"] == 401


def test_auth_logout_no_esta_en_allowlist_exige_token(client):
    """`/auth/logout` no está en el *allowlist* — el middleware lo intercepta
    con 401 antes de que la ausencia de la ruta en esta app sintética importe."""
    response = client.post("/auth/logout", json={"refresh_token": "x"})

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-missing"


def test_ruta_protegida_token_malformado_401_token_invalid(client):
    response = client.get(
        "/protected", headers={"Authorization": "Bearer token-basura-no-es-jwt"}
    )

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-invalid"


def test_ruta_protegida_sin_prefijo_bearer_401_token_missing(client):
    response = client.get("/protected", headers={"Authorization": "token-sin-bearer"})

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-missing"


def test_ruta_protegida_token_expirado_401_token_expired(client):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-1",
        "rol": "admin",
        "scope": "global",
        "project_id": None,
        "type": "access",
        "iat": now - timedelta(hours=1),
        "exp": now - timedelta(minutes=1),
    }
    expired = pyjwt.encode(payload, SECRET_KEY, algorithm="HS256")

    response = client.get("/protected", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-expired"


def test_ruta_protegida_usuario_inexistente_401_token_invalid(monkeypatch):
    client = _build_app(monkeypatch, users=[])  # sin usuarios: get_by_id -> None
    token = _access_token(user_id="ghost")

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-invalid"


def test_ruta_protegida_usuario_desactivado_401_token_invalid(monkeypatch):
    client = _build_app(monkeypatch, users=[_make_user(activo=False)])
    token = _access_token()

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["type"] == "https://hira.dev/errors/token-invalid"


def test_ruta_protegida_token_valido_fija_request_state_user(client):
    token = _access_token(user_id="user-1", rol="admin")

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "user-1"
    assert body["rol"] == "admin"
