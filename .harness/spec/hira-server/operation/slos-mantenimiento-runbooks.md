---
origen_vault: "7.1 - Hira Server/7.1.8 - Operación (diseño)/7.1.8.2 - SLOs, Mantenimiento y Runbooks.md"
título: SLOs, Mantenimiento y Runbooks — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Operación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, slo, mantenimiento, runbooks]
---

## SLOs — Instalación de Perfil Producción

El Server corre en infraestructura del cliente. Estos SLOs son objetivos de diseño del sistema, no compromisos de uptime gestionados centralmente por cjhirashi — cada instalación es independiente. Complementan los atributos de calidad de `.harness/spec/hira-server/architecture/calidad-y-riesgos.md` con el enfoque operativo (disponibilidad, recuperación).

| Métrica | Objetivo | Cómo se mide |
|---|---|---|
| Disponibilidad del sistema SCADA | 99.5% mensual | Health check cada 60s vía script local |
| Latencia API REST (P95) | < 200ms | Logs de Nginx en el servidor del cliente |
| Latencia WebSocket (actualización de punto asociado) | < 1s | Medición en pruebas de carga (`.harness/spec/hira-server/validation/test-plan.md`) |
| Tiempo de recuperación ante caída de servicio | < 2 min | Celery + Docker restart policy `unless-stopped` |
| Detección de dispositivo offline | < 2 ciclos de polling | Motor de Protocolos — config por defecto 5s |
| Capacidad de puntos simultáneos | 200 puntos asociados @ < 60% CPU (2 vCPU) | Validado en `.harness/spec/hira-server/validation/acceptance-criteria.md` |

---

## Rutina del Integrador

### Verificación de estado — al visitar una instalación

Desde el panel: **Admin → Sistema → Estado**

```
✅ Base de datos          Operando — último backup: hace 6h
✅ Motor de protocolos    Operando — N dispositivos activos
✅ Motor de alarmas       Operando — N alarmas activas
✅ Motor de lógica        Operando — N scripts corriendo
✅ Históricos             Operando
⚠️ Licencia              Vence en N días — renovar pronto
🔴 Crash reporter         Sin conexión a internet
```

### Procedimientos frecuentes

**Agregar un dispositivo nuevo:**
1. Panel → Dispositivos → Agregar
2. Seleccionar protocolo (BACnet / Modbus / MQTT)
3. Ingresar parámetros de red del dispositivo
4. Escanear → revisar puntos candidatos
5. Asociar los puntos que se van a usar, definiendo `access_mode` y prioridad si es BACnet (ver SRV-ADR-019)

**Reemplazar un dispositivo defectuoso:**
1. Panel → Dispositivos → [dispositivo] → Editar
2. Actualizar IP o dirección del nuevo dispositivo
3. Verificar que los puntos asociados siguen respondiendo
4. Sin pérdida de históricos — los datos anteriores se conservan

**Exportar proyecto para respaldo o migración:**
1. Panel → Proyecto → Exportar `.hira`
2. Archivo descargado incluye: dispositivos, puntos candidatos y asociados, mimics, scripts, alarmas
3. Importar en otra instalación con: Panel → Proyecto → Importar `.hira`

**Agregar un usuario:**
1. Panel Admin → Usuarios → Nuevo usuario
2. Asignar rol de operación (alcance del proyecto activo) o rol de integrador (alcance global de la instancia — ver SRV-ADR-020)
3. El usuario recibe credenciales por email (si hay internet) o el integrador las entrega manualmente

### Mantenimiento programado recomendado

| Frecuencia | Acción |
|---|---|
| Diario (automático) | Backup de base de datos a las 02:00 AM |
| Semanal | Revisar log de alarmas — ¿hay patrones repetitivos? |
| Mensual | Verificar espacio en disco — históricos crecen con el tiempo |
| Antes de cada visita | Revisar crash reports en Hub para anticipar problemas |
| Anual | Renovar licencia antes del vencimiento |

### Expansión de capacidad

| Síntoma | Acción |
|---|---|
| CPU > 80% sostenido | Aumentar recursos del servidor o reducir frecuencia de polling |
| Disco > 70% | Configurar retención de históricos (purgar datos de más de N días) |
| Cerca del tope de puntos en línea de la licencia | Considerar upgrade de tier (ver SRV-ADR-018) |
| Más de 10 usuarios concurrentes | Verificar límite de licencia actual |

---

## Runbooks

### RB-01 — Servicio caído (un contenedor no responde)

```
Síntoma: Panel muestra servicio en rojo / endpoint /health falla

1. Revisar estado desde Panel Admin → Sistema → Estado
2. Si el contenedor está caído:
   → El script de watchdog lo reinicia automáticamente en < 2 min
   → Si no reinicia solo: contactar al integrador
3. El integrador verifica: Panel Admin → Logs → [servicio]
4. Si el error es desconocido: exportar logs y reportar a Hub
```

### RB-02 — Dispositivo BACnet/Modbus no responde

```
Síntoma: Punto asociado marcado como "offline" en el dashboard

1. Verificar conectividad física del dispositivo (red, alimentación)
2. Desde panel → Dispositivos → [dispositivo] → Escanear
3. Si responde al escaneo pero sigue offline: reiniciar el polling
   Panel → Dispositivos → [dispositivo] → Reiniciar conexión
4. Si no responde al escaneo: problema físico, no de Hira
```

### RB-03 — Alarma que no se desactiva sola

```
Síntoma: Alarma en estado "activa" aunque el valor volvió a rango normal

1. Verificar en históricos que el valor realmente regresó al rango
2. Si sí regresó: posible bug en el motor de alarmas
   → Reconocer la alarma manualmente
   → Reportar a Hub con el ID de la alarma y timestamp
3. Si no regresó: el sistema está correcto, el equipo sigue en falla
```

### RB-04 — Script de lógica se detiene

```
Síntoma: Script en estado "detenido" inesperadamente

1. Panel Admin → Scripts → [script] → Ver log de ejecución
2. Si hay excepción Python: corregir el script y reactivar
3. Si se detuvo sin error visible: Celery reinició y el script
   no retomó automáticamente → reactivar manualmente desde el panel
4. Si se repite: revisar uso de memoria del servidor (posible OOM)
```

### RB-05 — Disco casi lleno

```
Síntoma: Alerta de disco > 80% en Panel Admin → Sistema

1. Panel Admin → Sistema → Almacenamiento → Ver distribución
2. Si son históricos: configurar retención
   Panel → Históricos → Configuración → Purgar datos de más de N días
3. Si son logs: Panel → Sistema → Logs → Limpiar logs de más de 30 días
4. Si persiste: notificar al cliente — necesita expandir disco del servidor
```

---

## Gate de Salida

- [ ] SLOs documentados y validados en pruebas de carga (`.harness/spec/hira-server/validation/test-plan.md`)
- [ ] Todos los runbooks probados al menos una vez en ambiente staging
- [ ] Panel Admin → Sistema → Estado muestra información correcta en tiempo real
