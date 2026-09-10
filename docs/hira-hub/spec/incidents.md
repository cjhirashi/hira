---
origen_vault: "7.2 - Hira Hub/7.2.10 - Incidencias.md"
título: Incidencias — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 10 — Incidencias
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, incidencias]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Clasificación de Incidencias

| Nivel | Criterio | Respuesta máxima |
|---|---|---|
| **P1 — Crítico** | Hub completamente inaccesible o BD corrupta | 4 horas |
| **P2 — Mayor** | Endpoint de licencias falla (Servers no pueden validar) | 8 horas |
| **P3 — Menor** | Crash reports no se reciben / Panel Admin con error | 48 horas |
| **P4 — Info** | Latencia elevada pero servicio funcional | Siguiente sprint |

> Tiempos de respuesta de cjhirashi — no hay SLA formal con integradores.

---

## Catálogo de Incidencias Conocidas

### INC-H01 — Hub completamente inaccesible

**Síntoma:** UptimeRobot alerta, `curl /health` no responde.

**Causas más frecuentes:**
- VPS reiniciado y Docker no arrancó solo
- Disco lleno → containers no pueden escribir
- Nginx caído

**Respuesta:** Ver RB-H01 en .harness/spec/hira-hub/deployment.md - Operación

---

### INC-H02 — Validación de licencias devuelve 500

**Síntoma:** Servers en campo reciben error 500 al validar licencia; entran en grace period.

**Causas más frecuentes:**
- PostgreSQL no responde (healthcheck falla)
- Cambio de schema sin migración de Alembic
- Query de validación tarda más de 30s (lock en tabla)

**Respuesta:**
```bash
# Ver logs del backend
docker compose logs --tail=100 backend | grep ERROR

# Ver estado de postgres
docker compose exec postgres psql -U hub -d hubdb -c "\dt"

# Si hay lock:
docker compose exec postgres psql -U hub -d hubdb \
  -c "SELECT pid, query, state FROM pg_stat_activity WHERE state='active';"
# Terminar query bloqueante: SELECT pg_terminate_backend(PID);

# Si es schema inconsistente: restaurar desde backup (RB-H04)
```

---

### INC-H03 — Fuerza bruta en `/api/licenses/validate`

**Síntoma:** Logs del Nginx muestran rafagas de 429 desde una misma IP; cjhirashi recibe alerta de UptimeRobot por latencia alta.

**Respuesta:**
```bash
# Identificar IP atacante
grep "429" /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head

# Bloquear IP temporalmente
ufw deny from [IP_ATACANTE]

# Si el ataque continúa desde múltiples IPs: revisar rate limits y ajustar si es necesario
```

**Nota:** Las license keys son largas y opacas — fuerza bruta no es viable pero el rate limit protege la disponibilidad del endpoint.

---

### INC-H04 — Certificado SSL vencido

**Síntoma:** Browsers y Servers reciben error de certificado; `/health` falla con SSL error.

**Causa:** Renovación automática de Certbot falló (cron no corrió, disco lleno, DNS mal configurado).

**Respuesta:** Ver RB-H03 en .harness/spec/hira-hub/deployment.md - Operación

**Impacto en el campo:** Los Servers con `HIRA_HUB_VERIFY_SSL=true` (recomendado) no pueden conectar a Hub → entran en grace period de 72h.

---

### INC-H05 — Pérdida de datos de licencias

**Síntoma:** Panel Admin Hub muestra tabla de licencias vacía o datos inconsistentes.

**Respuesta:** Ver RB-H04 en .harness/spec/hira-hub/deployment.md - Operación

**Nota:** Esta es la incidencia de mayor impacto — todas las licencias activas quedarían inaccesibles. El backup diario es la única mitigación.

---

## Registro de Incidencias

Cada incidencia mayor (P1 o P2) se registra en la Bitácora de la bóveda con:

| Campo | Contenido |
|---|---|
| Fecha y hora | Cuándo se detectó |
| Nivel | P1 / P2 |
| Descripción | Qué pasó |
| Duración | Desde detección hasta resolución |
| Causa raíz | Por qué ocurrió |
| Solución aplicada | Qué se hizo |
| Prevención | Qué cambio se hace para evitar recurrencia |

---

## Gate de Salida

- [x] Clasificación de niveles definida
- [x] Catálogo de incidencias conocidas documentado
- [x] Proceso de registro documentado
- [ ] Revisado y aprobado por Charlie
