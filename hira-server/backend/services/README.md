# services

Lógica de negocio / casos de uso. Importa solo de `core/ports/`, `core/security/*`
y `core/errors.py` — nunca de `adapters/` directamente ni de FastAPI (regla de oro
`SRV-ADR-017`).

- `health_service.py::aggregate_status(results: dict[str, bool]) -> Literal["ok",
  "degraded"]` — núcleo puro, sin I/O (RF-002). "ok" si los tres servicios están `ok`,
  "degraded" si al menos uno falla.
- `health_service.py::get_health(database, cache, notification)` — coordinación
  (RF-002, RF-005, RF-007): llama a los 3 puertos en paralelo, cada uno con
  `asyncio.wait_for(timeout=2)` (RNF-002); excepción o timeout → ese servicio queda
  `error` sin colgar la respuesta; agrega el `trace_id` vigente del `ContextVar` de
  `core/logger.py`. Recibe los puertos por parámetro — no instancia adaptadores
  (`adapters/factory.py` los inyecta, pendiente de T-019/T-020).
- `auth_service.py::login/refresh/logout` (`SRV-002-auth-rbac`, RF-001, RF-002,
  RF-010, RF-011, RF-013, RF-014) — `login` aplica fuerza bruta (`login_attempts:
  {email}:{ip}`, `MAX_LOGIN_ATTEMPTS=5`/`LOGIN_ATTEMPTS_WINDOW_SECONDS=900`), 401
  genérico idéntico en los 3 casos de fallo (evita enumeración), emite `TokenPair`
  (`core/security/jwt.py`) y guarda `refresh:{jti}` en cache (TTL 7 días); `refresh`
  reemite el access con `rol`/`scope`/`project_id` **vigentes** vía
  `rbac_service.resolve_permissions`; `logout` revoca el refresh, idempotente ante
  token ya inválido/expirado/revocado. Reciben `secret_key: str` explícito (misma
  convención que `core/security/jwt.py`, `services/` no lee `Settings()`).
- `rbac_service.py::resolve_permissions/invalidate_permissions_cache/
  update_user_role` (`SRV-002-auth-rbac`, RF-006, RF-007) — `resolve_permissions`
  es *cache-first* (`rbac:{user_id}`, TTL 7 días): *cache-hit* no consulta
  `UserRepositoryPort`; *cache-miss* consulta y repuebla; usuario no encontrado o
  desactivado → `ProblemDetailError(401, "token-invalid")`. `update_user_role`
  actualiza el rol y **luego** invalida el cache, en ese orden fijo (RF-006). Sin
  router HTTP en este sprint (`spec.md §2`) — invocable por un futuro endpoint/CLI
  de administración.
- `device_scan_service.py::scan_bacnet(transport, device_repo)`
  (`SRV-003-bacnet-adapter`, RF-001, RF-002, RF-006, RF-007, RF-008, RNF-001) —
  Who-Is (`WHOIS_TIMEOUT_SECONDS=3.0`, RF-001); sin ningún I-Am, retorna `[]`
  sin tocar el repositorio (RF-008). Por cada I-Am, lee objetos en paralelo
  (`asyncio.gather`, RNF-001) con `READ_TIMEOUT_SECONDS=2.0` (RF-010); un
  dispositivo que no responde a la lectura (`BacnetReadTimeoutError`) se loguea
  y no aborta el resto del escaneo (RF-006) — queda persistido con
  `last_seen_at` actualizado, sin candidatos nuevos en ese escaneo. Persiste
  dispositivo+candidatos vía `DeviceRepositoryPort` (RF-002). Nunca escribe en
  una tabla de puntos operables (RF-007, `SRV-ADR-012`) — no importa ningún
  `PointsRepositoryPort`, que no existe todavía.

Servicios de `SRV-006-simuladores`:

- `simulator_registry_service.py::SimulatorRegistryService` + `RunningSimulator`
  + `get_simulator_registry()` — estado en memoria del proceso de los
  simuladores actualmente en ejecución. **No es un puerto** (mismo criterio
  que `LocalPermissionsCache` en `rbac_service.py`, `SRV-002`): no habla con
  ningún sistema externo, es un `dict[device_id, RunningSimulator]` interno.
  Un reinicio del proceso lo vacía sin código adicional (RF-013, por omisión
  de diseño — `main.py` no lo persiste ni restaura). Vive en su propio
  archivo (no inline en `simulator_service.py`) porque las 3 funciones de
  arranque más `stop_simulator`/`GET /simulators` convergen sobre el **mismo**
  registro. `RunningSimulator` es un `@dataclass(frozen=True)` con `device_id`,
  `protocol`, `address`, `token`, `started_at` (RF-010). `SimulatorRegistryService`
  expone `self.lock` (`asyncio.Lock`) **público** — `simulator_service.py`
  lo adquiere para envolver la sección crítica completa "verificar conflicto
  → arrancar → registrar", no solo la mutación del `dict` (un único lock
  global serializa las llamadas de gestión de simuladores, `plan.md §2`
  Registro de decisiones). `get_simulator_registry()` — singleton de módulo,
  inyectado vía `Depends()` en `routers/simulators.py`.

- `simulator_service.py::start_bacnet_simulator / start_modbus_simulator /
  start_mqtt_simulator / stop_simulator` — coordinación de arranque/detención
  de simuladores (RF-001/RF-002/RF-003, RF-006, RF-007, RF-009, RF-012,
  RF-014, RF-015, RNF-001). Solo importa de `core/ports/`,
  `core/bacnet_address.py`, `core/modbus_address.py`, `core/errors.py`,
  `core/logger.py` y `services/simulator_registry_service.py` — nunca de
  `adapters/` ni de FastAPI. Recibe los puertos por parámetro.
  Cada `start_*_simulator` adquiere `registry.lock` para la sección crítica:
  (1) `_check_conflict` (RF-006: 409 si dirección real o ya corriendo, antes
  de arrancar nada); (2) `transport.start(...)` (arranca el proceso real);
  (3) `try/except` para limpiar defensivamente con `transport.stop(token)` si
  la persistencia falla tras el arranque; (4) `device_repo.upsert_device(...,
  is_simulator=True)` + candidatos; (5) `registry.register(entry)`. BACnet
  usa `format_simulator_device_address(device_instance)`; Modbus usa
  `format_modbus_address(host, port, unit_id)` (`SRV-004`, reutilizado tal
  cual). MQTT añade RF-015 (`interval_seconds<=0` → 400 antes del lock) y
  RF-014 (captura `MqttInvalidPublishError` de `transport.start()` → 400 sin
  `upsert_device`). `stop_simulator` adquiere `registry.lock`, busca la
  entrada y despacha al puerto correcto según `entry.protocol`, luego llama
  `registry.unregister(device_id)` — sin tocar `devices`/candidatos (RF-009,
  RF-011, por omisión de diseño: no importa ningún método de borrado).
