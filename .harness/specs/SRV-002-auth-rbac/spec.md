---
id: SPEC-SRV-002
tipo: spec
feature: SRV-002-auth-rbac
estado: in-review
anchor_commit: ‹pendiente›
anchor_mode: advisory
covers:
  - hira-server/backend/**
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-13 }
  fase_2: pendiente
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
  invalidar la entrada de caché Redis (`rbac:{user_id}`) de ese usuario antes de
  confirmar la modificación.
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
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-13).
