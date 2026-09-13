"""`require_role`/`require_project_scope` — autorización fina como `Depends()` de
FastAPI (RF-004, RF-005, RF-008, RF-009, `plan.md §2`/§7).

Excepción de complejidad documentada (`plan.md §7`): Starlette resuelve los
`path params` (p. ej. `project_id`) **después** de que corre
`BaseHTTPMiddleware.dispatch` — un middleware ASGI puro no puede leer
`project_id` de la ruta todavía. Estas factories de `Depends()` son la única
forma correcta de implementar decisiones que dependen del parámetro concreto de
la ruta, sin duplicar el parseo de rutas a mano dentro de
`AuthenticationMiddleware`.

Leen `request.state.user` (`AuthenticatedUser`, ya fijado por
`AuthenticationMiddleware`, `core/middleware.py`) y aplican
`core/security/rbac_policy.py` — sin I/O propio, a diferencia del resto de
`core/security/*` sí importan FastAPI (excepción ya aprobada, no reabre el
diseño de esa carpeta).
"""
from typing import Callable

from fastapi import Request

from core.errors import ProblemDetailError
from core.security.rbac_policy import can_access_project

_ERRORS_BASE_URL = "https://hira.dev/errors"


def require_role(*roles: str) -> Callable:
    """Bloquea con 403 (`insufficient-role`) si `request.state.user.rol` no está
    en `roles` (RF-004, RF-005).

    El router decide qué conjunto de roles exige cada recurso — p. ej.
    `require_role("admin", "operador")` para un recurso de escritura (el mismo
    conjunto que `core/security/rbac_policy.py::can_write`), o
    `require_role("admin")` para un recurso reservado (equivalente a `is_admin`).
    """

    async def dependency(request: Request) -> None:
        user = request.state.user
        if user.rol not in roles:
            raise ProblemDetailError(
                status=403,
                type_=f"{_ERRORS_BASE_URL}/insufficient-role",
                title="Rol insuficiente",
                detail=f"Se requiere uno de los roles: {', '.join(roles)}.",
            )

    return dependency


def require_project_scope(project_id_param: str = "project_id") -> Callable:
    """Bloquea con 403 (`project-scope-denied`) si `request.state.user` no puede
    acceder al `project_id` de la ruta (RF-008, RF-009).

    Aplica `core/security/rbac_policy.py::can_access_project`: `scope="global"`
    (usuario integrador, `SRV-ADR-020`) siempre pasa, sin exigir re-login al
    cambiar de proyecto; `scope="project"` solo pasa si coincide con el
    `project_id` del usuario.
    """

    async def dependency(request: Request) -> None:
        user = request.state.user
        requested_project_id = request.path_params.get(project_id_param)
        if not can_access_project(user.scope, user.project_id, requested_project_id):
            raise ProblemDetailError(
                status=403,
                type_=f"{_ERRORS_BASE_URL}/project-scope-denied",
                title="Proyecto fuera de alcance",
                detail=(
                    f"El usuario no tiene acceso al proyecto "
                    f"'{requested_project_id}'."
                ),
            )

    return dependency
