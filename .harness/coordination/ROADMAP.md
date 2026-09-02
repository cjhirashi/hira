---
título: Roadmap del ecosistema Hira
tipo: Coordinación
status: activo
última_actualización: 2026-09-02
---

# Roadmap del ecosistema

Tres tracks paralelos con dependencias. El sprint activo de cada track vive en
[`SPRINT.md`](SPRINT.md).

## Dependencias entre tracks

```
SRV (Hira Server, desde cero)
  └─ SRV v0.1 en producción  ─────────────┐
                                          ▼
HUB (Hira Hub)  H0 → H1 → H2 → H3   (puede arrancar en paralelo a SRV;
                                     CT-license se valida de verdad cuando ambos existen)
                                          │
STU (Hira Studio, cloud)                  │
  └─ requiere: OPEN-QUESTIONS cerradas ───┤
     + SRV con CT-engineering-session ────┘
```

## Track SRV — Hira Server

Reimplementación desde cero bajo el harness. El diseño está completo
(`spec/hira-server/`, 25 ADRs). El código previo se descartó (ver
`coordination/sprint-history.md`).

| Sprint | Objetivo | Anclas principales |
|---|---|---|
| **SRV-Sprint-1** *(siguiente)* | Walking Skeleton: Docker Compose (FastAPI + PostgreSQL/TimescaleDB + Redis + Mosquitto + Nginx), `/health`, logger JSON, `core/config.py`, Contract-First `docs/openapi.yaml` inicial | `AC-SRV-01`, `SRV-ADR-001`, `SRV-ADR-002`, `SRV-ADR-003`, `SRV-ADR-004`, `SRV-ADR-017` |
| SRV-Sprint-2 | Auth + RBAC dinámico + caché de permisos en Redis | `AC-SRV-02`, `SRV-ADR-005`, `VUL-SRV-004` |
| SRV-Sprint-3 | Puertos de protocolo + adaptadores BACnet/Modbus/MQTT + simuladores | `AC-SRV-03`, `AC-SRV-04`, `AC-SRV-05`, `SRV-ADR-014`, `VUL-SRV-001`, `VUL-SRV-005` |
| SRV-Sprint-4 | Modelo de puntos candidatos → asociación explícita (incorpora `REQ-SRV-candidatos`) | `AC-SRV-03`, `SRV-ADR-012`, `SRV-ADR-019` |
| SRV-Sprint-5 | WebSocket tiempo real + Dashboard + SVG HVAC | `AC-SRV-06`, `SRV-ADR-UI-03`, `SRV-ADR-UI-01` |
| SRV-Sprint-6 | Motor de Alarmas | `AC-SRV-07` |
| SRV-Sprint-7 | Históricos (TimescaleDB) | `AC-SRV-08`, `SRV-ADR-004` |
| SRV-Sprint-8 | Motor de Lógica + Motor de Pruebas (2 capas, locks) | `AC-SRV-09`, `SRV-ADR-007`, `SRV-ADR-009` |
| SRV-Sprint-9 | Licenciamiento por puntos en línea + multi-proyecto (`REQ-SRV-licencia-online`) + cliente de `CT-license` | `AC-SRV-12`, `SRV-ADR-018`, `SRV-ADR-020` |
| SRV-Sprint-10 | Agentes IA (Integrador + Cliente) + RAG + Ollama embebido | `AC-SRV-10`, `SRV-ADR-013`, `SRV-ADR-021` |
| SRV-Sprint-11 | Backup / portabilidad `.hira` + cliente de `CT-crash-report` / `CT-updates` | `AC-SRV-11`, `VUL-SRV-012` |
| SRV-Sprint-12 | Servidor de `CT-engineering-session` (para Studio) | `CT-engineering-session`, `SRV-ADR-016` |

> El orden exacto y el contenido fino de SRV-Sprint-2+ se detalla al planificar cada uno
> con la plantilla `templates/sprint.md`. SRV-Sprint-1 ya está detallado en `SPRINT.md`.

## Track HUB — Hira Hub

Diseño completo (`spec/hira-hub/`, 5 ADRs). Sin implementación. Puede arrancar en paralelo
a SRV. Detalle de tareas por sprint: `coordination/hira-hub-sprint-plan.md`.

| Sprint | Objetivo | Anclas |
|---|---|---|
| **HUB-H0** | Walking Skeleton: Compose (FastAPI + PostgreSQL + Redis + Nginx) + `/health` + logger JSON | `AC-HUB-H0`, `HUB-ADR-01`, `HUB-ADR-05` |
| HUB-H1 | Gestión de licencias: emitir/activar/validar/revocar + servidor de `CT-license` + Panel Admin | `AC-HUB-H1`, `HUB-ADR-02`, `HUB-ADR-03`, `CT-license`, `VUL-HUB-01`, `VUL-HUB-02`, `VUL-HUB-03` |
| HUB-H2 | Crash reports + versiones: servidor de `CT-crash-report` y `CT-updates` | `AC-HUB-H2`, `HUB-ADR-04`, `CT-crash-report`, `CT-updates`, `VUL-HUB-04` |
| HUB-H3 | Operación y resiliencia: backup probado, restart policy, UptimeRobot, dashboard | `AC-HUB-H3`, `VUL-HUB-05`, `VUL-HUB-06` |
| HUB-v0.2 | Portal de ventas (Stripe) + dashboard de instalaciones | — |
| HUB-v0.3 | Diseñador de bloques SVG + marketplace de plantillas `.hirat` + contrato real `CT-marketplace` | `CT-marketplace`, `VUL-SRV-015` |

## Track STU — Hira Studio

**Bloqueado** hasta cerrar `spec/hira-studio/OPEN-QUESTIONS.md` (SQ-1..SQ-8) → primeros
`STU-ADR-###`, y hasta que SRV exponga `CT-engineering-session` (SRV-Sprint-12).

| Fase | Objetivo |
|---|---|
| STU-Diseño | Resolver SQ-1..SQ-8, redactar `STU-ADR-*`, abrir `spec/hira-studio/` por módulo, sembrar `AC-STU-*` en el registry |
| STU-Sprint-1 | Walking Skeleton de Studio (según SQ-4: frontend + BFF) + cliente de `CT-engineering-session` contra un Server de pruebas |
| STU-Sprint-2+ | Configurador, edición de lógica/pruebas, mimics, Agente del Integrador (heredan de `spec/hira-server/` — ver `spec/hira-studio/inherited-from-server.md`) |

## Orden recomendado global

1. **SRV-Sprint-1** y **HUB-H0** en paralelo (ambos son Walking Skeleton, sin dependencia).
2. SRV-Sprint-2..8 (núcleo SCADA) ‖ HUB-H1..H3.
3. SRV-Sprint-9 (licenciamiento) valida `CT-license` de verdad contra HUB-H1.
4. SRV-Sprint-12 expone `CT-engineering-session`.
5. STU-Diseño (en cuanto haya ancho de banda) → STU-Sprint-1.
