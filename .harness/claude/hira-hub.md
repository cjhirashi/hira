<!-- FUENTE del overlay de Hira Hub. De-vaulteado de 7.2.15 - CLAUDE.md. -->

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
