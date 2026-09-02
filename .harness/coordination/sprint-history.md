---
origen_vault: "7.1 - Hira Server/7.1.9 - Coordinación Claude Code/7.1.9.2 - Historial de Sprints y Roadmap.md"
título: Historial de Sprints y Roadmap — implementación previa de Hira Server (descartada)
tipo: Registro histórico
status: referencia
última_actualización: 2026-09-02
---

> **Registro histórico.** Este es el log de la implementación previa de Hira Server
> (repo `github.com/cjhirashi/hira-server`, ~24 sprints), **descartada**: bajo el harness
> SDD-Anchored, Hira Server se reimplementa desde cero (ver
> `.harness/legacy/README.md` para el código archivado).
>
> Se conserva por dos razones:
> 1. **Lecciones del intento previo** — qué se construyó, qué bugs recurrentes aparecieron.
> 2. **Deudas arquitectónicas DA-003 / DA-004** — nunca se implementaron y siguen siendo
>    requisitos válidos para la nueva implementación (modelo de puntos candidatos/asociados,
>    licenciamiento por puntos en línea, multi-proyecto). Se reflejan como anclas
>    `REQ-SRV-*` / `AC-SRV-*` en `.harness/anchors/registry.yaml`.
>
> El sprint activo real vive en `.harness/coordination/SPRINT.md`. Los identificadores
> `T-XXX`, `DEV-XXX` y "Cowork" son del flujo de trabajo antiguo, ya retirado.

## Historial de Sprints (implementación previa)

| Sprint | Período | Estado | Notas |
|---|---|---|---|
| Sprint 0 — Walking Skeleton | 2026-07-24 → 2026-07-25 | ✅ Completo | Walking Skeleton validado. 2 fixes: Mosquitto log_dest stdout + package-lock.json |
| Sprint 1 — Auth + RBAC | 2026-07-25 → 2026-07-25 | ✅ Completo | 1 fix: bcrypt==4.0.1 + EmailStr → str pattern (Python 3.12 compat) |
| Sprint 2 — BACnet + MQTT + Simuladores | 2026-07-25 → 2026-07-25 | ✅ Completo | 2 fixes: BAC0 2024.x API + celery-poller separado. Endpoint GET /simulators/{id} agregado. |
| Sprint 3 — WebSocket + Tiempo Real | 2026-07-25 → 2026-07-26 | ✅ Completo | 1 fix: nginx trailing slash + auth/users prefix. Reconexión automática con backoff confirmada. |
| Sprint 4 — Dashboard + SVG HVAC | 2026-07-26 → 2026-07-26 | ✅ Completo | 7 componentes SVG (Fan, Damper, Valve, Chiller, AHU, Sensor, Setpoint). |
| Sprint 5 — Motor de Alarmas | 2026-07-26 → 2026-07-26 | ✅ Completo | 3 bugs: logger name conflict, alarm_worker Redis singleton, valor Redis string→JSON. Ciclo activo→acknowledged→resolved validado. |
| Sprint 6 — Históricos | 2026-07-26 → 2026-07-26 | ✅ Completo | TimescaleDB hypertable + time_bucket (raw/1min/5min/1hour/1day). HistoryWriter con Redis TTL. Plotly + CSV StreamingResponse. Retención 90 días. |
| Sprint 7 — Configurador | 2026-07-26 → 2026-07-26 | ✅ Completo | ConfigPage con 4 tabs (Áreas/Dispositivos/Puntos/Usuarios). CRUD + RBAC config:read/write. 2 fixes: DELETE 409 + URL tabs. |
| Sprint 8 — Motor de Lógica | 2026-07-26 → 2026-07-26 | ✅ Completo | HiraAPI + logic_worker reescritos síncronos (psycopg2 + redis-py) para Celery prefork. RestrictedPython sandbox. Monaco Editor. 3 fixes. |
| Sprint 9 — Agente del Integrador | 2026-07-26 → 2026-07-26 | ✅ Completo | LangChain LCEL manual. 4/7 checks automáticos (DEV-005: T-93.4/5/6 requieren API key real). 3 fixes de schema. |
| Sprint 10b — Diseño Visual | 2026-07-26 → 2026-07-26 | ✅ Completo | Design system Slate+Cyan. Sidebar 3 secciones + footer. Dashboard 2 columnas. Card/Badge/DataTable. AlarmsPage con tabs. |
| Sprint 10c — Separación Studio / Server | 2026-07-26 → 2026-07-26 | ✅ Completo | RBAC sidebar (Hira Studio solo Admin con Wrench). Agente del Cliente (5 tools). Config dual-mode SQLite/PostgreSQL. docker-compose.studio.yml. Color cyan-600. **Nota (2026-07-31): esta separación quedó parcialmente desalineada con SRV-ADR-015 — ver Roadmap, ítem de reconciliación arquitectónica.** |
| Sprint 10 — Notificaciones | 2026-07-29 → 2026-07-29 | ✅ Completo | health_service + monitor_system (Celery beat 60s) + notification_service (SMTP + webhook). SystemStatusPage + NotificationsConfigPage. Migration 0010. |
| Sprint 11 — Motor de Pruebas | 2026-07-29 → 2026-07-29 | ✅ Completo | 6 commits. HiraTestAPI + test_worker (Celery HIGH, one-shot, RestrictedPython). Redis lock:point:{id} TTL 300s. logic_worker respeta locks. celery-tests service. TestsPage con Monaco + historial + logs polling. Migration 0011. |
| Sprint 12 — Módulo de Análisis | 2026-07-29 → 2026-07-29 | ✅ Completo | 3 commits. analysis_service.py (chart data, compare, trend, PDF con reportlab 5.0.0). Router /analysis 5 endpoints. AnalysisPage 2 tabs. |
| Sprint 13 — Módulo de Documentación | 2026-07-29 → 2026-07-29 | ✅ Completo | 3 commits. ast_parser.py (stdlib ast → flowchart TD Mermaid). doc_service.py con upsert. Migration 0012. Router /docs. DocumentationPage con Mermaid.js. |
| Sprint 14 — Agente IA + RAG | 2026-07-29 → 2026-07-29 | ✅ Completo | 5 commits. Migration 0013 (pgvector, document_chunks, índice HNSW). rag_service.py: chunk_markdown, embed_texts, semantic_search. Router /rag/search. Tool search_docs en ambos agentes. |
| Sprint 15 — DA-001: Studio Dashboard | 2026-07-29 → 2026-07-29 | ✅ Completo | 3 commits. StudioDashboard.tsx: 7 endpoints paralelos, cards resumen, lista lógica, últimas pruebas, distribución por área. Ruta /studio/dashboard bajo AdminRoute. |
| Sprint 16 — Exportación e Importación de Proyecto | 2026-07-29 → 2026-07-29 | ✅ Completo | 2 commits. project_service.py: export gzip+JSON, import merge (ON CONFLICT) y replace (cascada). Router /project. Tab "Sistema" en ConfigPage. |
| Sprint 17 — Protocolo Modbus (pymodbus TCP/RTU) | 2026-07-30 → 2026-07-30 | ✅ Completo | 5 commits. Migration 0014 (campos Modbus en devices y points). ModbusAdapter: TCP + RTU, 4 tipos de registro y de dato. modbus_poller.py Celery 10s. |
| Sprint 18 — Escaneo Automático de Dispositivos | 2026-07-30 → 2026-07-30 | ✅ Completo | 3 commits. scan_service.py: scan_bacnet, scan_modbus, scan_mqtt. Router POST /devices/scan. Modal 3 fases en DevicesTab. **Nota: este escaneo hoy alimenta `points` directo — pendiente migrar a `device_points_candidates` + asociación explícita, ver Roadmap (SRV-ADR-012, SRV-ADR-019).** |
| Sprint 19 — Editor de Mimics (React Flow / SRV-ADR-008) | 2026-07-30 → 2026-07-30 | ✅ Completo | 4 commits. @xyflow/react. MimicsEditorPage: canvas, 7 nodos personalizados, toolbar drag-and-drop, panel de propiedades, auto-save 30s. MimicsViewerPage tiempo real. |
| Sprint 20 — Observabilidad (Prometheus + Grafana + ai_usage_log) | 2026-07-31 → 2026-07-31 | ✅ Completo | 4 commits. docker-compose: prometheus + grafana + exporters + dashboards provisionados. /metrics vía instrumentator. Migration 0015 (ai_usage_log). Router /ai-usage. |
| Sprint 21 — Sesión de Ingeniería Remota (SRV-ADR-016) | 2026-07-31 → 2026-07-31 | ✅ Completo | 4 commits. Migration 0016 (engineering_sessions). Router /engineering-sessions: 4 endpoints con RBAC. Celery beat expire_engineering_sessions cada 30s. Hook + banner en Shell. |
| Sprint 22 — Backup L2 | 2026-07-31 → 2026-08-03 | ✅ Completo | 3 bugs corregidos en T-187 (commit `9da8c4a`): `postgresql-client` faltaba en `backend/Dockerfile` (pg_dump no disponible), `extra={"filename": ...}` colisionaba con atributo reservado de `LogRecord` en el logger, volumen `backups_data` faltaba en el servicio `celery-alarm`. Aplicado `alembic stamp 0016` + `upgrade head` para alinear la BD. T-187.1 a T-187.8 todos ✅ |
| Sprint 23 — Separación de layouts Server/Studio | 2026-07-30 (planeado, no ejecutado) | ❌ Cancelado — superado por SRV-ADR-015 | Este sprint iba a construir `ServerShell`/`StudioShell` como experiencias de UI completamente independientes con árboles de rutas separados (`/server/*` y `/studio/*`) y una página de selección de modo. Ese diseño quedó superado el 2026-07-31 al corregir SRV-ADR-015: Hira Server y Hira Studio son un solo producto — Studio es el conjunto de herramientas de ingeniería accesible con credenciales de integrador dentro de la misma instancia, no una experiencia aislada con su propio árbol de rutas. Este sprint no se ejecuta. Ver Roadmap para el sprint de reconciliación que lo reemplaza. |

---

## Deuda Arquitectural

### DA-001 — Dashboard propio por producto (Studio vs Server) — ✅ Resuelto Sprint 15

### DA-002 — Reconciliar separación Server/Studio (Sprint 10c) con el modelo de un solo producto (SRV-ADR-015)

**Estado:** 🟢 Diagnosticada (T-189, 2026-08-03) — complejidad BAJA, resuelta en Sprint 24

**Diagnóstico real (auditoría T-189, `git grep` sobre el frontend):**

- **El modelo viejo de "dos shells separados" nunca se implementó.** Sin resultados para `ServerShell`, `StudioShell`, `ModeSelector`, ni para rutas `/server/*` o `/studio/*` como árbol separado. No hay deuda de desmontaje — SRV-ADR-015 nunca llegó a contradecirse en código.
- **La causa real es otra:** `App.tsx` ya define todas las rutas correctamente bajo una sola app (`AdminRoute`/`OperadorRoute`/`ProtectedRoute`), pero `Sidebar.tsx` (líneas 193-200) solo expone 8 ítems, **visibles para todos los roles**, y nunca implementó la ocultación condicional por rol que exige SRV-ADR-UI-02. Los módulos de Admin/Integrador existen en código y son alcanzables por URL, pero no aparecen en la navegación.
- **Ítems ausentes del sidebar:** Configurador (`/config`), Motor de Lógica (`/logic`), Motor de Pruebas (`/tests`), AI Integrador (`/ai/integrador`), Studio Dashboard (`/studio/dashboard`), Documentación (`/docs`), Notificaciones (`/studio/notifications`), Studio Mimics (`/studio/mimics`).
- **Nota menor, no bloqueante:** naming inconsistente — algunos ítems de Admin usan prefijo `studio/` y otros no. Es cosmético, no separación de árbol; no forma parte del alcance de Sprint 24.

Ver tareas concretas en Roadmap, Sprint 24.

### DA-003 — Modelo de puntos candidatos y asociación explícita (SRV-ADR-012, SRV-ADR-019) no implementado

**Estado:** 🔴 Abierto

**Descripción:** el escaneo de dispositivos (Sprint 18) hoy escribe directamente en `points` con `device_id`. El diseño vigente (`.harness/spec/hira-server/modules/modelo-de-datos.md`) requiere una tabla intermedia `device_points_candidates` y que cada punto usable en línea exista como asociación explícita en `points` con `access_mode` y, si es BACnet, `bacnet_write_priority`. Esto es una migración de esquema y de lógica en `scan_service.py`, los routers de `/devices` y `/points`, y el frontend del Configurador.

### DA-004 — Licenciamiento por puntos en línea (SRV-ADR-018) y multi-proyecto (SRV-ADR-020) no implementados

**Estado:** 🔴 Abierto

**Descripción:** el modelo de licencia actual no distingue tipo de licencia (integrador/comercial) ni limita puntos en línea — VUL-SRV-014 quedó "resuelto por rediseño" a nivel de diseño, pero el mecanismo real (tope de puntos en línea) no está en el código. Tampoco existe la tabla `projects` ni el alcance `project`/`global` en roles. Ambos son prerequisito para que una instalación local del integrador soporte multi-proyecto de forma segura.

---

## Roadmap

| Sprint | Contenido | Origen en diseño |
|---|---|---|
| DA-003 | Modelo de puntos candidatos / asociación explícita | SRV-ADR-012, SRV-ADR-019, `.harness/spec/hira-server/modules/modelo-de-datos.md`, `.harness/spec/hira-server/modules/dispositivos-protocolos-puntos.md` |
| DA-004 | Licenciamiento por puntos en línea + multi-proyecto | SRV-ADR-018, SRV-ADR-020, `.harness/spec/hira-server/modules/modelo-de-datos.md` |

DA-001 y DA-002 eran deudas *de la implementación previa* (dashboard por producto; sidebar
por rol) — no aplican al empezar de cero, porque la nueva implementación sigue el diseño
vigente desde el primer sprint. **DA-003 y DA-004 sí siguen vigentes** como requisitos y se
anclan en `.harness/anchors/registry.yaml`.

---

## Roadmap del ecosistema

El roadmap forward-looking (tracks SRV / HUB / STU y sus dependencias) vive en
`.harness/coordination/ROADMAP.md`. El sprint activo, en `.harness/coordination/SPRINT.md`.
