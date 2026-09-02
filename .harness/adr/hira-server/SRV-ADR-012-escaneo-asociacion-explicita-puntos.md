---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.12 - ADR-012 - Escaneo automático de dispositivos y asociación explícita de puntos.md"
título: SRV-ADR-012 — Escaneo automático de dispositivos y asociación explícita de puntos
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
última_actualización: 2026-07-31
tags: [adr, arquitectura, hira-server, escaneo, puntos]
---

## Contexto

Levantar manualmente la lista de puntos de un sistema BACnet o Modbus grande es tedioso y propenso a errores. BACnet tiene capacidad nativa de descubrimiento de dispositivos.

## Decisión

Hira implementa escaneo de red por protocolo: BACnet vía Who-Is/I-Am broadcast (BAC0 lo soporta nativamente) para descubrir dispositivos y leer todos sus objetos; Modbus por escaneo de rangos de registros configurables; MQTT por suscripción wildcard de topics.

El resultado del escaneo son **puntos crudos candidatos** — no se convierten automáticamente en puntos de Hira. Por SRV-ADR-019, ningún punto crudo de un controlador es utilizable en línea sin asociarse explícitamente a un punto de Hira, con su modo de acceso (lectura / lectura+escritura) y, en BACnet, su prioridad de escritura. El integrador revisa la lista de candidatos del escaneo y confirma qué puntos crea y asocia.

## Alternativas consideradas

Importación manual de lista de puntos vía CSV; solo configuración manual punto a punto; creación automática de puntos de Hira a partir del escaneo (descartado tras SRV-ADR-019 — todo punto en línea requiere asociación explícita con modo de acceso definido)

## Consecuencias

Ahorro significativo de tiempo en la integración de proyectos grandes; el escaneo alimenta un flujo de asociación guiado, no una creación automática silenciosa; la lista de puntos de Hira (ya asociados) es la fuente de verdad que alimenta el configurador, los históricos y el RAG
