---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.9 - Monitoreo y Notificaciones.md"
título: Monitoreo y Notificaciones — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, monitoreo, notificaciones, observabilidad]
---

## Arquitectura de Observabilidad

Prometheus + Grafana como contenedores adicionales en Docker Compose:

```
FastAPI ──────► /metrics (Prometheus endpoint)
Celery workers ► custom metrics vía prometheus_client
PostgreSQL ───► postgres_exporter
Redis ────────► redis_exporter
                        │
                   Prometheus ◄── scrape cada 15s
                        │
                   Grafana ──► dashboards embebidos en panel admin
```

## Capa 1 — Métricas operativas del sistema

| Categoría | Métrica | Tipo | Umbral de alerta |
|---|---|---|---|
| Contenedores | CPU por contenedor | Gauge | > 80% sostenido |
| Contenedores | RAM por contenedor | Gauge | > 85% del límite |
| API | Latencia de endpoints (p50, p95, p99) | Histogram | p95 > 500ms |
| API | Tasa de errores HTTP 5xx | Counter | > 1% de requests |
| Celery | Profundidad de cola `high` (pruebas) | Gauge | > 10 tareas pendientes |
| Celery | Profundidad de cola `normal` (lógica) | Gauge | > 50 tareas pendientes |
| Celery | Tareas con status `error` | Counter | Cualquiera |
| Redis | Uso de memoria | Gauge | > 80% del `maxmemory` |
| PostgreSQL | Tamaño de `point_history` | Gauge | > 80% del disco |
| PostgreSQL | Tiempo de query lento | Histogram | > 1 segundo |
| WebSocket | Conexiones activas de clientes | Gauge | Referencia |

## Capa 2 — Métricas de agentes IA

Ver `.harness/spec/hira-server/modules/agente-ia.md` — tabla `ai_usage_log` y métricas derivadas (`hira_ai_tokens_total`, `hira_ai_cost_usd_total`, etc.). Dashboards en Grafana: consumo diario/semanal por agente, costo acumulado, costo por usuario, top de operaciones más costosas.

## Capa 3 — Métricas de dispositivos

| Métrica | Descripción | Alerta |
|---|---|---|
| `device_online` | 1=online, 0=offline | Si 0 por más de N segundos (configurable) |
| `polling_success_rate` | % de polls exitosos en últimos 5 min | < 90% |
| `polling_latency_ms` | Latencia media de respuesta | > 2× el intervalo de polling |
| `point_value_age_seconds` | Tiempo desde la última lectura válida de un punto asociado | > 2× el intervalo configurado |
| `write_error_count` | Comandos de escritura fallidos | > 0 consecutivos |
| `reconnection_count` | Número de reconexiones | Tendencia ascendente es alerta |

Por protocolo: `bacnet_who_is_failures`, `modbus_exception_codes`, `mqtt_broker_connections` / `message_rate`.

## Sistema de Notificaciones

### Canal 1 — Notificaciones al Integrador

| Evento | Condición | Severidad default |
|---|---|---|
| `device_offline` | Dispositivo sin respuesta > umbral configurable | Crítico |
| `worker_crash` | Worker Celery termina con error no recuperable | Crítico |
| `disk_space_low` | Disco del servidor < 15% disponible | Alto |
| `backup_failed` | Tarea de backup programada falla | Alto |
| `alarm_flood` | > N alarmas activas simultáneas en < 1 minuto | Alto |
| `ai_budget_exceeded` | Consumo de tokens supera umbral configurado | Medio |
| `logic_script_error` | Script de lógica continua termina en estado `error` | Medio |
| `point_value_stale` | Punto sin actualización válida > 2× su intervalo por > 10 min | Medio |

Canales de entrega: Email (SMTP), Webhook (POST JSON firmado con HMAC en header `X-Hira-Signature`, HTTPS obligatorio), Panel in-app. Rate limiting por `cooldown_min` en `notification_config` evita flood del mismo evento repetido.

```json
{
  "hira_version": "0.1.0",
  "installation_id": "uuid-de-la-instalación",
  "project_name": "Edificio Torre Norte",
  "event": "device_offline",
  "severity": "critical",
  "timestamp": "2026-07-23T14:32:00Z",
  "details": { "device_id": 12, "device_name": "AHU-03", "protocol": "bacnet" },
  "panel_url": "http://192.168.1.100/devices/12"
}
```

### Canal 2 — Crash Reporter hacia el desarrollador (Hira Hub)

Telemetría técnica opt-in hacia Hira Hub (`crash.hira.cjhirashi.com`). Principios: desactivado por default, sin datos del proyecto (solo metadatos técnicos sanitizados), rate limiting de 1 reporte por hash de error por hora. El stack trace se sanitiza antes de enviarse: sin `locals()`, IPs reemplazadas, rutas normalizadas a relativas. Ver `7.2 - ÍNDICE - Hira Hub` para el lado receptor.

```json
{
  "report_id": "uuid",
  "hira_version": "0.1.0",
  "module": "protocol_engine.bacnet",
  "error_type": "UnhandledBAC0Exception",
  "stack_trace": "... (sanitizado)",
  "system_info": { "os": "linux", "python_version": "3.12.4", "docker": true, "memory_mb": 4096, "cpu_cores": 4 },
  "hira_state": { "device_count": 12, "point_count": 187, "active_scripts": 3, "uptime_hours": 142 }
}
```

Implementación: middleware de FastAPI + handler de errores de Celery → tarea `send_crash_report` → POST con retry (3 intentos, backoff exponencial). Instalaciones sin internet almacenan en buffer local y envían al recuperar conectividad.

---

## Gate de Salida

- [x] Tres capas de métricas documentadas
- [x] Dos canales de notificación documentados con estructura de payload
- [ ] Revisado y aprobado por Charlie
