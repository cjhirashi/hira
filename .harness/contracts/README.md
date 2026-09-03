---
título: Contratos entre componentes — Ecosistema Hira
tipo: README
status: activo
última_actualización: 2026-09-02
---

# `.harness/contracts/`

Fuente **única** de los contratos de API/eventos **entre** componentes del ecosistema.
Los contratos internos de cada app viven en `<app>/docs/openapi.yaml`.

| Archivo | Ancla | Dirección | Origen |
|---|---|---|---|
| `license.openapi.yaml` | `CT-license` | Hira Server → Hub · Hira Studio → Hub | `HUB-ADR-02`, `spec/hira-hub/detailed-design.md` |
| `crash-report.openapi.yaml` | `CT-crash-report` | Server → Hub · Studio → Hub | `HUB-ADR-04`, `VUL-SRV-012` |
| `updates.openapi.yaml` | `CT-updates` | Server → Hub · Studio → Hub | `spec/hira-hub/conceptual-design.md` |
| `engineering-session.openapi.yaml` | `CT-engineering-session` | Studio ↔ Server | `SRV-ADR-016` (promovido por `E-ADR-001`). **Ampliación pendiente** `REQ-CT-engsession-v2`: emparejamiento (`STU-ADR-003`), publicación de proyecto (`STU-ADR-004`), consultas para el Agente del Integrador (`STU-ADR-005`). |
| `marketplace.openapi.yaml` | `CT-marketplace` | Studio ↔ Hub · Server ← Hub | Hub v0.3 — **placeholder**, `VUL-SRV-015` |

## Reglas (ver `PROCESS.md` §6)

1. Un cambio de contrato es un commit `[<COMP>-Sprint-N][CONTRACT][…]` sobre este
   directorio, **antes** de tocar cliente o servidor.
2. `.harness/ci/contract_gate.py` verifica que el `openapi.yaml` de cada app que
   implementa o consume un contrato sigue siendo coherente con él.
3. `.harness/ci/openapi_lint.py` valida que cada archivo es OpenAPI 3.x correcto.

Todos los responses incluyen `trace_id` (Correlation ID). Autenticación:
`Authorization: Bearer <token>` salvo `/health` y donde se indique lo contrario.
