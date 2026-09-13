"""Correlation ID (RF-005) + Autenticación (RF-003, RF-007) — `spec.md`,
`SRV-002-auth-rbac` `plan.md §2`.

`CorrelationIdMiddleware` lee `X-Trace-ID` del request entrante; si el cliente no lo
envía, genera uno con `uuid4()`. Lo fija en `core.logger.trace_id_var` — el mismo
`ContextVar` que `core/logger.py` ya usa para sus logs (no se duplica) — durante todo
el ciclo de vida del request, y lo devuelve en la respuesta vía el header
`X-Trace-ID`. (`SRV-001-walking-skeleton`, sin cambios en este batch.)

`AuthenticationMiddleware` (`SRV-002-auth-rbac`, T-019/T-020) exige
`Authorization: Bearer <token>` para toda ruta fuera del *allowlist* público
(`PUBLIC_ALLOWLIST`); decodifica el access token (`core/security/jwt.py`) y
resuelve el usuario autenticado vía `services/rbac_service.py::
resolve_permissions` (cache-first), obteniendo `UserRepositoryPort`/`CachePort` de
`adapters/factory.py` — invocados directamente (sin `Depends()`, el middleware
ASGI no participa del sistema de inyección de FastAPI), mismo patrón que
`main.py::lifespan` usa con `get_notification_port()`. Fija
`request.state.user: AuthenticatedUser` para que routers/dependencias
posteriores (`core/security/dependencies.py`, T-021/T-022) lo consuman.

Cualquier 401 se retorna como `JSONResponse` (RFC 9457) directamente desde este
middleware — no se apoya en `app.add_exception_handler` de FastAPI: excepciones
lanzadas dentro de `call_next()` de un `BaseHTTPMiddleware` no llegan limpias a la
`ExceptionMiddleware` de Starlette (problema conocido de esa clase base).

La autorización fina (`require_role`/`require_project_scope`, RF-004/005/008/009)
NO vive aquí — Starlette resuelve los `path params` (p. ej. `project_id`) después
de que corre `BaseHTTPMiddleware.dispatch`, así que esas decisiones son
`Depends()` por router (excepción de complejidad documentada, `plan.md §7`).
"""
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from adapters.factory import get_cache_port, get_user_repository_port
from core.config import Settings
from core.errors import ProblemDetailError
from core.logger import trace_id_var
from core.security.jwt import TokenExpiredError, TokenInvalidError, decode_token
from services.rbac_service import resolve_permissions

TRACE_ID_HEADER = "X-Trace-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Propaga/genera el `trace_id` por request (RF-005)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid4())
        token = trace_id_var.set(trace_id)
        try:
            response = await call_next(request)
        finally:
            trace_id_var.reset(token)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response


PUBLIC_ALLOWLIST: frozenset[str] = frozenset(
    {"/health", "/auth/login", "/auth/refresh", "/docs", "/openapi.json", "/redoc"}
)

_ERRORS_BASE_URL = "https://hira.dev/errors"


def _problem_response(status: int, type_: str, title: str, detail: str) -> JSONResponse:
    """RFC 9457 — mismo *shape* de 4 campos que `schemas/errors.py::ProblemDetail`."""
    return JSONResponse(
        status_code=status,
        content={"type": type_, "title": title, "status": status, "detail": detail},
        media_type="application/problem+json",
    )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Exige un access token JWT válido para toda ruta fuera de `PUBLIC_ALLOWLIST`
    (RF-003, RF-007)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in PUBLIC_ALLOWLIST:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-missing",
                "Falta el token de acceso",
                "Se requiere el header 'Authorization: Bearer <token>'.",
            )

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            claims = decode_token(
                token, expected_type="access", secret_key=Settings().secret_key
            )
        except TokenExpiredError:
            return _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-expired",
                "Token expirado",
                "El access token expiró; solicite uno nuevo con /auth/refresh.",
            )
        except TokenInvalidError:
            return _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-invalid",
                "Token inválido",
                "El access token es inválido.",
            )

        try:
            authenticated_user = await resolve_permissions(
                claims.sub, get_user_repository_port(), get_cache_port()
            )
        except ProblemDetailError as exc:
            return _problem_response(exc.status, exc.type_, exc.title, exc.detail)

        request.state.user = authenticated_user
        return await call_next(request)
