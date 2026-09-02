---
origen_vault: "7.1 - Hira Server/7.1.3 - Arquitectura/7.1.3.2 - Casos de Uso Críticos.md"
título: Casos de Uso Críticos — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Arquitectura
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, arquitectura, casos-de-uso]
---

## Casos de Uso Críticos

| # | Actor | Acción | Resultado esperado |
|---|---|---|---|
| CU-01 | Integrador | Configura nuevo proyecto: agrega dispositivos BACnet/Modbus/MQTT, define puntos y crea pantallas gráficas desde el panel admin | Sistema mostrando datos reales del proyecto sin tocar código |
| CU-02 | Integrador | Crea roles personalizados con permisos específicos por módulo y área y asigna usuarios | Cada usuario ve y puede operar solo lo que su rol permite |
| CU-03 | Integrador | Escribe script Python en Monaco Editor para controlar un dispositivo sin lógica interna | Script ejecutándose en background vía Celery, operando el dispositivo según la lógica definida |
| CU-04 | Operador | Monitorea el estado del sistema en tiempo real con animaciones gráficas de los equipos | Dashboard mostrando estado actualizado de todos los puntos vía WebSocket |
| CU-05 | Operador | Recibe alarma activa, la reconoce y documenta la acción tomada | Alarma registrada con timestamps de activación, reconocimiento y resolución |
| CU-06 | Operador | Ajusta setpoint de temperatura desde un panel de control | Escritura del valor al dispositivo vía BACnet/Modbus/MQTT con confirmación en pantalla, respetando el `access_mode` y prioridad del punto asociado (ver SRV-ADR-019) |
| CU-07 | Operador | Consulta al agente IA sobre el estado del sistema o pide que ejecute una acción | IA responde en lenguaje natural y/o ejecuta la acción usando sus tools |
| CU-08 | Técnico | Consulta histórico de un punto en un rango de fechas y genera reporte PDF | Gráfica de tendencia + reporte exportado con los datos del período |
| CU-09 | Técnico | Ejecuta prueba de operación de un equipo y registra el resultado | Resultados almacenados, análisis generado, reporte disponible |
| CU-10 | Sistema | Detecta que un valor supera el umbral de alarma configurado | Alarma disparada automáticamente, notificación a usuarios autorizados, registro en histórico |
| CU-11 | Integrador | Diseña el proyecto completo en su instalación local (licencia de integrador) con simuladores, sin depender del hardware del cliente; valida lógica, mimics y alarmas; exporta paquete `.hira` y lo importa en el servidor comercial del cliente; reemplaza simuladores por dispositivos reales | Sistema operativo en campo con configuración validada — el comisionamiento es verificación, no diseño desde cero. La exportación `.hira` es opcional: solo necesaria para mover el proyecto entre instalaciones distintas (ver SRV-ADR-015) |
| CU-12 | Integrador | Desde su instalación local, abre una sesión de ingeniería remota (ver SRV-ADR-016) contra el Server activo de un cliente: agrega un nuevo punto BACnet, lo asocia con su `access_mode` y prioridad correspondiente, ajusta el umbral de una alarma y actualiza el script de lógica de un equipo — todo sin visitar la instalación físicamente | Cambios aplicados inmediatamente en el Server del cliente — no hay ciclo export/import. Lock de sesión de ingeniería visible en el panel del operador. Licencia que gobierna: la del Server remoto (ver SRV-ADR-018) |

---

## Gate de Salida

- [x] Casos de uso críticos definidos
- [x] Coherentes con el modelo de un solo producto (SRV-ADR-015) y con el modelo de puntos asociados (SRV-ADR-019)
- [ ] Revisado y aprobado por Charlie
