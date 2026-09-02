---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.15 - ADR-015 - Un solo producto Hira Server-Studio con proyectos multi-protocolo.md"
título: SRV-ADR-015 — Un solo producto Hira Server/Studio
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-31
tags: [adr, arquitectura, hira-server, licenciamiento]
---

> **Parcialmente superseded por [E-ADR-001](../ecosystem/E-ADR-001-studio-producto-cloud-independiente.md).**
> Sigue vigente: los proyectos viven en Hira Server y `.hira` es mecanismo de migración,
> no de sincronización. Ya no vigente: Server y Studio como un solo instalable — Studio es
> un producto cloud independiente, Server es el instalable on-premise.

## Contexto

El ecosistema tiene tres fases de trabajo del integrador: diseño, operación en producción, y gestión centralizada del desarrollador. La versión original de este ADR proponía dos productos instalables por separado — Hira Studio (PC del integrador, SQLite, modo offline aislado) y Hira Server (servidor del cliente, PostgreSQL, producción) — sincronizados mediante exportación e importación de paquetes `.hira`.

Ese modelo obligaba a construir, versionar y distribuir dos productos distintos, y creaba dos copias de datos que podían desincronizarse.

## Decisión

Hira Server y Hira Studio son **un solo producto, un solo instalador**: Hira Server/Studio.

- **Los proyectos/sistemas viven en Hira Server.** Un Server puede alojar uno o más proyectos, según el tipo de licencia (ver SRV-ADR-018 — Licenciamiento por puntos en línea, y SRV-ADR-020 — Multi-proyecto exclusivo de licencia de integrador).
- **Hira Studio es la herramienta de diseño e ingeniería**, no un contenedor de datos propio. Nunca opera aislado — siempre está conectado a un Server, ya sea:
  - **Local**: un Server corriendo en la misma PC del integrador, para diseño y demos sin depender del cliente.
  - **Remoto**: la instalación real del cliente, a la que Studio se conecta vía red con sesión de ingeniería controlada (ver SRV-ADR-016).
- Los cambios hechos desde Studio quedan operando de inmediato en el Server al que está conectado — no hay paso de exportar/importar como mecanismo principal de sincronización.
- La exportación como paquete `.hira` sigue existiendo, pero es opcional: sirve para mover un proyecto de un Server a otro (migración, respaldo, o llevar un diseño de la instalación local del integrador a la instalación real del cliente).

## Alternativas consideradas

- Dos productos separados con sincronización por paquete `.hira` (modelo original — descartado por duplicar mantenimiento y crear riesgo de desincronización de datos)
- Studio como aplicación completamente standalone sin capacidad de conexión remota (descartado — elimina la posibilidad de que el integrador modifique un proyecto sin estar físicamente frente al Server)

## Consecuencias

- Un solo pipeline de build, versión y release — no dos productos con ciclos independientes
- Una sola fuente de verdad de datos por proyecto — sin riesgo de desincronización entre copias
- El límite de negocio que impedía que Studio sustituyera a Server ya no se resuelve limitando controladores simultáneos (ver VUL-SRV-014, ahora obsoleto) sino limitando puntos en línea según el tipo de licencia — ver SRV-ADR-018
- `HIRA_DEPLOY_MODE` dejó de representar "dos productos" y ahora solo distingue el perfil de despliegue (local ligero vs. servidor de producción) dentro del mismo código base
