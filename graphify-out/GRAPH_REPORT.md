# Graph Report - hira  (2026-10-23)

## Corpus Check
- 356 files · ~509,631 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 6, .ini 3, .conf 3)

## Summary
- 3948 nodes · 6888 edges · 302 communities (233 shown, 69 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 1155 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e710bc20`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- DeviceRepositoryPort
- test_simulators_router.py
- test_simulator_service.py
- test_device_scan_service.py
- UserRepositoryPort
- SimulatorRegistryService
- LocalPermissionsCache
- test_rbac_dependencies.py
- Tareas Pendientes
- test_devices_router.py
- hira-studio/spec/context.md
- login
- spec_checksum.py
- RedisAdapter
- json
- PostgresAdapter
- test_devices_scan_e2e.py
- hira-server/backend/adapters/factory.py
- modbus_simulator_adapter.py
- E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md
- PostgreSQLUserRepository
- test_cache_port_contract.py
- ui-ux.md
- uuid
- LocalPermissionsCache
- decode_token
- env.py
- vision.md
- BAC0Adapter
- test_auth_security.py
- test_device_repository_adapter.py
- DeviceRecord
- scan_modbus
- routers/auth.py
- hira-server/backend/tests/test_health_service.py
- ModbusRegisterReading
- resolve_permissions
- test_bacnet_address.py
- test_authentication_middleware.py
- Bitácora del arnés — ecosistema Hira
- UserRecord
- auth_service.py
- PLAN-HUB-001 · Walking Skeleton de Hira Hub
- asyncio
- start_mqtt_simulator
- test_main_lifespan.py
- hira-hub/backend/tests/test_health_service.py
- BacnetTransportPort
- start_bacnet_simulator
- test_simulators_e2e.py
- test_rbac_latency.py
- hash_password
- _FakeDeviceRepository
- MqttPublisherAdapter
- mosquitto_adapter.py
- hira-server/spec/context.md
- Proceso SDD-Anchored
- hira-server/backend/core/middleware.py
- Instalación de Hira Server/Studio
- Registro Activo
- can_access_project
- CachePort
- test_auth_router.py
- hira-hub/backend/tests/test_correlation_id.py
- operation.md
- Tareas
- scan_bacnet
- MqttScanAdapter
- BacnetSimulatorAdapter
- detailed-design.md
- Método del arnés — `.harness/`
- pytest
- ProblemDetail
- PLAN-NNN · ‹Nombre›
- Ecosistema Hira — instrucciones base
- README.md
- hira-hub/backend/adapters/factory.py
- 9. Implementación por requisito
- Tareas
- AuthenticatedUser
- topic_instance_key
- Tareas
- _ExplodingCache
- hira-server/backend/routers/monitor.py
- mosquitto_adapter.py
- deployment.md
- modelo-de-datos.md
- acceptance-criteria.md
- Decisión
- harness
- SPRINT.md
- can_access_project
- BacnetDeviceAnnouncement
- hira-hub/backend/services/health_service.py
- hira-server/backend/services/health_service.py
- hira-server/spec/improvements.md
- Runbooks
- Constitución — ecosistema Hira
- ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)
- PostgreSQLUserRepository
- hira-hub/backend/routers/monitor.py
- Stakeholders del Proyecto
- Registro Activo
- Tareas
- Tareas
- AGENTS.md — mapa del ecosistema Hira
- hira-server/backend/tests/test_correlation_id.py
- dev-guide.md
- hira-hub/spec/improvements.md
- SPEC-HUB-001 · Walking Skeleton de Hira Hub
- PLAN-SRV-001 · Walking Skeleton de Hira Server
- SPEC-SRV-001 · Walking Skeleton de Hira Server
- SPEC-SRV-002 · Autenticación y RBAC (MVP — 3 roles fijos)
- SPEC-SRV-003 · Adaptador BACnet — escaneo y candidatos
- Tareas
- SPEC-SRV-004 · Adaptador Modbus — escaneo y candidatos
- Tareas
- SPEC-SRV-005 · Escaneo MQTT — suscripción wildcard y candidatos
- _FakeCache
- SPEC-NNN · ‹Nombre de la funcionalidad›
- _CountingCachePort
- hira-server/backend/tests/test_config.py
- _FakeModbusSimulatorPort
- hira-hub/spec/portfolio.md
- guia-backend.md
- Proceso de Respuesta
- hira-server/spec/portfolio.md
- Sistema de Diseño Visual
- check.sh
- SPEC-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT)
- hira-hub/backend/core/config.py
- _FakeMqttPublisherPort
- asyncio
- _FakeCache
- _FakeCache
- _FakeCache
- BacnetSimulatedObjectSpec
- Catálogo de Incidencias Conocidas
- dispositivos-protocolos-puntos.md
- especificacion-de-vistas.md
- test-plan.md
- Decisión
- Especialistas (F0 — se ajustan al avanzar)
- Adaptadores de entrada
- _FakeCache
- fastapi_testclient
- hira-hub/spec/context.md
- Atributos de Calidad
- flujos-de-datos.md
- monitoreo-y-notificaciones.md
- Deuda Arquitectural
- Overlay — `hira-hub/`
- Overlay — `hira-server/`
- Overlay — `hira-studio/`
- 2. Arquitectura de la feature *(Hexagonal)*
- CorrelationIdMiddleware
- list_device_candidates
- HUB-ADR-06-propiedad-y-vinculacion-de-proyectos.md
- general.md
- estructura-de-repositorio.md
- agente-ia.md
- auth-rbac-seguridad.md
- operacion-cliente-y-soporte.md
- STU-ADR-002-identidad-y-licencia.md
- CorrelationIdMiddleware
- Overlay — `hira-server/`
- §3 · Flujo de 5 fases (carril SDD)
- _FakeCache
- Overlay — `hira-server/`
- experto-ux-ui.md
- E-ADR-001-studio-producto-cloud-independiente.md
- E-ADR-003-convencion-rfc9457-type.md
- validation.md
- postmortems-y-aprendizaje.md
- navegacion-y-responsividad.md
- Anclas y `registry.yaml`
- Módulo `<nombre>`
- sprint.md
- Ecosistema Hira — instrucciones base
- ADR-000 · ‹Título de la decisión›
- ADR-004 · Refresco de rutas post-`ADR-001` y retiro de `MODULE.md`
- typing
- DatabasePort
- RedisAdapter
- _build_app
- _Subscriber
- Hira
- Glosario
- guia-frontend.md
- backup-y-portabilidad.md
- flujos-criticos-de-usuario.md
- ADR-002 · Forzar la Fase 1 y el gate automático (corrección de diseño del arnés)
- ADR-003 · Especialista de UX/UI en el arnés
- §7 · Gates 0–4 (checklists de revisión)
- _FakeUserRepository
- _FakeUserRepository
- _FakeUserRepository
- hira-server/backend/tests/test_health_policy.py
- hira-hub/backend/tests/test_health_policy.py
- implementador.md
- orquestador.md
- .claude/agents/ — binding de Claude Code
- HUB-ADR-01-mismo-stack-que-server.md
- HUB-ADR-02-license-keys-opacas-hash.md
- HUB-ADR-03-grace-period-72h.md
- HUB-ADR-04-crash-reports-opt-in-sanitizados.md
- SRV-ADR-001-despliegue-on-premise.md
- SRV-ADR-002-python-backend-unico.md
- SRV-ADR-003-redis-bus-tiempo-real.md
- SRV-ADR-004-timescaledb-series-de-tiempo.md
- SRV-ADR-005-rbac-dinamico.md
- SRV-ADR-006-modulo-ia-desacoplado-opcional.md
- SRV-ADR-007-motor-logica-python-monaco.md
- SRV-ADR-008-react-flow-mimics.md
- SRV-ADR-009-dos-capas-ejecucion-python.md
- SRV-ADR-010-auto-documentacion.md
- SRV-ADR-011-documentacion-base-rag.md
- SRV-ADR-012-escaneo-asociacion-explicita-puntos.md
- SRV-ADR-013-dos-agentes-ia-por-stakeholder.md
- SRV-ADR-014-simuladores-primera-clase.md
- SRV-ADR-015-un-solo-producto-server-studio.md
- SRV-ADR-016-sesion-ingenieria-remota.md
- SRV-ADR-018-licenciamiento-puntos-en-linea.md
- SRV-ADR-019-puntos-variables-unificadas.md
- SRV-ADR-020-multiproyecto-licencia-integrador.md
- SRV-ADR-021-modelo-ia-interno-ollama.md
- SRV-ADR-UI-01-material-design-3.md
- SRV-ADR-UI-02-sidebar-oculta-modulos.md
- SRV-ADR-UI-03-tiempo-real-sin-polling.md
- SRV-ADR-UI-04-monaco-editor.md
- apis.md
- motor-logica-y-pruebas.md
- STU-ADR-005-agente-integrador-en-studio.md
- architecture.md
- Migración vault → harness (F0)
- adr.md
- TASKS-NNN · ‹Nombre›
- DeviceCandidateRecord
- test_device_repository_adapter.py
- arquitecto.md
- autor-de-spec.md
- hira-alarmas
- hira-auth
- hira-backup
- hira-contratos
- hira-datos
- hira-frontend
- hira-ia
- hira-infra
- hira-licencia
- hira-logica
- hira-protocolos
- hira-qa
- hira-tiempo-real
- hub-licencias
- hub-reports
- alarmas-historicos.md
- stack-y-componentes.md
- `.harness/`
- docs/ — documentación del producto (ecosistema Hira)
- _AlwaysFailsDeviceRepository
- backend
- conftest.py
- Fronteras de salida
- mosquitto
- revisor.md
- `docs/contracts/`
- casos-de-uso-criticos.md
- run_all.sh
- alembic
- _reset_notification_port_singleton
- explorador.md
- deviation.md
- requirement.md
- session-report.md
- hira-hub-bitacora.md
- hira-server-bitacora.md
- project.sh
- specs/README.md
- hira-hub/backend/adapters/README.md
- hira-hub/backend/core/README.md
- hira-hub/backend/models/README.md
- hira-hub/backend/routers/README.md
- hira-hub/backend/schemas/README.md
- hira-hub/backend/services/README.md
- hira-hub/backend/tests/README.md
- hira-hub/docs/README.md
- hira-hub/nginx/README.md
- hira-server/backend/adapters/cache/README.md
- hira-server/backend/models/README.md
- websocket/README.md
- workers/README.md
- hira-server/docs/README.md
- frontend/README.md
- generate_password_file.sh
- hira-server/nginx/README.md
- Ecosistema Hira — instrucciones base
- SRV-ADR-017-arquitectura-hexagonal.md
- _NeverEndingCache

## God Nodes (most connected - your core abstractions)
1. `ProblemDetailError` - 77 edges
2. `SimulatorRegistryService` - 73 edges
3. `UserRecord` - 68 edges
4. `DeviceRepositoryPort` - 66 edges
5. `ModbusRegisterType` - 52 edges
6. `UserRepositoryPort` - 48 edges
7. `DeviceRecord` - 47 edges
8. `LocalPermissionsCache` - 44 edges
9. `PostgreSQLDeviceRepository` - 44 edges
10. `scan_modbus()` - 43 edges

## Surprising Connections (you probably didn't know these)
- `Adaptador de entrada — router` --references--> `SimulatorOut`  [INFERRED]
  .harness/specs/SRV-006-simuladores/tasks.md → hira-server/backend/schemas/simulators.py
- ``hira-hub` — núcleo y adaptadores` --references--> `NotificationPort`  [INFERRED]
  docs/decisions/ecosystem/E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md → hira-server/backend/core/ports/notification_port.py
- `Decisión` --references--> `NotificationPort`  [INFERRED]
  docs/hira-server/decisions/SRV-ADR-017-arquitectura-hexagonal.md → hira-server/backend/core/ports/notification_port.py
- `T-5 — Puertos + factory + adaptadores stub` --references--> `NotificationPort`  [INFERRED]
  docs/planning/SPRINT.md → hira-server/backend/core/ports/notification_port.py
- `Decisión` --references--> `NotificationPort`  [INFERRED]
  .harness/decisions/ADR-001-adopcion-arnes-sdd-anchored.md → hira-server/backend/core/ports/notification_port.py

## Import Cycles
- None detected.

## Communities (302 total, 69 thin omitted)

### Community 0 - "DeviceRepositoryPort"
Cohesion: 0.08
Nodes (22): Adaptadores de entrada, Implementación de RF-002, 3. Modelo de datos y contratos de E/S, Contrato — Contract-First, Puertos, BacnetSimulatorPort, ModbusSimulatedRegisterSpec, ModbusSimulatorPort (+14 more)

### Community 1 - "test_simulators_router.py"
Cohesion: 0.09
Nodes (19): make_client(), _make_user(), test_list_simulators_admin_200(), test_list_simulators_operador_200(), test_list_simulators_visor_403(), test_start_bacnet_simulator_admin_201(), test_start_bacnet_simulator_body_invalido_422(), test_start_bacnet_simulator_object_type_invalido_422() (+11 more)

### Community 2 - "test_simulator_service.py"
Cohesion: 0.05
Nodes (30): ProblemDetailError, _AlwaysFailsBacnetSimulatorPort, _AlwaysFailsModbusSimulatorPort, _AlwaysFailsMqttPublisherPort, _existing_device(), _FakeBacnetSimulatorPort, _FakeDeviceRepository, _FakeModbusSimulatorPort (+22 more)

### Community 3 - "test_device_scan_service.py"
Cohesion: 0.07
Nodes (19): ModbusRegisterReading, _AlwaysFailsModbusDeviceRepository, _AlwaysFailsModbusTransport, _FakeDeviceRepository, _FakeModbusTransport, _FakeMqttTransport, test_scan_bacnet_lectura_de_objetos_con_timeout_no_cuelga_la_respuesta_total(), test_scan_bacnet_nunca_importa_un_puerto_de_puntos_operables() (+11 more)

### Community 4 - "UserRepositoryPort"
Cohesion: 0.09
Nodes (19): Historial de Resoluciones, VUL-SRV-004 — RBAC con query a base de datos en cada request, Implementación de RF-007, Adaptador concreto — integración contra Postgres real, Adaptador de entrada — router, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Coordinación — auth_service, Coordinación — rbac_service (+11 more)

### Community 5 - "SimulatorRegistryService"
Cohesion: 0.09
Nodes (25): 0. Gates de simplicidad, 1. Cumplimiento constitucional, 3. Modelo de datos, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos (tests antes que código), Coordinación (casos de uso / fronteras de entrada), PLAN-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT), Registro de decisiones de diseño (nuevas de este plan) (+17 more)

### Community 6 - "LocalPermissionsCache"
Cohesion: 0.07
Nodes (15): _rbac_cache_key(), _FakeCache, _FakeUserRepository, _make_user(), _QueuePubSubCache, test_invalidacion_cruzada_entre_dos_procesos_via_pubsub(), test_invalidate_permissions_cache_borra_la_entrada(), test_local_cache_ttl_expira_y_vuelve_a_consultar_redis() (+7 more)

### Community 7 - "test_rbac_dependencies.py"
Cohesion: 0.11
Nodes (8): test_admin_permitido_en_escritura_200(), test_admin_permitido_en_recurso_reservado_a_admin_200(), test_operador_bloqueado_en_recurso_reservado_a_admin_403(), test_operador_permitido_en_escritura_200(), test_scope_global_accede_a_cualquier_proyecto_sin_relogin_200(), test_scope_project_cruzando_de_proyecto_403(), test_scope_project_mismo_proyecto_200(), test_visor_bloqueado_en_escritura_403_insufficient_role()

### Community 8 - "Tareas Pendientes"
Cohesion: 0.04
Nodes (43): Historial de Sprints, Notas para Cowork, Sprint Activo, T-00 — Copiar CLAUDE.md al repo (SIEMPRE primero), T-01 — Docker Compose base, T-02 — Logger JSON estructurado, T-03 — Configuración con Pydantic Settings, T-04 — Conexión a PostgreSQL (+35 more)

### Community 9 - "test_devices_router.py"
Cohesion: 0.08
Nodes (19): make_client(), _make_user(), test_list_candidates_de_device_existente_200(), test_list_candidates_de_device_inexistente_404_rfc9457(), test_list_candidates_visor_403(), test_list_devices_admin_200(), test_list_devices_visor_403(), test_scan_bacnet_admin_200_lista_dispositivos_del_escaneo() (+11 more)

### Community 10 - "hira-studio/spec/context.md"
Cohesion: 0.05
Nodes (40): Cómo se conecta, Diseño resuelto (SQ-1..SQ-8), Estado, Quién lo usa, Qué es Hira Studio, Qué NO es, Relación con el resto del ecosistema, Contratos que median entre Studio y el resto (+32 more)

### Community 11 - "login"
Cohesion: 0.11
Nodes (17): login(), _FakeCache, _FakeUserRepository, _make_user(), test_login_credenciales_validas_retorna_token_pair(), test_login_email_inexistente_mismo_401_que_password_incorrecto(), test_login_exito_resetea_contador_de_intentos(), test_login_password_incorrecto_401_invalid_credentials() (+9 more)

### Community 12 - "spec_checksum.py"
Cohesion: 0.07
Nodes (22): check_openapi_coverage(), check_registry(), check_superseded_refs(), load_entries(), run(), _superseded_adrs(), build(), load_manifest() (+14 more)

### Community 13 - "RedisAdapter"
Cohesion: 0.05
Nodes (8): RedisAdapter, PostgreSQLAdapter, get_database_port(), Archivos (T-019..T-023, T-024/T-025, T-027), Cómo correrlas, tests/integration, test_postgresql_adapter_ping_against_real_container(), test_redis_adapter_ping_against_real_container()

### Community 14 - "json"
Cohesion: 0.07
Nodes (14): _DynamicStdoutHandler, get_logger(), JSONFormatter, test_get_logger_defaults_trace_id_when_no_context(), test_get_logger_emits_structured_json(), test_get_logger_includes_trace_id_from_context(), test_no_print_used_in_logger_module(), _DynamicStdoutHandler (+6 more)

### Community 15 - "PostgresAdapter"
Cohesion: 0.12
Nodes (6): PostgresAdapter, adapters/db, core/ports, tests/integration, test_postgres_adapter_ping_against_real_container(), test_redis_adapter_ping_against_real_container()

### Community 16 - "test_devices_scan_e2e.py"
Cohesion: 0.11
Nodes (9): _make_simulated_device(), _make_simulated_modbus_device(), _publish_real_mqtt_message(), _reset_device_tables(), _shutdown_modbus_server(), test_scan_bacnet_e2e_real_bac0_and_postgres(), test_scan_modbus_e2e_real_pymodbus_and_postgres(), test_scan_mqtt_e2e_real_paho_mqtt_and_postgres() (+1 more)

### Community 17 - "hira-server/backend/adapters/factory.py"
Cohesion: 0.05
Nodes (26): Alcance (anclas), Cómo trabajas, hub-infra, [2026-09-14] SRV-005-mqtt-scanning — verified, 1. Cumplimiento constitucional, 2. Arquitectura de la feature *(Hexagonal)*, 3. Modelo de datos, 7. Seguimiento de complejidad (+18 more)

### Community 18 - "modbus_simulator_adapter.py"
Cohesion: 0.10
Nodes (12): _blocks(), ModbusSimulatorAdapter, _only_configured_addresses(), _RunningServer, _shutdown(), _values_by_type(), _wait_until_listening(), _client() (+4 more)

### Community 19 - "E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md"
Cohesion: 0.06
Nodes (32): Alternativas consideradas, Consecuencias, Contexto, Decisión, Enlaces, `hira-hub` — núcleo y adaptadores, `hira-studio` — núcleo y adaptadores, Alternativas consideradas (+24 more)

### Community 20 - "PostgreSQLUserRepository"
Cohesion: 0.10
Nodes (12): _clean_table(), _insert_user(), _reset_users_table(), test_duplicate_email_rejected_by_unique_constraint(), test_get_by_email_returns_matching_user_record(), test_get_by_email_returns_none_when_not_found(), test_get_by_id_returns_matching_user_record(), test_get_by_id_returns_none_when_not_found() (+4 more)

### Community 21 - "test_cache_port_contract.py"
Cohesion: 0.06
Nodes (8): _CacheSinPubSubDouble, _FullCacheDouble, _LivenessOnlyDouble, test_cache_port_declara_cada_metodo(), test_cache_port_es_runtime_checkable(), test_cache_port_exige_get_set_incr_expire_delete_publish_subscribe(), test_cache_port_rechaza_un_doble_sin_publish_subscribe(), test_cache_port_rechaza_un_doble_solo_liveness()

### Community 22 - "ui-ux.md"
Cohesion: 0.06
Nodes (34): ADR-UI-H01 — Material Design 3 unificado con diferenciación por layout y densidad, ADR-UI-H02 — Portal de Ventas no requiere cuenta para comprar, ADR-UI-H03 — Marketplace usa reviews como señal de calidad, ADRs UI/UX, Alcance y Versiones, Arquitectura de navegación — Marketplace, Arquitectura de navegación — Panel Admin, Arquitectura de navegación — Portal de Ventas (+26 more)

### Community 23 - "uuid"
Cohesion: 0.18
Nodes (7): adapter(), make_subscriber(), _make(), test_publishing_does_not_block_the_event_loop(), test_start_publishes_payload_periodically(), test_start_rejects_invalid_topic_immediately(), test_stop_halts_publication()

### Community 24 - "LocalPermissionsCache"
Cohesion: 0.15
Nodes (16): [2026-09-13] SRV-002-auth-rbac — implemented, 0. Gates de simplicidad, 6. Secuenciación de archivos (tests antes que código), 7. Seguimiento de complejidad, 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*, Impacto en tareas (aprobado 2026-09-13 por Carlos — ver `tasks.md`), Implementación de RF-006, Implementación de RNF-001 (+8 more)

### Community 25 - "decode_token"
Cohesion: 0.14
Nodes (19): Causa raíz, Implementación de RF-003, Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks, Núcleo — JWT, create_access_token(), create_refresh_token(), decode_token(), TokenClaims (+11 more)

### Community 26 - "env.py"
Cohesion: 0.09
Nodes (6): do_run_migrations(), run_async_migrations(), run_migrations_offline(), run_migrations_online(), upgrade(), upgrade()

### Community 27 - "vision.md"
Cohesion: 0.06
Nodes (27): El flywheel, Licenciamiento por puntos en línea (`SRV-ADR-018`), Segmentos, Tres ejes de ingreso, Viabilidad (orden de magnitud), Arquitectura interna por componente, Contratos entre componentes, Diagrama de contexto — post `E-ADR-001` (+19 more)

### Community 28 - "BAC0Adapter"
Cohesion: 0.10
Nodes (10): 6. Secuenciación de archivos (tests antes que código), Registro de decisiones de diseño (nuevas de este plan), BAC0Adapter, _normalize_units(), BacnetObjectReading, BacnetReadTimeoutError, _make_simulated_device(), test_read_device_objects_matches_real_objects() (+2 more)

### Community 29 - "test_auth_security.py"
Cohesion: 0.08
Nodes (10): _build_app(), _problem_detail_handler(), _clean_infra(), client(), _fresh_factory_singletons(), _reset_real_infra(), test_flujo_completo_login_acceso_protegido_refresh_logout(), test_fuerza_bruta_real_sexto_intento_429() (+2 more)

### Community 30 - "test_device_repository_adapter.py"
Cohesion: 0.12
Nodes (11): Adaptador de repositorio real — integración contra Postgres, PostgreSQLDeviceRepository, test_get_device_by_address_distinguishes_by_protocol(), test_get_device_by_address_returns_existing_device(), test_get_device_returns_the_persisted_device(), test_list_candidates_for_device_empty_when_none(), test_list_devices_reflects_persisted_devices(), test_upsert_candidate_creates_and_lists() (+3 more)

### Community 32 - "scan_modbus"
Cohesion: 0.06
Nodes (37): 0. Gates de simplicidad, 1. Cumplimiento constitucional, 2. Arquitectura de la feature *(Hexagonal)*, 4. Contratos, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos (tests antes que código), 7. Seguimiento de complejidad, 8. Impacto en documentación *(obligatorio — Constitución Art. 11)* (+29 more)

### Community 33 - "routers/auth.py"
Cohesion: 0.07
Nodes (13): Implementación de RF-001, Contrato — Contract-First, HealthResponse, ServicesStatus, login(), logout(), refresh(), AccessTokenResponse (+5 more)

### Community 34 - "hira-server/backend/tests/test_health_service.py"
Cohesion: 0.12
Nodes (10): _FailingPort, _FastOkPort, _NotificationFastOk, _SlowPort, test_get_health_all_ok_aggregates_status_ok(), test_get_health_defaults_trace_id_when_no_context(), test_get_health_exception_marks_service_error_without_propagating(), test_get_health_includes_trace_id_from_context() (+2 more)

### Community 35 - "ModbusRegisterReading"
Cohesion: 0.10
Nodes (15): `adapters/factory.py` (se amplía), PymodbusAdapter, adapters/modbus, ModbusReadFailure, ModbusRegisterType, _make_simulated_device(), _shutdown_server(), test_read_range_all_four_register_types_real_values() (+7 more)

### Community 36 - "resolve_permissions"
Cohesion: 0.11
Nodes (18): 10. RNF-001 — Directiva de Pausa (histórico) y solución aprobada (2026-09-13), 5. Estrategia de pruebas (por zona del patrón), Causa raíz #2 (confirmada en una ronda de revisión posterior, mismo 2026-09-13) — round-trip a Redis, Coordinación (casos de uso / fronteras de entrada), Evidencia (terminal real, 2026-09-13), Por qué es una asunción inviable de `plan.md` (no un bug de código), Qué se midió y cómo, Solución de raíz aprobada (Carlos, 2026-09-13) — ataca ambas causas (+10 more)

### Community 37 - "test_bacnet_address.py"
Cohesion: 0.13
Nodes (19): format_device_address(), format_simulator_device_address(), parse_device_address(), test_format_device_address_construye_instance_arroba_network(), test_format_luego_parse_round_trip_con_varios_valores(), test_format_rechaza_instance_number_negativo(), test_format_rechaza_network_address_solo_espacios(), test_format_rechaza_network_address_vacio() (+11 more)

### Community 38 - "test_authentication_middleware.py"
Cohesion: 0.10
Nodes (9): _access_token(), _build_app(), client(), _FakeSettings, _make_user(), test_auth_logout_no_esta_en_allowlist_exige_token(), test_ruta_protegida_token_valido_fija_request_state_user(), test_ruta_protegida_usuario_desactivado_401_token_invalid() (+1 more)

### Community 39 - "Bitácora del arnés — ecosistema Hira"
Cohesion: 0.20
Nodes (9): [2026-09-04] Corrección de diseño del arnés (propagada desde cjhirashi-career), [2026-09-04] Homogeneizar a Hexagonal los 3 productos — E-ADR-002, [2026-09-10] Especialista `experto-ux-ui` añadido al arnés — ADR-003, [2026-09-14] HUB-001-walking-skeleton — implemented, [2026-09-14] SRV-003-bacnet-adapter — implemented, [2026-09-14] SRV-004-modbus-adapter — implemented, [2026-10-15] SRV-006-simuladores — implemented, [2026-10-15] SRV-006-simuladores — verified (+1 more)

### Community 40 - "UserRecord"
Cohesion: 0.10
Nodes (4): UserRecord, _FakeUserRepository, _FakeUserRepository, _FakeUserRepository

### Community 41 - "auth_service.py"
Cohesion: 0.10
Nodes (16): 9. Implementación por requisito, Implementación de RF-002, Implementación de RF-005, Implementación de RF-010, Implementación de RF-011, Implementación de RF-012, Implementación de RF-013, Implementación de RF-014 (+8 more)

### Community 42 - "PLAN-HUB-001 · Walking Skeleton de Hira Hub"
Cohesion: 0.08
Nodes (24): 0. Gates de simplicidad, 1. Cumplimiento constitucional, 2. Arquitectura de la feature *(Hexagonal)*, 3. Modelo de datos, 4. Contratos, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos (tests antes que código), 7. Seguimiento de complejidad (+16 more)

### Community 44 - "start_mqtt_simulator"
Cohesion: 0.06
Nodes (24): 9. Implementación por requisito, Implementación de RF-003, Implementación de RF-004, Implementación de RF-005, Implementación de RF-006, Implementación de RF-007, Implementación de RF-008, Implementación de RF-009 (+16 more)

### Community 45 - "test_main_lifespan.py"
Cohesion: 0.16
Nodes (8): Adaptadores concretos — integración contra contenedores reales, _set_env(), test_lifespan_aborts_with_json_error_when_var_missing(), test_lifespan_invokes_mosquitto_connect_and_does_not_abort_on_failure(), test_lifespan_invokes_mosquitto_connect_and_reflects_success(), test_lifespan_no_partial_startup_names_all_missing_vars(), test_lifespan_starts_invalidation_subscriber_and_cancels_it_cleanly(), test_lifespan_starts_when_all_required_vars_present()

### Community 46 - "hira-hub/backend/tests/test_health_service.py"
Cohesion: 0.15
Nodes (9): _FailingPort, _FastOkPort, _SlowPort, test_get_health_all_ok_aggregates_status_ok(), test_get_health_cache_error_marks_redis_error(), test_get_health_defaults_trace_id_when_no_context(), test_get_health_exception_marks_service_error_without_propagating(), test_get_health_includes_trace_id_from_context() (+1 more)

### Community 47 - "BacnetTransportPort"
Cohesion: 0.16
Nodes (13): 1. Cumplimiento constitucional, 3. Modelo de datos, 4. Contratos, 5. Estrategia de pruebas (por zona del patrón), 7. Seguimiento de complejidad, 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*, Esquemas nuevos (`hira-server/docs/openapi.yaml` — extracto), Migraciones (+5 more)

### Community 48 - "start_bacnet_simulator"
Cohesion: 0.17
Nodes (3): Implementación de RF-001, Coordinación — servicio de simuladores (arranque BACnet), start_bacnet_simulator()

### Community 49 - "test_simulators_e2e.py"
Cohesion: 0.14
Nodes (8): _devices_by_address(), _subscribe(), test_api_keeps_responding_while_simulators_run(), test_bacnet_simulator_full_lifecycle(), test_modbus_simulator_survives_real_scan_and_rejects_real_address(), test_mqtt_simulator_publishes_and_validates_input(), test_rbac_and_unknown_simulator(), test_restart_empties_running_list_and_keeps_devices()

### Community 50 - "test_rbac_latency.py"
Cohesion: 0.13
Nodes (5): _build_bench_app(), _CountingUserRepository, _fire_concurrent_requests(), _insert_user(), test_middleware_rbac_agrega_menos_de_5ms_en_cache_hit()

### Community 51 - "hash_password"
Cohesion: 0.15
Nodes (14): 3. Modelo de datos, Migraciones (Alembic — primer uso en el repo), Seed (creación del primer usuario — `spec.md §2`: "creación por seed/migración"), Tabla `users`, Núcleo — passwords, hash_password(), verify_password(), scripts (+6 more)

### Community 52 - "_FakeDeviceRepository"
Cohesion: 0.14
Nodes (8): _FakeBacnetSimulatorPort, _FakeDeviceRepository, _make(), test_start_bacnet_simulator_direccion_real_409(), test_start_bacnet_simulator_ya_en_ejecucion_409(), test_start_modbus_simulator_ya_en_ejecucion_409(), test_start_mqtt_simulator_publish_invalido_400_rfc9457(), test_stop_simulator_admin_204()

### Community 53 - "MqttPublisherAdapter"
Cohesion: 0.19
Nodes (5): 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*, _disconnect_sync(), MqttPublisherAdapter, _publish_periodically(), _RunningPublisher

### Community 55 - "hira-server/spec/context.md"
Cohesion: 0.10
Nodes (19): Canal de fabricantes de controladores, De Contexto, De Negocio, De Tiempo, Económicas, Gate de Salida, Marketplace de Plantillas — Oportunidad Estratégica, Matriz de Riesgos (+11 more)

### Community 56 - "Proceso SDD-Anchored"
Cohesion: 0.10
Nodes (18): Desviaciones abiertas, Desviaciones resueltas, Desviaciones y reportes de sesión, DEV-000 · 2026-09-02 · tipo: diseño · Estado: Resuelta, Reporte de Sesión — 2026-09-02, Reporte de Sesión — 2026-09-03, Reportes de sesión, 10. Qué NUNCA se hace (+10 more)

### Community 58 - "Instalación de Hira Server/Studio"
Cohesion: 0.11
Nodes (18): Actualización de una instalación activa, Actualización de versión, Backup automático (perfil producción), Backup y Recuperación, Checklist de Pre-despliegue, Diferencias por perfil de instalación, En el servidor del cliente (licencia comercial), En la PC del integrador (licencia de integrador) (+10 more)

### Community 59 - "Registro Activo"
Cohesion: 0.11
Nodes (18): Cómo Agregar una Nueva Vulnerabilidad, Estados, Propósito, Registro Activo, Severidades, VUL-SRV-002 — Import de paquete .hira ejecuta SQL crudo, VUL-SRV-003 — Sin rate limiting en API ni en WebSocket, VUL-SRV-005 — BAC0 sin lock en escrituras concurrentes (+10 more)

### Community 60 - "can_access_project"
Cohesion: 0.16
Nodes (10): Implementación de RF-004, Núcleo — política RBAC, can_write(), is_admin(), test_can_access_project_scope_global_siempre_true_mismo_proyecto(), test_can_access_project_scope_global_siempre_true_otro_proyecto(), test_can_access_project_scope_project_coincide(), test_can_access_project_scope_project_no_coincide() (+2 more)

### Community 63 - "hira-hub/backend/tests/test_correlation_id.py"
Cohesion: 0.16
Nodes (10): lifespan(), _build_app(), _set_env(), test_generates_trace_id_when_header_missing(), test_lifespan_aborts_with_json_error_when_var_missing(), test_lifespan_no_partial_startup_names_all_missing_vars(), test_lifespan_starts_when_all_required_vars_present(), test_propagates_trace_id_from_request_header() (+2 more)

### Community 64 - "operation.md"
Cohesion: 0.11
Nodes (17): Criterios de criticidad, Emitir una nueva license key, Estado del Sistema, Extender vencimiento, Gate de Salida, Gestión de Crash Reports, Gestión de Licencias, Niveles de Servicio (SLOs) (+9 more)

### Community 65 - "Tareas"
Cohesion: 0.11
Nodes (17): Adaptador de entrada — router, Adaptadores concretos — integración contra contenedores reales, Arnés, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Config — arranque validado, Contrato — Contract-First, Correlation ID, Documentación (`plan.md §8`) — pueden correr en paralelo desde T-002 (+9 more)

### Community 66 - "scan_bacnet"
Cohesion: 0.08
Nodes (20): 0. Gates de simplicidad, 9. Implementación por requisito, Implementación de RF-001, Implementación de RF-002, Implementación de RF-003, Implementación de RF-005, Implementación de RF-006, Implementación de RF-007 (+12 more)

### Community 67 - "MqttScanAdapter"
Cohesion: 0.06
Nodes (22): 0. Gates de simplicidad, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos (tests antes que código), Adaptadores de entrada, `core/ports/mqtt_scan_transport_port.py` (nuevo), Fronteras de salida, Registro de decisiones de diseño (nuevas de este plan), Puerto (+14 more)

### Community 68 - "BacnetSimulatorAdapter"
Cohesion: 0.22
Nodes (6): BacnetSimulatorAdapter, test_start_answers_who_is_and_exposes_initial_objects(), test_start_does_not_block_the_event_loop(), test_stop_releases_udp_port_for_a_later_start(), test_two_concurrent_simulators_do_not_collide(), _who_is()

### Community 69 - "detailed-design.md"
Cohesion: 0.12
Nodes (16): API v0.1 — Contratos, `crash_reports`, Estructura de Carpetas del Proyecto, Gate de Salida, `GET /api/updates/latest?product=server`, `GET /health`, `hira_versions`, `license_activations` (+8 more)

### Community 70 - "Método del arnés — `.harness/`"
Cohesion: 0.17
Nodes (12): §0 · Qué es esto, §10 · Eficiencia de tokens (obligatorio), §11 · Procedencia, §1 · Génesis del proyecto, §2 · Rúbrica de decisión (Fase 0) — ¿entra al arnés?, §4 · EARS — sintaxis de los criterios de aceptación, §5 · Reglas transversales, §6 · La compuerta — `gate/check.sh` (+4 more)

### Community 71 - "pytest"
Cohesion: 0.12
Nodes (16): 3. Modelo de datos, _set_env(), test_settings_has_no_secret_key_or_admin_password_hash_fields(), test_settings_loads_when_all_required_vars_present(), test_settings_missing_var_raises_naming_it(), test_settings_rejects_partial_startup_no_default_for_required_fields(), format_modbus_address(), test_format_modbus_address_acepta_port_en_los_limites() (+8 more)

### Community 72 - "ProblemDetail"
Cohesion: 0.12
Nodes (14): 4. Contratos, Sobre de error — RFC 9457 (`Content-Type: application/problem+json`), Núcleo — catálogo de errores (RFC 9457, `E-ADR-003`), 4. Contratos, Esquema nuevo (`hira-server/docs/openapi.yaml` — extracto), Sobre de error — RFC 9457 (reutiliza `ProblemDetail`, `E-ADR-003`), 4. Contratos, Esquemas nuevos (`hira-server/docs/openapi.yaml` — extracto) (+6 more)

### Community 73 - "PLAN-NNN · ‹Nombre›"
Cohesion: 0.12
Nodes (16): 0. Gates de simplicidad, 1. Cumplimiento constitucional, 2. Arquitectura de la feature  *(según el patrón elegido)*, 3. Modelo de datos, 4. Contratos, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos, 7. Seguimiento de complejidad  *(opcional)* (+8 more)

### Community 74 - "Ecosistema Hira — instrucciones base"
Cohesion: 0.33
Nodes (6): Commits, Definition of Done, Ecosistema Hira — instrucciones base, Equipo de agentes, Los tres componentes, Reglas transversales (todas las apps)

### Community 77 - "9. Implementación por requisito"
Cohesion: 0.25
Nodes (8): 9. Implementación por requisito, Implementación de RF-001, Implementación de RF-002, Implementación de RF-003, Implementación de RF-004, Implementación de RF-005, Implementación de RF-006, Implementación de RF-007

### Community 78 - "Tareas"
Cohesion: 0.12
Nodes (15): Arnés, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Config — arranque validado, Contrato — Contract-First, Correlation ID, Estructura, Infraestructura de contenedores, Logger — observabilidad (+7 more)

### Community 79 - "AuthenticatedUser"
Cohesion: 0.15
Nodes (4): AuthenticatedUser, _FakeAuthHeaderMiddleware, _ExplodingUserRepository, test_local_cache_hit_no_llama_a_redis_ni_a_bd()

### Community 80 - "topic_instance_key"
Cohesion: 0.10
Nodes (16): 9. Implementación por requisito, Implementación de RF-001, Implementación de RF-002, Implementación de RF-003, Implementación de RF-004, Implementación de RF-005, Implementación de RF-006, Implementación de RNF-001 (+8 more)

### Community 81 - "Tareas"
Cohesion: 0.11
Nodes (16): Adaptador BACnet real — integración contra un cliente BACnet real, Adaptador de entrada — router, Adaptador de repositorio — Postgres real, Adaptador MQTT real — integración contra el Mosquitto real, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Coordinación — detener simulador, Coordinación — servicio de simuladores (arranque Modbus), Documentación (`plan.md §8`) — puede correr en paralelo desde T-001 (+8 more)

### Community 82 - "_ExplodingCache"
Cohesion: 0.12
Nodes (3): _ExplodingCache, test_update_user_role_orden_update_antes_que_invalidate(), delete()

### Community 84 - "mosquitto_adapter.py"
Cohesion: 0.18
Nodes (3): client(), _NoNetworkSubscribeCache, test_health_reflects_correlation_id_header()

### Community 85 - "deployment.md"
Cohesion: 0.13
Nodes (14): Actualización (versión nueva), Arquitectura del VPS, Automatizado (cron), Backup de Base de Datos, Configuración Nginx, Costos, Endpoints v0.1 en Producción, Gate de Salida (+6 more)

### Community 86 - "modelo-de-datos.md"
Cohesion: 0.13
Nodes (14): Alarmas, Backup, Convención, Dispositivos y puntos, Documentación, Gate de Salida, Históricos (TimescaleDB hypertable en instancia comercial; tabla estándar en SQLite), IA (+6 more)

### Community 87 - "acceptance-criteria.md"
Cohesion: 0.13
Nodes (14): AC-SRV-01 — Infraestructura y arranque, AC-SRV-02 — Autenticación y RBAC, AC-SRV-03 — BACnet, AC-SRV-04 — MQTT, AC-SRV-05 — Simuladores, AC-SRV-06 — Dashboard y tiempo real, AC-SRV-07 — Motor de Alarmas, AC-SRV-08 — Históricos (+6 more)

### Community 88 - "Decisión"
Cohesion: 0.13
Nodes (13): Alternativas consideradas, Consecuencias, Contexto, Decisión, 1. Túnel inverso iniciado por el Server (self-hosted), 2. Alcance mínimo expuesto — segmentación de red explícita, 3. Instalación personalizada emitida por Hub, 4. Gate de autorización por propiedad (depende de `HUB-ADR-06`) (+5 more)

### Community 89 - "harness"
Cohesion: 0.14
Nodes (11): ADR-001 · Reestructuración al esquema simplificado del arnés + perfiles de arquitectura, Consecuencias, Contexto y planteamiento del problema, Decisión, Enlaces, Opciones consideradas, [2026-09-04] Reestructuración del arnés al esquema simplificado — completada, harness() (+3 more)

### Community 90 - "SPRINT.md"
Cohesion: 0.17
Nodes (10): Dependencias entre tracks, Orden recomendado global, Roadmap del ecosistema, Track HUB — Hira Hub, Track SRV — Hira Server, Track STU — Hira Studio, Anclas del sprint, Contexto de arranque (+2 more)

### Community 91 - "can_access_project"
Cohesion: 0.24
Nodes (7): Implementación de RF-008, Implementación de RF-009, Dependencias — autorización fina, require_project_scope(), dependency(), dependency(), can_access_project()

### Community 92 - "BacnetDeviceAnnouncement"
Cohesion: 0.15
Nodes (7): BacnetDeviceAnnouncement, _FakeBacnetTransport, test_scan_bacnet_camino_feliz_dos_dispositivos_persiste_device_y_candidatos(), test_scan_bacnet_lee_objetos_en_paralelo_no_secuencial(), test_scan_bacnet_segundo_escaneo_actualiza_no_duplica(), test_scan_bacnet_timeout_de_un_dispositivo_no_aborta_el_resto(), _FakeBacnetTransport

### Community 93 - "hira-hub/backend/services/health_service.py"
Cohesion: 0.16
Nodes (3): aggregate_status(), get_health(), _ping_with_timeout()

### Community 94 - "hira-server/backend/services/health_service.py"
Cohesion: 0.16
Nodes (3): aggregate_status(), get_health(), _ping_with_timeout()

### Community 95 - "hira-server/spec/improvements.md"
Cohesion: 0.14
Nodes (13): Alcance, Backlog Completo, Ciclo de Revisión del Roadmap, Consolidación de la Experiencia del Integrador, Escala y Ecosistema, Fuentes del backlog, Gate de Salida, Madurez del Producto (+5 more)

### Community 96 - "Runbooks"
Cohesion: 0.14
Nodes (13): Expansión de capacidad, Gate de Salida, Mantenimiento programado recomendado, Procedimientos frecuentes, RB-01 — Servicio caído (un contenedor no responde), RB-02 — Dispositivo BACnet/Modbus no responde, RB-03 — Alarma que no se desactiva sola, RB-04 — Script de lógica se detiene (+5 more)

### Community 97 - "Constitución — ecosistema Hira"
Cohesion: 0.14
Nodes (14): Artículo 10 · Regla de raíz (prohibido el parche), Artículo 11 · Mapa de documentación del proyecto, Artículo 12 · Anti-hipersistema, Artículo 1 · Arquitectura, Artículo 2 · Perfil de arquitectura  *(registrado en la Génesis — decisiones ya tomadas por ADR)*, Artículo 3 · Testing, Artículo 4 · Persistencia, Artículo 5 · Seguridad (+6 more)

### Community 98 - "⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)"
Cohesion: 0.14
Nodes (13): [2026-09-02] Studio es un producto cloud independiente, no un perfil de Server, [2026-09-04] El patrón de arquitectura no es uniforme entre productos, [2026-09-04] Forzar la Fase 1 (corrección propagada desde cjhirashi-career), [2026-09-04] Los 3 productos son Hexagonal, no solo hira-server, [2026-09-10] Toda feature de frontend pasa por el especialista `experto-ux-ui`, ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar), Estado de features (2026-10-15), Estado del arnés — ecosistema Hira (+5 more)

### Community 99 - "PostgreSQLUserRepository"
Cohesion: 0.18
Nodes (7): 1. Cumplimiento constitucional, 2. Arquitectura de la feature *(Hexagonal)*, Adaptadores de entrada, `adapters/factory.py` (se amplía), Fronteras de salida, adapters/db, PostgreSQLUserRepository

### Community 101 - "Stakeholders del Proyecto"
Cohesion: 0.15
Nodes (12): cjhirashi — Propietario y Operador, Gate de Salida, Hira Server — Cliente Técnico Primario, Hira Studio — Cliente Técnico Secundario, Integrador — Usuario Indirecto, Mapa de Interacciones, Protocolo de Comunicación, Protocolo de Integración Tardía (+4 more)

### Community 102 - "Registro Activo"
Cohesion: 0.15
Nodes (12): Cómo Agregar una Nueva Vulnerabilidad, Estados, Historial de Resoluciones, Propósito, Registro Activo, Severidades, VUL-HUB-01 — License keys nunca deben almacenarse ni loguearse en claro, VUL-HUB-02 — Endpoint de validación vulnerable a enumeración de keys (+4 more)

### Community 103 - "Tareas"
Cohesion: 0.25
Nodes (8): T-1 — Estructura de repo + `.gitignore` + `docs/openapi.yaml` inicial, T-2 — Docker Compose base, T-3 — `core/logger.py` — logging JSON estructurado, T-4 — `core/config.py` — Pydantic Settings, T-5 — Puertos + factory + adaptadores stub, T-6 — `main.py` + `routers/monitor.py` — `GET /health`, T-7 — Tests de `AC-SRV-01`, Tareas

### Community 104 - "Tareas"
Cohesion: 0.17
Nodes (11): Adaptador de entrada — router, Adaptador MQTT real — integración contra Mosquitto real, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Contrato — Contract-First, Documentación (`plan.md §8`) — puede correr en paralelo desde T-001, Higiene de repo, Núcleo — clave de topic, Reglas (+3 more)

### Community 105 - "AGENTS.md — mapa del ecosistema Hira"
Cohesion: 0.17
Nodes (12): Agentes Base (6), AGENTS.md — mapa del ecosistema Hira, Antes de empezar (en orden), Bindings de herramienta — `.claude/agents/`, Contratos compartidos, Convenciones, Especialistas (17), Mapa de documentación (producto) (+4 more)

### Community 106 - "hira-server/backend/tests/test_correlation_id.py"
Cohesion: 0.24
Nodes (5): _build_app(), test_generates_trace_id_when_header_missing(), test_propagates_trace_id_from_request_header(), test_trace_id_context_reset_after_request(), test_trace_id_differs_between_requests_without_header()

### Community 107 - "dev-guide.md"
Cohesion: 0.17
Nodes (11): Comandos de operación frecuentes, Convenciones de código, Flujo de CI/CD, Gate de Salida, Repositorio, Sprint H0 — Walking Skeleton Hub, Sprint H1 — Gestión de Licencias, Sprint H2 — Crash Reports y Versiones (+3 more)

### Community 108 - "hira-hub/spec/improvements.md"
Cohesion: 0.17
Nodes (11): Backlog Sin Versión Asignada, Criterios para Avanzar de Versión, Gate de Salida, Hub v0.1 — Hub Mínimo (Sprint activo), Hub v0.2 — Hub con Ventas, Hub v0.3 — Diseñador de Bloques y Marketplace, MJR-H01 — Portal de ventas con Stripe, MJR-H02 — Dashboard de instalaciones activas (+3 more)

### Community 109 - "SPEC-HUB-001 · Walking Skeleton de Hira Hub"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (propuesto) (+3 more)

### Community 110 - "PLAN-SRV-001 · Walking Skeleton de Hira Server"
Cohesion: 0.22
Nodes (8): 0. Gates de simplicidad, 1. Cumplimiento constitucional, 3. Modelo de datos, 4. Contratos, 5. Estrategia de pruebas (por zona del patrón), 6. Secuenciación de archivos (tests antes que código), 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*, PLAN-SRV-001 · Walking Skeleton de Hira Server

### Community 111 - "SPEC-SRV-001 · Walking Skeleton de Hira Server"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (+3 more)

### Community 112 - "SPEC-SRV-002 · Autenticación y RBAC (MVP — 3 roles fijos)"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (propuesto) (+3 more)

### Community 113 - "SPEC-SRV-003 · Adaptador BACnet — escaneo y candidatos"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (propuesto) (+3 more)

### Community 114 - "Tareas"
Cohesion: 0.12
Nodes (15): Implementación de RF-004, Adaptador BACnet real — integración sin hardware, Adaptador de entrada — router, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Contrato — Contract-First, Documentación (`plan.md §8`) — puede correr en paralelo desde T-001, Higiene de repo, Modelo de datos (+7 more)

### Community 115 - "SPEC-SRV-004 · Adaptador Modbus — escaneo y candidatos"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (decidido) (+3 more)

### Community 116 - "Tareas"
Cohesion: 0.17
Nodes (11): Adaptador Modbus real — integración sin hardware, Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Contrato — Contract-First, Coordinación — servicio de escaneo (amplía `device_scan_service.py`), Documentación (`plan.md §8`) — puede correr en paralelo desde T-001, Higiene de repo, Núcleo — dirección Modbus, Reglas (+3 more)

### Community 117 - "SPEC-SRV-005 · Escaneo MQTT — suscripción wildcard y candidatos"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (propuesto) (+3 more)

### Community 119 - "SPEC-NNN · ‹Nombre de la funcionalidad›"
Cohesion: 0.17
Nodes (11): 1. Contexto del dominio, 2. Alcance, 3. Modelo de datos y contratos de E/S  ← INVENTARIO DE FRONTERAS, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF)  *(opcional)*, En alcance (+3 more)

### Community 121 - "hira-server/backend/tests/test_config.py"
Cohesion: 0.22
Nodes (5): _set_env(), test_settings_has_no_deploy_mode_field(), test_settings_loads_when_all_required_vars_present(), test_settings_missing_var_raises_naming_it(), test_settings_rejects_partial_startup_no_default_for_required_fields()

### Community 123 - "hira-hub/spec/portfolio.md"
Cohesion: 0.18
Nodes (10): 01 · Contexto — El problema, 02 · Enfoque — La solución, 03 · Arquitectura — Cómo funciona el sistema, 04 · Resultados — Impacto medido, Año, Categoría, Descripción narrativa, Métricas de impacto (+2 more)

### Community 124 - "guia-backend.md"
Cohesion: 0.18
Nodes (10): Alembic para migraciones, Cambio de infraestructura pendiente — Nginx → Caddy (2026-08-12), Comunicación Agente IA ↔ sistema, Decisiones de Implementación, Estructura del Backend, Flujo de datos principal, Gate de Salida, Integración entre Módulos (+2 more)

### Community 125 - "Proceso de Respuesta"
Cohesion: 0.18
Nodes (10): Clasificación de Incidencias, Definición de severidades, Gate de Salida, Paso 1 — Recibir y clasificar, Paso 2 — Abrir issue en GitHub, Paso 3 — Comunicar al integrador (SEV-1 y SEV-2), Paso 4 — Diagnóstico y resolución, Paso 5 — Fix o workaround (+2 more)

### Community 126 - "hira-server/spec/portfolio.md"
Cohesion: 0.18
Nodes (10): 01 · Contexto — El problema, 02 · Enfoque — La solución, 03 · Arquitectura — Cómo funciona el sistema, 04 · Resultados — Impacto medido, Año, Categoría, Descripción narrativa, Métricas de impacto (+2 more)

### Community 127 - "Sistema de Diseño Visual"
Cohesion: 0.18
Nodes (10): Alcance, Componentes Base, Control de Tema: Claro / Oscuro / Sistema, Espaciado, Forma y Elevación, Gate de Salida, Principios de Diseño, Roles de Color MD3, Sistema de Diseño Visual (+2 more)

### Community 128 - "check.sh"
Cohesion: 0.36
Nodes (9): budget(), err(), fm_value(), ok(), sec(), check.sh script, skip(), touched() (+1 more)

### Community 129 - "SPEC-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT)"
Cohesion: 0.18
Nodes (10): 1. Contexto del dominio, 2. Alcance, 4. Criterios de aceptación (EARS), 5. Casos límite y manejo de errores, 6. Registro de decisiones y descartes, 7. Requisitos no funcionales (RNF), En alcance (propuesto), Fuera de alcance (propuesto) (+2 more)

### Community 131 - "_FakeMqttPublisherPort"
Cohesion: 0.20
Nodes (4): _FakeMqttPublisherPort, test_start_mqtt_simulator_direccion_real_409(), test_start_mqtt_simulator_intervalo_invalido_400_rfc9457(), test_start_mqtt_simulator_ya_en_ejecucion_409()

### Community 132 - "asyncio"
Cohesion: 0.31
Nodes (3): Seed — único mecanismo de creación de usuarios de este sprint, main(), seed_admin_user()

### Community 134 - "_FakeCache"
Cohesion: 0.12
Nodes (3): _FakeCache, _FakeMqttTransport, _make()

### Community 136 - "BacnetSimulatedObjectSpec"
Cohesion: 0.18
Nodes (4): _build_object(), _RunningInstance, _wait_until_ready(), BacnetSimulatedObjectSpec

### Community 137 - "Catálogo de Incidencias Conocidas"
Cohesion: 0.20
Nodes (9): Catálogo de Incidencias Conocidas, Clasificación de Incidencias, Gate de Salida, INC-H01 — Hub completamente inaccesible, INC-H02 — Validación de licencias devuelve 500, INC-H03 — Fuerza bruta en `/api/licenses/validate`, INC-H04 — Certificado SSL vencido, INC-H05 — Pérdida de datos de licencias (+1 more)

### Community 138 - "dispositivos-protocolos-puntos.md"
Cohesion: 0.20
Nodes (9): Asociación explícita de puntos, BACnet MSTP, Concurrencia, Escaneo y descubrimiento, Escritura, Gate de Salida, Polling, Responsabilidad (+1 more)

### Community 139 - "especificacion-de-vistas.md"
Cohesion: 0.20
Nodes (9): 0. Biblioteca de Proyectos, 1. Dashboard, 2. Mimics (Gráficos SVG animados), 3. Gestor de Alarmas, 4. Históricos, 5. Motor de Lógica, 6. Configurador, 7. Agente IA (+1 more)

### Community 140 - "test-plan.md"
Cohesion: 0.20
Nodes (9): Ambiente de Pruebas, Gate de Salida, Issues Encontrados, Pruebas de Carga, Pruebas de Integración, Pruebas de Seguridad, Pruebas End-to-End, Pruebas Unitarias (+1 more)

### Community 141 - "Decisión"
Cohesion: 0.20
Nodes (9): Alternativas consideradas, Biblioteca de proyectos y multi-proyecto (SQ-6), Consecuencias, Contexto, Decisión, Dos modos de trabajo, Ejecución, Publicación del proyecto (+1 more)

### Community 142 - "Especialistas (F0 — se ajustan al avanzar)"
Cohesion: 0.20
Nodes (9): De módulo — Hira Hub, De módulo — Hira Server, Especialistas (F0 — se ajustan al avanzar), Fijos de proyecto (aplican a las tres apps), Hira Studio, Orquestación del equipo de agentes, Regla de modelo, Roles (+1 more)

### Community 143 - "Adaptadores de entrada"
Cohesion: 0.20
Nodes (9): 2. Arquitectura de la feature *(Hexagonal)*, Adaptadores de entrada, `adapters/factory.py` (se amplía), Coordinación (casos de uso / fronteras de entrada), `core/ports/bacnet_transport_port.py` (nuevo), `core/ports/device_repository_port.py` (nuevo), Fronteras de salida, Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks (+1 more)

### Community 147 - "hira-hub/spec/context.md"
Cohesion: 0.22
Nodes (8): Gate de Salida, Posición en el Ecosistema, Problema que Resuelve, Restricciones, Riesgos, Stakeholders, Versiones y Alcance, Viabilidad

### Community 148 - "Atributos de Calidad"
Cohesion: 0.22
Nodes (8): Atributos de Calidad, Confiabilidad, Gate de Salida, Portabilidad y Escalabilidad, Propósito, Rendimiento, Riesgos Arquitectónicos, Seguridad

### Community 149 - "flujos-de-datos.md"
Cohesion: 0.22
Nodes (8): Flujo 1 — Lectura en tiempo real (dispositivo → pantalla), Flujo 2 — Comando de escritura (operador → dispositivo), Flujo 3 — Alarma automática, Flujo 4 — Script de lógica Python (operación continua), Flujo 5 — Script de prueba funcional, Flujo 6 — Escaneo de dispositivos y asociación explícita de puntos, Flujo 7 — Agente IA con RAG, Gate de Salida

### Community 150 - "monitoreo-y-notificaciones.md"
Cohesion: 0.22
Nodes (8): Arquitectura de Observabilidad, Canal 1 — Notificaciones al Integrador, Canal 2 — Crash Reporter hacia el desarrollador (Hira Hub), Capa 1 — Métricas operativas del sistema, Capa 2 — Métricas de agentes IA, Capa 3 — Métricas de dispositivos, Gate de Salida, Sistema de Notificaciones

### Community 151 - "Deuda Arquitectural"
Cohesion: 0.22
Nodes (8): DA-001 — Dashboard propio por producto (Studio vs Server) — ✅ Resuelto Sprint 15, DA-002 — Reconciliar separación Server/Studio (Sprint 10c) con el modelo de un solo producto (SRV-ADR-015), DA-003 — Modelo de puntos candidatos y asociación explícita (SRV-ADR-012, SRV-ADR-019) no implementado, DA-004 — Licenciamiento por puntos en línea (SRV-ADR-018) y multi-proyecto (SRV-ADR-020) no implementados, Deuda Arquitectural, Historial de Sprints (implementación previa), Roadmap, Roadmap del ecosistema

### Community 152 - "Overlay — `hira-hub/`"
Cohesion: 0.22
Nodes (8): Arquitectura (`E-ADR-002`, supersede `HUB-ADR-05`), Contract-First, Frontend (Admin / Portal / Marketplace), Módulos para el commit, Orden de lectura al iniciar sesión, Overlay — `hira-hub/`, Prohibiciones específicas, Seguridad — reglas críticas

### Community 153 - "Overlay — `hira-server/`"
Cohesion: 0.22
Nodes (8): Arquitectura — regla de oro (`SRV-ADR-017`), Contract-First, Frontend (`hira-server/frontend/src/`), Orden de lectura al iniciar sesión, Overlay — `hira-server/`, Prohibiciones específicas, Puntos — asociación explícita (`SRV-ADR-012`, `SRV-ADR-019`), Scopes de commit (`<tipo>(<scope>): …`)

### Community 154 - "Overlay — `hira-studio/`"
Cohesion: 0.22
Nodes (8): Contratos que consume, Diseño de plataforma — CERRADO (`STU-ADR-001..005`, 2026-09-03), Estado de implementación, Herencia de diseño, Módulos para el commit, Orden de lectura, Overlay — `hira-studio/`, Reglas

### Community 155 - "2. Arquitectura de la feature *(Hexagonal)*"
Cohesion: 0.13
Nodes (13): [2026-09-13] SRV-001-walking-skeleton — implemented, 2. Arquitectura de la feature *(Hexagonal)*, 7. Seguimiento de complejidad, Adaptadores de entrada, `adapters/factory.py`, Coordinación (casos de uso / fronteras de entrada), Directiva de Pausa (2026-09-13, #2) — falta la tarea de wiring de `connect()` en el `lifespan`, Directiva de Pausa (2026-09-13) — `adapters/factory.py` se crea en el paso 7, no en el 9 (+5 more)

### Community 158 - "HUB-ADR-06-propiedad-y-vinculacion-de-proyectos.md"
Cohesion: 0.25
Nodes (7): Alternativas consideradas, Consecuencias, Contexto, Decisión, Modelo de datos (Hub), Qué no cambia, Reglas

### Community 159 - "general.md"
Cohesion: 0.25
Nodes (7): Descripción del Sistema, Diagrama de Contenedores (C4 L2), Diagrama de Contexto (C4 L1) — Ecosistema Hira, Gate de Salida, Hira Hub, Hira Server/Studio, Módulos del Sistema

### Community 160 - "estructura-de-repositorio.md"
Cohesion: 0.25
Nodes (7): Gate de Salida, Levantar el Entorno de Desarrollo, Perfil de Despliegue, Prerrequisitos, Simulación BACnet en Desarrollo, Variables de Entorno, Árbol de Carpetas

### Community 161 - "agente-ia.md"
Cohesion: 0.25
Nodes (7): Configuración, Gate de Salida, Modelo Interno (fallback) — ver SRV-ADR-021, Métricas y presupuesto, RAG (Agente del Cliente), Responsabilidad, Tools por agente

### Community 162 - "auth-rbac-seguridad.md"
Cohesion: 0.25
Nodes (7): Autenticación y Autorización, Backup y portabilidad, Datos sensibles, Ejecución de scripts Python, Gate de Salida, Red, Variables de entorno requeridas

### Community 163 - "operacion-cliente-y-soporte.md"
Cohesion: 0.25
Nodes (7): Acciones disponibles por rol, Canal de soporte, Comunicación con Integradores, Flujo de trabajo diario, Gate de Salida, Información mínima para reportar un bug, Perspectiva del Operador del Cliente

### Community 164 - "STU-ADR-002-identidad-y-licencia.md"
Cohesion: 0.25
Nodes (7): Alternativas consideradas, Consecuencias, Contexto, Decisión, Modelo de identidad, Reparto de responsabilidades de licencia, Sesión

### Community 166 - "Overlay — `hira-server/`"
Cohesion: 0.25
Nodes (8): Arquitectura — regla de oro (`SRV-ADR-017`), Contract-First, Frontend (`hira-server/frontend/src/`), Orden de lectura al iniciar sesión, Overlay — `hira-server/`, Prohibiciones específicas, Puntos — asociación explícita (`SRV-ADR-012`, `SRV-ADR-019`), Scopes de commit (`<tipo>(<scope>): …`)

### Community 167 - "§3 · Flujo de 5 fases (carril SDD)"
Cohesion: 0.25
Nodes (8): §3 · Flujo de 5 fases (carril SDD), Antes de Fase 4 *(de `using-git-worktrees`, `obra/superpowers`, 302k★)*, Cierre (Session-End), Fase 1 · Specify — elicitación interactiva con el usuario, Fase 2 · Plan, Fase 3 · Tasks, Fase 4 · Implement & Validate, Fase 5 · Converge *(tomado de `/speckit-converge`, spec-kit, GitHub, 141k★)*

### Community 169 - "Overlay — `hira-server/`"
Cohesion: 0.15
Nodes (10): Arquitectura — regla de oro (`SRV-ADR-017`), Contract-First, Frontend (`hira-server/frontend/src/`), Orden de lectura al iniciar sesión, Overlay — `hira-server/`, Prohibiciones específicas, Puntos — asociación explícita (`SRV-ADR-012`, `SRV-ADR-019`), Scopes de commit (`<tipo>(<scope>): …`) (+2 more)

### Community 170 - "experto-ux-ui.md"
Cohesion: 0.29
Nodes (6): Arranque, Cuándo intervienes, Entrega, Estándar que aplicas (checklist), Reglas duras, Sistema de diseño — ecosistema Hira

### Community 171 - "E-ADR-001-studio-producto-cloud-independiente.md"
Cohesion: 0.29
Nodes (6): Alternativas consideradas, Consecuencias, Contexto, Decisión, Qué queda por diseñar, Qué supersede

### Community 172 - "E-ADR-003-convencion-rfc9457-type.md"
Cohesion: 0.29
Nodes (5): Alternativas consideradas, Consecuencias, Contexto, Decisión, Enlaces

### Community 173 - "validation.md"
Cohesion: 0.29
Nodes (6): Gate de Salida, Pruebas de Seguridad, Sprint H0 — Walking Skeleton, Sprint H1 — Gestión de Licencias, Sprint H2 — Crash Reports y Versiones, Sprint H3 — Operación y Resiliencia

### Community 174 - "postmortems-y-aprendizaje.md"
Cohesion: 0.29
Nodes (6): Aprendizaje Continuo, Gate de Salida, Métricas de Incidencias, Postmortem (SEV-1 obligatorio), Registro de Incidencias, Registro de Postmortems

### Community 175 - "navegacion-y-responsividad.md"
Cohesion: 0.29
Nodes (6): Accesibilidad, Arquitectura de Navegación, Gate de Salida, Layout principal, Responsividad, Sidebar — estructura de navegación

### Community 176 - "Anclas y `registry.yaml`"
Cohesion: 0.29
Nodes (6): Anclas y `registry.yaml`, Estados, Lo que verifica `traceability_gate.py`, `registry.yaml`, Reglas, Tipos de ancla

### Community 177 - "Módulo `<nombre>`"
Cohesion: 0.29
Nodes (6): Anclas, Archivos, Cómo funciona, Dependencias, Módulo `<nombre>`, Propósito

### Community 178 - "sprint.md"
Cohesion: 0.29
Nodes (6): Anclas del sprint, Gate de cierre, Objetivo, T-1 — <título>, T-2 — <título>, Tareas

### Community 179 - "Ecosistema Hira — instrucciones base"
Cohesion: 0.29
Nodes (6): Commits, Definition of Done, Ecosistema Hira — instrucciones base, Equipo de agentes, Los tres componentes, Reglas transversales (todas las apps)

### Community 180 - "ADR-000 · ‹Título de la decisión›"
Cohesion: 0.29
Nodes (6): ADR-000 · ‹Título de la decisión›, Consecuencias, Contexto y planteamiento del problema, Decisión, Enlaces, Opciones consideradas

### Community 181 - "ADR-004 · Refresco de rutas post-`ADR-001` y retiro de `MODULE.md`"
Cohesion: 0.29
Nodes (6): ADR-004 · Refresco de rutas post-`ADR-001` y retiro de `MODULE.md`, Consecuencias, Contexto y planteamiento del problema, Decisión, Enlaces, Opciones consideradas

### Community 184 - "RedisAdapter"
Cohesion: 0.12
Nodes (4): adapters/cache, RedisAdapter, test_factory_get_cache_port_reads_password_from_settings(), test_redis_adapter_passes_password_to_client()

### Community 187 - "Hira"
Cohesion: 0.29
Nodes (7): Componentes, Cómo se desarrolla — Harness SDD-Anchored, Empieza por, Estado, Gates, Hira, Licencia

### Community 188 - "Glosario"
Cohesion: 0.33
Nodes (5): Datos y protocolos, Ecosistema, Glosario, Harness, Licencia y portabilidad

### Community 189 - "guia-frontend.md"
Cohesion: 0.33
Nodes (5): Decisiones de Implementación, Esquema JSON de Mimics, Estructura del Frontend, Gate de Salida, Zustand para estado global

### Community 190 - "backup-y-portabilidad.md"
Cohesion: 0.33
Nodes (5): Gate de Salida, L1 — Exportación de Proyecto (paquete `.hira`), L2 — Backup Automatizado Local, L3 — Replicación Activo-Pasivo (Enterprise), Niveles de Disponibilidad

### Community 191 - "flujos-criticos-de-usuario.md"
Cohesion: 0.33
Nodes (5): Flujo 1 — Reconocimiento de alarma crítica, Flujo 2 — Escritura de valor a un punto, Flujo 3 — Sesión de ingeniería remota activa, Flujo 4 — Conexión remota desde la instalación local del integrador, Gate de Salida

### Community 192 - "ADR-002 · Forzar la Fase 1 y el gate automático (corrección de diseño del arnés)"
Cohesion: 0.33
Nodes (5): ADR-002 · Forzar la Fase 1 y el gate automático (corrección de diseño del arnés), Consecuencias, Contexto y planteamiento del problema, Decisión, Enlaces

### Community 193 - "ADR-003 · Especialista de UX/UI en el arnés"
Cohesion: 0.33
Nodes (5): ADR-003 · Especialista de UX/UI en el arnés, Consecuencias, Contexto y planteamiento del problema, Decisión, Enlaces

### Community 194 - "§7 · Gates 0–4 (checklists de revisión)"
Cohesion: 0.29
Nodes (7): §7 · Gates 0–5 (checklists de revisión), Gate 0 — ¿entra al arnés?, Gate 1 — salida de Specify, Gate 2 — salida de Plan, Gate 3 — salida de Tasks *(mayormente automático)*, Gate 4 — antes del merge, Gate 5 — Converge

### Community 200 - "implementador.md"
Cohesion: 0.40
Nodes (4): Arranque, Directiva de Pausa (`method.md §5`), Por cada tarea, Reglas duras

### Community 201 - "orquestador.md"
Cohesion: 0.40
Nodes (4): Arranque (en orden), Ciclo, Cierre de sesión, Reglas duras

### Community 202 - ".claude/agents/ — binding de Claude Code"
Cohesion: 0.40
Nodes (4): Base (añadidos 2026-09-04, esquema simplificado), .claude/agents/ — binding de Claude Code, Especialista de UX/UI (activo — `ADR-003`), Especialistas de módulo (pre-diseñados)

### Community 203 - "HUB-ADR-01-mismo-stack-que-server.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 204 - "HUB-ADR-02-license-keys-opacas-hash.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 205 - "HUB-ADR-03-grace-period-72h.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 206 - "HUB-ADR-04-crash-reports-opt-in-sanitizados.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 207 - "SRV-ADR-001-despliegue-on-premise.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 208 - "SRV-ADR-002-python-backend-unico.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 209 - "SRV-ADR-003-redis-bus-tiempo-real.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 210 - "SRV-ADR-004-timescaledb-series-de-tiempo.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 211 - "SRV-ADR-005-rbac-dinamico.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 212 - "SRV-ADR-006-modulo-ia-desacoplado-opcional.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 213 - "SRV-ADR-007-motor-logica-python-monaco.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 214 - "SRV-ADR-008-react-flow-mimics.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 215 - "SRV-ADR-009-dos-capas-ejecucion-python.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 216 - "SRV-ADR-010-auto-documentacion.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 217 - "SRV-ADR-011-documentacion-base-rag.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 218 - "SRV-ADR-012-escaneo-asociacion-explicita-puntos.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 219 - "SRV-ADR-013-dos-agentes-ia-por-stakeholder.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 220 - "SRV-ADR-014-simuladores-primera-clase.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 221 - "SRV-ADR-015-un-solo-producto-server-studio.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 222 - "SRV-ADR-016-sesion-ingenieria-remota.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 223 - "SRV-ADR-018-licenciamiento-puntos-en-linea.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 224 - "SRV-ADR-019-puntos-variables-unificadas.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 225 - "SRV-ADR-020-multiproyecto-licencia-integrador.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 226 - "SRV-ADR-021-modelo-ia-interno-ollama.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 227 - "SRV-ADR-UI-01-material-design-3.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 228 - "SRV-ADR-UI-02-sidebar-oculta-modulos.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 229 - "SRV-ADR-UI-03-tiempo-real-sin-polling.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 230 - "SRV-ADR-UI-04-monaco-editor.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 231 - "apis.md"
Cohesion: 0.40
Nodes (4): Autenticación, Endpoints críticos, Gate de Salida, Grupos de endpoints

### Community 232 - "motor-logica-y-pruebas.md"
Cohesion: 0.40
Nodes (4): Gate de Salida, Motor de Lógica (operación continua), Motor de Pruebas (ejecución única o acotada), Sandbox

### Community 233 - "STU-ADR-005-agente-integrador-en-studio.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 234 - "architecture.md"
Cohesion: 0.40
Nodes (4): Contenedores, Fronteras, Módulos del BFF, Paridad con Hira Server

### Community 235 - "Migración vault → harness (F0)"
Cohesion: 0.40
Nodes (4): Cobertura, Contenido nuevo creado en F0, Migración vault → harness (F0), Transformaciones aplicadas

### Community 236 - "adr.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

### Community 237 - "TASKS-NNN · ‹Nombre›"
Cohesion: 0.40
Nodes (4): Cobertura (el gate exige 100 %; `Estado` lo rellena el gate), Reglas, Tareas, TASKS-NNN · ‹Nombre›

### Community 239 - "test_device_repository_adapter.py"
Cohesion: 0.15
Nodes (7): _clean_tables(), repository(), _reset_tables(), test_get_device_by_address_returns_none_if_not_found(), test_get_device_returns_none_if_not_found(), test_upsert_device_can_mark_existing_real_row_as_simulator(), test_upsert_device_creates_new_device()

### Community 240 - "arquitecto.md"
Cohesion: 0.50
Nodes (3): Arranque, Produces `plan.md` (plantilla: `.harness/specs/_template/plan.md`), Reglas duras

### Community 241 - "autor-de-spec.md"
Cohesion: 0.50
Nodes (3): Arranque, El bucle (hasta converger), Reglas duras

### Community 242 - "hira-alarmas"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-alarmas

### Community 243 - "hira-auth"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-auth

### Community 244 - "hira-backup"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-backup

### Community 245 - "hira-contratos"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-contratos

### Community 246 - "hira-datos"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-datos

### Community 247 - "hira-frontend"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-frontend

### Community 248 - "hira-ia"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-ia

### Community 249 - "hira-infra"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-infra

### Community 250 - "hira-licencia"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-licencia

### Community 251 - "hira-logica"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-logica

### Community 252 - "hira-protocolos"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-protocolos

### Community 253 - "hira-qa"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-qa

### Community 254 - "hira-tiempo-real"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hira-tiempo-real

### Community 255 - "hub-licencias"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hub-licencias

### Community 256 - "hub-reports"
Cohesion: 0.50
Nodes (3): Alcance (anclas), Cómo trabajas, hub-reports

### Community 257 - "alarmas-historicos.md"
Cohesion: 0.50
Nodes (3): Gate de Salida, Históricos, Motor de Alarmas

### Community 258 - "stack-y-componentes.md"
Cohesion: 0.50
Nodes (3): Diagrama de Componentes (C4 L3), Gate de Salida, Stack Tecnológico

### Community 259 - "`.harness/`"
Cohesion: 0.50
Nodes (3): `.harness/`, Mapa, Origen

### Community 260 - "docs/ — documentación del producto (ecosistema Hira)"
Cohesion: 0.50
Nodes (3): Convención de anclas de producto (histórica, se mantiene), docs/ — documentación del producto (ecosistema Hira), Mapa

### Community 262 - "backend"
Cohesion: 0.50
Nodes (3): backend, Subcarpetas, Tests

### Community 264 - "Fronteras de salida"
Cohesion: 0.29
Nodes (7): 2. Arquitectura de la feature *(Hexagonal)*, `core/ports/bacnet_simulator_port.py` (nuevo), `core/ports/modbus_simulator_port.py` (nuevo), `core/ports/mqtt_publisher_port.py` (nuevo), `DeviceRepositoryPort` — ampliación (`core/ports/device_repository_port.py`), Fronteras de salida, Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks

### Community 265 - "mosquitto"
Cohesion: 0.50
Nodes (3): Generar / regenerar `password_file`, mosquitto, Por qué no hay volumen de persistencia

### Community 299 - "Ecosistema Hira — instrucciones base"
Cohesion: 0.33
Nodes (6): Commits, Definition of Done, Ecosistema Hira — instrucciones base, Equipo de agentes, Los tres componentes, Reglas transversales (todas las apps)

### Community 300 - "SRV-ADR-017-arquitectura-hexagonal.md"
Cohesion: 0.40
Nodes (4): Alternativas consideradas, Consecuencias, Contexto, Decisión

## Knowledge Gaps
- **69 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NotificationPort` connect `hira-server/backend/adapters/factory.py` to `scan_bacnet`, `MqttScanAdapter`, `UserRepositoryPort`, `Bitácora del arnés — ecosistema Hira`, `Tareas`, `PLAN-HUB-001 · Walking Skeleton de Hira Hub`, `SRV-ADR-017-arquitectura-hexagonal.md`, `PLAN-SRV-001 · Walking Skeleton de Hira Server`, `SPEC-SRV-001 · Walking Skeleton de Hira Server`, `Tareas`, `E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md`, `hira-server/backend/routers/monitor.py`, `harness`, `2. Arquitectura de la feature *(Hexagonal)*`, `hira-server/backend/services/health_service.py`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `ProblemDetailError` (e.g. with `5. Estrategia de pruebas (por zona del patrón)` and `6. Secuenciación de archivos (tests antes que código)`) actually correct?**
  _`ProblemDetailError` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Should `DeviceRepositoryPort` be split into smaller, more focused modules?**
  _Cohesion score 0.07547169811320754 - nodes in this community are weakly interconnected._
- **Why does `ProblemDetailError` connect `test_simulator_service.py` to `DeviceRepositoryPort`, `test_device_scan_service.py`, `UserRepositoryPort`, `LocalPermissionsCache`, `test_rbac_dependencies.py`, `login`, `LocalPermissionsCache`, `test_auth_security.py`, `list_device_candidates`, `scan_modbus`, `resolve_permissions`, `auth_service.py`, `asyncio`, `start_mqtt_simulator`, `BacnetTransportPort`, `hash_password`, `hira-server/backend/core/middleware.py`, `_build_app`, `scan_bacnet`, `MqttScanAdapter`, `ProblemDetail`, `topic_instance_key`, `can_access_project`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `SimulatorRegistryService` (e.g. with `0. Gates de simplicidad` and `1. Cumplimiento constitucional`) actually correct?**
  _`SimulatorRegistryService` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_simulators_router.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09024390243902439 - nodes in this community are weakly interconnected._
- **Why does `MosquittoAdapter` connect `hira-server/backend/adapters/factory.py` to `test_simulators_router.py`, `PostgreSQLUserRepository`, `MqttScanAdapter`, `SimulatorRegistryService`, `test_devices_router.py`, `test_main_lifespan.py`, `test_devices_scan_e2e.py`, `test_simulators_e2e.py`, `mosquitto_adapter.py`, `mosquitto_adapter.py`, `harness`, `2. Arquitectura de la feature *(Hexagonal)*`, `test_auth_router.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._