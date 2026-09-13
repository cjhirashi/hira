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

Pendiente de un batch posterior de `tasks.md` (T-009 en adelante, fuera de
alcance de este batch): `dependencies.py` (`require_role`/`require_project_scope`,
`Depends()` de FastAPI — consumen `rbac_policy.py`).
