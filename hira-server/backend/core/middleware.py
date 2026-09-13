"""Correlation ID (RF-005) + Autenticación (RF-003, RF-007) — `spec.md`,
`SRV-002-auth-rbac` `plan.md §2`.

`CorrelationIdMiddleware` lee `X-Trace-ID` del request entrante; si el cliente no lo
envía, genera uno con `uuid4()`. Lo fija en `core.logger.trace_id_var` — el mismo
`ContextVar` que `core/logger.py` ya usa para sus logs (no se duplica) — durante todo
el ciclo de vida del request, y lo devuelve en la respuesta vía el header
`X-Trace-ID`. (`SRV-001-walking-skeleton`, sin cambios en este batch.)

`AuthenticationMiddleware` (`SRV-002-auth-rbac`, T-019/T-020; **migrado a ASGI
puro en T-038**, `plan.md §10`, resolución de RNF-001) exige `Authorization:
Bearer <token>` para toda ruta fuera del *allowlist* público
(`PUBLIC_ALLOWLIST`); decodifica el access token (`core/security/jwt.py`) y
resuelve el usuario autenticado vía `services/rbac_service.py::
resolve_permissions` (cache-first, local-primero desde T-035), obteniendo
`UserRepositoryPort`/`CachePort` de `adapters/factory.py` — invocados
directamente (sin `Depends()`, el middleware ASGI no participa del sistema de
inyección de FastAPI), mismo patrón que `main.py::lifespan` usa con
`get_notification_port()`. Fija `request.state.user: AuthenticatedUser` para
que routers/dependencias posteriores (`core/security/dependencies.py`,
T-021/T-022) lo consuman.

**Middleware ASGI puro (T-038), no `BaseHTTPMiddleware`:** la Directiva de
Pausa de RNF-001 (`plan.md §10`) confirmó que `BaseHTTPMiddleware`
(`anyio.create_task_group()` + *memory object stream* por request) impone un
piso de ~20-36ms a 100 concurrentes **antes** de que corra cualquier lógica
propia — inalcanzable bajo el umbral de <5ms. Un middleware ASGI puro
(`__init__(self, app)`, `async def __call__(self, scope, receive, send)`)
controla el ciclo de vida completo de la respuesta él mismo: puede construir y
enviar un `JSONResponse` de 401 directamente vía `await response(scope,
receive, send)` — `Response`/`JSONResponse` de Starlette ya implementan el
protocolo ASGI — sin pasar por `call_next()` ni por la `ExceptionMiddleware`.
Esto preserva el motivo original de usar una clase con control total de la
respuesta (una excepción lanzada dentro de `call_next()` de un
`BaseHTTPMiddleware` no llega limpia a la `ExceptionMiddleware` de Starlette)
sin pagar el costo de esa clase base: aquí nunca se lanza una excepción, se
construye y envía la respuesta directamente. `request.state.user` sigue
funcionando igual: el objeto `Request` que este middleware construye comparte
el mismo `scope` que la app interna recibirá — `Request.state` lee/escribe
`scope["state"]` (un `dict` mutable dentro de `scope`, creado con
`scope.setdefault("state", {})`), así que fijarlo aquí es visible para
cualquier `Request` construido más adelante en la cadena a partir del mismo
`scope`. **Contrato observable sin cambios** respecto a T-019/T-020: mismo
*allowlist*, mismo `request.state.user`, mismo *shape* RFC 9457 en los 401 —
`tests/test_authentication_middleware.py` (12 casos) pasa sin relajar ninguna
aserción.

La autorización fina (`require_role`/`require_project_scope`, RF-004/005/008/009)
NO vive aquí — Starlette resuelve los `path params` (p. ej. `project_id`) después
del enrutamiento (que corre dentro de `self.app(...)`, más adentro que este
middleware), así que esas decisiones son `Depends()` por router (excepción de
complejidad documentada, `plan.md §7`).
"""
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

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


class AuthenticationMiddleware:
    """Exige un access token JWT válido para toda ruta fuera de `PUBLIC_ALLOWLIST`
    (RF-003, RF-007). Middleware ASGI puro (T-038, ver docstring del módulo) —
    controla el ciclo de vida completo de la respuesta, sin `BaseHTTPMiddleware`."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)
        if request.url.path in PUBLIC_ALLOWLIST:
            await self.app(scope, receive, send)
            return

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            response = _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-missing",
                "Falta el token de acceso",
                "Se requiere el header 'Authorization: Bearer <token>'.",
            )
            await response(scope, receive, send)
            return

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            claims = decode_token(
                token, expected_type="access", secret_key=Settings().secret_key
            )
        except TokenExpiredError:
            response = _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-expired",
                "Token expirado",
                "El access token expiró; solicite uno nuevo con /auth/refresh.",
            )
            await response(scope, receive, send)
            return
        except TokenInvalidError:
            response = _problem_response(
                401,
                f"{_ERRORS_BASE_URL}/token-invalid",
                "Token inválido",
                "El access token es inválido.",
            )
            await response(scope, receive, send)
            return

        try:
            authenticated_user = await resolve_permissions(
                claims.sub, get_user_repository_port(), get_cache_port()
            )
        except ProblemDetailError as exc:
            response = _problem_response(exc.status, exc.type_, exc.title, exc.detail)
            await response(scope, receive, send)
            return

        request.state.user = authenticated_user
        await self.app(scope, receive, send)
