# hira-hub

Componente **cloud** del ecosistema Hira (VPS): licencias, crash reports, versiones,
ventas (v0.2), marketplace (v0.3). Sin implementar.

- Instrucciones: [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) (generados).
- Especificación: [`../docs/hira-hub/spec/`](../docs/hira-hub/spec/).
- Decisiones: [`../docs/hira-hub/decisions/`](../docs/hira-hub/decisions/) (arquitectura:
  `E-ADR-002`, Hexagonal — supersede `HUB-ADR-05`).
- Plan de sprints H0–H3: [`../docs/planning/hira-hub-sprint-plan.md`](../docs/planning/hira-hub-sprint-plan.md).
- Es el servidor de los contratos `CT-license`, `CT-crash-report`, `CT-updates` en
  [`../docs/contracts/`](../docs/contracts/).

Arranca por `HUB-H0` (Walking Skeleton) — puede correr en paralelo a la feature activa de Server.
