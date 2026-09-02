---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.2 - Modelo de Datos.md"
título: Modelo de Datos — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, modelo-de-datos]
---

## Convención

Esquema válido tanto para PostgreSQL (instancia comercial) como SQLite (instancia local del integrador) — mismo esquema relacional, sin las extensiones TimescaleDB/pgvector en SQLite (ver SRV-ADR-017).

---

## Usuarios y control de acceso

```sql
users           (id, email, name, password_hash, created_at, is_active)
roles           (id, name, description, scope, created_at)
  -- scope: project | global
  -- Roles de operación (Operador, Visor, roles de instalación) son scope=project
  -- Roles de integrador son scope=global — ver SRV-ADR-020
permissions     (id, role_id, module, area, access_level)
  -- access_level: read | write | admin
user_roles      (user_id, role_id, project_id NULL)
  -- project_id NULL cuando el rol es global (usuario integrador)
  -- project_id requerido cuando el rol es scope=project
```

## Proyectos

```sql
projects        (id, name, description, timezone, scan_interval_ms, created_at)
  -- En instancia comercial: máximo 1 registro (ver SRV-ADR-020)
  -- En instancia local del integrador: múltiples registros (multi-proyecto)
```

## Dispositivos y puntos

```sql
devices               (id, project_id, name, protocol, address, port, config_json, area, status, is_simulator)
  -- protocol: bacnet | modbus | mqtt

device_points_candidates (id, device_id, object_type, address, unit, description, discovered_at)
  -- Resultado crudo del escaneo (Who-Is/I-Am, scan de registros, discovery de topics)
  -- NUNCA utilizable en línea directamente — ver SRV-ADR-012, SRV-ADR-019

points                (id, project_id, name, description, kind, device_point_id NULL,
                       access_mode, bacnet_write_priority NULL, unit,
                       log_enabled, log_interval_ms, area)
  -- kind: bound | internal
  --   bound: device_point_id NOT NULL — asociado a un candidato de un dispositivo real
  --   internal: device_point_id NULL — variable interna de la plataforma, sin controlador asociado
  -- access_mode: read | read_write — definido en el momento de la asociación
  -- bacnet_write_priority: 1-16, solo aplica si el punto asociado es de protocolo BACnet
  -- Un punto solo es escribible, historizable, alarmable y consultable por el RAG
  --   si existe como registro en esta tabla — nunca directamente desde device_points_candidates
```

**Regla de negocio (SRV-ADR-019):** un punto sin asociar (solo en `device_points_candidates`) no participa en polling, escritura, alarmas, históricos, mimics ni RAG. El límite de puntos de la licencia (ver SRV-ADR-018) cuenta filas de `points`, sin importar si son `bound` o `internal`.

## Alarmas

```sql
alarm_definitions (id, point_id, condition, threshold, priority, message)
  -- condition: gt | lt | eq | ne | between
  -- priority: critical | high | medium | low
alarms          (id, definition_id, point_id, value_at_trigger,
                 triggered_at, acknowledged_at, acknowledged_by,
                 resolved_at, notes)
```

## Históricos (TimescaleDB hypertable en instancia comercial; tabla estándar en SQLite)

```sql
point_history   (time TIMESTAMPTZ, point_id, value DOUBLE, quality)
  -- Particionado por tiempo, retención configurable por punto
```

## Scripts de lógica y pruebas

```sql
logic_scripts   (id, project_id, name, description, code, status, created_by,
                 created_at, last_run_at)
  -- status: active | paused | error
test_scripts    (id, project_id, name, description, code, template_name,
                 created_by, created_at)
script_executions (id, script_id, script_type, started_at, finished_at,
                   status, log, result_json)
  -- script_type: logic | test
point_locks     (point_id, locked_by_execution_id, locked_at)
  -- En Redis con TTL obligatorio: SETEX lock:point:{id} {ttl} {execution_id}
  -- TTL default: 3600s (1 hora). Worker refresca el TTL cada 60s mientras la prueba corre
  -- Si el worker muere, el TTL expira automáticamente y los locks se liberan solos
  -- Tiempo máximo de prueba configurable en project_config (max_test_duration_s)
```

## Documentación

```sql
documents       (id, project_id, type, title, content, created_by, created_at, updated_at)
  -- type: manual | flowchart | wiring_diagram | points_list | procedure
document_embeddings (id, document_id, chunk_text, embedding VECTOR(1536))
  -- pgvector: indexado con ivfflat para búsqueda semántica — solo instancia comercial
```

## IA

```sql
ai_config       (id, project_id, instance, provider, api_key_encrypted, model, created_at)
  -- instance: integrator | client
  -- provider: claude | openai | ollama

ai_usage_log    (id, timestamp TIMESTAMPTZ, agent_type, user_id, project_id,
                 provider, model, tokens_input, tokens_output,
                 cost_usd NUMERIC(10,6), duration_ms, session_id UUID, metadata JSONB)
  -- agent_type: integrator | client
  -- Retención: 90 días rolling (TimescaleDB retention policy en instancia comercial)
```

## Notificaciones

```sql
notification_config (id, event_type, severity_min, channel, enabled,
                     recipients JSONB, webhook_url, webhook_secret,
                     cooldown_min INTEGER DEFAULT 30)
  -- channel: email | webhook | both | inapp

notifications       (id, timestamp TIMESTAMPTZ, event_type, severity,
                     details JSONB, sent_via JSONB, read_at TIMESTAMPTZ)

crash_reports_sent  (id, timestamp TIMESTAMPTZ, error_hash VARCHAR(64),
                     report_id UUID, status VARCHAR(20))
  -- status: sent | pending | failed
  -- error_hash: permite rate limiting (1 reporte/hash/hora)
```

## Sesión de ingeniería remota

```sql
engineering_sessions (id UUID PRIMARY KEY, project_id, started_at TIMESTAMPTZ,
                      integrator_user_id INTEGER REFERENCES users(id),
                      client_version VARCHAR(20), client_ip VARCHAR(45),
                      status VARCHAR(20) DEFAULT 'active')
  -- status: active | closed | expired
  -- Solo un registro active por proyecto (constraint único) — ver SRV-ADR-016
  -- Redis key espejo: engineering_session:{project_id} con TTL 300s, heartbeat 60s
```

## Backup

```sql
backup_log      (id, timestamp TIMESTAMPTZ, project_id, backup_type, status,
                 file_path, size_bytes, duration_ms, error_message)
  -- backup_type: scheduled | manual | pre-restore
  -- status: success | failed
```

## Licencia

```sql
license         (id, key_hash, license_type, tier, max_points_online, max_users,
                 issued_at, expires_support_at, hardware_fingerprint)
  -- license_type: integrator | commercial — ver SRV-ADR-018
  -- tier (solo commercial): starter | professional | enterprise
  -- max_points_online: tope de puntos con kind=bound O internal activos simultáneamente
  --   en licencia integrator, es un tope de demo fijo, no ligado a tier
  -- Multi-proyecto (tabla projects con >1 fila) solo válido si license_type=integrator — ver SRV-ADR-020
```

---

## Gate de Salida

- [x] Modelo de datos actualizado con el modelo de puntos candidatos/asociados (SRV-ADR-012, SRV-ADR-019)
- [x] `points.device_id` reemplazado por asociación explícita vía `device_point_id`, nullable
- [x] `projects` y alcance de roles (project/global) reflejan SRV-ADR-020
- [x] `license` refleja licenciamiento por puntos en línea (SRV-ADR-018)
- [ ] Revisado y aprobado por Charlie
