---
origen_vault: "7.2 - Hira Hub/7.2.2 - Stakeholders.md"
título: Stakeholders — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 02 — Stakeholders
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: pendiente
github: ""
tags: [proyecto, productos-software, hira-hub, stakeholders]
ecosistema: Hira
relacionado_con: 7.1 - ÍNDICE - Hira
---

## Stakeholders del Proyecto

### cjhirashi — Propietario y Operador

El único usuario humano de Hub. No hay otros operadores ni equipo.

| Aspecto | Detalle |
|---|---|
| **Rol** | Desarrollador, operador y administrador de Hub |
| **Acceso** | Panel Admin completo — licencias, crash reports, actualizaciones, métricas |
| **Responsabilidad** | Uptime de Hub, gestión de licencias, respuesta a crash reports, publicación de actualizaciones |
| **Expectativa** | Hub opera solo — mínimo tiempo operativo diario requerido |

---

### Hira Server — Cliente Técnico Primario

No es un usuario humano. Es el sistema que más interactúa con Hub en producción.

| Aspecto | Detalle |
|---|---|
| **Rol** | Valida licencia al arrancar y periódicamente; envía crash reports cuando ocurren; consulta versiones disponibles |
| **Acceso** | API Hub con API key por instalación |
| **Volumen esperado** | 1 request de validación por Server al arrancar + cada 24h + cada crash |
| **Dependencia** | Hub puede estar caído — Server tiene grace period de 72h antes de entrar en modo degradado |

---

### Hira Studio — Cliente Técnico Secundario

Mismo patrón que Server pero con menor volumen.

| Aspecto | Detalle |
|---|---|
| **Rol** | Valida licencia Studio; envía crash reports |
| **Acceso** | API Hub con API key por instalación de Studio |
| **Dependencia** | Studio puede operar offline — la validación falla silenciosamente si Hub no está disponible |

---

### Integrador — Usuario Indirecto

El integrador nunca accede a Hub directamente. Su relación es a través de las licencias que compra.

| Aspecto | Detalle |
|---|---|
| **Rol** | Comprador de licencias Server y Studio |
| **Acceso** | Ninguno a Hub — su Server se conecta automáticamente |
| **Touchpoint** | Recibe license key por email tras compra; ve notificaciones de vencimiento en su panel Server |
| **Expectativa** | La licencia funciona sin que tenga que hacer nada; las actualizaciones llegan sin intervención |

---

### Stripe — Sistema de Pagos (v0.2)

| Aspecto | Detalle |
|---|---|
| **Rol** | Procesa pagos de licencias en el portal de ventas |
| **Integración** | Webhook de Stripe → Hub crea license key automáticamente al confirmar pago |
| **Responsabilidad** | Stripe es responsable del procesamiento; Hub es responsable de la emisión de key tras confirmación |

---

## Mapa de Interacciones

```
cjhirashi
  └── Panel Admin Hub
        ├── Gestión de licencias (emitir, revocar, extender)
        ├── Revisión de crash reports
        └── Publicación de actualizaciones

Hira Server (instalación activa)
  └── API Hub
        ├── POST /api/licenses/validate (arranque + periódico)
        ├── POST /api/crash-reports (cuando hay crash)
        └── GET /api/updates/latest (consulta periódica)

Integrador
  └── (indirecto) Recibe license key → su Server la usa automáticamente

Stripe (v0.2)
  └── Webhook → Hub emite license key automáticamente
```

---

## Protocolos

### Protocolo de Comunicación

Hub es infraestructura interna — no hay usuarios externos que notificar. cjhirashi es el único operador.

| Situación | Acción |
|---|---|
| **Cambio breaking en API** (endpoint renombrado, schema modificado) | Documentar en `DEVIATIONS.md` del repo + actualizar `openapi.yaml` + dar ≥1 sprint de margen antes de deprecar la versión anterior |
| **Hub caído en producción** | Seguir Runbook RB-H01 — ver .harness/spec/hira-hub/deployment.md - Operación |
| **Vulnerabilidad crítica detectada** | Registrar en .harness/spec/hira-hub/portfolio.md - Registro de Vulnerabilidades + resolver en sprint activo o urgente |

### Protocolo de Resolución de Conflictos

cjhirashi es el único decisor. La tensión principal es **velocidad de desarrollo vs estabilidad de la API** (los Servers en campo dependen de ella).

Árbol de decisión:
1. ¿El cambio rompe compatibilidad con Servers activos? → No implementar sin grace period documentado (mínimo 1 sprint de antelación + versión de API nueva)
2. ¿El cambio afecta seguridad (VULs)? → Prioridad máxima — entra al sprint activo aunque no estaba planeado
3. ¿El cambio es un feature nuevo sin impacto en compatibilidad? → Entra al backlog en .harness/spec/hira-hub/incidents.md - Mejoras con prioridad según impacto

### Protocolo de Integración Tardía

Si se descubre un stakeholder nuevo (ej: sistema externo que necesita consultar Hub, cliente enterprise con requisitos especiales):
1. Documentar en este archivo: quién es, qué necesita, en qué fase se descubrió
2. Evaluar si afecta los ADRs de .harness/spec/hira-hub/conceptual-design.md - Diseño Conceptual
3. Si hay impacto en arquitectura: abrir revisión de Fase 03/04 antes de implementar
4. Registrar en Bitácora de Cambios

---

## Gate de Salida

- [x] Stakeholders identificados y roles documentados
- [x] Mapa de interacciones claro
- [x] Protocolos documentados (Comunicación, Conflictos, Integración Tardía)
- [ ] Revisado y aprobado por Charlie
