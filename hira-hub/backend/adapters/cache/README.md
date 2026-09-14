# adapters/cache

Implementará `CachePort` contra Redis (`redis_adapter.py`, `redis.asyncio`,
comando `PING`) — `tasks.md` T-018/T-019, RF-002. Vacío en este batch
(T-001..T-012); se verificará con `tests/integration/test_adapters.py` contra
el contenedor `redis` real del compose.
