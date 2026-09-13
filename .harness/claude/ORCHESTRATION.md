<!-- FUENTE. Orquestación del equipo de agentes. -->

# Orquestación del equipo de agentes

## Roles

- **Orquestador** — la sesión principal de Claude Code. Lee `.harness/memory/state.md` y
  las features activas en `.harness/specs/`, descompone en tareas (`tasks.md`), delega a
  los especialistas, integra su trabajo, corre `.harness/gate/check.sh`, actualiza la
  tabla de cobertura de `tasks.md`, cierra con el Session-End (`method.md §10`).
- **Especialistas de módulo** — `.claude/agents/`. Cada uno es dueño de un módulo y su
  **rango de anclas** es su límite de alcance. No tocan módulos ajenos; si necesitan un
  cambio fuera de su alcance, lo piden al orquestador.

## Regla de modelo

`haiku` para tareas mecánicas de bajo riesgo · `sonnet` para todo lo que requiere criterio
técnico (la mayoría de los módulos: BACnet/Modbus/MQTT, Motor de Lógica, Agente IA,
licenciamiento, contratos). Ningún agente fija `opus` por defecto.

## Especialistas (F0 — se ajustan al avanzar)

### Fijos de proyecto (aplican a las tres apps)

| Agente | Dueño de | Anclas de referencia |
|---|---|---|
| `hira-datos` | Modelo de datos, migraciones, esquema | `SPEC-SRV-data-model`, `SRV-ADR-004`, `SRV-ADR-019`, `REQ-SRV-candidatos` |
| `hira-contratos` | `docs/contracts/` y los `docs/openapi.yaml` de cada app; Contract-First | `CT-license`, `CT-crash-report`, `CT-updates`, `CT-engineering-session`, `SPEC-SRV-api` |
| `hira-frontend` | Frontend de Server y Hub (MD3 + Cyan), componentes base | `SRV-ADR-UI-01..04`, `docs/hira-server/spec/ui-ux/`, `docs/hira-hub/spec/ui-ux.md` |
| `hira-qa` | Tests de integración, mapeo test↔`AC-*`, gate | todos los `AC-*`, `.harness/gate/` |

### De módulo — Hira Server

| Agente | Dueño de | Anclas |
|---|---|---|
| `hira-infra` | Docker Compose, Nginx, Mosquitto, `core/` (config, logger), Walking Skeleton | `SRV-ADR-001..004`, `SRV-ADR-017`, `AC-SRV-01` |
| `hira-auth` | Auth JWT + RBAC dinámico + caché Redis de permisos | `SRV-ADR-005`, `SRV-ADR-020`, `AC-SRV-02`, `VUL-SRV-004`, `VUL-SRV-006` |
| `hira-protocolos` | Puertos de protocolo + adaptadores BACnet/Modbus/MQTT + simuladores + escaneo | `SRV-ADR-012`, `SRV-ADR-014`, `SRV-ADR-019`, `AC-SRV-03..05`, `VUL-SRV-001`, `VUL-SRV-005`, `VUL-SRV-010` |
| `hira-tiempo-real` | Redis pub/sub, WebSocket, Dashboard, SVG HVAC | `SRV-ADR-003`, `SRV-ADR-008`, `SRV-ADR-UI-03`, `AC-SRV-06` |
| `hira-alarmas` | Motor de Alarmas + Históricos (TimescaleDB) | `SRV-ADR-004`, `AC-SRV-07`, `AC-SRV-08`, `VUL-SRV-007` |
| `hira-logica` | Motor de Lógica + Motor de Pruebas (2 capas, locks, RestrictedPython, Monaco) | `SRV-ADR-007`, `SRV-ADR-009`, `SRV-ADR-UI-04`, `AC-SRV-09` |
| `hira-ia` | Agentes Integrador/Cliente, RAG (pgvector), Ollama embebido, auto-doc | `SRV-ADR-006`, `SRV-ADR-010`, `SRV-ADR-011`, `SRV-ADR-013`, `SRV-ADR-021`, `AC-SRV-10`, `VUL-SRV-008` |
| `hira-licencia` | Licenciamiento por puntos en línea, multi-proyecto, cliente de `CT-license` | `SRV-ADR-018`, `SRV-ADR-020`, `AC-SRV-12`, `REQ-SRV-licencia-online`, `VUL-SRV-014` |
| `hira-backup` | Exportación/importación `.hira`, backup L1/L2/L3, cliente de `CT-crash-report`/`CT-updates` | `AC-SRV-11`, `VUL-SRV-009`, `VUL-SRV-012`, `VUL-SRV-015` |

### De módulo — Hira Hub

| Agente | Dueño de | Anclas |
|---|---|---|
| `hub-infra` | Compose, Nginx, `core/`, Walking Skeleton, backup probado | `HUB-ADR-01`, `E-ADR-002`, `AC-HUB-H0`, `AC-HUB-H3`, `VUL-HUB-05` |
| `hub-licencias` | Emisión/activación/validación/revocación, servidor de `CT-license`, Panel Admin de licencias | `HUB-ADR-02`, `HUB-ADR-03`, `AC-HUB-H1`, `CT-license`, `VUL-HUB-01..03`, `VUL-HUB-06` |
| `hub-reports` | Crash reports (sanitización, dedup), versiones, servidor de `CT-crash-report`/`CT-updates` | `HUB-ADR-04`, `AC-HUB-H2`, `CT-crash-report`, `CT-updates`, `VUL-HUB-04` |

### Hira Studio

Sin especialistas todavía — el diseño de plataforma cerró (`docs/hira-studio/spec/OPEN-QUESTIONS.md`,
`STU-ADR-001..005`) pero falta la spec por módulo. Se derivan cuando exista.

## Transversales del sistema

Los agentes transversales (Git, CI/CD, Seguridad, Observabilidad, Docker, VPS,
Documentación técnica, LLM, RAG, IoT/Protocolos industriales, Backup, …) NO se definen en
este repo — se asumen disponibles en `~/.claude/agents/`. Si falta alguno, se documenta
como `DEV-###` (tipo `agentes-faltantes`), no se crea aquí.
