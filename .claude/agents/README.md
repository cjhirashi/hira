# .claude/agents/ — binding de Claude Code

Binding del arnés a Claude Code. El **manual operativo** de cada rol base vive en
`.harness/method.md §8`, no aquí.

## Base (añadidos 2026-09-04, esquema simplificado)

| Agente | Rol | `model` |
|---|---|---|
| `orquestador` | Coordinador — clasifica, sostiene las puertas humanas, delega, cierre | sonnet |
| `autor-de-spec` | Fase 1 · elicitación interactiva → `spec.md` | sonnet |
| `arquitecto` | Fase 2 · `plan.md` conforme al patrón del producto + `covers` | sonnet |
| `implementador` | Fase 4 · TDD, una tarea a la vez | sonnet |
| `revisor` | Verificador adversarial · corre el gate, traza `RF-↔test` | sonnet |
| `explorador` | Búsqueda read-only acotada antes de speccar | haiku |

`revisor` nunca es más débil que `implementador`.

**Retirado:** `hira-orquestador.md` (rol duplicado, referenciaba `.harness/coordination/`
y `.harness/ci/run_all.sh`, ambos retirados en `ADR-001`) — superseded por `orquestador`.

## Especialista de UX/UI (activo — `ADR-003`)

| Agente | Qué hace | model |
|---|---|---|
| `experto-ux-ui` | Diseña y **revisa** la UX/UI de los frontends de los 3 productos. Aporta flujos y estados en Fase 1/2; revisa la UI contra el estándar (contraste WCAG AA, consistencia con el sistema de diseño MD3+Cyan, accesibilidad, responsive, microcopy) en Fase 4, antes de que cierre el `revisor`. **Complementa a `hira-frontend`** (que implementa el código), no lo reemplaza. No escribe código de producción. | sonnet |

Sistema de diseño de referencia: `docs/hira-server/spec/ui-ux/`.

## Especialistas de módulo (pre-diseñados)

16 agentes fijados el 2026-09-02 (`.harness/claude/ORCHESTRATION.md` documentaba el
equipo completo), uno por dominio del ecosistema:

| Agente | Dueño de |
|---|---|
| `hira-datos` | Modelo de datos, migraciones, esquema |
| `hira-contratos` | Contratos compartidos, contract-first |
| `hira-frontend` | Frontend de Server y Hub (MD3 + Cyan) |
| `hira-qa` | Tests de integración, mapeo test↔criterio, gates |
| `hira-protocolos` | BACnet / Modbus / MQTT |
| `hira-logica` | Motor de lógica y pruebas |
| `hira-alarmas` | Alarmas e históricos |
| `hira-auth` | RBAC dinámico, auth |
| `hira-backup` | Backup y portabilidad |
| `hira-ia` | Agente IA (Server/Studio) |
| `hira-infra` | Infraestructura de `hira-server` |
| `hira-licencia` | Licenciamiento por puntos |
| `hira-tiempo-real` | Tiempo real (WebSocket, Redis Pub/Sub) |
| `hub-infra` | Infraestructura de `hira-hub` |
| `hub-licencias` | Licencias en Hub |
| `hub-reports` | Crash reports |

Rutas refrescadas (`ADR-004`, 2026-09-13): arranque → `.harness/method.md §2` +
`.harness/memory/state.md`; entrega → tabla de cobertura de `tasks.md`; contradicción
de diseño → Directiva de Pausa (`method.md §5`). Listos para invocar.

Se añaden como especialistas nuevos **vía un `ADR-`** si el dominio lo justifica.
