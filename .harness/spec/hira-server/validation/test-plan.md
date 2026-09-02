---
origen_vault: "7.1 - Hira Server/7.1.7 - Validación/7.1.7.2 - Plan de Pruebas.md"
título: Plan de Pruebas — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Validación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, validación, plan-de-pruebas]
---

## Pruebas Unitarias

Cobertura mínima aceptable: **80% de líneas** en módulos críticos.

| Módulo | Qué probar |
|---|---|
| `core/security.py` | Generación y verificación de JWT; bcrypt hash/verify |
| `services/alarm_engine.py` | Evaluación de condiciones: gt, lt, eq, between — valores límite y fuera de rango |
| `services/logic_engine.py` | RestrictedPython: imports bloqueados, API interna accesible, manejo de excepciones |
| `services/point_association_service.py` | Un candidato no asociado nunca es escribible; `access_mode` y `bacnet_write_priority` se validan al crear la asociación |
| `services/backup_service.py` | Serialización y deserialización del paquete .hira; validación de checksum |
| `services/simulators/` | Cada simulador genera valores en el rango configurado; responde a comandos de arranque/parada |
| `core/license.py` | License key válida acepta; expirada rechaza; hardware fingerprint consistente; tope de puntos en línea se calcula correctamente por tipo de licencia (SRV-ADR-018) |

## Pruebas de Integración

Escenarios que cruzan dos o más módulos:

| Escenario | Módulos involucrados |
|---|---|
| Polling BACnet sobre punto asociado → Redis → WebSocket → Frontend actualiza mimic | Motor de Protocolos + Redis + FastAPI WS + Frontend |
| Escaneo descubre candidato → asociación explícita → punto queda operable | Motor de Protocolos + point_association_service + BD |
| Condición de alarma detectada → WebSocket notifica a todos los clientes | Motor de Alarmas + Redis + FastAPI WS |
| Script Python escribe punto asociado → valor llega al dispositivo BACnet real | Motor de Lógica + Celery + Motor de Protocolos + BAC0 |
| Login → RBAC middleware → acceso a endpoint protegido, con alcance por proyecto o global | Auth + Redis RBAC cache + Router + SRV-ADR-020 |
| Export .hira → import en instalación limpia → sistema idéntico | Backup Service + ORM + BD |
| Agente IA recibe pregunta → recupera contexto (RAG o inyección directa) → retorna respuesta | AI Agent + FastAPI + BD |
| Sesión de ingeniería remota → lock Redis → segundo intento recibe 409 | Engineering Session Service + Redis + SRV-ADR-016 |

## Pruebas End-to-End

**E2E-01 — Flujo diseño local → campo**
1. Crear proyecto en instalación local del integrador (perfil studio) con simuladores BACnet y MQTT
2. Escanear, asociar candidatos a puntos, configurar mimic, alarma y script de lógica
3. Exportar `.hira`
4. Importar en instalación comercial limpia
5. Reemplazar simuladores por dispositivos reales — reasociar candidatos reales a los mismos puntos Hira
6. Verificar que alarmas, históricos y lógica funcionan con hardware real

**E2E-02 — Operación normal multi-usuario**
1. Admin configura proyecto con 3 dispositivos, escanea y asocia 20 puntos
2. Operador monitorea dashboard en tiempo real
3. Operador envía comando de escritura (setpoint) sobre un punto `access_mode=read_write`
4. Valor llega al dispositivo y se refleja en el dashboard
5. Alarma se activa — ambos usuarios la ven simultáneamente
6. Operador reconoce alarma — queda registrado

**E2E-03 — Motor de Lógica con Agente del Integrador**
1. Integrador consulta al agente: "genera un script que controle el ventilador según temperatura"
2. Agente genera script Python usando solo puntos asociados existentes
3. Integrador lo revisa en Monaco Editor y lo activa
4. Script corre en background y opera el dispositivo según la lógica
5. Históricos muestran el comportamiento del sistema bajo control del script

**E2E-04 — Sesión de ingeniería remota**
1. Integrador conecta desde su instalación local a un Server comercial activo (ver SRV-ADR-016)
2. Agrega un punto, lo asocia con `access_mode` y prioridad, ajusta una alarma
3. Verifica que los cambios se reflejan de inmediato en el Server sin ciclo export/import
4. Cierra sesión — el lock se libera y el panel de operadores vuelve a modo normal

## Pruebas de Carga

| Escenario | Parámetro | Criterio de aceptación |
|---|---|---|
| WebSocket concurrente | 20 clientes conectados simultáneamente | Latencia de actualización < 1s para todos |
| Polling masivo | 200 puntos asociados activos con intervalo 5s | CPU < 60% en servidor con 2 vCPU / 4GB RAM |
| Históricos | Consulta de 30 días de 50 puntos simultáneamente | Respuesta < 5s |
| API REST | 100 req/s durante 60s | P99 < 200ms; sin errores 5xx |
| Alarmas | 10 alarmas activas simultáneas | Todas evaluadas y notificadas en menos de 1 ciclo |

## Pruebas de Seguridad

| Prueba | Método | Criterio |
|---|---|---|
| MQTT sin credenciales | Cliente externo sin user/pass | Connection refused |
| SQL injection en import | `.hira` con payload en campo string | Rechazado por validación Pydantic antes de tocar BD |
| JWT falsificado | Token con firma inválida | 401 en todos los endpoints |
| Rate limiting | `ab -n 500 -c 50` contra endpoint REST | 429 para requests que superen el límite |
| Acceso cross-rol | Operador llamando endpoint de Admin | 403 Forbidden |
| Acceso cross-proyecto | Usuario de operación de un proyecto intenta acceder a otro | 403 Forbidden (SRV-ADR-020) |
| Sandbox escape | Script con `import subprocess` | Error RestrictedPython; sin ejecución del comando |
| Escritura sobre candidato no asociado | Request directo a un `device_point_id` sin asociación | 404 — no existe como punto operable (SRV-ADR-019) |
| Tope de licencia | Poner en línea puntos por encima del tope contratado | Rechazo con mensaje claro (SRV-ADR-018) |

## Ambiente de Pruebas

| Ambiente | Descripción | Cuándo usar |
|---|---|---|
| **Dev local** | Docker Compose en PC del desarrollador, simuladores activos | Pruebas unitarias e integración diaria |
| **Staging** | Servidor Linux limpio (VM o bare metal), simuladores + 1 dispositivo BACnet real | Pruebas E2E, carga y seguridad |
| **Beta cliente** | Servidor del primer cliente, hardware real de producción | Validación final antes de release comercial |

## Resultados de Pruebas

*Se completa durante la implementación.*

| Sprint | Módulo | Pruebas pasadas | Pruebas fallidas | Notas |
|---|---|---|---|---|
| — | — | — | — | — |

## Issues Encontrados

| ID | Sprint | Descripción | Severidad | Solución | Fecha cierre |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

## Gate de Salida

Para considerar Hira Server listo para el primer proyecto real:

- [ ] Todos los criterios AC-SRV-01 a AC-SRV-12 verificados y documentados
- [ ] Pruebas E2E-01 a E2E-04 ejecutadas sin errores críticos
- [ ] Pruebas de carga: ningún criterio excedido en ambiente Staging
- [ ] VUL-SRV-001, VUL-SRV-002, VUL-SRV-003, VUL-SRV-004 en estado 🟢 Resuelto; VUL-SRV-014 verificado como resuelto por rediseño (SRV-ADR-018)
- [ ] Sin issues de severidad Crítica o Alta abiertos
- [ ] Flujo E2E-01 ejecutado exitosamente con hardware BACnet real del primer cliente
- [ ] Sign-off de Charlie para despliegue en beta
