"""`ProblemDetailError` — excepción del sobre de error RFC 9457 (`plan.md §2`).

Núcleo puro: sin I/O. `services/`, `core/security/dependencies.py` y el
`AuthenticationMiddleware` (batches posteriores de `tasks.md`) la lanzan con los
campos concretos del catálogo de slugs de `plan.md §4` (`E-ADR-003`:
`type: https://hira.dev/errors/<slug>`); aquí solo se define la clase genérica —
el catálogo de slugs concretos no se anticipa en este batch.
"""


class ProblemDetailError(Exception):
    """Excepción que porta los 4 campos del sobre RFC 9457 (`ProblemDetail`).

    `main.py` la traduce a una respuesta HTTP vía
    `app.add_exception_handler(ProblemDetailError, ...)` (batch posterior).
    """

    def __init__(self, status: int, type_: str, title: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.type_ = type_
        self.title = title
        self.detail = detail
