# adapters/cache

Implementa `CachePort` contra Redis (`redis_adapter.py`, `redis.asyncio`):

- `ping()` — comando `PING` (`SRV-001`, `tasks.md` T-019/T-020, RF-002). Verificado
  con `tests/integration/test_adapters.py` contra el contenedor `redis` real del
  compose.
- `get`/`set`/`incr`/`expire`/`delete` — cache real (`SRV-002-auth-rbac`, T-010/T-011,
  `plan.md §2`): refresh tokens revocables (`refresh:{jti}`), caché de permisos
  (`rbac:{user_id}`), contador de fuerza bruta (`login_attempts:{email}:{ip}`).
  Verificado manualmente contra un contenedor Redis real (`docker run redis:7-alpine`,
  limpiado tras la verificación) — evidencia en `tasks.md` T-011.
