---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.3 - Especificación de APIs.md"
título: Especificación de APIs — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, api]
---

## Grupos de endpoints

| Grupo | Base path | Descripción |
|---|---|---|
| Autenticación | `/auth` | Login, refresh token, logout |
| Proyectos | `/projects` | CRUD de proyectos — solo relevante en instancia con licencia de integrador (SRV-ADR-020) |
| Dispositivos | `/devices` | CRUD de dispositivos + escaneo de red |
| Puntos candidatos | `/devices/{id}/candidates` | Resultado de escaneo, pendiente de asociación |
| Puntos | `/points` | Asociación, lectura, escritura, suscripción a puntos |
| Alarmas | `/alarms` | Estado, reconocimiento, historial, configuración |
| Históricos | `/historicals` | Consulta por rango, agregaciones, exportación |
| Lógica | `/logic` | CRUD scripts continuos, start/stop, estado de ejecución |
| Pruebas | `/tests` | CRUD scripts de prueba, ejecución, resultados |
| Análisis | `/analysis` | Consulta de resultados, generación PDF/CSV |
| Documentación | `/docs` | CRUD documentos, búsqueda semántica, diagramas |
| Usuarios | `/users` | CRUD usuarios, roles y permisos RBAC |
| Agente IA | `/ai` | Chat con agente integrador o cliente, config API keys |
| Monitoreo | `/monitor` | Métricas de sistema, dispositivos, consumo de tokens IA |
| Backup | `/backup` | Exportar/importar proyecto, estado y log de backups |
| Licencia | `/license` | Validación, estado, puntos en línea, info de tier |
| Ingeniería remota | `/engineering` | Sesión de ingeniería remota (ver SRV-ADR-016) |
| WebSocket | `ws://host/ws` | Stream de datos en tiempo real, notificaciones de alarma |

## Autenticación

- **JWT** con access token (15 min) + refresh token (7 días)
- Todos los endpoints protegidos excepto `/auth/login`
- RBAC evaluado en middleware por cada request — alcance por proyecto o global según el tipo de usuario (ver SRV-ADR-020)

## Endpoints críticos

```
POST   /auth/login              → { access_token, refresh_token, user, roles }
POST   /auth/refresh            → { access_token }

GET    /projects                → Lista de proyectos (solo licencia integrador)
POST   /projects                → Crea proyecto nuevo
PUT    /projects/{id}/activate  → Cambia el proyecto activo en la instancia local

GET    /devices                 → Lista de dispositivos del proyecto activo
POST   /devices/scan            → Inicia escaneo de red por protocolo
GET    /devices/{id}/candidates → Lista de puntos candidatos descubiertos en el dispositivo

POST   /points/associate        → Asocia un punto candidato a un punto Hira
                                   body: { device_point_id | null, kind, access_mode, bacnet_write_priority? }
GET    /points/{id}/value       → Valor actual del punto asociado
POST   /points/{id}/write       → Escribe valor al punto (verifica permisos RBAC + access_mode)
GET    /points/{id}/history     → Histórico del punto (params: from, to, interval)

GET    /alarms                  → Alarmas activas
POST   /alarms/{id}/acknowledge → Reconoce alarma con nota
GET    /alarms/history          → Historial de alarmas con filtros

POST   /logic/scripts           → Crea script de lógica continua
POST   /logic/scripts/{id}/start → Inicia ejecución
POST   /logic/scripts/{id}/stop  → Detiene ejecución
GET    /logic/scripts/{id}/diagram → Diagrama de flujo AST del script

POST   /tests/scripts           → Crea script de prueba
POST   /tests/scripts/{id}/run  → Ejecuta prueba (cola HIGH, registra locks)
GET    /tests/scripts/{id}/results → Resultados de la última ejecución

POST   /ai/integrator/chat      → Mensaje al Agente Integrador
POST   /ai/client/chat          → Mensaje al Agente Cliente
PUT    /ai/integrator/config    → Configura API key del Agente Integrador
PUT    /ai/client/config        → Configura API key del Agente Cliente

GET    /docs/search?q=...       → Búsqueda semántica en documentación (RAG)
POST   /docs/manual             → Crea documento manual
GET    /docs/points-list        → Lista de puntos asociados, auto-generada del proyecto

GET    /monitor/system          → Métricas de contenedores, API y workers (Prometheus/Grafana iframe)
GET    /monitor/devices         → Estado de conectividad y polling por dispositivo
GET    /monitor/ai-usage        → Consumo de tokens y costo estimado por agente y período
POST   /monitor/ai-budget       → Configura umbral de presupuesto de tokens por agente

GET    /backup/status           → Estado del último backup y log
POST   /backup/export           → Genera paquete .hira del proyecto activo
POST   /backup/import           → Restaura desde paquete .hira subido

GET    /license/status          → Tipo de licencia, tier, puntos en línea usados/tope
POST   /engineering/session     → Inicia sesión de ingeniería remota (ver SRV-ADR-016)
DELETE /engineering/session     → Cierra sesión de ingeniería remota
PUT    /engineering/session/heartbeat → Refresca TTL del lock cada 60s
GET    /engineering/session     → Estado: activo/inactivo, quién tiene el lock
```

---

## Gate de Salida

- [x] Grupos de endpoints y endpoints críticos definidos
- [x] Endpoints de asociación de puntos y proyectos multi-instancia añadidos
- [ ] Revisado y aprobado por Charlie
