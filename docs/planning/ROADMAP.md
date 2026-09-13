---
título: Roadmap del ecosistema Hira
tipo: Coordinación
status: activo
última_actualización: 2026-09-03
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
  ├─ diseño de plataforma: CERRADO (STU-ADR-001..005, 2026-09-03)
  └─ requiere para implementar: STU-Spec (módulos + AC-STU detallados)
     + SRV-Sprint-12 (CT-engineering-session ampliado: pair + publish + consultas) ──┘
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
| SRV-Sprint-12 | Servidor de `CT-engineering-session` **ampliado** para Studio: sesión de ingeniería + emparejamiento (`studio_pairings`, `/engineering/pair`, UI de panel) + recepción de publicación de proyecto (reutiliza import `.hira`) + endpoints de consulta para las tools del Agente del Integrador | `CT-engineering-session`, `SRV-ADR-016`, `REQ-SRV-studio-pairing`, `REQ-SRV-project-publish`, `REQ-CT-engsession-v2` |

> El orden exacto y el contenido fino de SRV-Sprint-2+ se detalla al planificar cada uno
> con la plantilla `templates/sprint.md`. SRV-Sprint-1 ya está detallado en `SPRINT.md`.

## Track HUB — Hira Hub

Diseño completo (`spec/hira-hub/`, 5 ADRs). Sin implementación. Puede arrancar en paralelo
a SRV. Detalle de tareas por sprint: `coordination/hira-hub-sprint-plan.md`.

| Sprint | Objetivo | Anclas |
|---|---|---|
| **HUB-H0** | Walking Skeleton: Compose (FastAPI + PostgreSQL + Redis + Nginx) + `/health` + logger JSON, por puertos/adaptadores | `AC-HUB-H0`, `HUB-ADR-01`, `E-ADR-002` |
| HUB-H1 | Gestión de licencias: emitir/activar/validar/revocar + servidor de `CT-license` + Panel Admin | `AC-HUB-H1`, `HUB-ADR-02`, `HUB-ADR-03`, `CT-license`, `VUL-HUB-01`, `VUL-HUB-02`, `VUL-HUB-03` |
| HUB-H2 | Crash reports + versiones: servidor de `CT-crash-report` y `CT-updates` | `AC-HUB-H2`, `HUB-ADR-04`, `CT-crash-report`, `CT-updates`, `VUL-HUB-04` |
| HUB-H3 | Operación y resiliencia: backup probado, restart policy, UptimeRobot, dashboard | `AC-HUB-H3`, `VUL-HUB-05`, `VUL-HUB-06` |
| HUB-v0.2 | Portal de ventas (Stripe) + dashboard de instalaciones | — |
| HUB-v0.3 | Diseñador de bloques SVG + marketplace de plantillas `.hirat` + contrato real `CT-marketplace` | `CT-marketplace`, `VUL-SRV-015` |

## Track STU — Hira Studio

**Diseño de plataforma cerrado** (SQ-1..SQ-8 → `STU-ADR-001..005`, 2026-09-03; ver
`spec/hira-studio/context.md` y `architecture.md`). Sigue **bloqueado para implementar**
hasta que: (a) exista la spec por módulo de Studio y sus `AC-STU-*` detallados, y (b) SRV
exponga `CT-engineering-session` **ampliado** (emparejamiento + publish + consultas para el
agente).

| Fase | Objetivo | Anclas |
|---|---|---|
| STU-Spec | Spec por módulo en `spec/hira-studio/` (auth, servers/pairing, projects, configurator, offline-runner, publish, ai) y `AC-STU-*` detallados a partir de los grupos `AC-STU-01..06` | `STU-ADR-001..005`, `SPEC-STU-architecture` |
| STU-Sprint-1 | Walking Skeleton: SPA + BFF (FastAPI + PostgreSQL + Redis), `auth` (cuenta + vínculo de licencia vía `CT-license`), aislamiento por `integrator_id` | `AC-STU-01`, `AC-STU-02`, `STU-ADR-001`, `STU-ADR-002` |
| STU-Sprint-2 | `servers` — emparejamiento por token, credencial cifrada, sesión de ingeniería contra un Server real | `AC-STU-03`, `STU-ADR-003` |
| STU-Sprint-3 | `projects` + `configurator` — borradores de diseño (dispositivos-simulador, puntos, asociaciones, mimics) heredando de `spec/hira-server/` | `AC-STU-04` (parcial), `STU-ADR-004` |
| STU-Sprint-4 | `offline-runner` — motor de simulación + sandbox RestrictedPython; ejecutar lógica y pruebas del borrador | `AC-STU-04`, `STU-ADR-004` |
| STU-Sprint-5 | `publish` — serializar borrador (`.hira` extendido) y cargarlo al Server; flujo simulador→real | `AC-STU-05`, `STU-ADR-004` |
| STU-Sprint-6 | `ai` — Agente del Integrador en el BFF (API key del integrador), tools offline/online/Hub, `ai_usage_log` | `AC-STU-06`, `STU-ADR-005` |
| STU-Sprint-7+ | Editor de mimics (React Flow), biblioteca de proyectos, catálogo `.hirat` (v0.3) | heredan de `spec/hira-server/` |

## Orden recomendado global

1. **SRV-Sprint-1** y **HUB-H0** en paralelo (ambos son Walking Skeleton, sin dependencia).
2. SRV-Sprint-2..8 (núcleo SCADA) ‖ HUB-H1..H3.
3. SRV-Sprint-9 (licenciamiento) valida `CT-license` de verdad contra HUB-H1.
4. **STU-Spec** puede redactarse en cualquier momento (el diseño de plataforma ya está
   cerrado) — no consume ancho de banda de código.
5. SRV-Sprint-12 expone `CT-engineering-session` ampliado (pair + publish + consultas).
6. STU-Sprint-1..6 — arranca cuando STU-Spec esté lista y SRV-Sprint-12 haya aterrizado.
