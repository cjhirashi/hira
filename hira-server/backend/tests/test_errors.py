"""Núcleo — sobre de error RFC 9457. Sin I/O, sin mocks.

`ProblemDetailError` (excepción) expone `status`/`type_`/`title`/`detail`
correctos (`plan.md §2`). El catálogo concreto de slugs (`E-ADR-003`) se consume
en `services/`/`routers/` de batches posteriores — aquí solo se prueba la clase
genérica y su traducción a `schemas/errors.py::ProblemDetail`.
"""
import pytest

from core.errors import ProblemDetailError
from schemas.errors import ProblemDetail


def test_problem_detail_error_expone_los_4_campos():
    error = ProblemDetailError(
        status=401,
        type_="https://hira.dev/errors/invalid-credentials",
        title="Credenciales inválidas",
        detail="El email o el password no coinciden con ningún usuario activo.",
    )

    assert error.status == 401
    assert error.type_ == "https://hira.dev/errors/invalid-credentials"
    assert error.title == "Credenciales inválidas"
    assert error.detail == "El email o el password no coinciden con ningún usuario activo."


def test_problem_detail_error_es_una_excepcion():
    with pytest.raises(ProblemDetailError):
        raise ProblemDetailError(
            status=403,
            type_="https://hira.dev/errors/insufficient-role",
            title="Rol insuficiente",
            detail="El rol actual no tiene permiso de escritura.",
        )


def test_problem_detail_schema_serializa_los_4_campos_rfc9457():
    problem = ProblemDetail(
        type="https://hira.dev/errors/token-expired",
        title="Token expirado",
        status=401,
        detail="El access token expiró; solicite uno nuevo con /auth/refresh.",
    )

    payload = problem.model_dump()

    assert payload == {
        "type": "https://hira.dev/errors/token-expired",
        "title": "Token expirado",
        "status": 401,
        "detail": "El access token expiró; solicite uno nuevo con /auth/refresh.",
    }


def test_problem_detail_desde_problem_detail_error():
    error = ProblemDetailError(
        status=429,
        type_="https://hira.dev/errors/rate-limited",
        title="Demasiados intentos",
        detail="Se excedió el máximo de intentos de login para esta combinación.",
    )

    problem = ProblemDetail(
        type=error.type_, title=error.title, status=error.status, detail=error.detail
    )

    assert problem.status == 429
    assert problem.type == "https://hira.dev/errors/rate-limited"
