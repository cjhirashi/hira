# hira-hub

Componente **cloud** del ecosistema Hira (VPS): licencias, crash reports, versiones,
ventas (v0.2), marketplace (v0.3). Sin implementar.

- Instrucciones: [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) (generados).
- Especificación: [`../.harness/spec/hira-hub/`](../.harness/spec/hira-hub/).
- Decisiones: [`../.harness/adr/hira-hub/`](../.harness/adr/hira-hub/).
- Plan de sprints H0–H3: [`../.harness/coordination/hira-hub-sprint-plan.md`](../.harness/coordination/hira-hub-sprint-plan.md).
- Es el servidor de los contratos `CT-license`, `CT-crash-report`, `CT-updates` en
  [`../.harness/contracts/`](../.harness/contracts/).

Arranca por `HUB-H0` (Walking Skeleton) — puede correr en paralelo a `SRV-Sprint-1`.
