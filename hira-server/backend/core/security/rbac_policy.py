"""Política RBAC de 3 roles fijos — RF-004, RF-005, RF-008, RF-009 (`spec.md`).

Núcleo puro: decisión sin I/O, reglas hardcodeadas del MVP (`SRV-ADR-005` fasea el
RBAC dinámico completo a v0.2 — no se anticipa aquí). Consumido por
`core/security/dependencies.py` en un batch posterior de `tasks.md`.
"""
from typing import Literal

Rol = Literal["admin", "operador", "visor"]
Scope = Literal["global", "project"]

_ROLES_CON_ESCRITURA: frozenset[str] = frozenset({"admin", "operador"})


def can_write(rol: str) -> bool:
    """`True` si `rol` puede realizar operaciones de escritura (RF-004).

    Admin y Operador sí; Visor no.
    """
    return rol in _ROLES_CON_ESCRITURA


def is_admin(rol: str) -> bool:
    """`True` si `rol` es Admin — único rol con acceso a recursos reservados (RF-005)."""
    return rol == "admin"


def can_access_project(
    scope: str, user_project_id: str | None, requested_project_id: str
) -> bool:
    """`True` si un usuario con `scope`/`user_project_id` puede acceder a
    `requested_project_id` (RF-008, RF-009).

    `scope="global"` (usuario integrador, `SRV-ADR-020`) → siempre `True`, sin
    exigir re-login al cambiar de proyecto (RF-009). `scope="project"` (usuario
    de operación) → solo si `user_project_id` coincide con `requested_project_id`
    (RF-008).
    """
    if scope == "global":
        return True
    return user_project_id == requested_project_id
