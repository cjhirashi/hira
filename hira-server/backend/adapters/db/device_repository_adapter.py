"""`PostgreSQLDeviceRepository` — implementación real de
`DeviceRepositoryPort` (`SRV-003-bacnet-adapter`, T-015/T-016, `plan.md §2`/§3).

Motor async propio (`AsyncEngine`, `asyncpg`), mismo estilo que
`user_repository_adapter.py`: SQLAlchemy Core (`select`/`insert`), sin ORM
declarativo. Opera contra `models/device_model.py::devices_table`/
`device_points_candidates_table`.

`upsert_device`/`upsert_candidate` usan `INSERT ... ON CONFLICT DO UPDATE`
nativo de PostgreSQL (`plan.md §2`, Anti-Abstraction) sobre los `UNIQUE`
`(protocol, address)`/`(device_id, object_type, object_instance)` — un
segundo escaneo actualiza la fila existente (refresca `last_seen_at`/
`present_value`+`updated_at`), nunca duplica (RF-002).

Solo `adapters/*` puede importar `sqlalchemy`/`asyncpg` — `services/` sigue
importando únicamente `core/ports/device_repository_port.py` (`SRV-ADR-017`).
"""
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from core.ports.device_repository_port import DeviceCandidateRecord, DeviceRecord
from models.device_model import device_points_candidates_table, devices_table


class PostgreSQLDeviceRepository:
    """Implementa `DeviceRepositoryPort` contra un PostgreSQL real."""

    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            database_url, pool_pre_ping=True
        )

    @staticmethod
    def _row_to_device(row) -> DeviceRecord:
        return DeviceRecord(
            id=str(row.id),
            name=row.name,
            protocol=row.protocol,
            address=row.address,
            is_simulator=row.is_simulator,
            last_seen_at=row.last_seen_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _row_to_candidate(row) -> DeviceCandidateRecord:
        return DeviceCandidateRecord(
            id=str(row.id),
            device_id=str(row.device_id),
            object_type=row.object_type,
            object_instance=row.object_instance,
            object_name=row.object_name,
            present_value=row.present_value,
            units=row.units,
            discovered_at=row.discovered_at,
            updated_at=row.updated_at,
        )

    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        """Crea o actualiza (único por `(protocol, address)`), refrescando
        `last_seen_at` (RF-002)."""
        insert_stmt = pg_insert(devices_table).values(
            name=name,
            protocol=protocol,
            address=address,
            is_simulator=is_simulator,
            last_seen_at=func.now(),
        )
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["protocol", "address"],
            set_={
                "name": insert_stmt.excluded.name,
                "is_simulator": insert_stmt.excluded.is_simulator,
                "last_seen_at": insert_stmt.excluded.last_seen_at,
                "updated_at": func.now(),
            },
        ).returning(devices_table)

        async with self._engine.begin() as connection:
            result = await connection.execute(stmt)
            row = result.first()
        return self._row_to_device(row)

    async def list_devices(self) -> list[DeviceRecord]:
        """RF-004."""
        async with self._engine.connect() as connection:
            result = await connection.execute(select(devices_table))
            rows = result.all()
        return [self._row_to_device(row) for row in rows]

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        """RF-009 — `None` si no existe."""
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(devices_table).where(devices_table.c.id == device_id)
            )
            row = result.first()
        return self._row_to_device(row) if row is not None else None

    async def upsert_candidate(
        self,
        *,
        device_id: str,
        object_type: str,
        object_instance: int,
        object_name: str | None,
        present_value: str | None,
        units: str | None,
    ) -> DeviceCandidateRecord:
        """Único por `(device_id, object_type, object_instance)` — actualiza
        `present_value`/`updated_at` si ya existía, no duplica (RF-002)."""
        insert_stmt = pg_insert(device_points_candidates_table).values(
            device_id=device_id,
            object_type=object_type,
            object_instance=object_instance,
            object_name=object_name,
            present_value=present_value,
            units=units,
        )
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["device_id", "object_type", "object_instance"],
            set_={
                "object_name": insert_stmt.excluded.object_name,
                "present_value": insert_stmt.excluded.present_value,
                "units": insert_stmt.excluded.units,
                "updated_at": func.now(),
            },
        ).returning(device_points_candidates_table)

        async with self._engine.begin() as connection:
            result = await connection.execute(stmt)
            row = result.first()
        return self._row_to_candidate(row)

    async def list_candidates_for_device(
        self, device_id: str
    ) -> list[DeviceCandidateRecord]:
        """RF-005."""
        async with self._engine.connect() as connection:
            result = await connection.execute(
                select(device_points_candidates_table).where(
                    device_points_candidates_table.c.device_id == device_id
                )
            )
            rows = result.all()
        return [self._row_to_candidate(row) for row in rows]

    async def close(self) -> None:
        """Libera el pool de conexiones — usado en tests de integración y
        shutdown (mismo criterio que `PostgreSQLUserRepository.close()`)."""
        await self._engine.dispose()
