---
título: Migración del corpus del vault a .harness/
tipo: Registro
status: cerrado
fecha: 2026-09-02
---

# Migración vault → harness (F0)

El diseño previo vivía en un vault de Obsidian (proyectos `7.1 - Hira Server`,
`7.2 - Hira Hub`). El 2026-09-02 se extrajo todo a `.harness/` y las carpetas del vault se
eliminaron del repo. El vault dejó de ser fuente de verdad.

## Cobertura

- **78** documentos de contenido en el vault.
  - **75** migrados 1:1 (con `origen_vault:` en el frontmatter): 25 ADRs de Server, 5 de
    Hub extraídos de `7.2.3`, arquitectura, diseño por módulo, UI/UX, criterios de
    aceptación, plan de pruebas, 15+6 vulnerabilidades, operación, mejoras, incidencias,
    portafolios, bitácoras, plan de sprints de Hub.
  - **2** migrados con transformación fuerte (de-vaulteados): `7.1.9.3 - CLAUDE.md` →
    `.harness/claude/hira-server.md`; `7.2.15 - CLAUDE.md` → `.harness/claude/hira-hub.md`.
  - **1** descartado intencionalmente: `7.1.9.1 - Sprint Activo.md` (Sprint 24 de la
    implementación previa, obsoleta). Su contenido de valor (deudas `DA-003`/`DA-004`,
    estado del intento previo) quedó en `.harness/coordination/sprint-history.md`.
- **24** documentos estructurales del vault (`* - README - *`, `* - ÍNDICE - *`) no se
  migraron — su función la cumplen los `README.md` de cada carpeta de `.harness/`.

## Transformaciones aplicadas

- Wikilinks `[[...]]` de Obsidian → texto plano / rutas.
- Numeración de vault `7.1.x` / `7.2.x` → rutas relativas del harness (o retiradas en
  registros históricos, con nota).
- IDs de anclas: `ADR-NNN` → `SRV-ADR-NNN`; `ADR-UI-NN` → `SRV-ADR-UI-NN`;
  `ADR-H0N` → `HUB-ADR-0N`; `CA-NN` → `AC-SRV-NN`; `VUL-NNN` → `VUL-SRV-NNN`;
  `VUL-H0N` → `VUL-HUB-0N`.
- Frontmatter: se añadió `origen_vault:` con la ruta original.

## Contenido nuevo creado en F0

`E-ADR-001` (Studio cloud), `HUB-ADR-01..05` (reformateados desde `7.2.3`),
`spec/ecosystem/{vision,business-model,ecosystem-architecture}.md`,
`spec/hira-studio/{context,inherited-from-server,OPEN-QUESTIONS}.md`,
`.harness/contracts/*` (5 contratos), `.harness/anchors/registry.yaml`,
`.harness/coordination/{ROADMAP,SPRINT}.md`, todo `.harness/{PROCESS.md,templates,ci,claude}`.
