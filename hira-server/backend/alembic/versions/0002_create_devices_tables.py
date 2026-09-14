"""Crea las tablas `devices` y `device_points_candidates` — segunda y tercera
tabla de negocio del producto.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-14

Escrita a mano (no autogenerada, `plan.md §3`: 2 `CREATE TABLE` no justifican
`alembic revision --autogenerate`). Columnas y constraints exactos de
`plan.md §3` / `models/device_model.py`. `SRV-003-bacnet-adapter`, T-012.
`devices` se crea antes que `device_points_candidates` porque esta última
tiene una FK hacia la primera.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("protocol", sa.String(20), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column(
            "is_simulator",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "protocol IN ('bacnet', 'modbus', 'mqtt')", name="ck_devices_protocol"
        ),
        sa.UniqueConstraint(
            "protocol", "address", name="uq_devices_protocol_address"
        ),
    )

    op.create_table(
        "device_points_candidates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("object_type", sa.String(50), nullable=False),
        sa.Column("object_instance", sa.Integer(), nullable=False),
        sa.Column("object_name", sa.String(255), nullable=True),
        sa.Column("present_value", sa.Text(), nullable=True),
        sa.Column("units", sa.String(50), nullable=True),
        sa.Column(
            "discovered_at",
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
        sa.UniqueConstraint(
            "device_id",
            "object_type",
            "object_instance",
            name="uq_device_points_candidates_device_object",
        ),
    )


def downgrade() -> None:
    op.drop_table("device_points_candidates")
    op.drop_table("devices")
