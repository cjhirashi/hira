---
título: Visión — Ecosistema Hira
componente: ecosystem
tipo: Especificación
status: activo
última_actualización: 2026-09-02
deriva_de: ["spec/hira-server/context.md", "spec/hira-hub/context.md", "E-ADR-001"]
---

## Objetivo

Desarrollar el **Ecosistema Hira**: una plataforma SCADA moderna, asequible y adaptable
sin código, con IA nativa, para integradores de automatización de edificios (HVAC, BMS,
IoT). Cubre el ciclo completo del integrador: **diseño → operación en campo → gestión
centralizada del desarrollador**.

## Las tres vertientes

| Componente | Dónde corre | Rol | Quién lo usa |
|---|---|---|---|
| **Hira Server** | Local / on-premise, con instalador (Docker Compose) | Núcleo SCADA: protocolos BACnet/Modbus/MQTT, alarmas, históricos, motor de lógica y pruebas, tiempo real, Agente del Cliente | Cliente final, Operador, Integrador (para configurar) |
| **Hira Studio** | Nube (instancia de cjhirashi) | Ingeniería y diseño de proyectos: configurador, edición de lógica/pruebas, mimics, Agente del Integrador. Se conecta a Servers remotos vía sesión de ingeniería | Integrador |
| **Hira Hub** | Nube (VPS de cjhirashi) | Licencias, crash reports, versiones/actualizaciones, portal de ventas (v0.2), marketplace de plantillas y bloques (v0.3) | cjhirashi y equipo |

Frontera clara: **Hub y Studio en la nube; Server local** (`E-ADR-001`). Los
proyectos/sistemas **viven siempre en un Hira Server** — Studio los edita, nunca los
aloja.

## Problemas que resuelve

1. Los SCADA comerciales (Ignition, Niagara, WonderWare) son costosos ($2k–$50k+) y de
   licencia restrictiva — barrera alta para integradores medianos y proyectos pequeños.
2. Adaptar el SCADA a cada proyecto exige programación o configuración técnica profunda.
3. Ninguna plataforma SCADA integra IA conversacional nativa como asistente de operación.
4. Los sistemas industriales (BACnet/Modbus) y los IoT/Smart Home (MQTT) viven en
   plataformas separadas.
5. El análisis de datos de control requiere herramientas externas (Excel, Python).
6. Dispositivos sin lógica interna requieren un PLC externo.
7. Los integradores no tienen una plataforma SCADA propia que ofrecer — dependen de
   software de terceros que no controlan y en el que no acumulan valor.

## Flujo del ecosistema

```
1. El integrador diseña el proyecto en Hira Studio (cloud), con simuladores, sin depender
   del hardware del cliente.
2. Studio abre una sesión de ingeniería contra un Hira Server (el local del integrador
   para diseño/demo, o el de producción del cliente) y aplica la configuración —
   dispositivos, asociación de puntos, mimics, scripts, alarmas.
3. Los cambios quedan operando de inmediato en ese Server. No hay ciclo export/import.
4. En campo, el integrador reemplaza simuladores por hardware real (cambio de
   configuración, no de estructura — SRV-ADR-014).
5. Hira Server valida su licencia contra Hira Hub; Studio valida la suya. Grace period de
   72h si Hub no responde (HUB-ADR-03).
6. Hub emite actualizaciones y (v0.3) nuevos bloques/plantillas hacia las instalaciones.
7. Los crash reports (opt-in, sanitizados) fluyen de Server y Studio hacia Hub.
```

## Restricciones de contexto

- El **núcleo SCADA de Server opera 100% en la red local** — no depende de internet
  (`SRV-ADR-001`). La capa de servicios (licencia online, actualizaciones, crash reports,
  IA externa, notificaciones) sí requiere conectividad; sin ella, el sistema opera con
  limitaciones conocidas.
- Server: Linux (Docker Engine) o Windows (Docker Desktop + WSL2).
- El módulo IA es opcional; cada instalación incluye además un modelo interno embebido
  (Ollama) como fallback (`SRV-ADR-021`).

## Documentos relacionados

- Modelo de negocio y flywheel → [`business-model.md`](business-model.md)
- Arquitectura del ecosistema (C4 L1) → [`ecosystem-architecture.md`](ecosystem-architecture.md)
- Stakeholders → [`stakeholders.md`](stakeholders.md)
- Decisión Studio cloud → `adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
