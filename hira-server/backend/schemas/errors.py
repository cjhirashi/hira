"""`ProblemDetail` — sobre de error RFC 9457 (`plan.md §4`, `E-ADR-003`).

Modelo Pydantic común a los 3 productos del ecosistema (`E-ADR-003`, convención
`type: https://hira.dev/errors/<slug>`). `main.py` lo usa para serializar
`core.errors.ProblemDetailError` con `media_type="application/problem+json"`
(batch posterior de `tasks.md`).
"""
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """Sobre de error RFC 9457 — `type`, `title`, `status`, `detail`."""

    type: str
    title: str
    status: int
    detail: str
