"""`UserRepositoryPort` — interfaz abstracta del repositorio de dominio de usuarios
(`Protocol`, `SRV-ADR-017`), `SRV-002-auth-rbac` (`plan.md §2`, Registro de decisiones:
puerto nuevo, no se fuerza en `DatabasePort` que es *liveness*-only).

`services/auth_service.py` y `services/rbac_service.py` importan este contrato,
nunca `sqlalchemy`/`asyncpg` directamente. La implementación real
(`adapters/db/user_repository_adapter.py::PostgreSQLUserRepository`) llega en un
batch posterior de `tasks.md` (T-024/T-025) — fuera de alcance aquí. Sin test
propio, igual que `database_port.py` en `SRV-001`: es una interfaz, no lógica.
"""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UserRecord:
    """Registro de un usuario tal como lo expone el repositorio de dominio.

    `rol` ∈ {"admin", "operador", "visor"}; `scope` ∈ {"global", "project"}
    (`plan.md §3`). `project_id` es `None` cuando `scope="global"`.
    """

    id: str
    email: str
    password_hash: str
    rol: str
    scope: str
    project_id: str | None
    activo: bool


class UserRepositoryPort(Protocol):
    """Contrato del repositorio de dominio de usuarios (RF-001, RF-002, RF-006,
    RF-007, RF-012)."""

    async def get_by_email(self, email: str) -> UserRecord | None:
        """Retorna el `UserRecord` de `email`, o `None` si no existe (RF-001, RF-002)."""
        ...

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        """Retorna el `UserRecord` de `user_id`, o `None` si no existe (RF-007)."""
        ...

    async def update_role(self, user_id: str, new_role: str) -> None:
        """Actualiza el `rol` de `user_id` (RF-006). No invalida caché — eso lo
        hace `services/rbac_service.py::update_user_role`, orquestando ambos pasos."""
        ...
