---
id: TASKS-SRV-002
tipo: tasks
feature: SRV-002-auth-rbac
estado: draft
actualizado: 2026-09-13
---

# TASKS-SRV-002 · Autenticación y RBAC (MVP — 3 roles fijos)

## Reglas
- Cada tarea: ≤ 30 min, un solo propósito, `(cubre RF-NNN)`, zona del patrón (o `[doc]`).
- Orden por dependencias. **Test antes que código.**
- Cada fila de `plan.md §8` (Impacto en documentación) → una tarea `[doc]`.
- Implementador: `hira-auth` (`.claude/agents/hira-auth.md`) — refrescar sus anclas
  contra `SRV-ADR-005`/`SRV-ADR-020` y este plan antes de invocarlo (nota de
  `memory/state.md` sobre los 16 especialistas de dominio).

## Tareas

### Núcleo — passwords
- [ ] T-001 — Test `test_password_hashing.py`: `hash_password`/`verify_password`
      con bcrypt real (factor 12); hash nunca igual al texto plano; verificación
      cruzada falla con password incorrecto (debe fallar) (cubre RF-012)
      [zona: test-núcleo]
- [ ] T-002 — Implementar `core/security/passwords.py` (cubre RF-012)
      [zona: núcleo]

### Núcleo — JWT
- [ ] T-003 — Test `test_jwt_tokens.py`: `create_access_token`/`create_refresh_token`/
      `decode_token` con JWT real; TTL correcto (15min/7días); `TokenExpiredError`
      con token vencido; `TokenInvalidError` con firma alterada o `type` incorrecto
      (debe fallar) (cubre RF-001, RF-003, RF-011, RF-013) [zona: test-núcleo]
- [ ] T-004 — Implementar `core/security/jwt.py` (cubre RF-001, RF-003, RF-011,
      RF-013) [zona: núcleo]

### Núcleo — política RBAC
- [ ] T-005 — Test `test_rbac_policy.py`: matriz completa de `can_write` por rol;
      `can_access_project` para las 4 combinaciones de `scope`/coincidencia de
      `project_id` (debe fallar) (cubre RF-004, RF-005, RF-008, RF-009)
      [zona: test-núcleo]
- [ ] T-006 — Implementar `core/security/rbac_policy.py` (cubre RF-004, RF-005,
      RF-008, RF-009) [zona: núcleo]

### Núcleo — catálogo de errores (RFC 9457, `E-ADR-003`)
- [ ] T-007 — Test `test_errors.py`: `ProblemDetailError` expone `status`/`type_`/
      `title`/`detail` correctos por slug (debe fallar) [zona: test-núcleo]
- [ ] T-008 — Implementar `core/errors.py` + `schemas/errors.py::ProblemDetail`
      [zona: núcleo]

### Puertos
- [ ] T-009 — Implementar `core/ports/user_repository_port.py` (`UserRepositoryPort`,
      `UserRecord` — `Protocol`, sin test propio, igual que `database_port.py` de
      `SRV-001`) [zona: puertos]
- [ ] T-010 — Test `test_cache_port_contract.py` (dobles): contrato ampliado de
      `CachePort` (`get/set/incr/expire/delete`) (debe fallar) [zona: test-puertos]
- [ ] T-011 — Ampliar `core/ports/cache_port.py` (`get/set/incr/expire/delete`) +
      `adapters/cache/redis_adapter.py` (implementación real) — sin tocar el
      contrato de `ping()` ya usado por `SRV-001` [zona: puertos/adaptadores]

### Coordinación — auth_service
- [ ] T-012 — Test `test_auth_service.py` con dobles de `UserRepositoryPort`/
      `CachePort`: fuerza bruta (6º intento → 429, resetea en éxito); mismo 401
      genérico en los 3 casos de RF-002; refresh con token revocado → 401; logout
      idempotente (debe fallar) (cubre RF-001, RF-002, RF-010, RF-011, RF-013,
      RF-014) [zona: test-coordinación]
- [ ] T-013 — Implementar `services/auth_service.py::login/refresh/logout` (cubre
      RF-001, RF-002, RF-010, RF-011, RF-013, RF-014) [zona: coordinación]

### Coordinación — rbac_service
- [ ] T-014 — Test `test_rbac_service.py` con dobles: *cache-hit* no llama a
      `UserRepositoryPort`; *cache-miss* sí consulta y repuebla con TTL correcto;
      `update_user_role` invalida el caché (debe fallar) (cubre RF-006, RF-007)
      [zona: test-coordinación]
- [ ] T-015 — Implementar `services/rbac_service.py::resolve_permissions/
      invalidate_permissions_cache/update_user_role` (cubre RF-006, RF-007)
      [zona: coordinación]

### Contrato — Contract-First
- [ ] T-016 — Ampliar `hira-server/docs/openapi.yaml` con `POST /auth/login|
      refresh|logout` y el componente `ProblemDetail` — antes del router, sin
      tocar `GET /health` (cubre RF-001, RF-002, RF-010, RF-011, RF-013, RF-014)
      [zona: contrato]

### Adaptador de entrada — router
- [ ] T-017 — Test `test_auth_router.py` (`TestClient`): contrato exacto de
      `openapi.yaml`, shape RFC 9457 en 401/429 (debe fallar) (cubre RF-001,
      RF-002, RF-010, RF-011, RF-013, RF-014) [zona: test-adaptador-entrada]
- [ ] T-018 — Implementar `routers/auth.py` + `schemas/auth.py` +
      `adapters/factory.py::get_user_repository_port()` (nace aquí con
      placeholder in-memory — mismo patrón que la Directiva de Pausa de `SRV-001`:
      el router necesita el punto de inyección desde que existe) + registro en
      `main.py` (`include_router`, exception handler de `ProblemDetailError`)
      (cubre RF-001, RF-002, RF-010, RF-011, RF-013, RF-014)
      [zona: adaptador-entrada]

### Middleware — autenticación
- [ ] T-019 — Test `test_authentication_middleware.py` (`TestClient` sobre app de
      prueba): token ausente/inválido/expirado → 401 con forma RFC 9457 exacta;
      ruta del *allowlist* no exige token; `request.state.user` disponible en ruta
      protegida (debe fallar) (cubre RF-003, RF-007) [zona: test-coordinación]
- [ ] T-020 — Implementar `AuthenticationMiddleware` en `core/middleware.py` +
      registro en `main.py` (después de `CorrelationIdMiddleware`) (cubre RF-003,
      RF-007) [zona: coordinación]

### Dependencias — autorización fina
- [ ] T-021 — Test `test_rbac_dependencies.py` (app sintética, sin tocar routers
      de producción): Visor bloqueado en escritura (403); Operador bloqueado en
      recurso Admin (403); `scope=project` cruzando de proyecto (403);
      `scope=global` sin re-login (200) (debe fallar) (cubre RF-004, RF-005,
      RF-008, RF-009) [zona: test-adaptador-entrada]
- [ ] T-022 — Implementar `core/security/dependencies.py::require_role/
      require_project_scope` (cubre RF-004, RF-005, RF-008, RF-009)
      [zona: adaptador-entrada]

### Modelo de datos — primera tabla de negocio
- [ ] T-023 — `models/user_model.py` (`Table` Core) + `alembic.ini`/`alembic/
      env.py` (async) + `alembic/versions/0001_create_users_table.py` (a mano) —
      tabla `users` de `plan.md §3` [zona: modelo-de-datos]

### Adaptador concreto — integración contra Postgres real
- [ ] T-024 — Test `tests/integration/test_user_repository_adapter.py` (requiere
      Postgres real + `alembic upgrade head`): `get_by_email`/`get_by_id`/
      `update_role`; `email` duplicado rechazado por `UNIQUE`; `CHECK` de
      `scope`/`project_id` rechaza combinaciones inválidas (debe fallar) (cubre
      RF-001, RF-002, RF-006, RF-007, RF-012) [zona: test-adaptadores]
- [ ] T-025 — Implementar `adapters/db/user_repository_adapter.py::
      PostgreSQLUserRepository` — reemplaza el **cuerpo** (no la firma) de
      `adapters/factory.py::get_user_repository_port()` (cubre RF-001, RF-002,
      RF-006, RF-007, RF-012) [zona: adaptadores]

### Seed — único mecanismo de creación de usuarios de este sprint
- [ ] T-026 — `backend/scripts/seed_admin_user.py` (idempotente) +
      `SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` en `.env.example` (sin valores
      reales) (cubre RF-012) [zona: infra]

### Seguridad end-to-end — contenedores reales
- [ ] T-027 — Test `tests/integration/test_auth_security.py` (Postgres+Redis
      reales, migración aplicada, seed corrido): fuerza bruta real (RF-014),
      revocación real (logout → refresh con ese token → 401, RF-010/RF-013),
      bcrypt+JWT reales de punta a punta (login→acceso protegido→refresh→logout),
      forma RFC 9457 exacta en cada 401/429 (debe fallar antes de T-025, pasa
      después) (cubre RF-001, RF-002, RF-010, RF-011, RF-012, RF-013, RF-014)
      [zona: test-seguridad]

### No funcional — latencia del middleware RBAC
- [ ] T-028 — Medición de latencia: 100 requests concurrentes contra un endpoint
      protegido con permisos ya cacheados (*cache-hit*), < 5ms agregados por el
      middleware — script documentado, evidencia de terminal pegada (cubre
      RNF-001) [zona: sistema-e2e]

### Documentación (`plan.md §8` + nota operativa de §3)
- [ ] T-029 — `hira-server/README.md`: añadir el paso operativo
      `docker compose exec backend alembic upgrade head` (antes de levantar
      tráfico) — nota de `plan.md §3`, no es fila de Art. 11 (no vuelve obsoleto
      nada existente) [doc]
- [ ] T-030 — Corregir `docs/hira-server/spec/modules/auth-rbac-seguridad.md`:
      reemplazar "Superusuario es el único que puede modificar roles y permisos"
      por "Admin" — no tocar el resto de la sección ni la referencia legacy a
      `backup-y-portabilidad.md` (deuda ya registrada, fuera de alcance) [doc]
- [ ] T-031 — Actualizar `docs/hira-server/spec/validation/vulnerabilities.md`:
      `VUL-SRV-004` de 🟡 En Proceso a 🟢 Resuelto — **tarea de cierre**, solo
      después de que T-014/T-015/T-020/T-028 estén verificados con evidencia real
      [doc]

## Cobertura (el gate exige 100 %; `Estado` lo rellena el gate)
| RF / doc | Tareas | Test(s) | Estado |
|---|---|---|---|
| RF-001 | T-003, T-004, T-012, T-013, T-017, T-018, T-024, T-025, T-027 | `test_jwt_tokens.py`, `test_auth_service.py`, `test_auth_router.py`, `test_user_repository_adapter.py`, `test_auth_security.py` | Pendiente |
| RF-002 | T-012, T-013, T-017, T-018, T-024, T-025, T-027 | `test_auth_service.py`, `test_auth_router.py`, `test_user_repository_adapter.py`, `test_auth_security.py` | Pendiente |
| RF-003 | T-003, T-004, T-019, T-020 | `test_jwt_tokens.py`, `test_authentication_middleware.py` | Pendiente |
| RF-004 | T-005, T-006, T-021, T-022 | `test_rbac_policy.py`, `test_rbac_dependencies.py` | Pendiente |
| RF-005 | T-005, T-006, T-021, T-022 | `test_rbac_policy.py`, `test_rbac_dependencies.py` | Pendiente |
| RF-006 | T-014, T-015, T-024, T-025 | `test_rbac_service.py`, `test_user_repository_adapter.py` | Pendiente |
| RF-007 | T-014, T-015, T-024, T-025 | `test_rbac_service.py`, `test_user_repository_adapter.py` | Pendiente |
| RF-008 | T-005, T-006, T-021, T-022 | `test_rbac_policy.py`, `test_rbac_dependencies.py` | Pendiente |
| RF-009 | T-005, T-006, T-021, T-022 | `test_rbac_policy.py`, `test_rbac_dependencies.py` | Pendiente |
| RF-010 | T-012, T-013, T-017, T-018, T-027 | `test_auth_service.py`, `test_auth_router.py`, `test_auth_security.py` | Pendiente |
| RF-011 | T-003, T-004, T-012, T-013, T-017, T-018 | `test_jwt_tokens.py`, `test_auth_service.py`, `test_auth_router.py` | Pendiente |
| RF-012 | T-001, T-002, T-024, T-025, T-026, T-027 | `test_password_hashing.py`, `test_user_repository_adapter.py`, `test_auth_security.py` | Pendiente |
| RF-013 | T-003, T-004, T-012, T-013, T-017, T-018, T-027 | `test_jwt_tokens.py`, `test_auth_service.py`, `test_auth_router.py`, `test_auth_security.py` | Pendiente |
| RF-014 | T-012, T-013, T-017, T-018, T-027 | `test_auth_service.py`, `test_auth_router.py`, `test_auth_security.py` | Pendiente |
| RNF-001 | T-020, T-028 | medición de latencia (T-028) | Pendiente |
| doc: hira-server/README.md (paso operativo) | T-029 | — | Pendiente |
| doc: auth-rbac-seguridad.md | T-030 | — | Pendiente |
| doc: vulnerabilities.md (VUL-SRV-004) | T-031 | — | Pendiente |

> Esta tabla **es** la trazabilidad de la feature (no hay `traceability-matrix.md`).
> Fila sin test, en `Fail` o `Pendiente` → el gate no abre.
