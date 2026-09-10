---
título: Diseño heredado de Hira Server — Hira Studio
componente: hira-studio
tipo: Índice de herencia
status: borrador
última_actualización: 2026-09-02
---

Bajo el diseño previo (`SRV-ADR-015`), las herramientas de ingeniería vivían dentro de
Hira Server. Con `E-ADR-001` pasan a Hira Studio (cloud). Este índice marca qué
especificación de `spec/hira-server/` es **fuente de diseño para Studio** y qué queda en
Server.

## Migra a Studio (herramientas de ingeniería)

| Tema | Doc de origen (Server) | Notas para Studio |
|---|---|---|
| Configurador (áreas, dispositivos, escaneo, asociación de puntos) | `spec/hira-server/modules/dispositivos-protocolos-puntos.md`, `spec/hira-server/ui-ux/especificacion-de-vistas.md` | La UI del configurador es de Studio; los datos se escriben en el Server destino vía sesión de ingeniería. `SRV-ADR-012`, `SRV-ADR-019` siguen rigiendo el modelo candidato→asociación. |
| Motor de Lógica (edición de scripts) | `spec/hira-server/modules/motor-logica-y-pruebas.md`, `SRV-ADR-007`, `SRV-ADR-UI-04` | Studio edita los scripts (Monaco). **La ejecución continua sigue en Server** (Celery cola `normal`). Falta decidir: ¿Studio empuja el script al Server y este lo corre? (ver OPEN-QUESTIONS). |
| Motor de Pruebas | `spec/hira-server/modules/motor-logica-y-pruebas.md`, `SRV-ADR-009` | Igual que lógica: se edita en Studio, se ejecuta contra el Server (cola `high`, locks Redis por punto). |
| Editor de Mimics | `SRV-ADR-008`, `spec/hira-server/ui-ux/especificacion-de-vistas.md` | Editor React Flow en Studio; el viewer en tiempo real es de Server (operadores). |
| Agente del Integrador | `spec/hira-server/modules/agente-ia.md`, `SRV-ADR-013`, `SRV-ADR-021` | Asistente de construcción. Falta decidir dónde corre (Studio propio vs proxy al Server). El Agente del **Cliente** se queda en Server. |
| Simuladores | `SRV-ADR-014` | El integrador diseña con simuladores. Los simuladores son entidades del Server (tabla `devices`); Studio los configura vía sesión de ingeniería. |
| Documentación / auto-doc / RAG de construcción | `SRV-ADR-010`, `SRV-ADR-011` | La generación de documentación desde código y config es una herramienta de ingeniería. El RAG del Agente del Cliente se queda en Server. |
| Exportación/importación `.hira` y plantillas `.hirat` | `spec/hira-server/modules/backup-y-portabilidad.md`, `VUL-SRV-015` | Studio orquesta export/import entre Servers y (v0.3) publica/consume `.hirat` del marketplace de Hub. |
| Biblioteca de proyectos (multi-proyecto) | `SRV-ADR-020` | Multi-proyecto era de la instalación local del integrador. En el modelo cloud, Studio lista los Servers/proyectos a los que el integrador tiene acceso. Falta rediseñar (OPEN-QUESTIONS). |

## Se queda en Hira Server (runtime on-premise)

- Motor de Protocolos (BACnet/Modbus/MQTT), Motor de Alarmas, Históricos (TimescaleDB),
  ejecución de lógica y pruebas, WebSocket de tiempo real, Dashboard operativo, Agente del
  Cliente + su RAG, Backup L1/L2/L3, licenciamiento por puntos en línea, RBAC de operación.
- Ver `spec/hira-server/architecture/general.md` (tabla de módulos).

## Contratos que median entre Studio y el resto

- `CT-engineering-session` — Studio ↔ Server (deriva de `SRV-ADR-016`).
- `CT-license`, `CT-crash-report` — Studio → Hub (`product: studio`).
- `CT-marketplace` — Studio ↔ Hub (v0.3).
