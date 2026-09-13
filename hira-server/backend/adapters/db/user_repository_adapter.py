"""`PostgreSQLUserRepository` — implementación real de `UserRepositoryPort`
(`SRV-002-auth-rbac`, T-024/T-025, `plan.md §2`/§3).

Motor async propio (`AsyncEngine`, `asyncpg`), mismo estilo que
`postgresql_adapter.py`: SQLAlchemy Core (`select`/`update`), sin ORM
declarativo — una sola tabla no lo justifica (Anti-Abstraction). Opera contra
`models/user_model.py::users_table`.

Solo `adapters/*` puede importar `sqlalchemy`/`asyncpg` — `services/` sigue
importando únicamente `core/ports/user_repository_port.py` (`SRV-ADR-017`).
"""
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from core.ports.user_repository_port import UserRecord
from models.user_model import users_table


class PostgreSQLUserRepository:
    """Implementa `UserRepositoryPort` contra un PostgreSQL real."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url, pool_pre_ping=True
        )

    @staticmethod
    def _row_to_record(row) -> UserRecord:
        return UserRecord(
            id=str(row.id),
            email=row.email,
            password_hash=row.password_hash,
            rol=row.rol,
            scope=row.scope,
            project_id=str(row.project_id) if row.project_id is not None else None,
            activo=row.activo,
        )

    async def get_by_email(self, email: str) -> UserRecord | None:
        """RF-001, RF-002 — busca por `email` (índice único)."""
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(users_table).where(users_table.c.email == email)
            )
            row = result.first()
        return self._row_to_record(row) if row is not None else None

    async def get_by_id(self, user_id: str) -> UserRecord | None:
        """RF-007 — busca por `id` (PK), usado en *cache-miss* de `resolve_permissions`."""
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(users_table).where(users_table.c.id == user_id)
            )
            row = result.first()
        return self._row_to_record(row) if row is not None else None

    async def update_role(self, user_id: str, new_role: str) -> None:
        """RF-006 — actualiza `rol` y `updated_at`. No invalida caché — eso lo
        hace `services/rbac_service.py::update_user_role`."""
        async with self._engine.begin() as connection:
            await connection.execute(
                update(users_table)
                .where(users_table.c.id == user_id)
                .values(rol=new_role, updated_at=func.now())
            )

    async def close(self) -> None:
        """Libera el pool de conexiones — usado en tests de integración y shutdown."""
        await self._engine.dispose()
