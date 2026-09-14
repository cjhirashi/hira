"""`RedisAdapter` — implementación real de `CachePort` (RF-002, T-018/T-019).

Usa `redis.asyncio` (cliente async oficial de `redis-py`). `ping()` ejecuta el
comando `PING`; el timeout de 2s (RNF-002) lo aplica quien llama
(`services/health_service.py::_ping_with_timeout`, `asyncio.wait_for`) — este
adaptador no impone uno propio.

**Corrección post-revisión (RF-002, `.env.example`/`docker-compose.yml`):**
el Redis del compose exige password (`command: redis-server --requirepass
${REDIS_PASSWORD}`), pero `REDIS_URL` (`redis://redis:6379/0`) no la lleva
embebida — son 2 variables separadas a propósito (`REDIS_PASSWORD` también
la consume `docker-compose.yml` directamente, fuera del proceso Python, para
armar el `command`/`healthcheck` del servicio `redis`; embeberla en la URL
del `.env` no funcionaría de todos modos, porque `env_file:` de Docker
Compose no interpola `${VAR}` dentro de otra variable del mismo archivo).
Por eso `RedisAdapter` recibe **ambos** campos explícitamente y los combina
al construir el cliente — sin esto, el cliente se conectaba sin credenciales
y cada `PING` fallaba con `AuthenticationError`, reportando `redis: error`
en `/health` aunque Redis estuviera sano (falso negativo, viola RF-002).

Sin métodos de negocio (`get`/`set`/`incr`/`expire`/`delete`) todavía —
ningún caso de uso de este sprint los necesita (Constitución Art. 10, no
anticipar). Se amplían cuando exista un caso de uso real que los consuma
(H1/H2: rate-limiting de `/api/licenses/validate`).

Solo `adapters/*` puede importar `redis` — `services/` sigue importando
únicamente `core/ports/cache_port.py` (`E-ADR-002`).
"""
import redis.asyncio as redis


class RedisAdapter:
    """Implementa `CachePort` contra un Redis real."""

    def __init__(self, redis_url: str, redis_password: str) -> None:
        self._client: redis.Redis = redis.from_url(redis_url, password=redis_password)

    async def ping(self) -> bool:
        """RF-002 — comando `PING` real contra Redis."""
        return bool(await self._client.ping())

    async def close(self) -> None:
        """Cierra la conexión — usado en tests de integración y shutdown."""
        await self._client.aclose()
