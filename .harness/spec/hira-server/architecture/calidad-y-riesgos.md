---
origen_vault: "7.1 - Hira Server/7.1.3 - Arquitectura/7.1.3.4 - Requisitos de Calidad y Riesgos.md"
título: Requisitos de Calidad y Riesgos — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Arquitectura
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, arquitectura, calidad, riesgos]
---

## Propósito

C4 describe la estructura del sistema pero no sus atributos de calidad ni sus riesgos arquitectónicos. Este documento cubre lo que C4 no cubre (enfoque arc42): qué tan rápido, confiable y seguro debe ser el sistema, y qué riesgos de diseño hay que vigilar. El registro operativo completo de vulnerabilidades — con estado, severidad y sprint asignado — vive en `.harness/spec/hira-server/validation/`; aquí solo se listan los riesgos de nivel arquitectónico que motivan decisiones de diseño.

## Atributos de Calidad

### Rendimiento

| Atributo | Objetivo | Contexto |
|---|---|---|
| Latencia de actualización en tiempo real | < 1s desde cambio en dispositivo hasta reflejo en dashboard | Vía WebSocket, bajo carga normal |
| Carga inicial del dashboard | < 2s con 50 puntos activos | Time to interactive en red local |
| Latencia de escritura de setpoint | < 2s desde click hasta confirmación visual | Incluye ida y vuelta al dispositivo |
| Latencia agregada por RBAC | < 5ms por request | Con caché de permisos en Redis |
| Consulta de históricos | < 3s para 7 días de un punto; < 5s para 30 días de 50 puntos simultáneos | TimescaleDB con hypertables |
| Respuesta del Agente IA | < 10s con proyecto de 200 puntos | Contexto de tamaño medio |
| API REST bajo carga | P99 < 200ms a 100 req/s, sin errores 5xx | Prueba de carga en Staging |
| Polling masivo | CPU < 60% en servidor 2 vCPU / 4GB RAM con 200 puntos a intervalo de 5s | Perfil de instalación comercial típica |

### Confiabilidad

- El núcleo SCADA (protocolos, alarmas, históricos, lógica) opera 100% en red local, sin depender de internet (ver SRV-ADR-001).
- Un worker de lógica que muere es reiniciado automáticamente por Celery en menos de 30s, sin pérdida de estado más allá del ciclo interrumpido.
- Las escrituras concurrentes sobre el mismo punto (polling vs. lógica vs. prueba) se serializan — nunca hay condición de carrera silenciosa (ver riesgo de BAC0 abajo, y el mecanismo de locks de SRV-ADR-009).
- Celery Beat es punto único de fallo del scheduler, mitigado por política de reinicio de Docker y por evaluación de alarmas dual (por Beat y por cada nuevo valor recibido vía Redis).

### Seguridad

- Ningún protocolo de comunicación (MQTT, API REST, WebSocket) acepta conexiones sin autenticación en producción.
- Ninguna escritura a un punto se ejecuta sin pasar por RBAC y sin respetar el `access_mode` de la asociación (ver SRV-ADR-019) — un punto candidato sin asociar nunca es escribible.
- El paquete `.hira` nunca contiene SQL ejecutable — se serializa y deserializa vía ORM con validación de esquema antes de tocar la base de datos.
- El Crash Reporter hacia Hira Hub sanitiza cualquier dato que pudiera identificar al proyecto o al cliente antes de enviarlo (ver ADR sobre Hub, en `7.2 - ÍNDICE - Hira Hub`).

### Portabilidad y Escalabilidad

- El mismo núcleo de dominio corre sobre PostgreSQL+TimescaleDB (instancia comercial) o SQLite (instancia local del integrador) sin cambios de lógica de negocio, gracias a la Arquitectura Hexagonal (SRV-ADR-017).
- Agregar un protocolo de comunicación nuevo se resuelve creando un adaptador nuevo, sin tocar el núcleo.
- El sistema de licenciamiento por puntos en línea (SRV-ADR-018) es el mecanismo de escalabilidad comercial — no hay límite arquitectónico al número de puntos que un proyecto puede definir, solo al número que puede tener activo simultáneamente según su tier.

## Riesgos Arquitectónicos

| Riesgo | Impacto | Mitigación de diseño |
|---|---|---|
| Escrituras concurrentes en BAC0 sin lock (polling vs. lógica) pueden producir datos inconsistentes | Alto — confiabilidad de control | `asyncio.Lock` por dispositivo en el adaptador BACnet; no bloquea dispositivos distintos |
| Celery Beat como proceso único para tareas periódicas | Medio — confiabilidad, mitigado | Restart policy de Docker + evaluación de alarmas por canal Redis además de por Beat |
| Contexto del Agente IA se satura en proyectos con muchos puntos | Medio — costo y calidad de respuesta | RAG con pgvector en vez de inyección completa de la lista de puntos |
| Compatibilidad de esquema del paquete `.hira` entre versiones | Medio — integridad de datos en migraciones | Política de versión mayor/menor explícita, con scripts de migración por versión |
| BACnet MSTP (serial) requiere acceso a puerto físico del host, no configurado por defecto | Alto si aparece en el primer proyecto de campo — planificación | Configuración opcional de puerto serial en Docker Compose, lista antes del primer despliegue con MSTP |
| Puntos candidatos de un escaneo mal entendidos como ya operativos por el integrador | Medio — riesgo de confusión operativa | La API nunca expone un punto candidato como escribible; el panel distingue visualmente candidato vs. asociado (SRV-ADR-012, SRV-ADR-019) |

El registro completo y con seguimiento activo de estas y otras vulnerabilidades — severidad, estado, sprint asignado — se documenta en `.harness/spec/hira-server/validation/`.

---

## Gate de Salida

- [x] Atributos de calidad definidos con objetivos medibles
- [x] Riesgos arquitectónicos identificados con mitigación de diseño
- [ ] Revisado y aprobado por Charlie
