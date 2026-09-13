# hira-studio

Producto **cloud** de ingeniería y diseño de proyectos (`E-ADR-001`). Diseño de
plataforma **cerrado** (SQ-1..SQ-8, `STU-ADR-001..005`, arquitectura Hexagonal por
`E-ADR-002`) — falta la spec por módulo antes de implementar.

- Instrucciones: [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) (generados).
- Contexto: [`../docs/hira-studio/spec/context.md`](../docs/hira-studio/spec/context.md).
- **Preguntas de diseño de plataforma (resueltas)**:
  [`../docs/hira-studio/spec/OPEN-QUESTIONS.md`](../docs/hira-studio/spec/OPEN-QUESTIONS.md).
- Diseño heredado de Server: [`../docs/hira-studio/spec/inherited-from-server.md`](../docs/hira-studio/spec/inherited-from-server.md).
- Consume el contrato `CT-engineering-session` (Studio ↔ Server) y `CT-license` / `CT-crash-report` (→ Hub).

No hay feature activa hasta escribir la spec por módulo (`docs/hira-studio/spec/` —
auth, servers/pairing, projects, configurator, offline-runner, publish, ai).
