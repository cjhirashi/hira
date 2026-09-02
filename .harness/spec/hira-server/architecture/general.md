---
origen_vault: "7.1 - Hira Server/7.1.3 - Arquitectura/7.1.3.1 - Arquitectura General.md"
título: Arquitectura General — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Arquitectura
fecha_creación: 2026-07-23
última_actualización: 2026-08-03
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, arquitectura]
---

## Descripción del Sistema

**Hira** es un ecosistema de dos productos: **Hira Server/Studio** (un solo producto, un solo instalador — ver SRV-ADR-015) y **Hira Hub** (plataforma cloud).

### Hira Server/Studio

Un solo código base, un solo instalador. Se instala en dos contextos posibles:

- **En la PC del integrador (licencia de integrador):** instancia local, para diseño, demos y trabajo sin depender del cliente. Soporta múltiples proyectos (ver SRV-ADR-020). Puntos en línea limitados a un tope de demo (ver SRV-ADR-018).
- **En el servidor del cliente (licencia comercial):** instancia de producción, un solo proyecto por servidor. Puntos en línea según el tier contratado (Starter/Professional/Enterprise).

**Hira Studio** es la herramienta de diseño e ingeniería sobre los proyectos que viven en un Server — nunca opera aislada, siempre conectada a un Server (local o remoto, ver SRV-ADR-016). El integrador, con sus credenciales, tiene acceso simultáneo a las herramientas operativas (SCADA) y de ingeniería (Studio) dentro de la misma instalación.

### Hira Hub

Componente cloud del ecosistema — VPS en cjhirashi.com. Valida licencias, distribuye actualizaciones, recibe crash reports y en versiones futuras aloja el marketplace de plantillas. No visible para integradores ni clientes. Ver `7.2 - ÍNDICE - Hira Hub` para toda la documentación de Hub.

---

## Diagrama de Contexto (C4 L1) — Ecosistema Hira

```mermaid
flowchart TB
    subgraph DEV["👨‍💻 cjhirashi — Equipo de Desarrollo"]
        A0[Desarrollador]
    end

    subgraph INTEGRADOR["🔧 Integrador"]
        A1[Integrador / Admin]
    end

    subgraph CLIENTE["🏢 Cliente Final"]
        A2[Operador]
        A3[Técnico]
        A4[Supervisor]
    end

    subgraph LOCAL["🟩 Hira Server/Studio — Instalación local del integrador (licencia integrador)"]
        ST["Multi-proyecto · Puntos en línea limitados (demo)\nHerramientas de Studio + SCADA en la misma instancia"]
    end

    subgraph SERVER["🟦 Hira Server/Studio — Servidor del cliente (licencia comercial)"]
        SV["Un solo proyecto · SCADA producción\nHerramientas de Studio integradas, accesibles con credenciales de integrador\nPuntos en línea según tier de licencia"]
    end

    subgraph HUB["☁️ Hira Hub — VPS cjhirashi.com (NUBE)"]
        HB[Licencias · Actualizaciones\nBloques Visuales · Crash Reports]
    end

    subgraph RED_CLIENTE["Red Local del Cliente (LOCAL)"]
        D1[BACnet — HVAC / Controladores]
        D2[Modbus — Variadores / Medidores]
        D3[MQTT — IoT / Sensores]
    end

    subgraph RED_INTEGRADOR["Red del Integrador — Banco de Pruebas (LOCAL)"]
        T1[Controladores reales\nBACnet · Modbus · MQTT]
    end

    subgraph IA_EXT["IA Externa — Internet (opcional)"]
        I1[Claude API / OpenAI]
    end

    A0 -->|Administra| HB
    A1 -->|"Diseño local, demos, multi-proyecto"| LOCAL
    A1 -->|"SCADA + Studio en la misma instancia\n(con credenciales de integrador)"| SV
    A2 & A3 & A4 -->|"Solo SCADA operativo"| SV

    LOCAL -->|"Conexión remota — sesión de ingeniería\n(Studio como cliente, SRV-ADR-016)"| SV
    LOCAL -->|"Exportación .hira opcional\n(migración/respaldo)"| SV
    SV -->|Valida licencia| HB
    SV -->|Recibe actualizaciones\ny bloques| HB
    SV -->|Envía crash reports| HB
    LOCAL -->|Envía crash reports| HB

    SV <-->|BACnet IP / MSTP| D1
    SV <-->|Modbus TCP / RTU| D2
    SV <-->|MQTT Pub/Sub| D3

    LOCAL <-->|"Banco de pruebas — 1 controlador activo máx (SRV-ADR-018)"| T1

    SV <-->|Módulo IA — internet, opcional| I1
    LOCAL <-->|Agente del Integrador — opcional| I1

    note1["Ambas instalaciones incluyen su propio\nmodelo IA interno (Ollama embebido, SRV-ADR-021)\ncomo fallback cuando no hay IA externa"]
```

Cada instalación (local o servidor) incluye siempre su propio contenedor Ollama embebido como fallback — no depende de `IA_EXT` para operar con asistencia IA básica (ver SRV-ADR-021 y diagrama de contenedores abajo).

---

## Diagrama de Contenedores (C4 L2)

```mermaid
flowchart TB
    subgraph Docker["Docker Compose — Instancia Hira Server/Studio"]

        subgraph FE["Frontend"]
            UI[React + TypeScript\nVite · Tailwind · React Flow\nPlotly.js · Monaco Editor\nSocket.io client]
        end

        subgraph GW["Gateway"]
            NX[Nginx\nReverse proxy]
        end

        subgraph BE["Backend"]
            API[FastAPI\nREST API + WebSocket]
            PROTO[Motor de Protocolos\nBAC0 · pymodbus · paho-mqtt]
            LOGIC[Motor de Lógica\nCelery workers\nEjecución de scripts Python]
            ALARM[Motor de Alarmas\nEvaluación continua\nCelery beat]
            AI[Agente IA\nLangChain · Tools de Hira\nExterno opcional + interno siempre disponible]
        end

        subgraph DATA["Datos"]
            PG[(PostgreSQL + TimescaleDB + pgvector\nInstancia comercial\nConfiguración · Usuarios · Alarmas · Históricos · RAG)]
            SQ[(SQLite\nInstancia local ligera del integrador\nmismo esquema, sin TimescaleDB)]
            RD[(Redis\nPub/Sub · Cache\nEstado en tiempo real\nPoint locks con TTL)]
            MQ[Mosquitto\nMQTT Broker]
        end

        subgraph LOCALAI["IA Local — siempre presente"]
            OLLAMA[Ollama\nModelo embebido — llama3.2:3b por defecto\nADR-021]
        end

        subgraph OBS["Observabilidad"]
            PROM[Prometheus\nRecolección de métricas]
            GRAF[Grafana\nDashboards embebidos\nen panel admin]
            EXP[postgres_exporter\nredis_exporter]
        end

    end

    subgraph EXT["Externos"]
        DEV[Dispositivos\nBACnet · Modbus · MQTT]
        LLMS[APIs de IA\nOpcional]
        USR[Usuarios\nNavegador web]
        REMOTO[Studio conectado remoto\nOtra instalación de Hira]
    end

    USR -->|HTTPS| NX
    NX -->|Sirve app| FE
    NX -->|Proxy API| API
    REMOTO -->|"API REST + sesión de ingeniería\n(SRV-ADR-016)"| API

    FE <-->|WebSocket tiempo real| API
    API --> PROTO
    API --> LOGIC
    API --> ALARM
    API --> AI

    PROTO <-->|Lecturas/escrituras| DEV
    PROTO -->|Publica datos| RD
    MQ <-->|MQTT| DEV
    PROTO <-->|Suscribe topics| MQ

    ALARM -->|Lee estado| RD
    ALARM -->|Persiste alarmas| PG
    ALARM -.->|Persiste alarmas — instancia local| SQ
    ALARM -->|Publica alertas| RD

    LOGIC -->|Lee/escribe puntos vía API interna| RD
    LOGIC -->|Registra ejecuciones| PG

    API <-->|Lee/escribe| PG
    API -.->|Lee/escribe — instancia local| SQ
    API <-->|Lee/publica| RD

    AI <-->|Tools: todos los módulos| API
    AI <-->|Calls opcionales, prioridad| LLMS
    AI <-->|Fallback siempre disponible| OLLAMA

    API -->|/metrics endpoint| PROM
    LOGIC -->|métricas de workers| PROM
    EXP -->|métricas BD/cache| PROM
    PROM --> GRAF
    PG -.->|monitorea| EXP
    RD -.->|monitorea| EXP
```

`adapters/factory.py` selecciona PostgreSQL o SQLite según el perfil de despliegue (ver SRV-ADR-017 — Arquitectura Hexagonal). El resto del stack (Redis, Motor de Protocolos, Motor de Lógica, Motor de Alarmas) es idéntico en ambos perfiles.

---

## Módulos del Sistema

| # | Módulo | Descripción |
|---|---|---|
| 1 | **Motor de Protocolos** | Comunicación con dispositivos BACnet, Modbus y MQTT. Polling configurable por punto asociado (ver SRV-ADR-019). Publica lecturas a Redis |
| 2 | **Motor de Alarmas** | Evalúa condiciones de alarma en tiempo real. Gestiona estados (activa, reconocida, resuelta), prioridades y notificaciones |
| 3 | **Históricos** | Almacena series de tiempo en TimescaleDB (o SQLite en instancia local). Configurable por punto: frecuencia, retención, compresión |
| 4 | **Configurador** | Panel admin para definir dispositivos, puntos, mimics gráficos, paneles de control, roles y usuarios sin tocar código |
| 5 | **Motor de Lógica** | Scripts Python de **operación continua** con API interna (`hira.read/write/subscribe`), editados en Monaco Editor. Celery los ejecuta indefinidamente en cola de prioridad normal. Se pausan automáticamente cuando una prueba bloquea sus puntos |
| 6 | **Motor de Pruebas** | Scripts Python de **ejecución única o acotada** para pruebas funcionales y de comisionamiento. Corren en cola Celery de alta prioridad. Bloquean en Redis los puntos que usan |
| 7 | **Módulo de Análisis** | Exploración de históricos, visualización de resultados de pruebas, comparación de comportamientos, generación de reportes PDF/CSV |
| 8 | **Agente IA** | Dos instancias independientes de LangChain (ver SRV-ADR-013): Agente del Integrador (construcción del proyecto) y Agente del Cliente (operación, con RAG sobre documentación). Cada una usa modelo externo si está configurado, o el modelo interno embebido (Ollama, ver SRV-ADR-021) como fallback siempre disponible |
| 9 | **Módulo de Documentación** | Centro de conocimiento técnico del proyecto — consumido por usuarios y por el Agente IA como base RAG (ver SRV-ADR-011) |
| 10 | **Módulo de Monitoreo y Notificaciones** | Métricas operativas del sistema, métricas de agentes IA, y sistema de notificaciones en dos canales (integrador y desarrollador) |
| 11 | **Backup y Portabilidad** | Exportación/importación de paquete `.hira` (opcional, para mover proyectos entre instalaciones — ver SRV-ADR-015), backup automatizado, replicación activo-pasivo |
| 12 | **Gestión de Usuarios** | RBAC dinámico — usuarios de operación por proyecto, usuarios integrador globales a la instancia (ver SRV-ADR-020) |
| 13 | **Licenciamiento** | License key atada al hardware. Distingue licencia de integrador (multi-proyecto, puntos en línea limitados) de licencia comercial (un proyecto, puntos en línea según tier) — ver SRV-ADR-018 |

---

## Gate de Salida

- [x] Arquitectura conceptual validada con el modelo de un solo producto (SRV-ADR-015)
- [x] Diagramas C4 actualizados con el modelo IA interno (SRV-ADR-021)
- [x] Módulos del sistema coherentes con los ADRs vigentes
- [ ] Revisado y aprobado por Charlie
