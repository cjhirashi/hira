"""`core/security/dependencies.py::require_role/require_project_scope` — RF-004,
RF-005, RF-008, RF-009 (`plan.md §2`/§7).

App **sintética** construida en este mismo archivo (mismo patrón que
`test_correlation_id.py::_build_app` — sin tocar routers de producción,
`plan.md §2`: "no se crea un endpoint de producción especulativo solo para
probarlas"). Un middleware de prueba (`_FakeAuthHeaderMiddleware`) fija
`request.state.user` a partir de headers `X-Test-*` — simula lo que
`AuthenticationMiddleware` real fija en producción, sin depender de él.

Debe fallar antes de T-022 (`require_role`/`require_project_scope` no existen
todavía en `core/security/dependencies.py`).
"""
import pytest
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from core.errors import ProblemDetailError
from core.security.dependencies import require_project_scope, require_role
from services.rbac_service import AuthenticatedUser


class _FakeAuthHeaderMiddleware(BaseHTTPMiddleware):
    """Sustituto sintético de `AuthenticationMiddleware` — fija
    `request.state.user` a partir de headers de prueba, sin JWT ni puertos
    reales (esta zona solo prueba la autorización fina, no la autenticación,
    ya cubierta por `test_authentication_middleware.py`)."""

    async def dispatch(self, request: Request, call_next):
        request.state.user = AuthenticatedUser(
            user_id="test-user",
            rol=request.headers.get("X-Test-Rol", "visor"),
            scope=request.headers.get("X-Test-Scope", "project"),
            project_id=request.headers.get("X-Test-Project-Id") or None,
            activo=True,
        )
        return await call_next(request)


def _build_app() -> TestClient:
    app = FastAPI()
    app.add_middleware(_FakeAuthHeaderMiddleware)

    @app.exception_handler(ProblemDetailError)
    async def _problem_detail_handler(
        request: Request, exc: ProblemDetailError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content={
                "type": exc.type_,
                "title": exc.title,
                "status": exc.status,
                "detail": exc.detail,
            },
            media_type="application/problem+json",
        )

    @app.get("/write", dependencies=[Depends(require_role("admin", "operador"))])
    async def write_endpoint():
        return {"ok": True}

    @app.get("/admin-only", dependencies=[Depends(require_role("admin"))])
    async def admin_only_endpoint():
        return {"ok": True}

    @app.get(
        "/projects/{project_id}/resource",
        dependencies=[Depends(require_project_scope())],
    )
    async def project_resource(project_id: str):
        return {"project_id": project_id}

    return TestClient(app)


@pytest.fixture
def client() -> TestClient:
    return _build_app()


def test_visor_bloqueado_en_escritura_403_insufficient_role(client):
    """RF-004 — Visor no puede escribir."""
    response = client.get("/write", headers={"X-Test-Rol": "visor"})

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/insufficient-role"
    assert body["status"] == 403


def test_admin_permitido_en_escritura_200(client):
    """RF-004 — Admin sí puede escribir."""
    response = client.get("/write", headers={"X-Test-Rol": "admin"})

    assert response.status_code == 200


def test_operador_permitido_en_escritura_200(client):
    """RF-004 — Operador sí puede escribir."""
    response = client.get("/write", headers={"X-Test-Rol": "operador"})

    assert response.status_code == 200


def test_operador_bloqueado_en_recurso_reservado_a_admin_403(client):
    """RF-005 — Operador no accede a un recurso reservado a Admin."""
    response = client.get("/admin-only", headers={"X-Test-Rol": "operador"})

    assert response.status_code == 403
    assert response.json()["type"] == "https://hira.dev/errors/insufficient-role"


def test_admin_permitido_en_recurso_reservado_a_admin_200(client):
    """RF-005 — Admin sí accede al recurso reservado."""
    response = client.get("/admin-only", headers={"X-Test-Rol": "admin"})

    assert response.status_code == 200


def test_scope_project_cruzando_de_proyecto_403(client):
    """RF-008 — `scope=project` no puede cruzar a otro `project_id`."""
    response = client.get(
        "/projects/proj-B/resource",
        headers={"X-Test-Scope": "project", "X-Test-Project-Id": "proj-A"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["type"] == "https://hira.dev/errors/project-scope-denied"
    assert body["status"] == 403


def test_scope_project_mismo_proyecto_200(client):
    """RF-008 — `scope=project` sí accede a su propio `project_id`."""
    response = client.get(
        "/projects/proj-A/resource",
        headers={"X-Test-Scope": "project", "X-Test-Project-Id": "proj-A"},
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == "proj-A"


def test_scope_global_accede_a_cualquier_proyecto_sin_relogin_200(client):
    """RF-009 — `scope=global` (usuario integrador) accede a cualquier proyecto
    sin exigir re-login al cambiar de proyecto."""
    response = client.get(
        "/projects/cualquier-proyecto/resource", headers={"X-Test-Scope": "global"}
    )

    assert response.status_code == 200
    assert response.json()["project_id"] == "cualquier-proyecto"
