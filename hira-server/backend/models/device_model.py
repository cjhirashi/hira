"""`devices_table`/`device_points_candidates_table` — SQLAlchemy Core (`Table`,
no ORM declarativo), segunda y tercera tabla de negocio del producto
(`SRV-003-bacnet-adapter`, `plan.md §3`, T-011).

Mismo estilo que `models/user_model.py` (Core, sin `declarative_base()`/
`Session` — 2 tablas no lo justifica, Anti-Abstraction `plan.md §0`). Ambas
`Table` se registran contra `models/base.py::metadata` (compartida con
`users_table`) para que `alembic/env.py::target_metadata` las vea todas.

`adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository`
(T-015/T-016) es el único módulo de `services`/`adapters` que debería
referenciar estas `Table` en operaciones `select`/`insert`/`update`
(`services/` sigue importando solo `core/ports/device_repository_port.py`,
`SRV-ADR-017`).
"""
import uuid

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID

from models.base import metadata

devices_table = Table(
    "devices",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("name", String(255), nullable=False),
    Column("protocol", String(20), nullable=False),
    Column("address", String(255), nullable=False),
    Column("is_simulator", Boolean, nullable=False, server_default="false"),
    Column("last_seen_at", TIMESTAMP(timezone=True), nullable=True),
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
    CheckConstraint(
        "protocol IN ('bacnet', 'modbus', 'mqtt')", name="ck_devices_protocol"
    ),
    UniqueConstraint("protocol", "address", name="uq_devices_protocol_address"),
)

device_points_candidates_table = Table(
    "device_points_candidates",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column(
        "device_id",
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("object_type", String(50), nullable=False),
    Column("object_instance", Integer, nullable=False),
    Column("object_name", String(255), nullable=True),
    Column("present_value", Text, nullable=True),
    Column("units", String(50), nullable=True),
    Column(
        "discovered_at",
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
    UniqueConstraint(
        "device_id",
        "object_type",
        "object_instance",
        name="uq_device_points_candidates_device_object",
    ),
)
