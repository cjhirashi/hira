---
título: SCHEMA — Convenciones de anclas y del registro
tipo: Referencia
status: activo
última_actualización: 2026-09-02
---

# Anclas y `registry.yaml`

## Tipos de ancla

| Prefijo | Significado | Vive en | Formato de archivo |
|---|---|---|---|
| `E-ADR-###` | Decisión de arquitectura de ecosistema (≥2 componentes) | `adr/ecosystem/` | `E-ADR-001-titulo-breve.md` |
| `SRV-ADR-###` | Decisión de Hira Server | `adr/hira-server/` | `SRV-ADR-001-titulo-breve.md` |
| `SRV-ADR-UI-##` | Decisión de UI/UX de Hira Server | `adr/hira-server/` | `SRV-ADR-UI-01-titulo-breve.md` |
| `HUB-ADR-##` | Decisión de Hira Hub | `adr/hira-hub/` | `HUB-ADR-01-titulo-breve.md` |
| `STU-ADR-###` | Decisión de Hira Studio | `adr/hira-studio/` | `STU-ADR-001-titulo-breve.md` |
| `REQ-<COMP>-###` | Requisito funcional | frontmatter del doc de spec + `registry.yaml` | — |
| `AC-<COMP>-##` | Grupo de criterios de aceptación | `spec/<comp>/validation/…` | — |
| `AC-<COMP>-##.n` | Criterio de aceptación individual | idem | — |
| `VUL-<COMP>-###` | Vulnerabilidad / riesgo con seguimiento | `spec/<comp>/validation/vulnerabilities.md` | — |
| `CT-<nombre>` | Contrato entre componentes | `contracts/<nombre>.openapi.yaml` | — |

`<COMP>` ∈ `SRV` · `HUB` · `STU`.

### Reglas

- Los ADRs son **inmutables** una vez `accepted`. Un cambio de fondo = ADR nuevo con el
  siguiente número, y un banner `> Superseded por <ID>` (o `> Parcialmente superseded…`)
  al inicio del ADR viejo.
- El número de ADR **no se reutiliza** entre componentes: `SRV-ADR-015` y un futuro
  `STU-ADR-015` son decisiones distintas de proyectos distintos.
- Un ancla se cita **verbatim** — mismo string en spec, `MODULE.md`, tests y commits.

## `registry.yaml`

Lista de entradas. Cada entrada:

```yaml
- id: AC-SRV-07.1                      # obligatorio, único
  kind: acceptance-criterion          # adr | requirement | acceptance-criterion | vulnerability | contract | spec-section
  component: hira-server              # hira-server | hira-hub | hira-studio | ecosystem
  title: "Alarma se activa al superar umbral"
  spec: .harness/spec/hira-server/validation/acceptance-criteria.md   # ruta relativa al repo
  requires: [SRV-ADR-005]             # otras anclas de las que depende (opcional)
  code: []                            # rutas de código que la realizan (se llena al implementar)
  tests: []                           # rutas de test que la verifican
  status: not-started                 # ver tabla de estados
  notes: ""                           # opcional
```

### Estados

| Estado | Significado |
|---|---|
| `accepted` | Solo ADRs — decisión vigente |
| `superseded` | Solo ADRs — reemplazada por otro ADR (campo `superseded_by:`) |
| `design-only` | Especificado, sin implementación planificada aún (Hub/Studio hoy) |
| `not-started` | En el registro, sin código |
| `in-progress` | Sprint activo trabajándola |
| `implemented` | Código existe y cita el ancla |
| `verified` | `implemented` + ≥1 test que cita el ancla y pasa |
| `open` / `mitigated` / `resolved` / `accepted-risk` | Solo `VUL-*` — estado de la vulnerabilidad |

### Lo que verifica `traceability_gate.py`

- El YAML parsea y no hay `id` duplicado.
- Toda ruta en `spec:`, `code:`, `tests:` existe en el repo.
- Todo ancla `verified` tiene ≥1 entrada en `tests:`.
- Ningún `code:` cita (por `MODULE.md`) un ADR con `status: superseded`.
- Todo endpoint declarado en un router de app está en el `openapi.yaml` de esa app.
- El checksum de cada archivo listado como `spec-section` coincide con `anchors/tools/spec_checksum.py`.
