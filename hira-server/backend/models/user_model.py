"""`users_table` — SQLAlchemy Core (`Table`, no ORM declarativo), primera tabla
de negocio del producto (`SRV-002-auth-rbac`, `plan.md §3`, T-023).

Mismo estilo que `adapters/db/postgresql_adapter.py` (Core, sin
`declarative_base()`/`Session`) — una sola tabla no lo justifica (Anti-Abstraction,
`plan.md §0`). `metadata` es el `target_metadata` de `alembic/env.py`;
`adapters/db/user_repository_adapter.py::PostgreSQLUserRepository` (T-024/T-025)
es el único módulo de `services`/`adapters` que debería referenciar `users_table`
en operaciones `select`/`insert`/`update` (`services/` sigue importando solo
`core/ports/user_repository_port.py`, `SRV-ADR-017`).
"""
import uuid

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Index,
    MetaData,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("rol", String(20), nullable=False),
    Column("scope", String(10), nullable=False),
    Column("project_id", UUID(as_uuid=True), nullable=True),
    Column("activo", Boolean, nullable=False, server_default="true"),
    Column(
        "created_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    Column(
        "updated_at",
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    ),
    CheckConstraint("rol IN ('admin', 'operador', 'visor')", name="ck_users_rol"),
    CheckConstraint("scope IN ('project', 'global')", name="ck_users_scope"),
    CheckConstraint(
        "(scope = 'global' AND project_id IS NULL) "
        "OR (scope = 'project' AND project_id IS NOT NULL)",
        name="ck_users_scope_project_id",
    ),
    Index("ix_users_project_id", "project_id"),
)
