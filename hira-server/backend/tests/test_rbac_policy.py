"""Núcleo — política RBAC de 3 roles fijos. Sin I/O, sin mocks.

Cubre RF-004 (Visor sin escritura), RF-005 (recurso reservado a Admin), RF-008
(scope=project no cruza de proyecto), RF-009 (scope=global sin re-login) —
`spec.md`. Reglas hardcodeadas del MVP — el RBAC dinámico es v0.2 (`SRV-ADR-005`).
"""
import pytest

from core.security.rbac_policy import can_access_project, can_write, is_admin


@pytest.mark.parametrize(
    "rol, expected",
    [
        ("admin", True),
        ("operador", True),
        ("visor", False),
    ],
)
def test_can_write_matriz_por_rol(rol, expected):
    assert can_write(rol) is expected


@pytest.mark.parametrize(
    "rol, expected",
    [
        ("admin", True),
        ("operador", False),
        ("visor", False),
    ],
)
def test_is_admin_matriz_por_rol(rol, expected):
    assert is_admin(rol) is expected


def test_can_access_project_scope_global_siempre_true_mismo_proyecto():
    assert can_access_project("global", None, "proyecto-1") is True


def test_can_access_project_scope_global_siempre_true_otro_proyecto():
    # RF-009: usuario integrador (scope=global) cambia de proyecto sin re-login.
    assert can_access_project("global", None, "proyecto-2") is True


def test_can_access_project_scope_project_coincide():
    assert can_access_project("project", "proyecto-1", "proyecto-1") is True


def test_can_access_project_scope_project_no_coincide():
    # RF-008: usuario de operación no accede a un proyecto distinto al suyo.
    assert can_access_project("project", "proyecto-1", "proyecto-2") is False
