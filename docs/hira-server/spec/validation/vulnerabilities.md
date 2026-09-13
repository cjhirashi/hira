---
origen_vault: "7.1 - Hira Server/7.1.7 - Validación/7.1.7.3 - Registro de Vulnerabilidades.md"
título: Registro de Vulnerabilidades — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Validación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Registro Técnico
status: activo
tags: [proyecto, productos-software, hira-server, vulnerabilidades, seguridad, confiabilidad]
---

## Propósito

Registro centralizado de vulnerabilidades, riesgos técnicos y mejoras de diseño identificados durante el desarrollo de Hira Server. El objetivo es anticiparse a los problemas antes de que ocurran en producción. Cualquier vulnerabilidad detectada — en revisión de diseño, en desarrollo, en pruebas o en campo — se registra aquí con su resolución y se da seguimiento hasta cierre.

**Principio:** un problema documentado y rastreado es un problema bajo control.

## Estados

| Estado | Descripción |
|---|---|
| 🔴 Abierto | Detectado, sin resolución implementada |
| 🟡 En Proceso | Resolución en desarrollo |
| 🟢 Resuelto | Resolución implementada y verificada |
| 🔵 Aceptado | Riesgo conocido, aceptado con limitación documentada |

## Severidades

| Severidad | Criterio |
|---|---|
| **Crítico** | Puede comprometer seguridad, integridad de datos o disponibilidad del sistema |
| **Alto** | Afecta funcionalidad principal o confiabilidad bajo condiciones normales |
| **Medio** | Afecta experiencia o introduce deuda técnica significativa |
| **Bajo** | Mejora de diseño o planificación que no tiene impacto inmediato |

---

## Registro Activo

### VUL-SRV-001 — Mosquitto sin autenticación
| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Seguridad |
| **Estado** | 🟢 Resuelto |
| **Afecta** | Toda instalación |

**Descripción:** Mosquitto con configuración por defecto permite conexiones anónimas. Cualquier dispositivo en la red local puede publicar datos falsos a los topics monitoreados por Hira, disparar alarmas incorrectas o alimentar lógica errónea.

**Resolución:** `mosquitto.conf` con `allow_anonymous false` + `password_file`. Credenciales en variables de entorno `MQTT_USER`/`MQTT_PASSWORD`. El servicio paho-mqtt del backend se autentica al conectarse.

**Verificación:** implementado y verificado en `SRV-001-walking-skeleton` contra el broker Mosquitto real (no mocks) — T-016/T-017 (`mosquitto.conf` con `allow_anonymous false` + `password_file` generado y montado, `HEALTHCHECK` con credencial válida alcanza `healthy`), T-021/T-022 (`MosquittoAdapter.connect()` con `MQTT_USER`/`MQTT_PASSWORD`; credencial inválida agota su backoff fijo 1s/2s/4s sin loop ciego, log `level: error`, sin lanzar excepción — RF-008) y T-023 (`tests/integration/test_mqtt_security.py::test_anonymous_mqtt_client_is_rejected_by_real_broker`: cliente `paho-mqtt` externo sin credenciales, `CONNACK rc != 0`, contra el broker real del compose). Reverificado en la verificación e2e formal (T-024, `docker compose up`): `mosquitto` alcanza `healthy` con credencial real y `/health` refleja `mosquitto: ok`.

---

### VUL-SRV-002 — Import de paquete .hira ejecuta SQL crudo
| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Seguridad / Integridad de datos |
| **Estado** | 🟡 En Proceso |
| **Afecta** | Toda instalación |

**Descripción:** Si el formato de exportación es un SQL dump y el proceso de importación lo ejecuta directamente, un paquete `.hira` malicioso puede contener SQL arbitrario que altere datos fuera del proyecto o comprometa la base de datos.

**Resolución:** el formato de exportación es JSON estructurado serializado por el ORM. La importación deserializa el JSON y usa el ORM con queries parametrizadas. Nunca se ejecuta SQL proveniente del archivo importado.

**Verificación:** intentar importar un paquete con SQL inyectado en el JSON debe ser rechazado por validación de esquema Pydantic antes de tocar la BD.

---

### VUL-SRV-003 — Sin rate limiting en API ni en WebSocket
| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Disponibilidad |
| **Estado** | 🟡 En Proceso |
| **Afecta** | Toda instalación |

**Descripción:** Sin límites de frecuencia, un cliente puede hacer flood al API REST o abrir miles de conexiones WebSocket simultáneas, colapsando el servidor. Especialmente relevante en servidores on-premise con recursos limitados.

**Resolución:** Nginx con `limit_req_zone` por IP para REST (100 req/s), `limit_conn_zone` para WebSocket (10 conexiones/IP).

**Verificación:** prueba de carga con 200 req/s desde un cliente — el servidor debe responder 429 a las que superen el límite sin degradación de servicio para otros clientes.

---

### VUL-SRV-004 — RBAC con query a base de datos en cada request
| Campo | Valor |
|---|---|
| **Severidad** | Crítico |
| **Tipo** | Rendimiento / Confiabilidad |
| **Estado** | 🟡 En Proceso |
| **Afecta** | Toda instalación |

**Descripción:** Si el middleware RBAC hace una query a la base de datos por cada request HTTP, la latencia acumulada es visible en dashboards de tiempo real con múltiples usuarios. Bajo carga alta, puede saturar el pool de conexiones.

**Resolución:** al login, cargar los permisos del usuario en Redis (`rbac:{user_id}`, TTL igual al refresh token). El middleware lee de Redis en cada request. Al modificar un rol, invalidar la entrada Redis del usuario afectado.

**Verificación:** medir latencia de endpoint con RBAC activo — debe añadir < 5ms por request.

---

### VUL-SRV-005 — BAC0 sin lock en escrituras concurrentes
| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Confiabilidad |
| **Estado** | 🔴 Abierto |
| **Afecta** | Toda instalación — bajo carga alta |

**Descripción:** BAC0 no está diseñado para escrituras concurrentes desde múltiples threads. Si el Motor de Lógica escribe a un punto asociado al mismo tiempo que el worker de polling lo lee, puede haber condiciones de carrera que generen datos incorrectos o errores silenciosos.

**Resolución propuesta:** `asyncio.Lock` por dispositivo en el adaptador BACnet. Todas las operaciones sobre un mismo dispositivo (lectura de polling + escritura desde lógica) adquieren el lock antes de ejecutar. Los locks son por instancia de dispositivo, no globales.

**Verificación:** prueba con 10 escrituras concurrentes sobre el mismo punto — verificar que el valor final es consistente y sin errores.

---

### VUL-SRV-006 — Sin invalidación inmediata de sesión JWT comprometida
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Seguridad |
| **Estado** | 🔵 Aceptado (limitación conocida) |
| **Afecta** | Toda instalación |

**Descripción:** Si se compromete la cuenta de un usuario, el access token JWT sigue válido hasta 15 minutos aunque se revoque el refresh token. En un sistema con acceso de escritura a equipos reales, 15 minutos es una ventana de riesgo.

**Resolución futura:** lista de revocación de JTIs (JWT IDs) en Redis con TTL de 15 minutos. El middleware verifica que el JTI no esté en la lista negra.

**Aceptado** porque el contexto inicial es instalaciones pequeñas con pocos usuarios de confianza. Se documenta como limitación conocida en la guía de operación.

---

### VUL-SRV-007 — Celery Beat como punto único de fallo del scheduler
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Confiabilidad |
| **Estado** | 🔵 Aceptado (mitigado por Docker restart policy) |
| **Afecta** | Toda instalación |

**Descripción:** Celery Beat corre en una sola instancia. Si el proceso muere, las tareas periódicas (evaluación de alarmas por beat, backup programado) se detienen hasta que Docker lo reinicia.

**Mitigación actual:** Docker restart policy `always`. La evaluación de alarmas tiene un canal adicional — el Motor de Alarmas también evalúa al recibir cada nuevo valor vía Redis, por lo que las alarmas no quedan completamente ciegas durante una caída del Beat.

**Resolución futura:** RedBeat — scheduler distribuido para Celery con Redis como backend, eliminando el SPOF.

---

### VUL-SRV-008 — Contexto del Agente IA se satura en proyectos grandes
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Rendimiento / Costo |
| **Estado** | 🔴 Abierto |
| **Afecta** | Proyectos con 500+ puntos asociados |

**Descripción:** Si el Agente del Integrador inyecta la lista completa de puntos asociados en cada conversación, para proyectos con 500+ puntos consume una porción significativa del context window y aumenta el costo por conversación.

**Resolución:** el Agente del Cliente ya usa RAG con pgvector (ver SRV-ADR-011, `.harness/spec/hira-server/modules/agente-ia.md`). Extender la misma estrategia al Agente del Integrador cuando el proyecto supera un umbral de puntos, en vez de inyección completa.

---

### VUL-SRV-009 — Sin estrategia de compatibilidad de versiones del paquete .hira
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Diseño / Mantenibilidad |
| **Estado** | 🔴 Abierto |
| **Afecta** | Cualquier migración de proyecto entre versiones de Hira Server |

**Descripción:** Si el esquema del paquete `.hira` cambia entre versiones (campo nuevo en dispositivos, tabla nueva), importar un paquete antiguo en una instalación más nueva puede fallar silenciosamente o generar datos corruptos.

**Resolución propuesta:** política de compatibilidad explícita — Hira siempre puede importar paquetes de la misma versión mayor. Paquetes de versiones anteriores se importan con migración automática (script de migración por versión). Paquetes de versiones futuras se rechazan con mensaje claro indicando la versión requerida.

---

### VUL-SRV-010 — BACnet MSTP puede aparecer en el primer proyecto de campo
| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Planificación |
| **Estado** | 🔴 Abierto |
| **Afecta** | Cualquier proyecto con dispositivos MSTP |

**Descripción:** BACnet MSTP (RS-485 serial) es muy común en HVAC para controladores de zonas, termostatos y cajas VAV. BAC0 soporta MSTP, pero requiere que el contenedor Docker tenga acceso al puerto serial del host. Este parámetro no está configurado por defecto.

**Resolución propuesta:** configuración opcional de puerto serial en Docker Compose con comentario explicativo (ver `.harness/spec/hira-server/implementation-guide/estructura-de-repositorio.md`), activa solo si hay dispositivos MSTP.

---

### VUL-SRV-011 — Simuladores con flag en tabla devices: riesgo de confusión
| Campo | Valor |
|---|---|
| **Severidad** | Bajo |
| **Tipo** | Diseño |
| **Estado** | 🔴 Abierto |
| **Afecta** | Toda instalación |

**Descripción:** Si un Admin elimina accidentalmente el flag `is_simulator: true` de un dispositivo simulador, el Motor de Protocolos intentará hacer polling a una dirección de red inexistente, generando errores silenciosos en el log.

**Resolución propuesta:** columna `device_class` (`real | simulator`) en lugar de un flag booleano. Al tipo `simulator`, el Motor de Protocolos no hace polling — delega al `SimulatorService`. Eliminar el class requiere confirmación explícita en el panel.

---

### VUL-SRV-012 — Crash Reporter puede filtrar datos del proyecto en stack traces
| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Privacidad / Seguridad |
| **Estado** | 🔴 Abierto |
| **Afecta** | Canal de Crash Reporter hacia Hira Hub |

**Descripción:** Los stack traces de Python frecuentemente contienen nombres de variables locales, valores de parámetros y rutas del filesystem. Sin sanitizar, pueden filtrar nombres de dispositivos, valores de puntos, IPs de la red del cliente o rutas del proyecto.

**Resolución propuesta:** sanitizador antes de enviar cualquier reporte: elimina `locals()`, reemplaza IPs con `[IP_REDACTED]`, normaliza rutas del filesystem a relativas, normaliza el stack trace para hash estable entre versiones del mismo bug. Test unitario que verifica ausencia de datos sensibles en reportes de prueba.

---

### VUL-SRV-013 — Webhook del integrador sin validación de SSL del destino
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Seguridad |
| **Estado** | 🔴 Abierto |
| **Afecta** | Sistema de notificaciones, canal webhook |

**Descripción:** Si el webhook del integrador apunta a una URL HTTP (no HTTPS) o a un servidor con certificado inválido, el payload de notificación viaja sin cifrado.

**Resolución propuesta:** el `NotificationEngine` valida que las URLs webhook son HTTPS (rechaza HTTP con mensaje claro), verifica el certificado SSL del destino, y firma el payload con HMAC en el header `X-Hira-Signature`.

---

### VUL-SRV-014 — Límite de puntos en línea entre instalación local del integrador e instalación comercial
| Campo | Valor |
|---|---|
| **Severidad** | Alto |
| **Tipo** | Regla de Negocio / Licenciamiento |
| **Estado** | 🟢 Resuelto (por rediseño) |
| **Afecta** | Licenciamiento — ver SRV-ADR-018 |

**Descripción original:** en el modelo de dos productos separados (Studio/Server, ver versión original de SRV-ADR-015), si Studio no limitaba el número de controladores reales activos simultáneamente, el integrador podía operar un proyecto completo en producción desde Studio sin comprar Server, destruyendo el modelo de negocio. La resolución propuesta originalmente era limitar a 1 controlador activo simultáneo en modo online de Studio.

**Resolución real:** con el modelo de un solo producto (SRV-ADR-015), esta vulnerabilidad ya no aplica en su forma original — no hay un "Studio" separado que limitar. El mecanismo de negocio equivalente es el **licenciamiento por puntos en línea** (SRV-ADR-018): la licencia de integrador permite escaneo e integración ilimitados y creación de puntos ilimitada, pero limita cuántos puntos pueden estar **en línea simultáneamente** a un tope de demo. Una licencia comercial limita los puntos en línea según el tier contratado. Esto impide que una instalación local del integrador sustituya a una instalación comercial en un proyecto real, sin necesidad de contar controladores.

**Verificación:** ver AC-SRV-12.5 en `.harness/spec/hira-server/validation/acceptance-criteria.md` — poner en línea un punto que exceda el tope de la licencia debe ser rechazado con mensaje claro.

---

### VUL-SRV-015 — Formato de plantilla no definido antes del marketplace bloquea compatibilidad futura
| Campo | Valor |
|---|---|
| **Severidad** | Medio |
| **Tipo** | Diseño / Planificación |
| **Estado** | 🔴 Abierto |
| **Afecta** | Transición hacia el marketplace de plantillas en Hira Hub |

**Descripción:** una plantilla de proyecto es un subconjunto del paquete `.hira` — incluye estructura de dispositivos, puntos asociados, mimics, scripts de lógica y alarmas, pero excluye datos históricos, configuración de red específica del cliente y credenciales. Si el formato de plantilla no se define antes de que el marketplace exista, cada versión de Hira Server podría generar plantillas incompatibles entre sí.

**Resolución propuesta:** definir el esquema de plantilla `.hirat` (Hira Template) como extensión del formato `.hira`, con campos obligatorios (`template_version`, `category`, `protocols`, `device_count_range`, `point_count`) y campos excluidos (`network_config`, `historical_data`, `license_key`). Hira Hub valida el esquema al publicar una plantilla y rechaza versiones incompatibles con el marketplace vigente.

---

## Historial de Resoluciones

| ID | Resolución | Fecha |
|---|---|---|
| VUL-SRV-001 | Resuelto — `allow_anonymous false` + `password_file` en Mosquitto, credencial propia del backend (`MQTT_USER`/`MQTT_PASSWORD`), verificado contra broker real (`SRV-001-walking-skeleton` T-016/T-017/T-021/T-022/T-023) | 2026-09-13 |
| VUL-SRV-014 | Resuelto por rediseño — reemplazado por licenciamiento por puntos en línea (SRV-ADR-018) tras adoptar el modelo de un solo producto (SRV-ADR-015) | 2026-07-31 |

---

## Cómo Agregar una Nueva Vulnerabilidad

1. Asignar ID correlativo: `VUL-NNN`
2. Completar todos los campos de la tabla de encabezado
3. Describir el problema con precisión: qué pasa, en qué condición, cuál es el impacto
4. Documentar la resolución propuesta (aunque sea parcial)
5. Registrar en Bitácora de la bóveda si es crítico o alto

**Cuándo agregar:** en revisiones de diseño, durante desarrollo al descubrir un edge case inesperado, en pruebas cuando un test falla por una razón no anticipada, o en campo cuando un despliegue real revela un comportamiento inesperado.
