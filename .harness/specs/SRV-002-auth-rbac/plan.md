---
id: PLAN-SRV-002
tipo: plan
feature: SRV-002-auth-rbac
estado: approved
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-13 }
actualizado: 2026-09-13
---

# PLAN-SRV-002 · Autenticación y RBAC (MVP — 3 roles fijos)

> El *cómo*. Traduce cada `RF-001..RF-014`/`RNF-001` de `spec.md` al patrón **Hexagonal**
> (Constitución Art. 1–2, `SRV-ADR-017`), construyendo sobre `SRV-001-walking-skeleton`
> (`verified`): reutiliza `core/config.py::Settings` (ya tiene `secret_key`),
> `core/logger.py`, `core/middleware.py` (se **amplía**, no se reemplaza),
> `core/ports/{database_port.py,cache_port.py}` (sin tocar su contrato de *liveness*),
> `adapters/factory.py` (se amplía con un cuarto puerto).

## 0. Gates de simplicidad
- [x] **Simplicity** — un puerto nuevo (`UserRepositoryPort`), una tabla (`users`),
      3 endpoints (`/auth/login|refresh|logout`), sin tabla de permisos dinámica (RBAC
      dinámico es v0.2, `SRV-ADR-005`). Sin `HIRA_DEPLOY_MODE`. TTLs de JWT fijos por
      constante (15 min / 7 días) — no configurables por env en este MVP.
- [x] **Anti-Abstraction** — `UserRepositoryAdapter` usa SQLAlchemy Core (`Table`/
      `select`/`update`), igual estilo que `postgresql_adapter.py::ping()`; sin ORM
      declarativo para una sola tabla. Sin CRUD de usuarios (fuera de alcance,
      `spec.md §2`) — `update_role` es la única mutación, sin router propio (§2, nota
      de alcance). Una excepción declarada y justificada en §7 (dependencia de FastAPI
      en vez de middleware puro para autorización por proyecto — ver justificación).
- [x] **Integration-First** — `hira-server/docs/openapi.yaml` se amplía **antes** que
      `routers/auth.py` (paso 8 de §6); `core/ports/user_repository_port.py` (`Protocol`)
      se define antes que `adapters/db/user_repository_adapter.py`.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/auth_service.py` y `services/rbac_service.py` solo importan de `core/ports/` (`UserRepositoryPort`, `CachePort`); `adapters/factory.py` inyecta `PostgreSQLUserRepository`. Ningún router ni middleware instancia un adaptador directamente. |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo (`core/security/*`) sin mocks con bcrypt/JWT reales; coordinación con dobles de `UserRepositoryPort`/`CachePort`; adaptador contra Postgres real; middleware RBAC contra una app sintética (mismo patrón que `test_correlation_id.py` de `SRV-001`); seguridad end-to-end con contenedores reales (bcrypt, JWT, fuerza bruta, forma RFC 9457). |
| Art. 4 (persistencia) | `UserRepositoryPort` es el `StoragePort` de dominio para `users` — distinto de `DatabasePort` (que sigue siendo *liveness*-only, sin tocar su contrato, `SRV-001`). Primera tabla de negocio del producto → primera migración Alembic (§3). |
| Art. 5 (seguridad) | bcrypt factor 12 (RF-012); `SECRET_KEY` desde `Settings` (ya existe, sin nuevo secreto); JWT HS256; nunca se loguea password ni token completo — el logger de auditoría (dentro de `services/auth_service.py`) solo registra `user_id`/`email`/resultado, nunca `password`/`password_hash`/el JWT emitido. |
| Art. 6 (contratos/errores) | `POST /auth/login|refresh|logout` sí usan el sobre RFC 9457 (decisión ya cerrada en `spec.md §3`: son endpoints de negocio, a diferencia de `/health`). Convención de `type` fijada en §4. |
| Art. 10 (regla de raíz) | No se introduce `HIRA_DEPLOY_MODE` ni ramas por perfil. `UserRepositoryPort` nuevo (no forzar los métodos de dominio dentro de `DatabasePort` genérico) es la corrección de raíz frente a la alternativa descartada (§ Registro de decisiones abajo). |
| Art. 11 (documentación) | §8 de este plan — 2 filas, cada una tarea `[doc]` en `tasks.md`. |

## Registro de decisiones de diseño (nuevas de este plan)
| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| `UserRepositoryPort` nuevo, no reutilizar `DatabasePort` | `DatabasePort.ping()` (`SRV-001`) es un contrato de *liveness* genérico, no un repositorio de dominio; forzar `get_by_email`/`update_role` ahí violaría su propósito y ataría cada futuro repositorio de dominio (points, devices, alarms) al mismo `Protocol` monolítico — contradice Art. 4 ("un `StoragePort` por backend") y la regla de raíz (Art. 10: la corrección va al puerto, no a un parche). | Añadir métodos de dominio a `DatabasePort` |
| `UserRepositoryAdapter` con SQLAlchemy Core (`Table`), no ORM declarativo | Consistente con el estilo ya usado en `postgresql_adapter.py` (Core + `text()`); una sola tabla en este sprint no justifica introducir `declarative_base()`/`Session` todavía (Anti-Abstraction) | Introducir ORM declarativo completo para una tabla |
| Autenticación como **middleware** (JWT + resolución de permisos vía Redis) + autorización fina (`require_role`/`require_project_scope`) como **`Depends()` de FastAPI** | Starlette resuelve `path params` (p. ej. `project_id`) **después** de que corre `BaseHTTPMiddleware.dispatch` — un middleware ASGI puro no puede leer `project_id` de la ruta todavía. La validación de JWT/resolución de rol-scope (agnóstica de ruta) sí es correcta como middleware cross-cutting (RF-003, RF-007); las decisiones que dependen del parámetro de la ruta concreta (RF-004/005/008/009) deben ser `Depends()` por router. Documentado como excepción en §7. | Un único middleware ASGI para todo (RBAC incluido) |
| `update_user_role` (RF-006) sin router HTTP propio en este sprint | `spec.md §2` excluye explícitamente "gestión de usuarios más allá del mínimo" — no hay `PATCH /users/{id}/role` en el contrato de esta feature. Se implementa y prueba como función de coordinación (`services/rbac_service.py`), invocable por un futuro endpoint de administración o un script, sin bloquear el cierre de esta feature | Añadir un endpoint `PATCH /users/{id}/role` fuera del alcance ya cerrado en Fase 1 |
| Sobre RFC 9457 con `type: https://hira.dev/errors/<slug>` | Constitución Art. 6 exige RFC 9457; el ecosistema no tenía convención de `type` todavía (primer sprint que lo usa, `SRV-001` optó por no usarlo). Se fija aquí un URI estable (no necesita resolver) para no reinventar el formato en cada feature futura | `type: "about:blank"` (RFC 9457 default, pierde valor de distinguir causas) |
| TTLs de JWT y umbral de fuerza bruta como constantes de código, no variables de entorno | `spec.md` los fija como valores concretos (15 min/7 días/5 intentos/15 min) — no hay necesidad de configurarlos por instalación en este MVP (regla de oro Art. 10: no anticipar) | Añadir `ACCESS_TOKEN_TTL_MINUTES` etc. a `Settings` |
| **(2026-09-13, resolución de RNF-001 — ver §10)** `CachePort` se amplía **de nuevo** con `publish(channel, message)`/`subscribe(channel) -> AsyncIterator[str]`, no un puerto nuevo (`RbacPubSubPort`/`CacheInvalidationPort`) | Mismo criterio ya aplicado a `get/set/incr/expire/delete` (T-010/T-011): el propósito de `CachePort` ("acceso a Redis") no cambia, solo crece su superficie — y a diferencia del caso `UserRepositoryPort` vs `DatabasePort` (donde el segundo era *liveness-only* y forzar ahí métodos de dominio violaba su propósito), aquí Pub/Sub **es** acceso a Redis, la misma tecnología, sin lógica de dominio de por medio. Además la Constitución (Art. 2, `adaptadores_salida` de `hira-server`) **ya lista "Redis Pub/Sub"** como capacidad anticipada — no es abstracción especulativa, es la capacidad prevista desde la Génesis que hasta ahora nadie había necesitado | Puerto nuevo dedicado a invalidación/pub-sub — fragmentaría el acceso a Redis en 2+ puertos sin una razón de dominio (viola Anti-Abstraction, `plan.md §0`) |
| **(2026-09-13)** Caché en memoria del proceso (`LocalPermissionsCache`) vive en `services/rbac_service.py`, no en un puerto/adaptador nuevo | Es una estructura de datos en proceso (`dict` + TTL), sin I/O — no es una "frontera de salida" (no habla con ningún sistema externo), por lo tanto no le corresponde un puerto (Art. 1: `services/` puede tener estado interno puro, lo que no puede hacer es importar `adapters/`) | Modelarla como si fuera un `CachePort` adicional ("`InProcessCachePort`") — confundiría "puerto = frontera con el exterior" con una simple optimización interna |
| **(2026-09-13)** `AuthenticationMiddleware` migra de `BaseHTTPMiddleware` a ASGI puro (`__call__(scope, receive, send)`), reemplazando la implementación de T-019/T-020 | Resuelve la Directiva de Pausa de RNF-001 (§10): el piso de latencia de `BaseHTTPMiddleware` (~20-40ms a 100 concurrentes) es inherente a la clase base, no a la lógica de negocio — un middleware ASGI puro construye y envía la respuesta 401 directamente vía `send()`, sin `call_next()`, preservando el motivo original de usar una clase con control total de la respuesta (evitar que una excepción se pierda en la `ExceptionMiddleware`) sin pagar el costo de `anyio.create_task_group()`/*memory stream* por request. Cambio de implementación interna, no de contrato — `tests/test_authentication_middleware.py` (T-019) debe seguir pasando sin relajar ninguna aserción | Mantener `BaseHTTPMiddleware` y optimizar solo `services/rbac_service.py` — no alcanza (§10: el piso ya existe con un middleware vacío) |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks
- **`core/security/passwords.py`** ← implementa **RF-012**: `hash_password(password: str) -> str` (bcrypt, `rounds=12`), `verify_password(password: str, password_hash: str) -> bool`. Nunca texto plano persistido.
- **`core/security/jwt.py`** ← implementa **RF-001, RF-003, RF-011, RF-013**: `create_access_token(user_id, rol, scope, project_id) -> str` (HS256, `exp` = 15 min), `create_refresh_token(user_id, jti) -> str` (HS256, `exp` = 7 días), `decode_token(token, expected_type) -> TokenClaims` — lanza `TokenExpiredError`/`TokenInvalidError` (definidas aquí, sin depender de FastAPI) si el JWT expiró, tiene firma inválida, o `type` no coincide con el esperado (`access`/`refresh`). Recibe `SECRET_KEY` como parámetro explícito (no lee `Settings()` internamente) — mantiene el módulo sin I/O.
- **`core/security/rbac_policy.py`** ← implementa **RF-004, RF-005, RF-008, RF-009** (decisión pura, sin I/O): `can_write(rol: str) -> bool` (Admin/Operador sí, Visor no), `is_admin(rol: str) -> bool`, `can_access_project(scope: str, user_project_id: str | None, requested_project_id: str) -> bool` (scope `global` → siempre `True`; scope `project` → solo si coincide `project_id`). Reglas hardcodeadas del MVP de 3 roles fijos — la tabla de permisos dinámica es v0.2 (`SRV-ADR-005`), no se anticipa aquí.
- **`core/errors.py`** — `ProblemDetailError(status, type_, title, detail)` (excepción) + registro de slugs de este dominio: `invalid-credentials` (401), `token-missing`/`token-invalid`/`token-expired`/`token-revoked` (401), `insufficient-role`/`project-scope-denied` (403), `rate-limited` (429). Sin I/O — es un catálogo + clase de excepción; lo consumen `services/`, `core/security/dependencies.py` y el middleware.

### Coordinación (casos de uso / fronteras de entrada)
- **`services/auth_service.py`**:
  - `login(email, password, ip, users_repo: UserRepositoryPort, cache: CachePort) -> TokenPair` ← **RF-001, RF-002, RF-014**: `is_locked_out(email, ip, cache)` (lee contador `login_attempts:{email}:{ip}`) → si excede 5/15min, `ProblemDetailError(429, "rate-limited")`; si no, busca `users_repo.get_by_email(email)`, verifica `password_hash` (`core/security/passwords.py`) y `activo`; **cualquier** fallo (no existe / password incorrecto / desactivado) → `ProblemDetailError(401, "invalid-credentials")` idéntico en los 3 casos (RF-002, evita enumeración) y además incrementa el contador de intentos fallidos; éxito → resetea el contador, emite `access`+`refresh` (`core/security/jwt.py`), guarda `refresh:{jti} = user_id` en Redis con TTL 7 días (`cache`).
  - `refresh(refresh_token, cache) -> str` (nuevo access) ← **RF-011, RF-013**: decodifica el refresh (`core/security/jwt.py`, `type="refresh"`) → JWT inválido/expirado → `ProblemDetailError(401, "token-invalid"/"token-expired")`; verifica `refresh:{jti}` existe en `cache` → si no, `ProblemDetailError(401, "token-revoked")`; emite nuevo access con el `rol`/`scope`/`project_id` **vigentes** (releídos vía `services/rbac_service.py::resolve_permissions`, no los del JWT viejo — para que un cambio de rol aplique también aquí).
  - `logout(refresh_token, cache) -> None` ← **RF-010**: decodifica el refresh, `DEL refresh:{jti}` en `cache` (idempotente si ya no existe).
  - Constantes: `MAX_LOGIN_ATTEMPTS = 5`, `LOGIN_ATTEMPTS_WINDOW_SECONDS = 900` (RF-014).
- **`services/rbac_service.py`** — **ampliado (2026-09-13) para resolver RNF-001, ver §10**:
  - `LocalPermissionsCache` ← clase nueva, **sin I/O** (no es un puerto — ver Registro de decisiones): envuelve un `dict[str, tuple[AuthenticatedUser, float]]` (valor + timestamp de expiración) con `LOCAL_CACHE_TTL_SECONDS = 30` (red de seguridad si el pub/sub falla — no es el mecanismo principal de invalidación, es el respaldo). Expone `get(user_id) -> AuthenticatedUser | None` (`None` si no existe o expiró), `set(user_id, user, ttl_seconds=LOCAL_CACHE_TTL_SECONDS)`, `invalidate(user_id)`. Se instancia un *singleton* de módulo (`_default_local_cache`) para el uso real en producción; todas las funciones de abajo aceptan `local_cache: LocalPermissionsCache = _default_local_cache` como parámetro **inyectable** — no para DI de puertos (no es una frontera externa), sino para que los tests puedan simular **2 procesos** con 2 instancias independientes de `LocalPermissionsCache` en el mismo test (§5).
  - `resolve_permissions(user_id, users_repo: UserRepositoryPort, cache: CachePort, local_cache: LocalPermissionsCache = _default_local_cache) -> AuthenticatedUser` ← **RF-006, RF-007, RNF-001**: 1) `local_cache.get(user_id)` → *hit* → retorna **sin ningún I/O** (ni Redis ni BD) — esta es la ruta caliente que resuelve RNF-001; 2) *miss* local → `GET rbac:{user_id}` en `cache` (Redis, como antes) → *hit* → deserializa, repuebla `local_cache.set(user_id, ...)`, retorna (sin tocar `users_repo`, sigue cumpliendo RF-007 literal: "no consulta BD salvo *cache-miss*" — *cache* aquí es el nivel Redis, el nivel local es una capa adicional, no sustituye la semántica ya verificada); 3) *miss* en ambos niveles → `users_repo.get_by_id(user_id)`, construye `AuthenticatedUser`, repuebla **ambos** niveles (`cache.set` TTL 7 días, `local_cache.set` TTL 30s), retorna. Usuario no encontrado o `activo=False` → `ProblemDetailError(401, "token-invalid")` (sin cachear en ningún nivel).
  - `invalidate_permissions_cache(user_id, cache: CachePort, local_cache: LocalPermissionsCache = _default_local_cache) -> None` ← **RF-006**: `DEL rbac:{user_id}` en `cache` (Redis, como antes) + `local_cache.invalidate(user_id)` (invalida **solo la instancia de este proceso** — ver `run_invalidation_subscriber` abajo para la propagación a otros procesos) + `cache.publish("rbac:invalidations", user_id)` (nuevo — dispara la propagación).
  - `update_user_role(user_id, new_role, users_repo: UserRepositoryPort, cache: CachePort, local_cache: LocalPermissionsCache = _default_local_cache) -> None` ← **RF-006**: `users_repo.update_role(user_id, new_role)` y **luego** `invalidate_permissions_cache(..., local_cache=local_cache)` (mismo orden fijado ya en `spec.md`: invalida antes de confirmar). **Matiz de semántica (nuevo, ver §10 y Registro de decisiones):** lo que ocurre "antes de confirmar la modificación" — invalidación de Redis + del `LocalPermissionsCache` **del proceso que ejecuta la llamada** — sigue siendo síncrono y atómico dentro de la misma función, sin cambios respecto al comportamiento ya verificado (T-014/T-015). Lo que es **nuevo y distinto**: si hay más de un proceso/réplica de backend corriendo, la caché en memoria de **esos otros procesos** converge por el mensaje pub/sub, típicamente en milisegundos pero **sin garantía atómica cruzada** — es propagación *best-effort*, con la TTL de 30s de `LocalPermissionsCache` como cota máxima de obsolescencia ante un mensaje perdido. Sin router HTTP en este sprint (ver Registro de decisiones); se prueba con dobles en `tests/test_rbac_service.py` y queda disponible para el futuro endpoint/CLI de gestión de usuarios.
  - `run_invalidation_subscriber(cache: CachePort, local_cache: LocalPermissionsCache = _default_local_cache) -> None` ← función nueva, coordinación pura (solo importa `core/ports/cache_port.py`, `SRV-ADR-017`): `async for user_id in cache.subscribe("rbac:invalidations"): local_cache.invalidate(user_id)` — bucle infinito, pensado para correr como tarea de fondo (`asyncio.create_task`) desde `main.py::lifespan` (ver abajo), uno por proceso backend. Debe salir limpio ante `asyncio.CancelledError` (no debe tragarse la cancelación) para que el `lifespan` pueda apagarlo en el *shutdown*.
- **`core/middleware.py`** (se amplía, no se reemplaza) — **`AuthenticationMiddleware`** ← implementa **RF-003, RF-007** — **migrado (2026-09-13) de `BaseHTTPMiddleware` a middleware ASGI puro para resolver RNF-001 (§10), reemplazando la implementación de T-019/T-020**:
  ```python
  class AuthenticationMiddleware:
      def __init__(self, app: ASGIApp) -> None:
          self.app = app

      async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
          if scope["type"] != "http":
              await self.app(scope, receive, send)
              return
          request = Request(scope, receive=receive)
          if request.url.path in PUBLIC_ALLOWLIST:
              await self.app(scope, receive, send)
              return
          # ... misma lógica de validación de token / resolve_permissions que hoy ...
          if <error>:
              response = _problem_response(...)  # JSONResponse, sin cambios
              await response(scope, receive, send)  # envía directo por send(), sin call_next()
              return
          request.state.user = authenticated_user  # persiste en scope["state"], visible río abajo
          await self.app(scope, receive, send)
  ```
  Para toda ruta que no esté en el *allowlist* público (`/health`, `/auth/login`, `/auth/refresh`, `/docs`, `/openapi.json`, `/redoc`), exige `Authorization: Bearer <token>`; ausente → `token-missing`; decodifica con `core/security/jwt.py` (`type="access"`) → inválido/expirado → `token-invalid`/`token-expired`; válido → `services/rbac_service.py::resolve_permissions(sub, ...)` (vía `adapters/factory.py`, mismo patrón que hoy) y fija `request.state.user: AuthenticatedUser`. **Cómo se envía un 401 sin `call_next()`:** `starlette.responses.Response`/`JSONResponse` ya implementa el protocolo ASGI (`async def __call__(self, scope, receive, send)` construye y emite los mensajes `http.response.start`/`http.response.body`); el middleware ASGI puro simplemente invoca `await response(scope, receive, send)` directamente — no hay `ExceptionMiddleware` de por medio porque nunca se lanza una excepción ni se llama a una app interna, se construye y envía la respuesta él mismo. `request.state.user` sigue funcionando igual porque el objeto `Request` que construye el middleware comparte el mismo `scope` que la app interna recibirá — `Request.state` lee/escribe `scope["state"]` (un `dict` mutable dentro de `scope`), así que fijarlo aquí es visible para cualquier `Request` construido más adelante en la cadena a partir del mismo `scope`. **Contrato observable sin cambios:** mismo *allowlist*, mismo `request.state.user`, mismo *shape* RFC 9457 en los 401 — `tests/test_authentication_middleware.py` (T-019, 12 casos) debe seguir pasando **sin relajar ninguna aserción**; solo su fixture interna (`monkeypatch.setattr(middleware_module, ...)`) podría necesitar ajustes menores si el nombre de algún atributo de instancia cambia. `/auth/logout` **sí** requiere este middleware; `/auth/refresh` y `/auth/login` están en el *allowlist*.
- **`core/security/dependencies.py`** — `require_role(*roles: str)` y `require_project_scope(project_id_param: str = "project_id")`, factories de `Depends()` que leen `request.state.user` (ya fijado por el middleware) y aplican `core/security/rbac_policy.py` ← implementan **RF-004, RF-005, RF-008, RF-009** a nivel de *cualquier* router futuro que las use. En este sprint, sin router de negocio real que proteger todavía (`spec.md §2`: solo backend/contrato de auth), se verifican con una app FastAPI sintética construida en el propio test (mismo patrón que `tests/test_correlation_id.py::_build_app()` de `SRV-001`) — no se crea un endpoint de producción especulativo solo para probarlas.
- **Exception handler** — `main.py` registra `app.add_exception_handler(ProblemDetailError, ...)` que serializa a `schemas/errors.py::ProblemDetail` (RFC 9457) con `media_type="application/problem+json"`.

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| PostgreSQL (tabla `users`) | Repositorio de dominio de usuarios (login, resolución de permisos, cambio de rol) | `adapters/db/user_repository_adapter.py::PostgreSQLUserRepository` implementa `UserRepositoryPort` — SQLAlchemy Core (`AsyncEngine` propio, `Table`/`select`/`update`), mismo estilo que `postgresql_adapter.py` |
| Redis | Refresh tokens revocables (`refresh:{jti}`), caché de permisos (`rbac:{user_id}`), contador de fuerza bruta (`login_attempts:{email}:{ip}`) | Reutiliza `CachePort`/`RedisAdapter` **ya existentes** (`SRV-001`) — sin puerto nuevo; solo se le exige a `RedisAdapter` soportar `get/set/setex/incr/expire/delete` genéricos (ver nota de ampliación abajo) |

> **Nota de ampliación de `CachePort`/`RedisAdapter`:** `SRV-001` solo definió `ping()`
> (*liveness*). Este plan **amplía** `CachePort` (mismo archivo, no uno nuevo) con los
> métodos genéricos de key-value que RF-006/007/010/011/013/014 necesitan: `get(key)`,
> `set(key, value, ttl_seconds=None)`, `incr(key)`, `expire(key, ttl_seconds)`,
> `delete(key)`. Es una ampliación de contrato (Art. 10: el puerto crece, no se
> parchea con un cliente Redis crudo importado en `services/`), no un puerto nuevo —
> el propósito de `CachePort` (acceso a Redis) no cambia, solo se completa su
> superficie mínima de *liveness-only* a *cache real*, que es exactamente para lo que
> se preveía (`SRV-ADR-003`, "Redis" en Art. 2 ya lo lista como cache/pub-sub futuro).
>
> **Segunda ampliación (2026-09-13, resolución de RNF-001 — §10):** `CachePort` crece
> **de nuevo**, en el mismo archivo, con `publish(channel: str, message: str) -> None`
> y `subscribe(channel: str) -> AsyncIterator[str]` — necesarios para que
> `services/rbac_service.py::update_user_role` (RF-006) propague la invalidación de su
> caché en memoria a otros procesos/réplicas del backend (`RedisAdapter` los
> implementa con `client.publish(...)`/`client.pubsub()` reales). Mismo criterio que
> la ampliación anterior — ver Registro de decisiones arriba para la justificación
> completa frente a la alternativa de un puerto nuevo.

### Adaptadores de entrada
- `routers/auth.py` — `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`
  (FastAPI); contrato = `hira-server/docs/openapi.yaml#/paths/~1auth~1login` (+
  `~1auth~1refresh`, `~1auth~1logout`). Inyecta `UserRepositoryPort`/`CachePort` vía
  `Depends(adapters.factory.*)` — nunca instancia un adaptador concreto (`SRV-ADR-017`).
- `AuthenticationMiddleware` — registrado en `main.py` después de
  `CorrelationIdMiddleware` (el `trace_id` debe existir antes, para que los logs de
  fallo de autenticación ya lo lleven).
- `main.py::lifespan` — **ampliado (2026-09-13, §10)**: arranca
  `services/rbac_service.py::run_invalidation_subscriber(get_cache_port())` como
  tarea de fondo (`asyncio.create_task`, guardada en una variable local del
  `lifespan`) **junto al `connect()` de `MosquittoAdapter` ya existente** — mismo
  punto del ciclo de vida, mismo patrón de "arranca infraestructura de fondo sin
  bloquear el resto del arranque". A diferencia de `connect()` (que retorna), la
  suscripción es un bucle infinito — por eso es una tarea (`asyncio.create_task`),
  no un `await` directo. En el *shutdown* (después del `yield`), el `lifespan`
  cancela la tarea (`task.cancel()`) y espera su terminación limpia (`await task`
  dentro de un `try/except asyncio.CancelledError`) — sin tareas huérfanas al
  apagar el proceso (relevante para que la suite de tests no deje *warnings* de
  tareas sin recoger).

### `adapters/factory.py` (se amplía)
- Nueva función `get_user_repository_port() -> UserRepositoryPort`: nace en el paso 9
  de §6 con un placeholder in-memory (mismo patrón que la Directiva de Pausa de
  `SRV-001` §7 — `routers/auth.py` necesita el punto de inyección desde que existe,
  `PostgreSQLUserRepository` real llega en el paso 12 sin cambiar la firma).

## 3. Modelo de datos
**Primera tabla de negocio del producto** — primera migración Alembic del repo.

### Tabla `users`
| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `UUID` | PK, default `uuid4()` (lado Python, sin extensión `pgcrypto`) |
| `email` | `VARCHAR(255)` | `UNIQUE NOT NULL` |
| `password_hash` | `TEXT` | `NOT NULL` (bcrypt, ~60 caracteres, `TEXT` por margen) |
| `rol` | `VARCHAR(20)` | `NOT NULL`, `CHECK (rol IN ('admin','operador','visor'))` |
| `scope` | `VARCHAR(10)` | `NOT NULL`, `CHECK (scope IN ('project','global'))` |
| `project_id` | `UUID` | `NULL` — sin FK todavía (tabla `projects` no existe aún); `CHECK ((scope = 'global' AND project_id IS NULL) OR (scope = 'project' AND project_id IS NOT NULL))` |
| `activo` | `BOOLEAN` | `NOT NULL DEFAULT true` |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`, actualizado por la app en `update_role` |

Índices: único ya cubierto por `email UNIQUE`; índice simple en `project_id` (consultas
futuras de usuarios por proyecto).

### Migraciones (Alembic — primer uso en el repo)
- `hira-server/backend/alembic.ini` + `hira-server/backend/alembic/env.py` (plantilla
  **async**, reutiliza `asyncpg` ya en `requirements.txt` — sin añadir un driver
  síncrono nuevo solo para migrar) + `hira-server/backend/alembic/versions/
  0001_create_users_table.py` (escrita a mano, no autogenerada — un solo `CREATE TABLE`
  no lo justifica).
- `target_metadata` = el `MetaData` de `models/user_model.py` (SQLAlchemy Core
  `Table`, no ORM declarativo — ver §2/Registro de decisiones).
- **No se ejecuta automáticamente** en el arranque del contenedor `backend` (evita
  condiciones de carrera si en el futuro hay más de una réplica). Se documenta como
  paso operativo explícito: `docker compose exec backend alembic upgrade head`, antes
  de levantar tráfico — se añade a `hira-server/README.md` (sección de operación, no
  es una fila de Art. 11 porque no vuelve obsoleto nada existente, solo añade un paso).
- `models/user_model.py` — `metadata = MetaData()`, `users_table = Table("users",
  metadata, ...)` con las columnas de la tabla de arriba.

### Seed (creación del primer usuario — `spec.md §2`: "creación por seed/migración")
- `hira-server/backend/scripts/seed_admin_user.py` — script standalone, idempotente
  (no falla si el email ya existe), lee `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` de
  variables de entorno (nuevas en `.env.example`, sin valores reales), hashea con
  `core/security/passwords.py::hash_password` antes de insertar — nunca password en
  claro en un artefacto versionado. Es el único mecanismo de creación de usuarios de
  este sprint (sin CRUD, `spec.md §2`).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-002-auth-rbac/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** es `hira-server/docs/openapi.yaml` (se **amplía**, no se reemplaza — sigue conteniendo `GET /health` intacto) | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` | `gate/check.sh` bloque 5 (Spectral lint, mismo warn conocido que `SRV-001` — sin bloquear, deuda de tooling ya aceptada) |

### Sobre de error — RFC 9457 (`Content-Type: application/problem+json`)
Convención de `type` formalizada en [`E-ADR-003`](../../../docs/decisions/ecosystem/E-ADR-003-convencion-rfc9457-type.md)
(2026-09-13, aprobada por Carlos en este Gate 2) — aplica a los 3 productos, no solo
a esta feature. Esquema común (`schemas/errors.py::ProblemDetail`, componente
`ProblemDetail` en `openapi.yaml`):
```yaml
type: string       # URI estable, no necesita resolver — https://hira.dev/errors/<slug>
title: string       # resumen legible, fijo por slug
status: integer     # duplica el código HTTP, exigido por RFC 9457
detail: string      # mensaje específico de la instancia (sin datos sensibles)
```

| Endpoint | HTTP | `type` (slug) | `title` | Cuándo |
|---|---|---|---|---|
| `POST /auth/login` | 401 | `invalid-credentials` | "Credenciales inválidas" | email no existe, password incorrecto, o usuario desactivado — **mismo** mensaje en los 3 casos (RF-002) |
| `POST /auth/login` | 429 | `rate-limited` | "Demasiados intentos" | 5º+ intento fallido en 15 min para la misma combinación email+IP (RF-014) |
| Cualquier ruta protegida | 401 | `token-missing` | "Falta el token de acceso" | sin header `Authorization` (RF-003) |
| Cualquier ruta protegida | 401 | `token-invalid` | "Token inválido" | firma inválida, malformado, o usuario desactivado/no encontrado (RF-003) |
| Cualquier ruta protegida | 401 | `token-expired` | "Token expirado" | `exp` del access token vencido (RF-003) |
| `POST /auth/refresh` | 401 | `token-revoked` | "Refresh token revocado" | `jti` no existe en Redis (RF-013) |
| Cualquier ruta protegida (futuro, vía `require_role`) | 403 | `insufficient-role` | "Rol insuficiente" | RF-004, RF-005 |
| Cualquier ruta protegida (futuro, vía `require_project_scope`) | 403 | `project-scope-denied` | "Proyecto fuera de alcance" | RF-008 |

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`core/security/passwords.py`) | `hash_password`/`verify_password` con bcrypt **real** (factor 12); hash nunca igual al texto plano; verificación cruzada falla con password incorrecto | unit puro (pytest, **sin mocks**) — RF-012 |
| Núcleo (`core/security/jwt.py`) | `create_access_token`/`create_refresh_token`/`decode_token` con JWT **real** (`PyJWT`); TTL correcto (15min/7días); `decode_token` lanza `TokenExpiredError` con un token ya vencido (`freezegun` o `exp` manual en el pasado); `TokenInvalidError` con firma alterada o `type` incorrecto | unit puro, **sin mocks** — RF-001, RF-003, RF-011, RF-013 |
| Núcleo (`core/security/rbac_policy.py`) | Matriz completa: `can_write` por cada rol; `can_access_project` para las 4 combinaciones de `scope`/coincidencia de `project_id` | unit puro, **sin mocks** — RF-004, RF-005, RF-008, RF-009 |
| Núcleo (`core/errors.py`) | `ProblemDetailError` expone `status`/`type_`/`title`/`detail` correctos por slug | unit puro |
| Coordinación (`services/auth_service.py`) | Fuerza bruta (6º intento → 429, contador resetea en éxito); mismo 401 genérico en los 3 casos de RF-002; refresh con token revocado → 401; logout idempotente | unit + dobles (`Protocol` fakes) de `UserRepositoryPort`/`CachePort` |
| Coordinación (`services/rbac_service.py`) | *Cache-hit* no llama a `UserRepositoryPort` (verificado con un doble que lanza si se invoca); *cache-miss* sí consulta y repuebla con el TTL correcto; `update_user_role` invalida el caché | unit + dobles |
| Coordinación (`services/rbac_service.py`, ampliado §10) | **Hit en memoria evita Redis:** con `LocalPermissionsCache` ya caliente, `resolve_permissions` no llama a `CachePort.get` (doble de `CachePort` que lanza si se invoca) ni a `UserRepositoryPort`. **Miss local + hit Redis:** repuebla el nivel local sin tocar `UserRepositoryPort`. **TTL local expira:** tras `LOCAL_CACHE_TTL_SECONDS`, vuelve a consultar Redis (usar reloj inyectable o `freezegun`, no `sleep` real). **Invalidación cruza de proceso:** simulado con **2 instancias** de `LocalPermissionsCache` (`local_cache_a`, `local_cache_b`) en el mismo test — representan 2 procesos backend — y un doble de `CachePort` cuyo `publish`/`subscribe` está respaldado por un `asyncio.Queue` en memoria (simula el canal Redis real sin un Redis real); `update_user_role(..., local_cache=local_cache_a)` invalida `local_cache_a` síncronamente y publica; una tarea `run_invalidation_subscriber(fake_cache, local_cache_b)` corriendo en el mismo test loop consume el mensaje y se verifica (`await asyncio.sleep(0)` o `asyncio.wait_for` con timeout corto) que `local_cache_b` quedó invalidado — sin necesidad de 2 procesos ni contenedores reales | unit + dobles — RF-006, RF-007, RNF-001 |
| Puertos (`CachePort`/`RedisAdapter`, ampliado §10) | Contrato ampliado expone `publish`/`subscribe`; con un Redis real (mismo patrón que T-011), un `publish` en un cliente es recibido por un `subscribe` en otro cliente del mismo canal | unit (dobles, contrato) + verificación manual contra Redis real (mismo patrón que T-011) |
| Adaptador de entrada (`main.py::lifespan`, ampliado §10) | El `lifespan` arranca la tarea de suscripción al entrar y la cancela limpio (`CancelledError` capturado, sin *warning* de tarea huérfana) al salir — verificado con un doble de `CachePort.subscribe` controlado por el test | unit, `TestClient` como *context manager* (mismo patrón que `tests/test_main_lifespan.py` ya usa para Mosquitto) |
| Middleware (`AuthenticationMiddleware`) | Token ausente/inválido/expirado → 401 con forma RFC 9457 exacta; ruta del *allowlist* no exige token; `request.state.user` disponible en la ruta protegida | unit, app FastAPI real de prueba + `TestClient` (mismo patrón que `test_correlation_id.py`) |
| Middleware (`AuthenticationMiddleware`, migración a ASGI puro, §10) | **Mismos 12 casos ya verificados en T-019** (`tests/test_authentication_middleware.py`) deben seguir pasando **sin relajar ninguna aserción** tras la migración — es la prueba de regresión de que el contrato observable no cambió (solo la implementación interna) | unit, `TestClient` (archivo existente, ejecutado de nuevo contra la nueva implementación) |
| Dependencias (`require_role`, `require_project_scope`) | Visor bloqueado en escritura (403); Operador bloqueado en recurso Admin (403); scope=project cruzando de proyecto (403); scope=global sin re-login (200) | unit, app FastAPI **sintética** construida en el test (sin tocar routers de producción) — RF-004, RF-005, RF-008, RF-009 |
| Adaptador (`PostgreSQLUserRepository`) | `get_by_email`/`get_by_id`/`update_role` contra Postgres **real** con la migración aplicada; `email` duplicado rechazado por `UNIQUE`; `CHECK` de `scope`/`project_id` rechaza combinaciones inválidas | integración — `docker compose up -d postgres` + `alembic upgrade head` + `pytest -m integration` |
| Router (`routers/auth.py`) | Contrato exacto de `openapi.yaml` (`TestClient`, con `UserRepositoryPort`/`CachePort` in-memory del `factory.py` placeholder) — 200/401/429 con el *shape* RFC 9457 correcto | unit + `TestClient`, sin contenedores |
| Seguridad end-to-end | Fuerza bruta real contra Redis real; bcrypt real de extremo a extremo (seed → login); revocación de refresh real (logout → refresh con ese token → 401); **re-medición real** de la latencia del middleware RBAC < 5ms con 100 requests concurrentes (RNF-001) con el diseño **completo** (caché en memoria + pub/sub + middleware ASGI puro) — **obligatorio medir de verdad, no asumir** que el rediseño alcanza el umbral: es el primer paso de implementación de esta pieza en Fase 4, exactamente porque una suposición sin medir fue la causa de la Directiva de Pausa original (§10). Si la medición real no da <5ms, se abre una **nueva** Directiva de Pausa (no se relaja el umbral ni se fuerza un `Pass`) | integración — contenedores reales del compose, evidencia de terminal pegada |

## 6. Secuenciación de archivos (tests antes que código)
1. `tests/test_password_hashing.py` (falla) → `core/security/passwords.py` — RF-012.
2. `tests/test_jwt_tokens.py` (falla) → `core/security/jwt.py` — RF-001, RF-003, RF-011, RF-013.
3. `tests/test_rbac_policy.py` (falla) → `core/security/rbac_policy.py` — RF-004, RF-005, RF-008, RF-009.
4. `tests/test_errors.py` (falla) → `core/errors.py` + `schemas/errors.py::ProblemDetail` — base para todo lo que sigue.
5. `core/ports/user_repository_port.py` (`UserRepositoryPort`, `UserRecord` — `Protocol`, sin test propio, igual que `database_port.py` en `SRV-001`).
6. `core/ports/cache_port.py` — **ampliar** (`get/set/incr/expire/delete`) + `adapters/cache/redis_adapter.py` — ampliar su implementación real; `tests/test_cache_port_contract.py` (dobles) antes del cambio.
7. `tests/test_auth_service.py` (dobles de `UserRepositoryPort`/`CachePort`, falla) → `services/auth_service.py::login/refresh/logout` — RF-001, RF-002, RF-010, RF-011, RF-013, RF-014.
8. `tests/test_rbac_service.py` (dobles, falla) → `services/rbac_service.py::resolve_permissions/invalidate_permissions_cache/update_user_role` — RF-006, RF-007.
9. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) — amplía con `/auth/login|refresh|logout`, sin tocar `/health`.
10. `tests/test_auth_router.py` (`TestClient`, falla) → `routers/auth.py` + `schemas/auth.py` + **`adapters/factory.py::get_user_repository_port()`** (nace aquí con placeholder in-memory — mismo patrón que la Directiva de Pausa de `SRV-001` §7: el router necesita el punto de inyección desde que existe) + registro en `main.py` (`include_router`, exception handler de `ProblemDetailError`) — RF-001, RF-002, RF-010, RF-011, RF-013, RF-014 vía HTTP con repo/caché in-memory.
11. `tests/test_authentication_middleware.py` (`TestClient` sobre una app de prueba con el middleware real, falla) → `AuthenticationMiddleware` en `core/middleware.py` + registro en `main.py` — RF-003, RF-007.
12. `tests/test_rbac_dependencies.py` (app sintética, falla) → `core/security/dependencies.py::require_role/require_project_scope` — RF-004, RF-005, RF-008, RF-009.
13. `models/user_model.py` (`Table` Core) + `alembic.ini`/`alembic/env.py`/`alembic/versions/0001_create_users_table.py` — soporta el modelo de datos de §3.
14. `tests/integration/test_user_repository_adapter.py` (falla, requiere Postgres real + migración aplicada) → `adapters/db/user_repository_adapter.py::PostgreSQLUserRepository` — reemplaza el **cuerpo** (no la firma) de `adapters/factory.py::get_user_repository_port()` — RF-001, RF-002, RF-006, RF-007, RF-012 (reales).
15. `backend/scripts/seed_admin_user.py` + `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` en `.env.example` — necesario para poder ejercer login end-to-end sin CRUD de usuarios.
16. `tests/integration/test_auth_security.py` (contenedores reales: Postgres+Redis) → fuerza bruta real (RF-014), revocación real (RF-010/013), bcrypt+JWT reales de punta a punta (login→acceso protegido→refresh→logout), forma RFC 9457 exacta.
17. **(2026-09-13, resolución de RNF-001 — §10)** `tests/test_cache_port_contract.py` — ampliar (falla) → `core/ports/cache_port.py` (**ampliar de nuevo**: `publish`/`subscribe`) + `adapters/cache/redis_adapter.py` (implementación real vía `client.publish`/`client.pubsub()`). Debe ir **antes** del paso 18 — `rbac_service.py` va a depender de estos métodos.
18. `tests/test_rbac_service.py` — ampliar (falla: hit en memoria evita Redis; miss local + hit Redis repuebla el local; invalidación cruzada entre 2 instancias de `LocalPermissionsCache` simulando 2 procesos, ver §5) → `services/rbac_service.py::LocalPermissionsCache` (nueva) + `resolve_permissions`/`invalidate_permissions_cache`/`update_user_role` (ampliados) + `run_invalidation_subscriber` (nueva) — RF-006, RF-007, RNF-001.
19. `tests/test_main_lifespan.py` — ampliar (falla) → `main.py::lifespan` arranca `run_invalidation_subscriber(get_cache_port())` como tarea de fondo (junto al `connect()` de Mosquitto) y la cancela limpio en el *shutdown* — RF-006.
20. Migrar `core/middleware.py::AuthenticationMiddleware` de `BaseHTTPMiddleware` a ASGI puro (`__init__(app)`, `async def __call__(scope, receive, send)`) — **reemplaza** la implementación de T-019/T-020, mismo contrato observable. `tests/test_authentication_middleware.py` (ya existente) se corre de nuevo **sin modificar sus aserciones** — es la prueba de regresión de esta migración — RF-003, RF-007, RNF-001.
21. `tests/integration/test_rbac_latency.py` — ampliar (sigue `xfail(strict=True)` por ahora): además de verificar 0 consultas a `UserRepositoryPort` tras el warm-up, verificar 0 consultas a `CachePort.get` durante la medición (el cache-hit ahora es 100 % en memoria, ni siquiera toca Redis) — RNF-001.
22. **Re-medición real de RNF-001** (100 requests concurrentes, Postgres+Redis reales) con el diseño completo del paso 17-20 — **primer paso de implementación de esta pieza, no un supuesto** (ver §5, nota de "obligatorio medir de verdad"). Si <5ms: quitar `xfail(strict=True)` de `tests/integration/test_rbac_latency.py` y pegar la evidencia de terminal real en `tasks.md`/`plan.md §10`. Si no: nueva Directiva de Pausa (`method.md §5`), no se relaja el umbral.
23. `hira-server/README.md` — añadir el paso operativo `alembic upgrade head` (no es Art. 11, ver nota de §3).
24. Tareas `[doc]` de §8 — pueden ejecutarse en paralelo desde el paso 1; la que cierra `VUL-SRV-004` a 🟢 depende del resultado del paso 22, no antes.

> `.harness/gate/services.txt` ya declara `hira-server/backend:python` (`SRV-001`) —
> sin cambios necesarios, la suite nueva se integra en la misma suite de `pytest`.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| Autorización fina (`require_role`/`require_project_scope`) como `Depends()` de FastAPI en vez de vivir enteramente dentro del middleware ASGI | Restricción real de Starlette: los `path params` no están disponibles todavía cuando corre `BaseHTTPMiddleware.dispatch` (se resuelven en el enrutamiento, después de los middlewares). No es una capa especulativa: es la única forma correcta de implementar RF-008/009 (dependen de `project_id` de la ruta) sin duplicar el parseo de rutas a mano dentro del middleware. |
| `CachePort` se amplía con métodos genéricos (`get/set/incr/expire/delete`) en vez de crear un `RbacCachePort`/`AuthCachePort` separado | El propósito del puerto (acceso a Redis) no cambia — solo pasa de *liveness-only* a *cache real*, que ya era su rol previsto (`SRV-ADR-003`). Introducir un puerto nuevo solo para no tocar el archivo existente sería abstracción especulativa y fragmentaría el acceso a Redis en 2+ puertos sin razón de dominio. |
| `update_user_role` sin router HTTP en este sprint (queda "sin llamador" en producción hasta el futuro endpoint/CLI de gestión de usuarios) | `spec.md §2` ya cerró explícitamente "sin CRUD de usuarios más allá del mínimo" en Fase 1 — añadir un endpoint ahora sería expandir un alcance ya decidido y aprobado por el usuario. Se prueba con dobles para dejar RF-006 verificable sin violar esa decisión (ver Registro de decisiones). |
| **(2026-09-13, §10)** `CachePort` se amplía **de nuevo** con `publish`/`subscribe` en vez de un puerto nuevo dedicado a invalidación | Ver Registro de decisiones (arriba) y Nota de ampliación de §2 — mismo criterio ya usado, y Redis Pub/Sub ya está anticipado en Constitución Art. 2. |
| **(2026-09-13, §10)** `LocalPermissionsCache` lleva su propia TTL de seguridad (30s) **además de** la invalidación por pub/sub, en vez de confiar solo en el mensaje | El pub/sub es *best-effort* (§10, matiz de RF-006): un mensaje puede perderse (reinicio de Redis, red). La TTL acota el peor caso de obsolescencia a 30s sin necesidad de una cola persistente ni reintentos de entrega — no se anticipa más mecanismo de fiabilidad que ese (Art. 10: no anticipar); si en producción real 30s resulta insuficiente o excesivo, es un ajuste de constante, no un rediseño. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/modules/auth-rbac-seguridad.md` | Línea "Superusuario es el único que puede modificar roles y permisos" — **choca** con la decisión ya cerrada en `spec.md §6`/§2 (2026-09-13): en el modelo de 3 roles fijos no existe un concepto de "superusuario" separado de Admin; Admin ya cubre esa responsabilidad. Implementado en código real por este plan (`services/rbac_service.py::update_user_role`, invocable solo por Admin) | `[doc]` corregir: reemplazar "Superusuario" por "Admin" en esa línea; no tocar el resto de la sección (JWT/TTL/caché Redis ya coinciden con este plan) ni la referencia legacy a `backup-y-portabilidad.md` (fuera de alcance — deuda ya registrada en `.harness/memory/state.md`, backlog de higiene de `docs/<producto>/spec/` separado de `ADR-004`) |
| `docs/hira-server/spec/validation/vulnerabilities.md` | `VUL-SRV-004` (RBAC con query a BD en cada request) pasa de 🟡 En Proceso a 🟢 Resuelto una vez RF-006/RF-007/RNF-001 estén verificados con evidencia real (latencia <5ms, cache-hit sin tocar BD) | `[doc]` actualizar estado a 🟢 Resuelto — tarea de **cierre** (Fase 4, no antes), cita las tareas/tests de este plan como evidencia, añade fila en "Historial de Resoluciones". **`VUL-SRV-003` no se toca** — el rate limiting genérico de Nginx sigue fuera de alcance de esta feature (`spec.md §6`: esta feature solo añade el límite específico de `/auth/login`, extensión ya registrada, no resolución del vulnerability genérico) |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es el contrato de
producto de esta frontera, ya cubierto en §4 (se amplía, no se reemplaza).

`docs/hira-server/spec/validation/acceptance-criteria.md` (`AC-SRV-02.3`/`2.4`) **no**
se toca: esos criterios referencian recursos de negocio (puntos, Configurador) que no
existen todavía — se verifican de punta a punta cuando esas features lleguen. Este
plan deja el mecanismo de RBAC genérico verificado (§5), no esos criterios específicos
completos; no hay nada que quede obsoleto en ese documento por este plan.

## 9. Implementación por requisito

### Implementación de RF-001
- `core/security/jwt.py::create_access_token/create_refresh_token`.
- `services/auth_service.py::login`.
- `routers/auth.py::POST /auth/login`, `schemas/auth.py::TokenResponse`.
- `hira-server/docs/openapi.yaml#/paths/~1auth~1login`.
- Tests: `tests/test_jwt_tokens.py`, `tests/test_auth_service.py`, `tests/test_auth_router.py`, `tests/integration/test_auth_security.py`.
- `covers`: `hira-server/backend/core/security/jwt.py`, `hira-server/backend/services/auth_service.py`, `hira-server/backend/routers/auth.py`.

### Implementación de RF-002
- `services/auth_service.py::login` (rama de fallo unificada) + `core/errors.py::invalid-credentials`.
- Tests: `tests/test_auth_service.py` (3 causas → mismo 401), `tests/test_auth_router.py`, `tests/integration/test_auth_security.py`.

### Implementación de RF-003
- `core/middleware.py::AuthenticationMiddleware` — **(2026-09-13, §10)** migrado
  de `BaseHTTPMiddleware` a ASGI puro (`__call__(scope, receive, send)`), mismo
  contrato observable, resuelve la Causa raíz #1 de RNF-001.
- `core/security/jwt.py::decode_token` (rama `access`).
- Tests: `tests/test_authentication_middleware.py` (mismo archivo, mismas
  aserciones — regresión de la migración).

### Implementación de RF-004
- `core/security/rbac_policy.py::can_write`.
- `core/security/dependencies.py::require_role`.
- Tests: `tests/test_rbac_policy.py`, `tests/test_rbac_dependencies.py`.

### Implementación de RF-005
- `core/security/dependencies.py::require_role` (recurso reservado a Admin).
- Tests: `tests/test_rbac_dependencies.py`.

### Implementación de RF-006
- `services/rbac_service.py::update_user_role/invalidate_permissions_cache`.
- `core/ports/user_repository_port.py::UserRepositoryPort.update_role`.
- `adapters/db/user_repository_adapter.py::PostgreSQLUserRepository.update_role`.
- **(2026-09-13, §10)** `services/rbac_service.py::LocalPermissionsCache`,
  `run_invalidation_subscriber` — invalidación del caché en memoria del proceso
  que ejecuta la llamada (síncrona, antes de retornar, sin cambio de contrato) +
  propagación *best-effort* sub-segundo a otros procesos/réplicas vía
  `cache.publish("rbac:invalidations", user_id)` (ver matiz de semántica en §2 y
  §10 — **recomendado** añadir una nota aclaratoria en `spec.md §4 RF-006`,
  pendiente de confirmación de Carlos por tocar un documento de Fase 1 ya
  aprobado).
- `core/ports/cache_port.py` (ampliado: `publish`/`subscribe`) +
  `adapters/cache/redis_adapter.py` (real).
- `main.py::lifespan` — arranca/cancela `run_invalidation_subscriber`.
- Tests: `tests/test_rbac_service.py` (ampliado), `tests/test_cache_port_contract.py`
  (ampliado), `tests/test_main_lifespan.py` (ampliado),
  `tests/integration/test_user_repository_adapter.py`.
- Doc: fila de cierre en `docs/hira-server/spec/validation/vulnerabilities.md` (`VUL-SRV-004`).

### Implementación de RF-007
- `services/rbac_service.py::resolve_permissions` (cache-first).
- `core/ports/cache_port.py` (ampliado: `get/set`).
- **(2026-09-13, §10)** `services/rbac_service.py::LocalPermissionsCache` — nivel
  adicional consultado **antes** que Redis, sin I/O en *hit* (resuelve RNF-001).
- Tests: `tests/test_rbac_service.py` (dobles que fallan si se consulta
  `CachePort.get`/`UserRepositoryPort` en un *hit* de `LocalPermissionsCache`).
- Doc: misma fila de cierre `VUL-SRV-004`.

### Implementación de RF-008
- `core/security/rbac_policy.py::can_access_project`.
- `core/security/dependencies.py::require_project_scope`.
- Tests: `tests/test_rbac_policy.py`, `tests/test_rbac_dependencies.py`.

### Implementación de RF-009
- `core/security/rbac_policy.py::can_access_project` (rama `scope=global`).
- `core/security/dependencies.py::require_project_scope`.
- Tests: `tests/test_rbac_dependencies.py`.

### Implementación de RF-010
- `services/auth_service.py::logout`.
- `routers/auth.py::POST /auth/logout`.
- `hira-server/docs/openapi.yaml#/paths/~1auth~1logout`.
- Tests: `tests/test_auth_service.py`, `tests/test_auth_router.py`, `tests/integration/test_auth_security.py`.

### Implementación de RF-011
- `services/auth_service.py::refresh`.
- `routers/auth.py::POST /auth/refresh`.
- `hira-server/docs/openapi.yaml#/paths/~1auth~1refresh`.
- Tests: `tests/test_auth_service.py`, `tests/test_auth_router.py`.

### Implementación de RF-012
- `core/security/passwords.py::hash_password/verify_password`.
- `backend/scripts/seed_admin_user.py` (único punto de creación de usuarios de este sprint).
- Tests: `tests/test_password_hashing.py`, `tests/integration/test_auth_security.py`.

### Implementación de RF-013
- `services/auth_service.py::refresh` (rama revocado/expirado).
- `core/errors.py::token-revoked/token-expired`.
- Tests: `tests/test_auth_service.py`, `tests/integration/test_auth_security.py`.

### Implementación de RF-014
- `services/auth_service.py::login` (contador de intentos, `MAX_LOGIN_ATTEMPTS`/`LOGIN_ATTEMPTS_WINDOW_SECONDS`).
- `core/ports/cache_port.py` (ampliado: `incr/expire`).
- Tests: `tests/test_auth_service.py`, `tests/integration/test_auth_security.py`.

### Implementación de RNF-001
> **Estado (2026-09-13): Directiva de Pausa resuelta en el papel — pendiente de
> re-medición real. Ver §10 para el detalle completo (histórico + solución
> aprobada).**
- `core/middleware.py::AuthenticationMiddleware` — migrado a ASGI puro (§2, §10):
  elimina el piso de latencia de `BaseHTTPMiddleware` (~20-40ms a 100 concurrentes).
- `services/rbac_service.py::LocalPermissionsCache` + `resolve_permissions`
  ampliado (cache-first **en memoria**, sin ningún I/O en *hit* — ni Redis ni BD)
  + `invalidate_permissions_cache`/`update_user_role` ampliados +
  `run_invalidation_subscriber` (nuevo).
- `core/ports/cache_port.py` (ampliado: `publish`/`subscribe`) +
  `adapters/cache/redis_adapter.py` (real).
- `main.py::lifespan` — arranca/cancela la tarea de suscripción.
- Medición: `tests/integration/test_rbac_latency.py` (100 requests concurrentes,
  cache-hit puro con 0 consultas a `UserRepositoryPort` **y** 0 a `CachePort.get`)
  — **re-ejecutar contra el diseño completo de arriba y pegar evidencia de
  terminal real antes de quitar el `xfail(strict=True)`** (paso 22 de §6, primer
  paso de implementación de esta pieza en Fase 4 — no se asume el resultado).

## 10. RNF-001 — Directiva de Pausa (histórico) y solución aprobada (2026-09-13)

**Estado actual: Directiva de Pausa RESUELTA por decisión de Carlos (2026-09-13,
mismo día) — diseño aprobado, documentado en §2/§5/§6/§9 de este plan y en
`tasks.md` (T-032..T-040). No se marca `RNF-001` como `Pass` todavía: la
resolución está aprobada **en el papel**; falta la re-medición real (paso 22 de
§6, T-040) antes de quitar el `xfail(strict=True)` de
`tests/integration/test_rbac_latency.py` y cerrar `VUL-SRV-004`. Esta sección
conserva el historial completo de qué se midió y por qué (no se borra), y añade
al final la causa raíz #2 (confirmada en una ronda de revisión posterior) y el
diseño de la solución de raíz para ambas causas.**

### Qué se midió y cómo
Método exacto (documentado también en el docstring del test): dos apps
FastAPI/Starlette con un único `GET /bench` que no toca Postgres/Redis; la
única diferencia es si registran `AuthenticationMiddleware` o no. Se disparan
100 requests **concurrentes** (`asyncio.gather`) contra cada una — primero vía
`httpx.AsyncClient(transport=ASGITransport(...))`, y luego, para descartar que
`httpx` fuera la causa, con una llamada ASGI directa (`await app(scope,
receive, send)`, sin ninguna librería HTTP de por medio). Ambos métodos dan el
mismo patrón. Se repitió con `starlette.applications.Starlette` puro (sin
FastAPI) para descartar que fuera un costo de la capa de *dependency
injection* de FastAPI.

### Evidencia (terminal real, 2026-09-13)
Con un `AuthenticationMiddleware`-equivalente **completamente vacío** (`class
NoopMiddleware(BaseHTTPMiddleware): async def dispatch(self, request,
call_next): return await call_next(request)` — sin JWT, sin Redis, sin
`resolve_permissions`), llamada ASGI directa, FastAPI:

```
n=   1 avg=   0.374ms max=   0.374ms
n=   5 avg=   1.135ms max=   1.226ms
n=  10 avg=   2.195ms max=   2.385ms
n=  25 avg=   8.634ms max=   9.755ms
n=  50 avg=   9.763ms max=  10.711ms
n= 100 avg=  26.388ms max=  28.718ms
n= 200 avg=  39.836ms max=  43.432ms
```

Sin el middleware (mismo harness, misma ruta): `n=100 avg=0.070ms`. Con
`starlette.applications.Starlette` puro (sin FastAPI) a n=100: `avg≈14-22ms`
con el mismo `NoopMiddleware`, `avg≈0.02ms` sin él. El `AuthenticationMiddleware`
real (con JWT+Redis reales, cache-hit puro verificado con un espía que cuenta
0 consultas a `UserRepositoryPort` durante la medición) mide `~54ms` de
overhead sobre el mismo `GET /bench` a 100 concurrentes — consistente con el
piso ya impuesto por la clase base antes de sumarle ninguna lógica propia.

### Causa raíz
El overhead es de `starlette.middleware.base.BaseHTTPMiddleware` en sí mismo
(`anyio.create_task_group()` + *memory object stream* por request para poder
interceptar la respuesta antes de que salga) — **no** de
`core/security/jwt.py::decode_token` ni de `services/rbac_service.py::
resolve_permissions`/Redis (probado aislado, sin ninguna de las dos). Escala
**superlineal** con la concurrencia (n=10 ≈ 2ms, n=25 ≈ 8.6ms ya sobre el
umbral, n=100 ≈ 26ms solo de la clase base) — un problema de rendimiento
documentado de esa clase en el ecosistema Starlette/FastAPI, reproducido aquí
de forma directa y aislada (3 métodos de medición distintos, mismo patrón).

### Por qué es una asunción inviable de `plan.md` (no un bug de código)
`plan.md §2` fija `AuthenticationMiddleware(BaseHTTPMiddleware)` por una razón
funcional real, ya documentada ahí y en `core/middleware.py`: un
`BaseHTTPMiddleware` puede devolver un `JSONResponse` (401) directamente desde
`dispatch()` sin depender de `app.add_exception_handler`, porque las
excepciones lanzadas dentro de `call_next()` no llegan limpias a la
`ExceptionMiddleware` de Starlette. Esa elección de clase base, **tal como
está**, no puede cumplir RNF-001 (<5ms agregados, medido con 100 concurrentes,
`spec.md §7`) bajo ningún ajuste de `services/`/Redis — el techo lo impone la
clase base antes de que la lógica de negocio del middleware corra siquiera una
línea.

### Solución de raíz recomendada (para decisión de Carlos, no aplicada)
Migrar `AuthenticationMiddleware` de `BaseHTTPMiddleware` a **middleware ASGI
puro** (`class AuthenticationMiddleware: def __init__(self, app): ...; async
def __call__(self, scope, receive, send): ...`). Un middleware ASGI puro
controla el ciclo de vida completo de la respuesta él mismo (puede construir y
enviar un `JSONResponse` de 401 directamente vía `send()`, sin pasar por
`call_next()` ni por la `ExceptionMiddleware`) — **resuelve las dos
restricciones a la vez**: (1) el problema original que motivó usar
`BaseHTTPMiddleware` (propagación de excepciones) deja de aplicar, porque ya
no hay un `call_next()` intermedio; (2) el costo de `anyio.create_task_group()`
+ *memory stream* por request desaparece (confirmado: la llamada ASGI directa
sin middleware mide ~0.02-0.4ms a 100 concurrentes, prácticamente sin *floor*).
Es un cambio de implementación interna, no de contrato — `request.state.user`,
`PUBLIC_ALLOWLIST`, y el *shape* RFC 9457 de los 401 se mantienen idénticos;
`tests/test_authentication_middleware.py` debería seguir verificando el mismo
comportamiento observable, aunque su fixture (`app.add_middleware`) y el mock
interno de Starlette pueden requerir ajustes menores.

**Alternativas descartadas (peores que la de arriba):**
| Alternativa | Por qué se descarta |
|---|---|
| Relajar el umbral de RNF-001 (p. ej. a 30-60ms) o medir con menos de 100 concurrentes | No resuelve el riesgo real de producción bajo carga concurrente (varios dashboards/usuarios simultáneos) — solo esconde la métrica; contradice Art. 10 (solución de raíz, no parche) |
| Optimizar `services/rbac_service.py`/Redis | No aplica **por sí sola** — el overhead ya existe con un middleware vacío, sin ninguna llamada a Redis/JWT de por medio (medido y aislado). Ver Causa raíz #2 abajo: sí es **necesaria como parte** de la solución completa (junto con la migración del middleware), no como sustituto de ella |
| Quitar `AuthenticationMiddleware` del *request path* global y mover la autenticación a `Depends()` por router | Cambia el contrato de RF-003 (`plan.md §2`: "toda ruta fuera del allowlist" exige el middleware) — expansión de alcance mayor que la opción recomendada, mismo riesgo de excepciones no capturadas que ya se documentó al elegir `BaseHTTPMiddleware` originalmente |

### Causa raíz #2 (confirmada en una ronda de revisión posterior, mismo 2026-09-13) — round-trip a Redis
Además del piso de `BaseHTTPMiddleware` (Causa raíz #1, arriba), una **segunda
causa aditiva** fue confirmada de forma independiente por dos rondas de
revisor, con mediciones reproducidas 3 veces por métodos distintos: el
round-trip real a Redis por request (`resolve_permissions` en *cache-hit*
todavía hace un `GET rbac:{user_id}` real) cuesta **~27-30ms** bajo 100
concurrentes dentro del stack de despacho de FastAPI/Starlette — este costo
**persiste incluso sin ningún middleware** (medido con una llamada directa a
Redis desde el handler, sin `AuthenticationMiddleware` de por medio); es
inherente a hacer I/O de red real bajo esa concurrencia en ese stack, no un
defecto de `RedisAdapter`. Es aditivo a la Causa raíz #1: `BaseHTTPMiddleware`
(~20-36ms) + Redis por request (~27-30ms) ≈ el `~54ms` medido con el
`AuthenticationMiddleware` real de punta a punta. **Ninguna de las dos causas
por sí sola explica el total ni se resuelve optimizando solo la otra** — de
ahí que la solución de raíz deba atacar **ambas a la vez** (ver subsección
siguiente).

### Solución de raíz aprobada (Carlos, 2026-09-13) — ataca ambas causas
1. **Causa raíz #1 (piso de `BaseHTTPMiddleware`):** migrar
   `AuthenticationMiddleware` a middleware ASGI puro — diseño exacto en `§2`.
2. **Causa raíz #2 (round-trip a Redis por request):** caché en memoria del
   proceso (`LocalPermissionsCache`) delante de Redis en `resolve_permissions`,
   con invalidación por pub/sub de Redis para mantener coherencia entre
   procesos/réplicas cuando `update_user_role` cambia un rol — diseño exacto en
   `§2` (`services/rbac_service.py`) y ampliación de `CachePort` (`§2`, Nota de
   ampliación, y Registro de decisiones al inicio del plan).

**Ambas son necesarias juntas** — ya verificado con evidencia: con solo el
caché en memoria (sin migrar el middleware), `AuthenticationMiddleware` seguiría
constando ~20-36ms de la clase base sola (Causa raíz #1 sigue intacta), muy por
encima del umbral de 5ms. Con solo la migración del middleware (sin el caché en
memoria), cada request en *cache-hit* seguiría pagando ~27-30ms de round-trip a
Redis (Causa raíz #2 sigue intacta). Ninguna de las dos por separado alcanza
RNF-001 — la combinación de ambas sí tiene el potencial de hacerlo, **pero eso
se confirma midiendo de verdad (T-040), no se asume** (§5, §6 paso 22).

### Impacto en tareas (aprobado 2026-09-13 por Carlos — ver `tasks.md`)
- T-028 queda **fusionada/superada por T-040** (re-medición real con el diseño
  completo) — no se vuelve a ejecutar como tarea separada; su nota en
  `tasks.md` se actualiza para señalar esta resolución y no se marca `[x]`
  hasta que T-040 mida <5ms real.
- RF-003/RF-007 no cambian de estado (`Pass`, ya verificadas funcionalmente
  con dobles y con Postgres/Redis reales, T-024/T-025/T-027) — el hallazgo
  sigue siendo de **rendimiento** (RNF-001), no de corrección funcional; la
  migración del middleware y la ampliación de `rbac_service.py` deben mantener
  ese `Pass` intacto (regresión verificada por los mismos tests, §5/§6).
- Tareas nuevas **aprobadas y numeradas** (`tasks.md`, no reabren T-001..T-031):
  `T-032`..`T-040` — ampliación de `CachePort`/`RedisAdapter` (pub/sub),
  `LocalPermissionsCache` + invalidación cruzada en `rbac_service.py`,
  suscriptor en `main.py::lifespan`, migración del middleware a ASGI puro, y la
  re-medición real de RNF-001 (T-040, condición de cierre).
- `docs/hira-server/spec/validation/vulnerabilities.md::VUL-SRV-004` (T-031)
  **sigue sin cerrarse** a 🟢 — su condición cambia de "T-028 verificado" a
  "T-040 verificado" (mismo criterio: no evidencia real, no cierre).
- **Pendiente de confirmación explícita de Carlos** (no autoaprobado por este
  plan): si `spec.md §4 RF-006` necesita una nota aclaratoria sobre la
  propagación *best-effort* sub-segundo entre procesos (ver matiz de semántica
  en `§2`, bullet de `update_user_role`) — es un cambio a un documento de Fase 1
  ya aprobado (Gate 1), fuera de lo que este plan (Fase 2) puede decidir por su
  cuenta.
