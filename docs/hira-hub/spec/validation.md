---
origen_vault: "7.2 - Hira Hub/7.2.7 - Validación.md"
título: Validación — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 07 — Validación
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, validación]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Sprint H0 — Walking Skeleton

**Criterios de aceptación:**

- [ ] `docker compose up -d` levanta todos los contenedores sin errores
- [ ] `GET /health` responde 200 con `{"status": "ok", "services": {"postgres": "ok", "redis": "ok"}}`
- [ ] Los logs del backend son JSON estructurado (no texto plano)
- [ ] Los logs incluyen los campos: `timestamp`, `level`, `service`, `module`, `message`
- [ ] Nginx sirve correctamente en el dominio configurado

---

## Sprint H1 — Gestión de Licencias

**Criterios de aceptación:**

- [ ] cjhirashi puede emitir una license key desde el Panel Admin — la key se muestra UNA sola vez
- [ ] La key se almacena en BD como hash bcrypt — nunca en claro
- [ ] `POST /api/licenses/activate` con una key válida responde 201 con `{"valid": true, ...}`
- [ ] `POST /api/licenses/validate` con la misma key y hardware fingerprint responde 200 con `{"valid": true}`
- [ ] `POST /api/licenses/validate` con key inválida responde 403 con `{"valid": false, "reason": "..."}`
- [ ] `POST /api/licenses/validate` con más de 10 req/min desde misma IP es bloqueado por Nginx (429)
- [ ] cjhirashi puede revocar una key desde Panel Admin — validación siguiente devuelve 403
- [ ] HTTPS activo con certificado válido Let's Encrypt
- [ ] Las license keys NO aparecen en logs — solo el `key_prefix` (`HIRA-XXXX`)

---

## Sprint H2 — Crash Reports y Versiones

**Criterios de aceptación:**

- [ ] `POST /api/crash-reports` con datos válidos responde 201 y el report aparece en Panel Admin
- [ ] Reports con el mismo stack trace se agrupan (mismo `stack_trace_hash`) — el contador incrementa
- [ ] Stack traces con datos potencialmente sensibles son rechazados o sanitizados
- [ ] `GET /api/updates/latest?product=server` devuelve la versión marcada como `is_latest=true`
- [ ] Publicar nueva versión desde Panel Admin actualiza correctamente el flag `is_latest`
- [ ] Solo puede haber una versión con `is_latest=true` por producto a la vez
- [ ] cjhirashi puede marcar un crash report como revisado y agregar URL de issue de GitHub

---

## Sprint H3 — Operación y Resiliencia

**Criterios de aceptación:**

- [ ] Reiniciar el VPS → todos los contenedores vuelven solos (restart policy)
- [ ] Backup diario ejecuta y genera un archivo `.sql.gz` válido
- [ ] UptimeRobot detecta correctamente cuando Hub está caído
- [ ] Dashboard del Panel Admin muestra métricas correctas: licencias activas, reports sin revisar
- [ ] `docker compose ps` muestra todos los servicios en estado `healthy`

---

## Pruebas de Seguridad

| Prueba | Resultado Esperado |
|---|---|
| Fuerza bruta en `/api/licenses/validate` (>10 req/min) | 429 Too Many Requests |
| Intento de acceso a `/admin/*` sin autenticar | 401 / Redirect a login |
| Envío de stack trace con IPs hardcodeadas | Datos sanitizados o rechazados |
| Request a endpoint con payload oversized (>1MB) | 413 Request Entity Too Large (Nginx) |
| Consultar BD: `SELECT key_hash FROM license_keys` | Hash bcrypt visible — key original no recuperable |

---

## Gate de Salida

- [ ] Sprint H0 validado completo
- [ ] Sprint H1 validado completo
- [ ] Sprint H2 validado completo
- [ ] Sprint H3 validado completo
- [ ] Pruebas de seguridad ejecutadas
- [ ] Revisado y aprobado por Charlie
