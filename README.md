# Hira

Monorepo del **ecosistema Hira** — plataforma SCADA moderna, asequible y adaptable sin
código, con IA nativa, para integradores de automatización de edificios (HVAC, BMS, IoT).

## Componentes

| Carpeta | Qué es | Dónde corre |
|---|---|---|
| [`hira-server/`](hira-server/) | Núcleo SCADA: protocolos BACnet/Modbus/MQTT, alarmas, históricos, motor de lógica y pruebas, tiempo real | **Local / on-premise**, con instalador |
| [`hira-studio/`](hira-studio/) | Ingeniería y diseño de proyectos: configurador, lógica/pruebas, mimics, Agente del Integrador | **Nube** |
| [`hira-hub/`](hira-hub/) | Licencias, crash reports, versiones, ventas, marketplace | **Nube** (VPS) |

Frontera: Hub y Studio en la nube; Server local. Los proyectos viven siempre en un Hira
Server. Ver [`docs/decisions/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`](docs/decisions/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md).

## Cómo se desarrolla — Harness SDD-Anchored

Cómo trabajamos vive en [`.harness/`](.harness/) (maquinaria del arnés). La
especificación y las decisiones de **producto** viven en [`docs/`](docs/) — ver
`docs/README.md`. Cada feature nueva traza a un `RF-`/`RNF-` estable que aparece a la
vez en la spec y en el código/tests; la deriva spec↔código se detecta en el gate.

| Empieza por | |
|---|---|
| [`.harness/method.md`](.harness/method.md) | El método completo (obligatorio antes de tocar código) |
| [`.harness/constitution.md`](.harness/constitution.md) | Principios innegociables + perfil de arquitectura por producto |
| [`docs/planning/ROADMAP.md`](docs/planning/ROADMAP.md) | Roadmap del ecosistema (3 tracks) |
| [`.harness/specs/`](.harness/specs/) | Features en curso (`spec.md`/`plan.md`/`tasks.md`) |
| [`AGENTS.md`](AGENTS.md) / `CLAUDE.md` | Mapa para agentes (stub manual en la raíz; generados de `.harness/claude/` en cada producto) |

### Gates

```bash
bash .harness/gate/check.sh      # integridad + trazabilidad + anclaje + docs + contratos
```

## Estado

Harness reestructurado al esquema simplificado (`ADR-001`, 2026-09-04). Diseño de
plataforma cerrado en los 3 productos (Server: `SRV-ADR-*`; Hub: `HUB-ADR-*`; Studio:
`STU-ADR-001..005`) — los 3 son **Hexagonal** (`E-ADR-002`). Sin código de aplicación
todavía. Primera feature real en curso: `SRV-001-walking-skeleton` (Fase 2 · Plan).

La implementación previa de Hira Server está archivada en la rama
`legacy/hira-server-snapshot` — ver [`docs/legacy/README.md`](docs/legacy/README.md).

## Licencia

Ver [`LICENSE`](LICENSE).
