# tests

Pruebas unitarias y de coordinación (sin contenedores — corren con `pytest` local).
Un test por cada `AC-*`/`RF-*` que la tarea de `tasks.md` deja verificable; cada test
cita la ancla que cubre.

- `test_health_policy.py` — `aggregate_status`, 8 combinaciones de 3 booleanos (RF-002).
- `test_config.py` — `Settings`, variable de entorno faltante nombrada en el error
  (RF-003).
- `test_logger.py` — log JSON con `timestamp, level, service, module, trace_id,
  message`, cero `print()` (RF-004).
- `test_health_service.py` — `get_health` con dobles (`Protocol` fakes) de
  `DatabasePort`/`CachePort`/`NotificationPort`: timeout de 2s no cuelga la respuesta
  (RF-007/RNF-002), agrega `trace_id` (RF-005), usa `aggregate_status` (RF-002).
- `test_correlation_id.py` — `CorrelationIdMiddleware`: propaga `X-Trace-ID` o genera
  `uuid4()`, lo fija en el `ContextVar` de `core/logger.py` (RF-005).
- `test_main_lifespan.py` — `main.py::lifespan`: `ValidationError` de `Settings()` →
  log JSON `level: error` nombrando el/los campo(s) faltante(s) + `sys.exit(1)`, sin
  arranque parcial (RF-003).

### `SRV-002-auth-rbac` (núcleo puro, T-001..T-008 — sin mocks, sin puertos)

- `test_password_hashing.py` — `hash_password`/`verify_password` con bcrypt real
  (factor 12); hash nunca igual al texto plano; salt aleatorio por llamada;
  verificación cruzada falla con password incorrecto (RF-012).
- `test_jwt_tokens.py` — `create_access_token`/`create_refresh_token`/
  `decode_token` con JWT real (`PyJWT`); TTL exacto (15min/7días);
  `TokenExpiredError` con `exp` fijado manualmente en el pasado (sin
  `time.sleep`); `TokenInvalidError` con firma alterada, `type` incorrecto o
  token malformado (RF-001, RF-003, RF-011, RF-013).
- `test_rbac_policy.py` — matriz completa de `can_write`/`is_admin` por rol; las
  4 combinaciones de `can_access_project` (`scope`/coincidencia de
  `project_id`) (RF-004, RF-005, RF-008, RF-009).
- `test_errors.py` — `ProblemDetailError` expone `status`/`type_`/`title`/
  `detail`; `schemas/errors.py::ProblemDetail` serializa el sobre RFC 9457
  exacto.

### `SRV-002-auth-rbac` (coordinación, T-010..T-015 — dobles de `UserRepositoryPort`/`CachePort`)

- `test_cache_port_contract.py` — contrato ampliado de `CachePort` (`get/set/
  incr/expire/delete`, `@runtime_checkable`).
- `test_auth_service.py` — `login/refresh/logout`: fuerza bruta (6º intento →
  429, resetea en éxito), mismo 401 genérico en los 3 casos de RF-002, refresh
  con token revocado → 401, logout idempotente (RF-001, RF-002, RF-010, RF-011,
  RF-013, RF-014).
- `test_rbac_service.py` — `resolve_permissions` *cache-first* (cache-hit no
  toca `UserRepositoryPort`; cache-miss consulta y repuebla); `update_user_role`
  invalida el cache (RF-006, RF-007).

### `SRV-002-auth-rbac` (adaptador de entrada, T-017..T-022)

- `test_auth_router.py` — `POST /auth/login|refresh|logout` contra la app real
  de `main.py` (`TestClient`), con `UserRepositoryPort`/`CachePort` in-memory vía
  `app.dependency_overrides` (router) + `monkeypatch` sobre `core.middleware`
  (para que `AuthenticationMiddleware` resuelva contra las mismas instancias en
  `/auth/logout`); shape exacto de `openapi.yaml`, 200/401/429 con el sobre RFC
  9457 correcto (RF-001, RF-002, RF-010, RF-011, RF-013, RF-014).
- `test_authentication_middleware.py` — `AuthenticationMiddleware` sobre una app
  de prueba: token ausente/inválido/expirado → 401 RFC 9457 exacto; rutas del
  *allowlist* (`/health`, `/auth/login`) no exigen token; `/auth/logout` (fuera
  del *allowlist*) sí lo exige; `request.state.user` disponible en una ruta
  protegida tras un token válido (RF-003, RF-007).
- `test_rbac_dependencies.py` — `require_role`/`require_project_scope` sobre una
  app **sintética** (sin tocar routers de producción): Visor bloqueado en
  escritura, Operador bloqueado en recurso Admin, `scope=project` cruzando de
  proyecto, `scope=global` sin re-login (RF-004, RF-005, RF-008, RF-009).

`asyncio_mode = auto` (`pytest.ini`) — los tests `async def` no necesitan el marcador
`@pytest.mark.asyncio` explícito, aunque algunos lo declaran por claridad.

`tests/integration/` — pruebas contra contenedores reales (`@pytest.mark.integration`),
fuera del alcance de este batch.
