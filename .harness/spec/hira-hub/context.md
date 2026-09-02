---
origen_vault: "7.2 - Hira Hub/7.2.1 - Diagnóstico.md"
título: Diagnóstico — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 01 — Diagnóstico
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, diagnóstico]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Posición en el Ecosistema

Hira Hub es el componente cloud del ecosistema Hira. Es la infraestructura que hace posible que el ecosistema funcione como un negocio — gestión de licencias, actualizaciones, ventas y diagnóstico de campo.

| Producto | Quién lo usa | Dónde corre |
|---|---|---|
| Hira Server | Cliente / Operador | On-premise del cliente |
| Hira Studio | Integrador | PC del integrador |
| **Hira Hub** | **cjhirashi** | **VPS en la nube** |

Hub es el único producto del ecosistema que **cjhirashi opera directamente**. Los integradores y clientes nunca lo ven — es infraestructura interna.

---

## Problema que Resuelve

Sin Hub, Hira Server sería un producto sin ciclo de vida gestionable:

| Problema | Sin Hub | Con Hub |
|---|---|---|
| Validación de licencias | No hay forma de activar/revocar keys remotamente | Endpoint `/api/licenses/validate` en cada arranque |
| Detección de bugs en campo | cjhirashi se entera cuando el integrador reporta | Crash reports automáticos con stack trace |
| Distribución de actualizaciones | El integrador tendría que buscar la versión nueva manualmente | Hub registra última versión; Server notifica cuando hay update |
| Ingresos directos | Solo por transferencia manual | Portal de ventas con Stripe integrado (v0.2) |
| Marketplace de plantillas | Imposible | Catálogo de pre-ingenierías descargables desde Studio (v0.2–v0.3) |

---

## Versiones y Alcance

| Versión | Nombre | Qué hace | Prerequisito |
|---|---|---|---|
| **v0.1** | Hub Mínimo | Validación de license keys + recepción de crash reports | Lanzar antes de que Server v0.1 vaya a campo |
| **v0.2** | Hub con Ventas | Portal de venta de licencias + dashboard de instalaciones activas | Server v0.1 en producción con al menos 1 integrador |
| **v0.3** | Diseñador de Bloques | Editor visual de bloques SVG + catálogo descargable para Server | Hub v0.2 con ventas operando |

---

## Stakeholders

| Actor | Rol |
|---|---|
| **cjhirashi** | Único operador — gestiona licencias, revisa crash reports, publica actualizaciones |
| **Integrador** | Compra licencias Server/Studio. No accede a Hub directamente — su Server se conecta a Hub para validar |
| **Hira Server (instalación activa)** | Cliente técnico de Hub — valida licencia, envía crash reports, consulta versiones |
| **Stripe** | Procesador de pagos (v0.2) |

---

## Restricciones

- **Costo cero hasta que haya ingresos:** VPS $5–15/mes; SSL gratuito; email gratuito (Resend free tier)
- **Operado solo por cjhirashi** — no hay equipo, no hay SLA formal con los integradores para Hub
- **Hub puede caer sin afectar SCADA:** si Hub está caído, los Servers de los clientes siguen operando. Solo pierden validación de licencia y crash reports durante la caída
- **Seguridad:** Hub expone endpoints públicos — cualquier IP puede intentar llamar a `/api/licenses/validate`. Las keys deben ser opacas y la validación debe ser resistente a fuerza bruta

---

## Viabilidad

| Concepto | Estimación |
|---|---|
| Costo mensual fijo | $5–15 (VPS) |
| Costo por transacción | 2.9% + $0.30 (Stripe) — solo al procesar pagos |
| Ingresos que requiere para ser rentable | Una sola licencia Server ($399+) cubre más de 2 años de VPS |
| Costo de desarrollo v0.1 | Tiempo de cjhirashi — stack conocido (FastAPI, PostgreSQL) |

La viabilidad es muy alta. Hub v0.1 es mínimo y de bajo costo. El riesgo principal es de seguridad, no económico.

---

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| VPS cae y Servers no pueden validar licencia | Baja | Bajo (Server sigue operando en modo grace period) | UptimeRobot + restart automático Docker |
| Alguien intenta fuerza bruta en `/api/licenses/validate` | Media | Medio | Rate limiting por IP en Nginx; keys largas y opacas |
| Base de datos Hub corrupta / pérdida de datos de licencias | Muy baja | Crítico | Backup diario de PostgreSQL + respaldo externo |
| Integradores no consienten envío de crash reports | Media | Bajo | El campo `CRASH_REPORTER_ENABLED` es opt-in — sistema funciona sin él |

---

## Gate de Salida

- [x] Posición de Hub en el ecosistema definida
- [x] Versiones v0.1 / v0.2 / v0.3 con alcance claro
- [x] Restricciones y riesgos documentados
- [x] Viabilidad económica validada
- [ ] Revisado y aprobado por Charlie
