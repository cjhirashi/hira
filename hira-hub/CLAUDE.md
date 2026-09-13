<!-- GENERADO por .harness/claude/build_claude.py — NO EDITAR A MANO.
     Editar los overlays en .harness/claude/ y volver a ejecutar el script. -->

# Ecosistema Hira — instrucciones base

Monorepo con tres componentes y un harness SDD-Anchored. **Antes de tocar código, lee
`.harness/method.md §2` (rúbrica) y `.harness/constitution.md`.**

## Los tres componentes

| Carpeta | Qué es | Corre en | Arquitectura |
|---|---|---|---|
| `hira-server/` | Núcleo SCADA (protocolos, alarmas, históricos, lógica, tiempo real) | Local / on-premise, con instalador | Hexagonal (`docs/hira-server/decisions/SRV-ADR-017`) |
| `hira-studio/` | Ingeniería y diseño de proyectos (configurador, lógica/pruebas, mimics, Agente Integrador) | Nube | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |
| `hira-hub/` | Licencias, crash reports, versiones, ventas, marketplace | Nube (VPS) | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |

Frontera: **Hub y Studio en la nube, Server local** (`E-ADR-001`). Los proyectos viven
siempre en un Hira Server.

## Reglas transversales (todas las apps)

1. **Spec-first.** Solo se implementa lo que está especificado (`docs/<producto>/spec/`
   para el diseño ya cerrado; `.harness/specs/<PRODUCTO>-NNN-slug/spec.md` para features
   nuevas). Lo no especificado → Directiva de Pausa (`.harness/method.md §5`) y se espera.
   No inventes diseño.
2. **Anclas.** Toda tarea cita las anclas que toca (`RF-`/ADR de producto) y los
   `AC-<COMP>-*` que deja verificables. Cada carpeta que creas lleva su `README.md`.
3. **Contract-First.** Endpoint nuevo → primero al contrato (`docs/contracts/` si es
   entre componentes, `<app>/docs/openapi.yaml` si es interno), luego el router.
4. **Observabilidad.** Logger JSON estructurado desde `core/logger.py`. Cero `print()` en
   producción. Todo log de un request lleva `trace_id` (middleware Correlation ID,
   header `X-Trace-ID`).
5. **Seguridad.** Secrets solo en variables de entorno. Nada de SQL por concatenación
   (ORM con parámetros). Ver el registro de vulnerabilidades de cada componente.
6. **READMEs.** Cada carpeta que creas lleva su `README.md` en el mismo paso.
7. **No edites un ADR aceptado.** Se supersede con uno nuevo.
8. **No resuelvas contradicciones de diseño por tu cuenta.** Directiva de Pausa
   (`.harness/method.md §5`) y esperar revisión humana.

## Commits

Features nuevas → **Conventional Commits** + sufijo con la ancla:

```
<tipo>(<scope>): qué se hizo en imperativo (RF-NNN)
```

`<tipo>` ∈ `feat` `fix` `refactor` `test` `docs` `chore` `security`.
`<scope>` = componente o módulo tocado — catálogo por componente en su sección de abajo.
Fin del commit: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

> Los commits previos a la reestructuración del arnés (`ADR-001`) usan
> `[<COMP>-Sprint-N][TIPO][MÓDULO] … · Anchors: <lista>` — convención histórica, **no
> se retroactiva**.

## Definition of Done

Anclas citadas · contrato actualizado antes del router · cada `AC-*` con test que lo cita
y pasa · `.harness/gate/check.sh` en verde · tabla de cobertura de `tasks.md` al día ·
READMEs de las carpetas nuevas.

## Equipo de agentes

El orquestador (sesión principal) reparte a los especialistas de `.claude/agents/`, cada
uno dueño de un módulo con su rango de anclas como límite. Detalle:
`.harness/claude/ORCHESTRATION.md`.

# Overlay — `hira-hub/`

Componente cloud del ecosistema. Desplegado en un VPS (`hub.hira.cjhirashi.com`). Tres
capas que evolucionan por versión:

- **Backend API + Panel Admin (v0.1):** license keys, crash reports, versiones. Solo cjhirashi accede al Panel Admin.
- **Portal de Ventas (v0.2):** compra de licencias con Stripe; tras pago confirmado, Hub emite y envía la key por email.
- **Marketplace (v0.3):** catálogo de plantillas `.hirat` y bloques SVG.

Stack: FastAPI · PostgreSQL · Redis · Nginx · Docker Compose · GitHub Actions / GHCR.

## Orden de lectura al iniciar sesión

1. `.harness/memory/state.md` — próximo paso y correcciones del usuario.
2. `docs/planning/ROADMAP.md` — track HUB; `docs/planning/hira-hub-sprint-plan.md`.
3. `docs/hira-hub/spec/detailed-design.md` — modelos de BD, contratos, estructura.
4. `docs/hira-hub/spec/conceptual-design.md` y `docs/hira-hub/decisions/` — ADRs.
5. `docs/hira-hub/spec/validation.md` — criterios (`AC-HUB-*`).
6. `docs/hira-hub/spec/validation/vulnerabilities.md` — `VUL-HUB-*`, reglas que no puedes violar.

## Arquitectura (`E-ADR-002`, supersede `HUB-ADR-05`)

**Hexagonal**, mismo criterio que Server y Studio:

```
backend/core/ports/   → interfaces abstractas (LicenseStoragePort, CrashReportPort,
                         UpdateDistributionPort, NotificationPort, PaymentPort [reservado])
backend/adapters/     → implementaciones concretas (PostgreSQL, Redis, SMTP/webhook, GHCR/S3)
backend/services/     → lógica de negocio — solo importa de core/ports/, nunca de adapters/
backend/routers/      → endpoints (implementan docs/openapi.yaml), inyectan el adapter vía factory
backend/models/       → SQLAlchemy ORM · backend/schemas/ → Pydantic
```

## Contract-First

`hira-hub/docs/openapi.yaml` es el contrato interno. Hub es el **servidor** de
`CT-license`, `CT-crash-report`, `CT-updates` (en `docs/contracts/`) — su
`openapi.yaml` debe mantenerse coherente con ellos (bloque de contrato de
`.harness/gate/check.sh`, `method.md §6`).

## Seguridad — reglas críticas

| Regla | Ancla |
|---|---|
| License keys nunca en claro en BD ni logs — solo hash bcrypt + `key_prefix` (`HIRA-XXXX`) | `HUB-ADR-02`, `VUL-HUB-01` |
| El logger filtra el patrón `HIRA-[A-Z0-9]{4}-...` | `VUL-HUB-01` |
| Rate limiting en `/api/licenses/validate` (enumeración) | `VUL-HUB-02` |
| Hub no arranca sin `ADMIN_PASSWORD_HASH` | `VUL-HUB-03` |
| Crash reports sanitizados antes de persistir — nunca IPs, device names, point values, datos de usuario | `HUB-ADR-04`, `VUL-HUB-04` |
| `GET /health` siempre responde sin auth (UptimeRobot depende de esto) | — |
| Backup diario **con restore probado** | `VUL-HUB-05` |
| JWT del Panel Admin con expiración corta | `VUL-HUB-06` |

## Frontend (Admin / Portal / Marketplace)

Implementa lo de `docs/hira-hub/spec/ui-ux.md`. **Un seed MD3 + Cyan único para las
tres capas** — la diferencia es layout y densidad, no colores. No hardcodees hex.
- Panel Admin: solo Expanded (banner en breakpoints menores), default tema Sistema.
- Portal / Marketplace: responsive completo, default tema Claro.

## Módulos para el commit

`INFRA` `CORE` `MODELS` `SCHEMAS` `ROUTERS` `SERVICES` `LICENSES` `CRASHREPORTS`
`VERSIONS` `ADMIN` `CONTRACT` `FRONTEND`

## Prohibiciones específicas

`print()` en producción · license key en claro (BD o logs) · crash report sin sanitizar ·
paletas distintas por capa · vista no especificada en `ui-ux.md` · `LOG_LEVEL=DEBUG`
hardcodeado · lógica de negocio sin Walking Skeleton validado.
