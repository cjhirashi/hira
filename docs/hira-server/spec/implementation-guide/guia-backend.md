---
origen_vault: "7.1 - Hira Server/7.1.6 - Guías de Implementación/7.1.6.2 - Guía Backend.md"
título: Guía Backend — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Guías de Implementación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, backend, hexagonal]
---

## Estructura del Backend

Aplicación práctica de la Arquitectura Hexagonal (ver SRV-ADR-017):

```
backend/
├── Dockerfile
├── requirements.txt            # Versiones exactas fijadas
├── main.py                     # Entrypoint FastAPI
│
├── core/
│   ├── config.py                # Configuración desde variables de entorno
│   ├── redis.py                 # Conexión Redis (infraestructura fija — no cambia por perfil)
│   ├── security.py              # JWT, bcrypt, verificación de permisos
│   ├── license.py               # Validación de license key (ver SRV-ADR-018)
│   └── ports/                   # [HEXAGONAL] Interfaces abstractas — el núcleo NUNCA importa infra directamente
│       ├── database_port.py     # Protocol: get_session(), execute(), etc.
│       ├── protocol_port.py     # Protocol: connect(), read_point(), write_point(), scan()
│       └── notification_port.py # Protocol: send()
│
├── adapters/                    # [HEXAGONAL] Implementaciones concretas de los puertos
│   ├── factory.py               # Punto único de selección/instanciación de adaptadores concretos (SRV-ADR-017)
│   ├── db/
│   │   └── postgresql_adapter.py   # Implementa DatabasePort — único perfil (`E-ADR-001`)
│   └── protocol/
│       ├── bacnet_adapter.py       # Implementa ProtocolPort — BAC0 (IP y MSTP)
│       ├── modbus_adapter.py       # Implementa ProtocolPort — pymodbus
│       └── mqtt_adapter.py         # Implementa ProtocolPort — paho-mqtt
│
├── routers/                     # Adaptadores primarios — ver .harness/spec/hira-server/modules/apis.md para el contrato completo
│   ├── auth.py
│   ├── projects.py
│   ├── devices.py
│   ├── points.py
│   ├── alarms.py
│   ├── historicals.py
│   ├── logic.py
│   ├── tests.py
│   ├── users.py
│   ├── ai.py
│   ├── backup.py
│   ├── monitor.py
│   ├── license.py
│   └── engineering.py           # Sesión de ingeniería remota — ver SRV-ADR-016
│
├── models/                      # SQLAlchemy ORM models
├── schemas/                     # Pydantic schemas (request/response)
│
├── services/                    # Lógica de negocio — importa solo de core/ports/, nunca de adapters/
│   ├── simulators/
│   │   ├── simulator_manager.py    # Gestiona instancias activas de simuladores
│   │   ├── bacnet_sim.py           # BAC0 device virtual con puntos y patrones configurables
│   │   ├── modbus_sim.py           # pymodbus server con registros configurables
│   │   └── mqtt_sim.py             # Publica a Mosquitto con payload/topic/frecuencia conf.
│   ├── point_association_service.py  # Asocia candidatos de escaneo a puntos Hira (SRV-ADR-012, SRV-ADR-019)
│   ├── alarm_engine.py             # Evaluación de condiciones
│   ├── logic_engine.py             # RestrictedPython sandbox + hira API — ver .harness/spec/hira-server/modules/motor-logica-y-pruebas.md
│   ├── hira_api.py                 # API interna que expone hira.read/write/subscribe
│   ├── ai_agent.py                 # LangChain — Agente Integrador y Agente Cliente
│   ├── engineering_session_service.py  # Lock de sesión de ingeniería remota (SRV-ADR-016)
│   └── backup_service.py           # Exportar/importar paquete .hira
│
├── workers/
│   ├── celery_app.py            # Configuración Celery + colas (normal, high)
│   ├── polling_worker.py        # Polling de puntos asociados
│   ├── alarm_worker.py          # Evaluación periódica de alarmas
│   └── logic_worker.py          # Ejecución de scripts de lógica y pruebas
│
└── websocket/
    └── manager.py                # Gestión de conexiones WebSocket
```

**Regla de oro:** `services/` solo importa de `core/ports/`. Nunca de `adapters/` directamente. `adapters/factory.py` es el punto único de instanciación de la implementación concreta (un solo perfil de despliegue, `E-ADR-001` — sin `HIRA_DEPLOY_MODE`).

## Integración entre Módulos

### Flujo de datos principal

```
Adaptador de protocolo (lectura de punto asociado) → Redis pub/sub → WebSocket manager → Frontend
                                                                    → Alarm worker (evaluación)
                                                                    → TimescaleDB writer (histórico)
                                                                    → Logic worker (hira.read())
```

### Comunicación Agente IA ↔ sistema

```
Chat frontend → POST /ai/integrator/chat (o /ai/client/chat)
    → LangChain Agent
    → RAG (Agente Cliente) o contexto directo (Agente Integrador) — ver .harness/spec/hira-server/modules/agente-ia.md
    → Tool call → endpoint interno correspondiente (ej. GET /points/{id}/value)
    → Toda escritura respeta RBAC + access_mode del punto (SRV-ADR-019)
    → Respuesta al frontend con texto + acciones ejecutadas
```

### Sincronización de estado de scripts de lógica

```
Frontend → POST /logic/scripts/{id}/start
    → FastAPI → Celery: cola normal, tarea run_logic_script
    → Worker carga script de la base de datos
    → RestrictedPython sandbox ejecuta ciclo
    → Log de ejecución → script_executions
    → Estado visible en frontend vía polling GET /logic/scripts/{id}
```

## Decisiones de Implementación

### Alembic para migraciones

Alembic es el ORM de migraciones estándar para SQLAlchemy. Genera scripts de migración versionados — permite actualizar el esquema entre versiones de Hira sin perder datos. Crítico para instalaciones on-premise donde no se puede recrear la base de datos.

### Simuladores como parte del `services/`, no del entorno de desarrollo

Los simuladores no son una herramienta de desarrollo interno — son una funcionalidad del producto (ver SRV-ADR-014). `SimulatorService` vive junto a los demás servicios de negocio y los simuladores se almacenan como cualquier otro dispositivo (`devices.is_simulator = true`). El Motor de Protocolos los trata exactamente igual que hardware real.

---

## Cambio de infraestructura pendiente — Nginx → Caddy (2026-08-12)

Hira Server actualmente usa Nginx como reverse proxy propio. Con la definición de la infraestructura compartida del servidor de Charlie (`~/infraestructura/`), **Nginx debe eliminarse del docker-compose de Hira Server** y ser reemplazado por el Caddy global que gestiona todos los proyectos del servidor.

**Cambios requeridos en Hira Server:**
- Eliminar el servicio `nginx` (o equivalente) del `docker-compose.yml`
- Exponer el backend solo en red Docker interna (sin mapeo de puertos al host)
- Registrar el subdominio de Hira Server en el `Caddyfile` de infraestructura
- Caddy gestiona Let's Encrypt automáticamente — no se requiere certbot

Referencia: `1.1.6.2 - Entorno de Desarrollo` del proyecto Synapse documenta la arquitectura de infraestructura compartida.

## Gate de Salida

- [x] Estructura de backend detallada, aplicando Arquitectura Hexagonal (SRV-ADR-017)
- [x] Integración entre módulos documentada
- [x] Decisiones de implementación específicas documentadas
- [ ] Revisado y aprobado por Charlie
- [ ] Pendiente: eliminar Nginx del compose y migrar a Caddy global (infraestructura compartida)
