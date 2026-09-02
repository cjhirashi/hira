---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.1 - Stack Tecnológico y Diagrama de Componentes.md"
título: Stack Tecnológico y Diagrama de Componentes — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-08-03
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, stack, componentes]
---

## Stack Tecnológico

| Componente | Tecnología | Versión | Justificación |
|---|---|---|---|
| Backend framework | FastAPI | Latest stable | Asíncrono, WebSocket nativo, ecosistema Python completo |
| Comunicación BACnet | BAC0 | Latest stable | Librería más madura para BACnet en Python, soporta IP y MSTP |
| Comunicación Modbus | pymodbus | Latest stable | Estándar de facto para Modbus TCP/RTU en Python |
| Comunicación MQTT | paho-mqtt | Latest stable | Librería oficial Eclipse para MQTT client |
| MQTT Broker | Mosquitto | Latest stable | Broker MQTT ligero, contenedor dedicado en Docker Compose |
| Base de datos (instancia comercial) | PostgreSQL + TimescaleDB + pgvector | 16+ | Relacional + series de tiempo + vectores RAG — un solo motor, tres extensiones |
| Base de datos (instancia local del integrador) | SQLite | Latest stable | Mismo esquema relacional, sin TimescaleDB — ver SRV-ADR-017 |
| Cache / Pub-Sub | Redis | 7+ | Bus de datos en tiempo real, bloqueo de puntos, estado de alarmas |
| Tareas background | Celery + Redis | Latest stable | Colas `high` (pruebas) y `normal` (lógica), polling, alarmas, reportes |
| Métricas | Prometheus + prometheus_client | Latest stable | Recolección de métricas del sistema, dispositivos y agentes IA — expuesto en `/metrics` |
| Dashboards | Grafana | Latest stable | Visualización de métricas, embebible en panel admin vía iframe, datasource Prometheus |
| DB metrics | postgres_exporter + redis_exporter | Latest stable | Exportan métricas internas de PostgreSQL y Redis a Prometheus |
| Sandboxing de scripts | RestrictedPython | Latest stable | Ejecución segura de scripts Python del integrador — acceso solo a API interna de Hira |
| Editor de código | Monaco Editor | Latest stable | Editor Python embebido en panel admin, mismo motor que VS Code |
| Frontend framework | React + TypeScript | 18+ | Componentes reutilizables, tipado estricto |
| Build tool | Vite | Latest stable | Compilación rápida, HMR en desarrollo |
| Estilos | Tailwind CSS | 3+ | Utilitario, consistente, sin CSS externo |
| Editor visual | React Flow | Latest stable | Canvas drag-and-drop para mimics, diagramas de conexionado y futuro FBD |
| Gráficos de equipos | SVG animado + React | — | Componentes React con SVG animado enlazados a puntos en tiempo real |
| Gráficas de tendencias | Plotly.js | Latest stable | Gráficas interactivas 100% local, sin CDN |
| Tiempo real cliente | Socket.io | Latest stable | WebSocket bidireccional para datos y alarmas en tiempo real |
| IA — orquestación | LangChain | Latest stable | Dos instancias: Agente Integrador + Agente Cliente |
| IA — modelos externos | Claude API · OpenAI API · Ollama externo | — | Configurable por instancia; el sistema opera sin ninguno activo |
| IA — modelo interno (fallback) | Ollama embebido | `llama3.2:3b` por defecto | Contenedor incluido siempre en el compose, sin configuración — cubre la ausencia de modelo externo (ver SRV-ADR-021) |
| RAG — embeddings | LangChain + pgvector | — | Indexación y búsqueda semántica sobre documentación del proyecto |
| Infraestructura | Docker + Docker Compose | Latest stable | Mismo compose en Linux (Docker Engine) y Windows (Docker Desktop + WSL2) |
| Reverse proxy | Nginx | Latest stable | Sirve frontend estático, proxy al backend, terminación SSL |
| Licenciamiento | Python backend custom | — | License key atada a hardware (MAC address + hostname); valida puntos en línea contra tier (ver SRV-ADR-018) |
| Control de acceso | RBAC dinámico en base de datos | — | Roles y permisos configurables: módulos, áreas, tipo de acceso; alcance por proyecto o global según tipo de usuario (ver SRV-ADR-020) |

---

## Diagrama de Componentes (C4 L3)

```mermaid
flowchart TB
    subgraph FE["Frontend — React + TypeScript"]
        UI_DASH[Dashboard\nMimics SVG animados\nPaneles de control]
        UI_ALARM[Gestor de Alarmas\nListado · Reconocimiento]
        UI_HIST[Históricos\nPlotly.js tendencias]
        UI_LOGIC[Motor de Lógica\nMonaco Editor Python]
        UI_TEST[Motor de Pruebas\nMonaco Editor Python]
        UI_ANAL[Análisis\nResultados · Reportes]
        UI_DOC[Documentación\nConsulta por rol]
        UI_CONF[Configurador\nDispositivos · Puntos\nMimics · Roles]
        UI_AI_INT[Agente IA — Integrador\nChat + asistencia de construcción\nExterno o interno — SRV-ADR-021]
        UI_AI_CLI[Agente IA — Cliente\nChat + operación en lenguaje natural\nExterno o interno — SRV-ADR-021]
    end

    subgraph API["Backend — FastAPI"]
        RT_AUTH[/auth — JWT\nLogin · Refresh · Logout/]
        RT_DEV[/devices — Dispositivos\nCRUD · Escaneo de red/]
        RT_PTS[/points — Puntos\nCandidatos · Asociación · Lectura · Escritura · Suscripción/]
        RT_ALM[/alarms — Alarmas\nEstado · Reconocimiento · Histórico/]
        RT_HIST[/historicals — Históricos\nConsulta por rango · Agregaciones/]
        RT_LOGIC[/logic — Scripts de lógica\nCRUD · Start · Stop · Estado/]
        RT_TEST[/tests — Scripts de prueba\nCRUD · Ejecutar · Resultados/]
        RT_ANAL[/analysis — Análisis\nConsulta · Exportar PDF/CSV/]
        RT_DOC[/documentation — Documentación\nCRUD · Búsqueda · Embeddings/]
        RT_USR[/users — Usuarios y Roles\nCRUD · RBAC/]
        RT_AI[/ai — Agente IA\nChat · Configurar API key/]
        RT_LIC[/license — Licencia\nValidar · Estado · Puntos en línea/]
        RT_ENG[/engineering — Sesión de ingeniería remota\nADR-016/]
        WS[WebSocket /ws\nDatos tiempo real · Alarmas]
    end

    subgraph WORKERS["Celery Workers"]
        W_POLL[Worker: Polling\nBACnet · Modbus · MQTT\nSolo puntos asociados — publica a Redis]
        W_ALARM[Worker: Motor Alarmas\nEvalúa condiciones\nCelery Beat]
        W_LOGIC[Worker: Lógica Continua\nCola NORMAL\nRestrictedPython sandbox]
        W_TEST[Worker: Pruebas\nCola HIGH\nLocks en Redis]
        W_DOC[Worker: Documentación\nParser AST · Embeddings]
        W_REPORT[Worker: Reportes\nGeneración PDF/CSV]
    end

    subgraph PROTO["Motor de Protocolos"]
        P_BAC[BAC0\nBACnet IP/MSTP\nDiscovery · R/W]
        P_MOD[pymodbus\nModbus TCP/RTU\nScan · R/W]
        P_MQTT[paho-mqtt\nPublish · Subscribe\nWildcard discovery]
    end

    subgraph DB["Datos"]
        PG[(PostgreSQL / SQLite\nUsuarios · Roles · Permisos\nDispositivos · Puntos candidatos y asociados\nAlarmas · Scripts\nDocumentación · Config)]
        TS[(TimescaleDB — solo instancia comercial\nHistóricos — Hypertable\nRetención configurable)]
        VEC[(pgvector — solo instancia comercial\nEmbeddings RAG\nDocumentación indexada)]
        RD[(Redis\nPub/Sub datos\nLocks de puntos\nEstado alarmas\nCelery broker)]
        MQ[Mosquitto\nMQTT Broker]
    end

    FE <-->|REST + WS| API
    API --> WORKERS
    API <--> DB
    WORKERS <--> DB
    WORKERS <--> RD
    W_POLL --> PROTO
    PROTO <-->|Red local| DEV([Dispositivos\nBACnet · Modbus · MQTT])
    P_MQTT <-->|MQTT| MQ
```

`adapters/factory.py` selecciona PostgreSQL o SQLite según `HIRA_DEPLOY_MODE` (ver SRV-ADR-017). El Motor de Protocolos solo hace polling y escritura sobre puntos asociados — nunca sobre candidatos crudos del escaneo (ver SRV-ADR-019).

---

## Gate de Salida

- [x] Stack definido y justificado
- [x] Diagrama de componentes actualizado con puntos candidatos/asociados y sesión de ingeniería
- [x] Modelo IA interno (Ollama embebido, SRV-ADR-021) incorporado al stack
- [ ] Revisado y aprobado por Charlie
