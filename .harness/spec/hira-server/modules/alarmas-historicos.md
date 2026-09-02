---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.6 - Alarmas e Históricos.md"
título: Alarmas e Históricos — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, alarmas, históricos]
---

## Motor de Alarmas

**Responsabilidad:** evaluar condiciones de alarma en tiempo real sobre puntos asociados, gestionar estados y notificar.

- Definición: `alarm_definitions` — condición (`gt | lt | eq | ne | between`), umbral, prioridad (`critical | high | medium | low`), mensaje
- Evaluación dual: (1) al recibir cada nuevo valor vía Redis Pub/Sub, (2) por ciclo de Celery Beat — el segundo canal evita que una caída del Beat deje al sistema ciego a alarmas
- Estados: `activa → reconocida → resuelta`, cada transición con timestamp
- Reconocimiento requiere nota obligatoria del operador (`acknowledged_by`, `notes`)
- Publicación a Redis Pub/Sub (canal de alarmas) → WebSocket → frontend en tiempo real para todos los usuarios conectados

## Históricos

**Responsabilidad:** almacenar y servir series de tiempo de puntos asociados.

- Tabla `point_history` como hypertable de TimescaleDB en instancia comercial; tabla estándar en SQLite (instancia local del integrador)
- Configurable por punto: frecuencia de registro (`log_interval_ms`), si se historiza (`log_enabled`), retención
- Consulta por rango con agregaciones — objetivo de rendimiento: < 3s para 7 días de un punto, < 5s para 30 días de 50 puntos simultáneos (ver `.harness/spec/hira-server/architecture/calidad-y-riesgos.md`)
- Exportación CSV con columnas `timestamp, value, unit, point_name`
- Visualización: Plotly.js, zoom/pan interactivo, eje Y doble si hay unidades distintas

---

## Gate de Salida

- [x] Motor de Alarmas documentado con evaluación dual
- [x] Históricos documentados con objetivos de rendimiento
- [ ] Revisado y aprobado por Charlie
