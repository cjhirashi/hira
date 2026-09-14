# adapters/cache

`redis_adapter.py::RedisAdapter` — implementa `CachePort` contra Redis
(`redis.asyncio`, comando `PING`) — RF-002. Recibe `redis_url` +
`redis_password` por separado y los combina al construir el cliente
(`redis.from_url(url, password=...)`) — el Redis del compose exige password
(`--requirepass`), así que ninguno de los dos campos de `Settings` puede
faltar sin dejar la conexión real sin autenticar. Verificado en
`tests/test_cache_adapter_wiring.py` (mockeado, wiring de la password) y en
`tests/integration/test_adapters.py` contra el contenedor `redis` real del
compose (`@pytest.mark.integration`).
