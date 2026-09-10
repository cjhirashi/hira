# docs/ — documentación del producto (ecosistema Hira)

Todo lo que describe **qué es** el ecosistema y sus 3 productos vive aquí. Cómo
trabajamos (el arnés) vive en `.harness/` — ver `.harness/method.md` y
`.harness/constitution.md`.

Este árbol se relocalizó el 2026-09-04 desde `.harness/` en la reestructuración al
esquema simplificado del arnés (`.harness/decisions/ADR-001-*`). El contenido no
cambió, solo la ubicación.

## Mapa

| Carpeta | Qué es | Antes vivía en |
|---|---|---|
| `GLOSSARY.md` | Términos de negocio del ecosistema | `.harness/GLOSSARY.md` |
| `ecosystem/spec/` | Visión, modelo de negocio, stakeholders, arquitectura C4 del ecosistema | `.harness/spec/ecosystem/` |
| `decisions/ecosystem/` | ADRs que gobiernan ≥2 productos (`E-ADR-###`) | `.harness/adr/ecosystem/` |
| `hira-server/spec/` | Arquitectura, módulos, UI/UX, operación, validación, guía de implementación | `.harness/spec/hira-server/` |
| `hira-server/decisions/` | ADRs de Server (`SRV-ADR-###`, `SRV-ADR-UI-##`) — incl. **`SRV-ADR-017` (Hexagonal)** | `.harness/adr/hira-server/` |
| `hira-studio/spec/` | Arquitectura, contexto, preguntas de diseño resueltas | `.harness/spec/hira-studio/` |
| `hira-studio/decisions/` | ADRs de Studio (`STU-ADR-###`) | `.harness/adr/hira-studio/` |
| `hira-hub/spec/` | Diseño conceptual/detallado, deployment, operación, validación | `.harness/spec/hira-hub/` |
| `hira-hub/decisions/` | ADRs de Hub (`HUB-ADR-##`) | `.harness/adr/hira-hub/` |
| `contracts/` | 5 contratos OpenAPI compartidos entre productos | `.harness/contracts/` |
| `planning/` | Roadmap del ecosistema, sprint(s), bitácoras pre-reestructuración | `.harness/coordination/` |
| `legacy/` | Sistema de anclas, gates de CI, plantillas y `PROCESS.md`/`README.md` del arnés viejo — **referencia histórica, no se mantiene activamente** | `.harness/{anchors,ci,templates,deviations}/`, `.harness/{README,PROCESS}.md`, `.harness/spec/MIGRATION.md`, `.harness/legacy/` |

## Convención de anclas de producto (histórica, se mantiene)

Los documentos ya migrados usan prefijos por producto en sus identificadores; **no se
renumeran** al adoptar el esquema simplificado (Constitución Art. 9):

| Prefijo | Significado |
|---|---|
| `E-ADR-###` | Decisión de ecosistema |
| `SRV-ADR-###`, `SRV-ADR-UI-##` | Decisión de Hira Server |
| `HUB-ADR-##` | Decisión de Hira Hub |
| `STU-ADR-###` | Decisión de Hira Studio |
| `CT-<nombre>` | Contrato entre componentes (`docs/contracts/`) |

Las **features nuevas**, a partir de ahora, usan `RF-NNN` (EARS) en
`.harness/specs/<PRODUCTO>-NNN-slug/` — ver `.harness/method.md §4`.
