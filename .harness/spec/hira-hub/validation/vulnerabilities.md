---
origen_vault: "7.2 - Hira Hub/7.2.13 - Registro de Vulnerabilidades.md"
título: Registro de Vulnerabilidades — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Registro Técnico
status: activo
tags: [proyecto, productos-software, hira-hub, vulnerabilidades, seguridad]
ecosistema: Hira
---

## Propósito

Registro centralizado de vulnerabilidades, riesgos técnicos y mejoras de diseño identificados durante el desarrollo de Hira Hub. Cualquier vulnerabilidad detectada — en revisión de diseño, desarrollo, pruebas o producción — se registra aquí con su resolución y se da seguimiento hasta cierre.

**Principio:** un problema documentado y rastreado es un problema bajo control.

---

## Estados

| Estado | Descripción |
|---|---|
| 🔴 Abierto | Detectado, sin resolución implementada |
| 🟡 En Proceso | Resolución en desarrollo o integrada en sprint activo |
| 🟢 Resuelto | Resolución implementada y verificada |
| 🔵 Aceptado | Riesgo conocido, aceptado con limitación documentada |

## Severidades

| Severidad | Criterio |
|---|---|
| **Crítico** | Puede comprometer seguridad, integridad de datos o disponibilidad |
| **Alto** | Afecta funcionalidad principal o confiabilidad bajo condiciones normales |
| **Medio** | Afecta experiencia o introduce deuda técnica significativa |
| **Bajo** | Mejora de diseño que no tiene impacto inmediato |

---

## Registro Activo

### VUL-HUB-01 — License keys nunca deben almacenarse ni loguearse en claro

| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Seguridad |
| **Estado** | 🟡 En Proceso |
| **Detectado** | 2026-07-24 — Revisión de diseño Fase 04 |
| **Afecta** | Hub v0.1 |
| **Sprint** | Sprint H1 |

**Descripción:** Si la license key se almacena en claro en BD, se loguea accidentalmente, o aparece en un stack trace, un atacante con acceso a logs o BD puede extraer todas las keys activas de los integradores.

**Resolución:** la key se almacena como hash bcrypt en `license_keys.key_hash`. Solo el campo `key_prefix` (`HIRA-XXXX`) se usa para identificación en logs y Panel Admin. Al validar, se compara el hash — la key en claro nunca persiste. El logger filtra cualquier string que coincida con el patrón `HIRA-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}` y lo reemplaza con `[KEY_REDACTED]`.

**Verificación:** revisar todos los logs de una sesión de activación — la key completa no debe aparecer. Test unitario que verifica el filtro del logger.

---

### VUL-HUB-02 — Endpoint de validación vulnerable a enumeración de keys

| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Seguridad |
| **Estado** | 🟡 En Proceso |
| **Detectado** | 2026-07-24 — Revisión de diseño |
| **Afecta** | Hub v0.1 |
| **Sprint** | Sprint H1 |

**Descripción:** Si el endpoint `POST /api/licenses/validate` responde con tiempos distintos para "key no existe" vs "key existe pero está revocada", un atacante puede inferir si una key es válida antes de conocer el hardware fingerprint.

**Resolución:** el endpoint siempre toma el mismo tiempo de respuesta — realizar el hash bcrypt independientemente del resultado. Respuesta unificada en caso de error: siempre `{"valid": false, "reason": "invalid_or_revoked"}`, sin distinguir "no existe" de "revocada". Rate limiting en Nginx: máx 10 req/min por IP.

**Verificación:** medir tiempo de respuesta con key válida, inválida y revocada — deben ser estadísticamente iguales (±50ms).

---

### VUL-HUB-03 — Panel Admin accesible sin autenticación en arranque inicial

| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Seguridad |
| **Estado** | 🔴 Abierto |
| **Detectado** | 2026-07-24 — Revisión de despliegue |
| **Afecta** | Hub v0.1 — primer arranque |
| **Sprint** | Sprint H1 |

**Descripción:** Si Hub arranca sin `ADMIN_PASSWORD_HASH` configurado en `.env`, el Panel Admin podría quedar accesible sin autenticación hasta que cjhirashi configure la variable. Una ventana de vulnerabilidad breve pero real en el primer despliegue.

**Resolución:** al arrancar, Hub verifica que `ADMIN_PASSWORD_HASH` esté definido y no vacío. Si no lo está, el backend rechaza arrancar con error claro en logs: `CRITICAL: ADMIN_PASSWORD_HASH not configured. Set it in .env before starting Hub.`. Ningún endpoint — ni siquiera `/health` — responde hasta que la variable esté configurada.

**Verificación:** intentar arrancar Hub sin `ADMIN_PASSWORD_HASH` → debe fallar en startup con mensaje de error claro.

---

### VUL-HUB-04 — Crash reports pueden contener datos sensibles del cliente

| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Privacidad |
| **Estado** | 🟡 En Proceso |
| **Detectado** | 2026-07-24 — Diseño del módulo de crash reports |
| **Afecta** | Hub v0.1 |
| **Sprint** | Sprint H2 |

**Descripción:** Los crash reports enviados desde Servers en campo pueden contener en el stack trace: IPs de la red del cliente, nombres de dispositivos, valores de puntos, o rutas del filesystem que revelan información del proyecto. Hub los almacena tal cual — si hay un breach de la BD de Hub, esa información queda expuesta.

**Resolución:** Hub aplica un sanitizador al recibir cada crash report antes de persistirlo:
1. Reemplazar IPs con `[IP_REDACTED]`
2. Reemplazar números de puerto con `[PORT]`
3. Eliminar rutas absolutas del filesystem (mantener solo módulo + función)
4. El stack trace sanitizado es lo que se almacena — el original nunca persiste

Esta sanitización es complementaria a la que hace el Server antes de enviar (-4). Dos capas de protección.

**Verificación:** enviar crash report con IP en el stack trace → verificar que la BD almacena `[IP_REDACTED]`.

---

### VUL-HUB-05 — BD de Hub sin backup probado equivale a sin backup

| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Confiabilidad / Operación |
| **Estado** | 🔴 Abierto |
| **Detectado** | 2026-07-24 — Revisión de operación |
| **Afecta** | Hub v0.1 — producción |
| **Sprint** | Sprint H3 |

**Descripción:** La BD de Hub contiene todas las license keys de todos los integradores activos. Si se pierde y el backup nunca fue probado, la restauración puede fallar. Una restauración fallida en ese momento implica que todos los Servers de todos los clientes entran en modo degradado cuando expira el grace period de 72h.

**Resolución:** el proceso de backup (Sprint H3) incluye obligatoriamente una prueba de restauración en ambiente de staging antes de considerarse válido. El script de backup registra el checksum del archivo y lo verifica. Semanalmente, el script de monitoreo verifica que el backup más reciente tiene menos de 25h de antigüedad y que el archivo no está corrupto (gunzip -t).

**Verificación:** restaurar un backup en un contenedor limpio → verificar que las licencias de prueba están presentes.

---

### VUL-HUB-06 — JWT del Panel Admin sin expiración corta

| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Seguridad |
| **Estado** | 🔴 Abierto |
| **Detectado** | 2026-07-24 — Revisión de diseño |
| **Afecta** | Hub v0.1 |
| **Sprint** | Sprint H1 |

**Descripción:** Si el JWT de sesión del Panel Admin tiene expiración larga (días) y el token se compromete, el atacante tiene acceso prolongado a todas las funciones de gestión de licencias.

**Resolución:** JWT de sesión con expiración de 8h. Al expirar, cjhirashi hace login de nuevo. Sin refresh tokens para el Panel Admin — no vale la complejidad adicional para un único usuario. Las sesiones del Panel Admin no son críticas de mantener vivas 24/7.

---

## Historial de Resoluciones

| ID | Resolución | Fecha | Sprint |
|---|---|---|---|
| — | — | — | — |

*Este historial se actualiza cuando un VUL pasa a estado Resuelto.*

---

## Cómo Agregar una Nueva Vulnerabilidad

1. Asignar ID correlativo: `VUL-HNN`
2. Completar todos los campos de la tabla de encabezado
3. Describir el problema con precisión: qué pasa, en qué condición, cuál es el impacto
4. Documentar la resolución propuesta
5. Asignar sprint o versión objetivo
6. Registrar en Bitácora si es crítico o alto
