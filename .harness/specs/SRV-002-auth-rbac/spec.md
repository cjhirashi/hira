---
id: SPEC-SRV-002
tipo: spec
feature: SRV-002-auth-rbac
estado: implemented
anchor_commit: f8157ed6efb7668b90c3dd4a61a97a2616301cf3
anchor_mode: strict
covers:
  - hira-server/backend/**
  - hira-server/docs/openapi.yaml
  - hira-server/README.md
  - docs/hira-server/spec/modules/auth-rbac-seguridad.md
  - docs/hira-server/spec/validation/vulnerabilities.md
  - docs/decisions/ecosystem/E-ADR-003-convencion-rfc9457-type.md
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-13 }
  fase_2: { por: "Carlos", fecha: 2026-09-13 }
actualizado: 2026-09-13
---

# SPEC-SRV-002 · Autenticación y RBAC (MVP — 3 roles fijos)

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Base: `SRV-ADR-005`
> (RBAC dinámico es v0.2; v0.1 usa 3 roles fijos), `SRV-ADR-020` (scope por proyecto/
> integrador), `AC-SRV-02`, `docs/hira-server/spec/modules/auth-rbac-seguridad.md`.
> Construye sobre `SRV-001-walking-skeleton` (`verified`).

## 1. Contexto del dominio
- Proteger todos los endpoints de Hira Server con autenticación (JWT) y autorización
  (RBAC de 3 roles fijos: Admin, Operador, Visor) — sin esto, cualquier módulo de
  negocio posterior (puntos, alarmas, lógica) queda sin control de acceso.
- Alcance de roles (`SRV-ADR-020`): roles de operación (Admin/Operador/Visor) son
  `scope=project` — el usuario solo actúa en su proyecto. Rol integrador es
  `scope=global` — accede a todos los proyectos de la instancia (relevante en
  licencia de integrador, multi-proyecto).

## 2. Alcance
### En alcance (propuesto)
- Modelo de datos: tabla `users` (email, password hash bcrypt, rol, `scope`,
  `project_id` si `scope=project`), sin tabla de permisos dinámica (eso es v0.2).
- `POST /auth/login` — valida credenciales, retorna JWT access (15 min) + refresh
  (7 días); refresh almacenado en Redis con revocación posible (`AC-SRV-02.1`).
- `POST /auth/refresh`, `POST /auth/logout` (revoca el refresh en Redis).
- Middleware RBAC en cada request protegido: valida JWT, resuelve rol/scope,
  cachea permisos en Redis (`rbac:{user_id}`, TTL = TTL del refresh) — no consulta
  BD en cada request (`AC-SRV-02.6`, <5ms de latencia agregada).
- Invalidación de caché Redis al modificar el rol de un usuario (`AC-SRV-02.5`).
- Passwords con bcrypt factor 12. `SECRET_KEY` para firma JWT (HS256) — ya existe
  en `.env.example` desde `SRV-001`.
- Solo el rol **Admin** puede modificar el rol de otro usuario — decidido
  (2026-09-13): en el modelo de 3 roles fijos no se introduce un concepto
  separado de "superusuario"; ese concepto encaja mejor en el RBAC dinámico de
  v0.2 (`SRV-ADR-005`).

### Fuera de alcance (decidido)
- RBAC dinámico completo (roles definidos en BD por el superusuario) — v0.2,
  `SRV-ADR-005`.
- Vista de login del frontend — decidido (2026-09-13): este sprint es solo
  backend/contrato (`POST /auth/login|refresh|logout` + middleware). La UI se
  especifica cuando arranque el sprint de frontend correspondiente, con
  `experto-ux-ui`.
- Gestión de usuarios (crear/editar/desactivar) más allá del mínimo para probar
  el flujo (creación por seed/migración, no un CRUD completo de usuarios en
  este sprint).

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `POST /auth/login` | entrada | REST | `hira-server/docs/openapi.yaml` (ampliar) |
| `POST /auth/refresh` | entrada | REST | ídem |
| `POST /auth/logout` | entrada | REST | ídem |
| Redis (`rbac:{user_id}`, refresh tokens, intentos de login) | salida | `CachePort` (ya existe) | interno |
| PostgreSQL (`users`) | salida | `DatabasePort` (ya existe) | interno |

Sobre de error — **RFC 9457** (confirmado, 2026-09-13): estos son endpoints de
negocio, a diferencia de `/health`. `type`/`title` a fijar en `plan.md` (p.ej.
`invalid-credentials`, `insufficient-role`, `token-expired`, `rate-limited`) —
el 401 de login usa el mismo `title` genérico para credenciales inválidas y
usuario desactivado (RF-002, evita enumeración).

## 4. Criterios de aceptación (EARS)
> Traducidos de `AC-SRV-02` (2.1–2.7). A confirmar.

- **RF-001** — CUANDO se recibe `POST /auth/login` con credenciales válidas, el
  sistema DEBE retornar un JWT access (TTL 15 min) y un JWT refresh (TTL 7 días).
- **RF-002** — SI las credenciales de `POST /auth/login` son inválidas (email no
  existe, password incorrecto, o usuario desactivado) ENTONCES el sistema DEBE
  responder 401 con el mismo mensaje genérico en los tres casos (no distinguir
  causa, evita enumeración de usuarios).
- **RF-003** — SI un request a un endpoint protegido llega con JWT access
  expirado, inválido o ausente ENTONCES el sistema DEBE responder 401 sin
  conceder acceso.
- **RF-004** — SI un usuario con rol Visor intenta una operación de escritura
  ENTONCES el sistema DEBE responder 403.
- **RF-005** — SI un usuario con rol Operador intenta acceder a un recurso
  reservado a Admin ENTONCES el sistema DEBE responder 403.
- **RF-006** — CUANDO Admin modifica el rol de un usuario, el sistema DEBE
  invalidar la entrada de caché Redis (`rbac:{user_id}`) y la caché en memoria
  del proceso que ejecuta la modificación, antes de confirmar la modificación.
  En procesos/réplicas adicionales del backend, la invalidación se propaga por
  *pub/sub* de forma *best-effort* (típicamente sub-segundo), acotada por un
  TTL de seguridad de 30s como cota máxima de obsolescencia si un mensaje se
  pierde — decisión de la Directiva de Pausa RNF-001 (2026-09-13, `plan.md
  §10`), no garantiza invalidación instantánea cruzada entre procesos.
- **RF-007** — El middleware RBAC DEBE resolver permisos desde caché Redis sin
  consultar PostgreSQL en cada request (solo en *cache-miss*) — resuelve
  `VUL-SRV-004` (RBAC con query a BD en cada request, crítico).
- **RF-008** — SI un usuario de operación (`scope=project`) intenta acceder a un
  proyecto distinto al suyo ENTONCES el sistema DEBE responder 403.
- **RF-009** — CUANDO un usuario integrador (`scope=global`) cambia de proyecto,
  el sistema DEBE conceder acceso sin exigir un nuevo login.
- **RF-010** — CUANDO se invoca `POST /auth/logout`, el sistema DEBE revocar el
  refresh token en Redis (ya no sirve para `POST /auth/refresh`).
- **RF-011** — CUANDO se invoca `POST /auth/refresh` con un refresh token válido
  y no revocado, el sistema DEBE emitir un nuevo access token.
- **RF-012** — El sistema DEBE almacenar contraseñas con bcrypt factor 12, nunca
  en texto plano.

## 5. Casos límite y manejo de errores
- **RF-013** — SI `POST /auth/refresh` recibe un refresh token revocado o
  expirado ENTONCES el sistema DEBE responder 401 (no emitir un nuevo access
  token).
- **RF-014** — SI se exceden **5 intentos fallidos** de `POST /auth/login` para
  la misma combinación email+IP en una ventana de **15 minutos** ENTONCES el
  sistema DEBE rechazar intentos adicionales de esa combinación con 429,
  independientemente del rate limiting genérico de Nginx (`VUL-SRV-003`).

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| MVP con 3 roles fijos, no RBAC dinámico completo | `SRV-ADR-005` fasea explícitamente v0.1 (fijo) vs v0.2 (dinámico); `AC-SRV-02` ya está escrito para el modelo fijo | Adelantar RBAC dinámico completo | `SRV-ADR-005` |
| Solo backend/contrato, sin vista de login | Evita mezclar dos zonas de patrón (backend hexagonal vs frontend MD3) en una sola feature; la UI necesita a `experto-ux-ui` (Art. 8) en su propio ciclo | Incluir la vista de login en este sprint | — |
| Solo Admin modifica roles (sin concepto de "superusuario" aparte) | En el modelo de 3 roles fijos, Admin ya cubre esa responsabilidad; "superusuario" encaja mejor como concepto de v0.2 | Mantener "superusuario" separado de Admin ya en el MVP | — |
| Sobre de error RFC 9457 para 401/403 | Son endpoints de negocio (a diferencia de `/health`); Constitución ya fija RFC 9457 como estándar | Shape propio simplificado | Constitución Art. 6 |
| Rate limiting específico en `/auth/login`, además del genérico de Nginx | `VUL-SRV-003` ya resuelve el caso genérico (100 req/s) pero es insuficiente para frenar fuerza bruta de contraseñas en un solo endpoint | Confiar solo en el rate limiting genérico de `VUL-SRV-003` | `VUL-SRV-003` (extensión) |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — El middleware RBAC DEBE agregar menos de 5ms de latencia por
  request, medido con 100 requests concurrentes (`AC-SRV-02.6`).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 1` (2026-09-13, **Directiva de Pausa RNF-001,
  `method.md §5` — solución de raíz APROBADA por Carlos el mismo día, pendiente
  de re-medición real**): midiendo RNF-001 con el método que esta misma spec
  exige (100 requests concurrentes), la implementación original de
  `AuthenticationMiddleware` (`starlette.middleware.base.BaseHTTPMiddleware`)
  no cumplía el umbral de <5ms — dos causas aditivas confirmadas de forma
  independiente (por dos rondas de revisor, medidas 3 veces por métodos
  distintos): (1) el piso de latencia de esa clase base y (2) el round-trip
  real a Redis por request en *cache-hit*. Carlos aprobó atacar ambas a la vez:
  migrar el middleware a ASGI puro + caché en memoria del proceso con
  invalidación por pub/sub de Redis en `services/rbac_service.py`. Diseño
  completo, evidencia de ambas causas y tareas (`T-032..T-040`): `plan.md`,
  sección "10. RNF-001 — Directiva de Pausa (histórico) y solución aprobada".
  Este marcador sigue en `1` (no se cierra a `0`) hasta que la re-medición real
  (`T-040`) confirme <5ms con el diseño completo —
  `tests/integration/test_rbac_latency.py` sigue `xfail(strict=True)` mientras
  tanto, no se relaja el umbral ni se asume el resultado sin medir.
  **Nota de RF-006 ya aplicada y confirmada por Carlos (2026-09-13):** el
  matiz de semántica de invalidación cruzada entre procesos/réplicas
  (propagación *best-effort* vía pub/sub, TTL 30s de cota máxima) queda
  explícito en el propio texto de RF-006 (§4) — no queda pendiente.
  Resto de la spec (2026-09-13, "así es") sin cambios.
