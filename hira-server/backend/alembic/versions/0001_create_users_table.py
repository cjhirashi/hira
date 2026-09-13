"""Crea la tabla `users` — primera tabla de negocio del producto.

Revision ID: 0001
Revises:
Create Date: 2026-09-13

Escrita a mano (no autogenerada, `plan.md §3`: un solo `CREATE TABLE` no
justifica `alembic revision --autogenerate`). Columnas y `CHECK` exactos de
`plan.md §3` / `models/user_model.py`. `SRV-002-auth-rbac`, T-023.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("scope", sa.String(10), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "activo", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "rol IN ('admin', 'operador', 'visor')", name="ck_users_rol"
        ),
        sa.CheckConstraint("scope IN ('project', 'global')", name="ck_users_scope"),
        sa.CheckConstraint(
            "(scope = 'global' AND project_id IS NULL) "
            "OR (scope = 'project' AND project_id IS NOT NULL)",
            name="ck_users_scope_project_id",
        ),
    )
    op.create_index("ix_users_project_id", "users", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_users_project_id", table_name="users")
    op.drop_table("users")
