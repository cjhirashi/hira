---
origen_vault: "7.2 - Hira Hub/7.2.11 - Mejoras.md"
título: Mejoras — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 11 — Mejoras
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, mejoras, roadmap]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Roadmap Hub

Las mejoras de Hub están organizadas por versión. Cada versión tiene un prerequisito de negocio — no se inicia sin él.

---

## Hub v0.1 — Hub Mínimo (Sprint activo)

**Prerequisito:** Tener al menos un Hira Server v0.1 listo para ir a campo.

**Entregables:**
- Validación de license keys
- Recepción de crash reports
- Publicación de versiones
- Panel Admin básico (solo cjhirashi)
- `/health` para monitoreo

**Estado:** En desarrollo (documentación completa, implementación pendiente)

---

## Hub v0.2 — Hub con Ventas

**Prerequisito:** Hub v0.1 en producción con al menos 1 integrador activo.

### MJR-H01 — Portal de ventas con Stripe

**Qué hace:** Página pública donde un integrador puede comprar una license key de Hira Server o Studio. Tras confirmación de pago (webhook de Stripe), Hub emite la key automáticamente y la envía por email (Resend).

**Por qué:** Actualmente el proceso de venta es manual — cjhirashi debe emitir la key manualmente. Con este módulo, la venta y emisión son automáticas.

**Alcance:**
- Página de producto con precios por tier (Starter, Professional, Enterprise)
- Checkout via Stripe Payment Links o Stripe Checkout
- Webhook `checkout.session.completed` → crear licencia en BD → enviar key por email
- Email de confirmación con key y guía de instalación

### MJR-H02 — Dashboard de instalaciones activas

**Qué hace:** Vista en Panel Admin que muestra qué integradores tienen licencias activas, cuántas instalaciones tiene cada uno, versión de Hira instalada, y fecha de próximo vencimiento.

**Por qué:** Hoy cjhirashi no tiene visibilidad del ecosistema en campo — cuántos Servers están activos, en qué versión están, cuándo vencen las licencias.

**Alcance:**
- Tabla de integradores con: email, licencias activas, número de activaciones, versión en campo
- Filtros por: próximo vencimiento (< 30 días), licencias con 0 validaciones en los últimos 7 días
- Export CSV de la tabla

---

## Hub v0.3 — Diseñador de Bloques y Marketplace

**Prerequisito:** Hub v0.2 con al menos 5 integradores activos y ventas recurrentes.

### MJR-H03 — Marketplace de plantillas `.hirat`

**Qué hace:** Catálogo de pre-ingenierías descargables desde Hira Studio. Una pre-ingeniería es un paquete `.hirat` que contiene una configuración parcial de un proyecto (dispositivos simulados, puntos, lógica, mimics) que el integrador usa como punto de partida.

**Por qué:** Reducir el tiempo de ingeniería de los integradores. En lugar de construir un proyecto HVAC desde cero, descargan una plantilla de chiller system y la adaptan.

**Tipos de plantillas:**
- Gratuitas: creadas por cjhirashi, sin costo
- De pago: creadas por integradores terceros, comisión Hub
- Oficiales: cjhirashi certifica la calidad

**Alcance:**
- Catálogo público con: nombre, descripción, preview (captura del mimic), tipo (gratuita/pago), rating
- Descarga desde Studio integrada al marketplace
- Sistema de reviews y rating por integradores
- Backend: tabla `marketplace_templates` con metadatos y enlace a archivo `.hirat` en storage

### MJR-H04 — Diseñador de Bloques SVG

**Qué hace:** Editor visual web (Panel Admin) donde cjhirashi diseña nuevos bloques SVG para el ecosistema HVAC (Fan, Chiller, Cooling Tower, VAV Box, AHU, etc.) y los publica como una actualización del catálogo de bloques disponibles en Hira Studio y Server.

**Por qué:** Actualmente los SVG de los bloques HVAC son archivos estáticos en el código. Para añadir un nuevo tipo de equipo, cjhirashi tiene que editar el código. Con el Diseñador, es una operación visual sin tocar código.

**Alcance:**
- Editor SVG vectorial con herramientas básicas (path, rect, circle, text, group)
- Definición de "puertos" del bloque: puntos de conexión con señales de campo
- Definición de estados visuales: normal, alarma, fallo, fuera-de-servicio
- Publicar bloque → Hub registra nueva versión del catálogo → Servers y Studios lo descargan
- Tabla `svg_blocks` con versión, SVG data, estados, puertos

---

## Backlog Sin Versión Asignada

| ID | Mejora | Descripción |
|---|---|---|
| MJR-H05 | Notificaciones de vencimiento | Hub envía email al integrador 30 días antes de que venza su licencia |
| MJR-H06 | API de estado para integradores | Endpoint autenticado donde el integrador consulta el estado de sus licencias (sin Panel Admin) |
| MJR-H07 | 2FA para Panel Admin | Segundo factor de autenticación para el acceso de cjhirashi |
| MJR-H08 | Métricas de uso por instalación | Cuántos puntos tiene cada Server en campo, cuántas alarmas disparó en el último mes |

---

## Criterios para Avanzar de Versión

| Versión | Prerequisito de negocio |
|---|---|
| v0.2 | Hub v0.1 en producción + al menos 1 integrador activo |
| v0.3 | Hub v0.2 + al menos 5 integradores + ventas recurrentes |

No se inicia una versión nueva sin cumplir el prerequisito — el riesgo de construir sin demanda validada es mayor que el beneficio de adelantar el trabajo.

---

## Gate de Salida

- [x] Roadmap v0.1 → v0.3 definido
- [x] Mejoras por versión documentadas con alcance claro
- [x] Criterios para avanzar de versión establecidos
- [x] Backlog sin versión asignada registrado
- [ ] Revisado y aprobado por Charlie
