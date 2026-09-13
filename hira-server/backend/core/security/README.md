# core/security

Núcleo de seguridad de `SRV-002-auth-rbac` — sin I/O, sin `Settings()`, sin
dependencia de `core/ports/`, `adapters/` ni FastAPI (`plan.md §2`). Testeable sin
mocks, con librerías reales (`bcrypt`, `PyJWT`).

- `passwords.py` — `hash_password`/`verify_password`, bcrypt factor 12 (RF-012).
- `jwt.py` — `create_access_token` (TTL 15 min), `create_refresh_token` (TTL 7
  días), `decode_token` (`HS256`, recibe `secret_key` explícito) — RF-001,
  RF-003, RF-011, RF-013. `TokenExpiredError`/`TokenInvalidError` definidas aquí.
- `rbac_policy.py` — `can_write`, `is_admin`, `can_access_project`: reglas puras
  del MVP de 3 roles fijos (RF-004, RF-005, RF-008, RF-009). El RBAC dinámico
  completo es v0.2 (`SRV-ADR-005`), no se anticipa aquí.
- `dependencies.py` — `require_role(*roles)`/`require_project_scope(project_id_param)`
  (T-021/T-022, RF-004, RF-005, RF-008, RF-009): factories de `Depends()` de
  FastAPI (única excepción de esta carpeta que sí importa FastAPI, justificada en
  `plan.md §7` — Starlette resuelve los `path params` **después** de que corre
  `BaseHTTPMiddleware.dispatch`, así que la autorización que depende de
  `project_id` no puede vivir en el middleware). Leen `request.state.user` (ya
  fijado por `AuthenticationMiddleware`) y aplican `rbac_policy.py`.
