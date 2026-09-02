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
Server. Ver [`.harness/adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`](.harness/adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md).

## Cómo se desarrolla — Harness SDD-Anchored

Todo el proceso, la especificación y las decisiones viven en [`.harness/`](.harness/).
Cada unidad de código traza a un **ancla** estable que aparece a la vez en la spec y en el
código/tests; la deriva spec↔código se detecta en CI.

| Empieza por | |
|---|---|
| [`.harness/PROCESS.md`](.harness/PROCESS.md) | El proceso completo (obligatorio antes de tocar código) |
| [`.harness/README.md`](.harness/README.md) | Mapa de `.harness/` |
| [`.harness/coordination/ROADMAP.md`](.harness/coordination/ROADMAP.md) | Roadmap del ecosistema (3 tracks) |
| [`.harness/coordination/SPRINT.md`](.harness/coordination/SPRINT.md) | Sprint activo |
| [`AGENTS.md`](AGENTS.md) / `CLAUDE.md` | Instrucciones para agentes (generadas de `.harness/claude/`) |

### Gates

```bash
bash .harness/ci/run_all.sh      # trazabilidad + contratos + lint OpenAPI
```

## Estado

Harness sembrado (F0, 2026-09-02): diseño de Server y Hub migrado y anclado; Studio con el
diseño abierto. Sin código de aplicación todavía. Siguiente: `SRV-Sprint-1` y `HUB-H0`.

La implementación previa de Hira Server está archivada en la rama
`legacy/hira-server-snapshot` — ver [`.harness/legacy/README.md`](.harness/legacy/README.md).

## Licencia

Ver [`LICENSE`](LICENSE).
