# core/ports

Interfaces abstractas (`typing.Protocol`) del patrón Hexagonal (`E-ADR-002`).
`services/` importa únicamente de aquí — nunca de `adapters/` directamente.

Puertos del Walking Skeleton:

- `database_port.py` — `DatabasePort.ping()` (*liveness*, RF-002).
- `cache_port.py` — `CachePort.ping()` (*liveness*, RF-002).

Sin métodos de negocio (`save`, `get`, `set_ttl`, etc.) todavía — ningún caso de
uso de este sprint los necesita (Art. 10, no anticipar). Se amplían cuando
`LicenseStoragePort`/`CrashReportPort` (Constitución Art. 2) tengan un caso de
uso real, en H1/H2.

Implementaciones concretas: `adapters/db/postgres_adapter.py::PostgresAdapter`,
`adapters/cache/redis_adapter.py::RedisAdapter` (T-018/T-019).
