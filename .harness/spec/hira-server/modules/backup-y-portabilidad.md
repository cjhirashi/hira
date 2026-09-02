---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.10 - Backup y Portabilidad (.hira).md"
título: Backup y Portabilidad (.hira) — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, backup, portabilidad]
---

## Niveles de Disponibilidad

| Nivel | Nombre | Descripción | Tier disponible |
|---|---|---|---|
| **L1** | Exportación de proyecto (`.hira`) | Paquete exportable/importable para migrar un proyecto entre instalaciones — opcional, ver SRV-ADR-015 | Todos |
| **L2** | Backup automatizado local | pg_dump + config automático programado | Professional + Enterprise |
| **L3** | Replicación activo-pasivo | Streaming replication a servidor secundario | Enterprise |

---

## L1 — Exportación de Proyecto (paquete `.hira`)

Paquete ZIP (DEFLATE nivel 6) firmado con checksum SHA-256, que contiene todo lo necesario para restaurar el proyecto en otra instalación:

```
project_export_2026-07-31.hira
├── metadata.json          # versión de Hira, fecha, checksum SHA-256 del paquete
├── project_data.json      # config, dispositivos, puntos candidatos y asociados, alarmas, scripts, roles, usuarios
├── documents/              # documentación técnica del proyecto (manual/ y generated/)
├── mimics/                 # definición de mimics/gráficos (JSON)
├── ai_config.json          # config de agentes IA (sin API keys — se reconfiguran en destino)
└── history_export/         # OPCIONAL: históricos por rango de fechas (CSV comprimido)
                             # Tamaño máximo incluido: 5 GB sin comprimir; si se supera,
                             # el sistema avisa y permite exportar históricos por separado
```

**Serialización:** JSON estructurado por el ORM — nunca SQL crudo. La importación deserializa con validación de esquema Pydantic antes de tocar la base de datos (ver `.harness/spec/hira-server/modules/auth-rbac-seguridad.md`).

**Compatibilidad de versiones:** Hira siempre puede importar paquetes de la misma versión mayor. Paquetes de versiones anteriores se importan con migración automática (script de migración por versión). Paquetes de versiones futuras se rechazan con mensaje claro indicando la versión requerida.

**Estimación de tamaño típico (sin históricos):** < 50 MB para la mayoría de proyectos.

**API:** `POST /backup/export` (retorna URL de descarga temporal), `POST /backup/import` (restaura desde paquete subido).

**Proceso de restauración en instalación nueva:**
1. Instalar Docker + Docker Compose
2. Levantar Hira Server/Studio del mismo tier
3. Importar el paquete `.hira` desde el panel
4. Activar la license key de la instalación destino
5. Verificar conectividad con dispositivos — reemplazar simuladores por hardware real si aplica (ver CU-11)

Tiempo estimado de restauración: 5–20 minutos según el tamaño del proyecto.

---

## L2 — Backup Automatizado Local

- `Celery Beat` programa la tarea `backup_postgresql` según cron configurado
- Incluye `pg_dump` completo (datos + schema) + configuración de aplicación
- Almacenamiento local en volumen Docker persistente (`/backups`); opcionalmente copia a destino de red (UNC Windows o path Linux)

```json
{
  "backup": {
    "enabled": true,
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "include_history": true,
    "network_destination": "\\\\NAS\\hira-backups",
    "notify_on_failure": true
  }
}
```

Auditoría en tabla `backup_log` (ver `.harness/spec/hira-server/modules/modelo-de-datos.md`).

---

## L3 — Replicación Activo-Pasivo (Enterprise)

```
Servidor Primario (Hira activo) ──PostgreSQL streaming──► Servidor Secundario (Hira standby)
Redis (sync periódico, no streaming nativo)
```

- **PostgreSQL:** streaming replication nativo (WAL)
- **Redis:** sin streaming replication — sincronización periódica, aceptable para estado de sesiones
- **Config:** volumen compartido o rsync
- **Health check:** endpoint `/health` monitoreado por el secundario

**Failover:**
1. El secundario detecta que el primario no responde (timeout configurable)
2. Manual (default): el administrador promueve el secundario desde el panel o vía script
3. Semi-automático (config avanzada): promoción automática tras N segundos sin respuesta
4. El nuevo primario asume la license key

**Limitación:** BACnet y Modbus requieren un único cliente activo por red — si ambos servidores intentan conectarse simultáneamente puede haber conflicto. El failover manual evita este riesgo. Solo tier Enterprise, requiere dos licencias.

---

## Gate de Salida

- [x] Formato del paquete `.hira` documentado, alineado con SRV-ADR-015 (exportación opcional)
- [x] L2 y L3 documentados sin cambios respecto al diseño original
- [ ] Revisado y aprobado por Charlie
