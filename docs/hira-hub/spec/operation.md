---
origen_vault: "7.2 - Hira Hub/7.2.9 - Operación.md"
título: Operación — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 09 — Operación
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, operación]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Niveles de Servicio (SLOs)

| Indicador | Objetivo | Acción si se incumple |
|---|---|---|
| Disponibilidad Hub | ≥ 99% mensual (máx ~7h caídas/mes) | Investigar causa, documentar en bitácora |
| Latencia `POST /api/licenses/validate` P95 | < 500ms | Revisar queries a BD |
| Backup diario | 100% éxito (0 fallos/semana) | Restaurar proceso, verificar espacio en disco |

> **Nota:** Los SLOs son compromisos internos de cjhirashi — no hay SLA formal con integradores para Hub.

---

## Estado del Sistema

| Componente | Indicador de salud | Cómo revisar |
|---|---|---|
| Hub Backend | `GET /health` → `"backend": "ok"` | UptimeRobot + Panel Admin |
| PostgreSQL | `GET /health` → `"postgres": "ok"` | `docker compose ps postgres` |
| Redis | `GET /health` → `"redis": "ok"` | `docker compose ps redis` |
| Nginx | Código de respuesta 200/301 | UptimeRobot |
| SSL | Certificado válido (expira en > 30 días) | `certbot certificates` |

---

## Rutina Diaria

Tiempo estimado: 2–3 minutos

1. Revisar UptimeRobot — alertas de las últimas 24h
2. Abrir Panel Admin Hub:
   - **Licencias:** alguna próxima a vencer o revocada por error?
   - **Crash Reports:** nuevos reportes sin revisar?
   - **Versiones:** hay update pendiente de publicar?

---

## Gestión de Licencias

### Emitir una nueva license key

1. Panel Admin → Licencias → "Emitir nueva key"
2. Completar: producto (server/studio), tier, email del integrador, max_activations, fecha de expiración (opcional)
3. Copiar la key inmediatamente — se muestra UNA SOLA VEZ
4. Enviar al integrador por correo con instrucciones de uso

### Revocar una license key

1. Panel Admin → Licencias → buscar por `key_prefix`
2. Clic en "Revocar" → confirmar
3. Efecto inmediato: la siguiente validación devuelve 403
4. Registrar razón de revocación en el campo `notes` de la key

### Extender vencimiento

1. Panel Admin → Licencias → buscar → "Editar"
2. Modificar `expires_at`
3. El Server lo detecta en la siguiente validación periódica

---

## Gestión de Crash Reports

### Proceso semanal de revisión

1. Panel Admin → Crash Reports → filtrar `is_reviewed = false`
2. Para cada grupo de reports:
   a. Leer el stack trace — ¿es un bug conocido?
   b. Si es bug nuevo: crear issue en GitHub con el stack trace
   c. Pegar URL del issue en el campo `github_issue_url`
   d. Marcar como revisado
3. Si el crash es crítico (afecta funcionalidad core): priorizar en sprint activo de Hira Server

### Criterios de criticidad

| Criticidad | Criterio |
|---|---|
| Crítico | Crash en módulo de protocolos (BACnet, Modbus) o en auth |
| Mayor | Crash repetido (> 5 veces) en el mismo módulo |
| Menor | Crash aislado en módulo no crítico |

---

## Publicación de Actualizaciones

```
cjhirashi hace git tag v0.X.X en hira-server
  → GitHub Actions construye y publica imagen en GHCR
  → Panel Admin Hub → Versiones → "Publicar versión"
  → Completar: product, version, release_notes, docker_image_tag
  → Activar "Marcar como latest"
  → Los Servers consultan /api/updates/latest cada 24h
  → Panel Admin del Server muestra notificación al integrador
  → El integrador decide cuándo actualizar (no es automático)
```

---

## Runbooks (RB)

### RB-H01 — Hub caído (VPS inaccesible o servicio down)

```
Detectado por: UptimeRobot → email de alerta

1. SSH al VPS:
   ssh cjhirashi@hub.hira.cjhirashi.com

2. Ver estado de servicios:
   cd /opt/hira-hub
   docker compose ps

3. Si algún contenedor está Down o Restarting:
   docker compose logs --tail=50 [nombre-servicio]
   docker compose restart [nombre-servicio]

4. Si el problema persiste tras restart:
   docker compose down
   docker compose up -d

5. Verificar:
   curl https://hub.hira.cjhirashi.com/health

6. Si el VPS mismo es inaccesible:
   → Panel de control del proveedor VPS (Hetzner/DigitalOcean)
   → Reiniciar el servidor desde el panel

Nota: Si Hub está caído, los Servers continúan operando durante 72h
(grace period) — el impacto en los clientes es mínimo en el corto plazo.
```

### RB-H02 — Disco lleno en el VPS

```
Detectado por: logs de Docker con "no space left on device"

1. Ver uso de disco:
   df -h

2. Limpiar imágenes Docker antiguas:
   docker image prune -a --filter "until=168h"

3. Limpiar backups viejos:
   ls -lh /opt/backups/
   find /opt/backups -name "hub_*.sql.gz" -mtime +7 -delete

4. Si el problema persiste: ampliar disco en panel del proveedor VPS
```

### RB-H03 — Certificado SSL próximo a vencer

```
Certbot renueva automáticamente. Si falla:

1. Verificar estado del certificado:
   certbot certificates

2. Renovar manualmente:
   certbot renew --force-renewal

3. Recargar Nginx:
   systemctl reload nginx

4. Verificar:
   curl -I https://hub.hira.cjhirashi.com/health
```

### RB-H04 — Base de datos corrupta o pérdida de datos

```
1. Detener el backend:
   docker compose stop backend

2. Identificar el backup más reciente:
   ls -lt /opt/backups/hub_*.sql.gz | head -5

3. Restaurar:
   gunzip -c /opt/backups/hub_FECHA.sql.gz | \
     docker compose exec -T postgres psql -U hub -d hubdb

4. Reiniciar:
   docker compose start backend

5. Verificar:
   curl https://hub.hira.cjhirashi.com/health
   # Revisar en Panel Admin que las licencias estén intactas
```

---

## Gate de Salida

- [x] SLOs definidos
- [x] Rutina diaria documentada
- [x] Gestión de licencias documentada
- [x] Proceso de crash reports documentado
- [x] Flujo de publicación de actualizaciones documentado
- [x] Runbooks RB-H01 a RB-H04 listos
- [ ] Revisado y aprobado por Charlie
