---
origen_vault: "7.1 - Hira Server/7.1.7 - Validación/7.1.7.1 - Criterios de Aceptación.md"
título: Criterios de Aceptación — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Validación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, validación, criterios-de-aceptación]
---

## Alcance

Criterios de aceptación verificables para dar por lista una instalación de Hira Server para su primer proyecto real. Cada criterio tiene un escenario concreto y un resultado esperado verificable.

## AC-SRV-01 — Infraestructura y arranque

| # | Criterio | Resultado esperado |
|---|---|---|
| 1.1 | `docker compose up` en servidor Linux limpio levanta todos los servicios sin errores | Todos los contenedores en estado `healthy` en menos de 60s |
| 1.2 | `docker compose up` en Windows con Docker Desktop + WSL2 produce el mismo resultado | Idéntico al anterior |
| 1.3 | Endpoint `/health` responde con estado de cada servicio | JSON con status de base de datos, Redis, Mosquitto — todos `ok` |
| 1.4 | Variables de entorno faltantes producen error explícito en arranque | Mensaje claro indicando qué variable falta — sin arranque parcial silencioso |

## AC-SRV-02 — Autenticación y RBAC

| # | Criterio | Resultado esperado |
|---|---|---|
| 2.1 | Login con credenciales válidas retorna JWT access + refresh | Tokens con TTL correcto (15min / 7 días) |
| 2.2 | Request con JWT expirado retorna 401 | Sin acceso a ningún endpoint protegido |
| 2.3 | Usuario con rol Visor intenta escribir a un punto | 403 Forbidden |
| 2.4 | Usuario con rol Operador intenta acceder al Configurador | 403 Forbidden |
| 2.5 | Admin modifica rol de un usuario — los permisos se actualizan en la próxima request | Caché Redis invalidada; el usuario ya no puede acceder al recurso restringido |
| 2.6 | Middleware RBAC agrega menos de 5ms de latencia por request | Medido con 100 requests concurrentes contra endpoint protegido |
| 2.7 | Usuario integrador (rol global) accede a un proyecto distinto sin re-login | Acceso concedido sin fricción — usuarios de operación no pueden cruzar de proyecto (SRV-ADR-020) |

## AC-SRV-03 — BACnet

| # | Criterio | Resultado esperado |
|---|---|---|
| 3.1 | Escaneo Who-Is en red local descubre al menos un dispositivo BACnet real o simulado | Puntos candidatos listados en `device_points_candidates` con instance number, IP, nombre |
| 3.2 | Un punto candidato sin asociar no aparece en polling ni es escribible | 404 o 403 al intentar leer/escribir directamente un candidato |
| 3.3 | Al asociar un candidato con `access_mode=read_write` y prioridad BACnet, el punto queda operable | Lectura y escritura funcionan según lo definido en la asociación (SRV-ADR-019) |
| 3.4 | Polling configurable de un punto asociado analógico (temperatura) a 5s actualiza el valor en Redis | Valor en Redis se refresca cada 5 ± 0.5s |
| 3.5 | Escritura de setpoint desde el panel llega al controlador BACnet respetando la prioridad asociada | Valor confirmado leyendo el punto inmediatamente después de la escritura |
| 3.6 | Dispositivo BACnet se desconecta — el sistema lo detecta y marca el punto como `offline` | Estado reflejado en dashboard en menos de 2 ciclos de polling |
| 3.7 | Lock `asyncio.Lock` por dispositivo previene condiciones de carrera en escrituras concurrentes | 10 escrituras concurrentes al mismo punto producen resultado consistente sin errores |

## AC-SRV-04 — MQTT

| # | Criterio | Resultado esperado |
|---|---|---|
| 4.1 | Mosquitto rechaza conexión sin credenciales | Connection refused — sin acceso anónimo |
| 4.2 | Backend se suscribe a topic con wildcard y recibe mensajes de subtopics | Datos de `edificio/piso1/#` recibidos y listados como candidatos |
| 4.3 | Publicación a un topic desde el panel llega al broker (punto asociado con `access_mode=read_write`) | Mensaje visible en cliente MQTT externo suscrito al mismo topic |
| 4.4 | Nuevo dispositivo MQTT publica a un topic nuevo — el sistema lo detecta | Topic aparece como candidato en el panel |

## AC-SRV-05 — Simuladores

| # | Criterio | Resultado esperado |
|---|---|---|
| 5.1 | Simulador BACnet arranca y responde a Who-Is | Dispositivo virtual visible en escaneo de red |
| 5.2 | Simulador Modbus arranca y responde a lectura de registros | Registros accesibles vía pymodbus client |
| 5.3 | Simulador MQTT publica a intervalo configurable | Mensajes recibidos en Mosquitto con frecuencia correcta |
| 5.4 | Un simulador y un dispositivo real del mismo protocolo coexisten en la misma instalación | Ambos visibles en panel, datos independientes, sin interferencia |
| 5.5 | Flag `is_simulator: true` de un dispositivo simulado no puede eliminarse sin confirmación explícita | UI muestra advertencia; backend valida antes de permitir el cambio |

## AC-SRV-06 — Dashboard y tiempo real

| # | Criterio | Resultado esperado |
|---|---|---|
| 6.1 | Dashboard carga en menos de 2s con 50 puntos asociados activos | Time to interactive < 2s en red local |
| 6.2 | Valor de punto asociado cambia en el controlador — el mimic animado se actualiza sin recargar la página | Actualización vía WebSocket en menos de 1s |
| 6.3 | 5 usuarios conectados simultáneamente al dashboard — sin degradación visible | Latencia de WebSocket < 500ms para todos los usuarios bajo carga simultánea |
| 6.4 | Mimic con componente SVG de Fan&Coil muestra estado correcto (encendido/apagado/falla) según el valor del punto | Animación coherente con el valor real del punto |
| 6.5 | Escritura de setpoint desde el panel de control — confirmación visual en menos de 2s | Nuevo valor reflejado en el mimic tras la escritura |

## AC-SRV-07 — Motor de Alarmas

| # | Criterio | Resultado esperado |
|---|---|---|
| 7.1 | Valor de temperatura supera umbral configurado — alarma se activa automáticamente | Alarma en estado `activa` en menos de 1 ciclo de evaluación |
| 7.2 | Operador reconoce la alarma — queda registrado con timestamp y usuario | Registro en BD con datos de reconocimiento |
| 7.3 | Valor vuelve a rango normal — alarma pasa a `resuelta` | Estado actualizado automáticamente |
| 7.4 | Alarma activa es visible en el dashboard en tiempo real para todos los usuarios conectados | Notificación vía WebSocket a todos los clientes |
| 7.5 | Historial de alarmas muestra activación, reconocimiento y resolución con timestamps | Datos completos y ordenados por fecha |

## AC-SRV-08 — Históricos

| # | Criterio | Resultado esperado |
|---|---|---|
| 8.1 | Punto asociado configurado para historizar almacena valor cada intervalo definido | Registros en la tabla de históricos con timestamps correctos |
| 8.2 | Consulta de histórico de 7 días de un punto retorna datos en menos de 3s | Respuesta con todos los registros del período |
| 8.3 | Gráfica Plotly muestra tendencia del punto con zoom y pan interactivo | Gráfica funcional con datos reales |
| 8.4 | Exportación CSV de un rango de fechas produce archivo descargable | CSV con columnas timestamp, value, unit, point_name |

## AC-SRV-09 — Motor de Lógica

| # | Criterio | Resultado esperado |
|---|---|---|
| 9.1 | Script Python con `hira.read('punto_temp')` retorna el valor actual del punto asociado | Valor correcto sin error de sandbox |
| 9.2 | Script con `hira.write('punto_setpoint', 22.0)` escribe al controlador | Valor confirmado en el dispositivo, respetando `access_mode` |
| 9.3 | Script con `import os` es rechazado por RestrictedPython | Error de sandbox — importación bloqueada |
| 9.4 | Script en ejecución continua procesa un ciclo cada segundo durante 1 hora sin fugas de memoria | Uso de memoria estable; sin crecimiento acumulado |
| 9.5 | Worker de lógica muere — Celery lo reinicia automáticamente | Script retoma ejecución en menos de 30s |
| 9.6 | Lock Redis de punto activo impide que el script lo sobreescriba durante una prueba activa | Escritura ignorada; log de conflicto registrado |

## AC-SRV-10 — Agentes IA

| # | Criterio | Resultado esperado |
|---|---|---|
| 10.1 | Pregunta sobre estado del sistema retorna respuesta coherente con los puntos asociados actuales | IA responde con datos reales del proyecto |
| 10.2 | Solicitud "genera un script que encienda el ventilador si la temperatura supera 25°C" produce código ejecutable | Script válido que pasa la validación RestrictedPython y funciona al ejecutarse |
| 10.3 | Agente sin API key configurada — el panel muestra estado "no configurado" sin errores | Sistema SCADA opera con normalidad; solo el módulo IA está inactivo |
| 10.4 | Proyecto con 200 puntos asociados — el agente responde en menos de 10s | Latencia aceptable |
| 10.5 | Agente del Cliente responde citando fuentes recuperadas por RAG | Fragmentos de documentación relevantes citados en la respuesta |

## AC-SRV-11 — Backup y portabilidad (.hira)

| # | Criterio | Resultado esperado |
|---|---|---|
| 11.1 | Exportar proyecto produce archivo `.hira` válido (ZIP DEFLATE con checksum SHA-256) | Archivo descargable, checksum verificable |
| 11.2 | Importar el `.hira` en una instalación limpia recrea la configuración completa | Dispositivos, puntos candidatos y asociados, mimics, scripts y alarmas idénticos al original |
| 11.3 | Importar un `.hira` con JSON malformado es rechazado con mensaje claro | Error descriptivo; base de datos sin cambios |
| 11.4 | `.hira` exportado es importable de forma idempotente | 3 importaciones consecutivas producen el mismo resultado |

## AC-SRV-12 — Seguridad y licenciamiento

| # | Criterio | VUL / ADR | Resultado esperado |
|---|---|---|---|
| 12.1 | Cliente MQTT sin credenciales es rechazado por Mosquitto | VUL-SRV-001 | Connection refused |
| 12.2 | `.hira` con SQL inyectado en JSON es rechazado por validación Pydantic | VUL-SRV-002 | Error de schema; sin ejecución de SQL externo |
| 12.3 | 200 req/s desde un cliente — el servidor responde 429 sin degradar a otros | VUL-SRV-003 | Rate limiting activo |
| 12.4 | RBAC middleware < 5ms de latencia con caché Redis | VUL-SRV-004 | Latencia medida por debajo del umbral |
| 12.5 | Se intenta poner en línea un punto que excede el tope de puntos en línea de la licencia | SRV-ADR-018 (resuelve VUL-SRV-014) | Rechazo con mensaje claro indicando el tope de la licencia; el punto queda creado pero no en línea |
| 12.6 | Instancia con licencia comercial intenta crear un segundo proyecto | SRV-ADR-020 | Rechazado — multi-proyecto exclusivo de licencia de integrador |

---

## Gate de Salida

- [x] Criterios AC-SRV-01 a AC-SRV-12 actualizados al modelo de puntos asociados (SRV-ADR-019) y licenciamiento por puntos en línea (SRV-ADR-018)
- [ ] Todos los criterios verificados y documentados con resultado real
- [ ] Revisado y aprobado por Charlie
