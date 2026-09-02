---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.18 - ADR-018 - Licenciamiento por puntos en línea.md"
título: SRV-ADR-018 — Licenciamiento por puntos en línea
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-31
tags: [adr, arquitectura, hira-server, licenciamiento, seguridad]
---

## Contexto

Bajo el modelo de un solo producto (SRV-ADR-015), hace falta un mecanismo que impida que la instalación local del integrador (licencia de integrador, de bajo costo) se use como sustituto de una licencia comercial de cliente — el mismo problema de fondo que documentaba VUL-SRV-014 bajo el modelo anterior de dos productos, ahora resuelto de forma distinta.

## Decisión

El límite de licencia se mide en **puntos en línea simultáneos**, no en cantidad de puntos creados ni en controladores conectados:

- **Licencia de integrador:** escaneo e integración de dispositivos sin restricción. La cantidad de puntos que puede **diseñar/crear** no tiene límite. La cantidad de puntos que puede tener **en línea (activos) al mismo tiempo** sí está limitada a un tope de demo.
- **Licencia comercial (Starter/Professional/Enterprise):** el tope de puntos en línea corresponde al tier contratado — ya definido en la tabla `license` (`max_points`) del modelo de datos existente.
- Cuando Studio se conecta a un Server remoto (SRV-ADR-016), la licencia que rige es la del Server remoto, no la del integrador. El integrador puede así validar el sistema completo en línea siempre que el Server remoto tenga licencia suficiente para la cantidad de puntos del proyecto.

## Alternativas consideradas

- Limitar por cantidad de controladores reales simultáneos (modelo VUL-SRV-014 original — descartado porque ya no existe un "modo Studio" separado que limitar; el riesgo ahora es el Server local, no Studio)
- Limitar por cantidad de puntos creados en el diseño (descartado — impediría diseñar sistemas grandes en fase de diseño, que es exactamente lo que la licencia de integrador debe permitir)

## Consecuencias

- No se requiere tabla nueva — `license.max_points` ya cubre este caso; se reinterpreta como tope de puntos en línea, no de puntos totales del proyecto
- El diseño del proyecto puede exceder el límite de la licencia de integrador sin error — solo se restringe cuántos puntos pueden estar activos (recibiendo datos en tiempo real) simultáneamente
- **VUL-SRV-014 queda resuelto por este ADR** — actualizar su estado en el documento de Vulnerabilidades y Seguridad de 🔴 Abierto a 🟢 Resuelto por rediseño, referenciando este documento
