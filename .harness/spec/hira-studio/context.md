---
título: Contexto — Hira Studio (producto cloud)
componente: hira-studio
tipo: Especificación
status: borrador
última_actualización: 2026-09-02
ancla_origen: E-ADR-001
---

## Qué es Hira Studio

Hira Studio es la **vertiente cloud de ingeniería** del ecosistema Hira: el entorno donde
el integrador diseña, configura, prueba y documenta proyectos SCADA, sin instalar nada.
Se accede por navegador contra la instancia cloud de Studio operada por cjhirashi.

Formalizado en `E-ADR-001` — supersede parcialmente `SRV-ADR-015/016/017`.

## Qué NO es

- **No aloja proyectos.** Los proyectos viven en un Hira Server (local del integrador o de
  producción del cliente). Studio es un cliente de ingeniería sobre esos Servers.
- **No es un runtime SCADA.** No hace polling de dispositivos, no evalúa alarmas, no
  ejecuta lógica continua en producción. Eso es Hira Server.
- **No se instala.** No hay `docker compose` para el integrador, no hay perfil
  `HIRA_DEPLOY_MODE=studio`.

## Quién lo usa

| Actor | Uso |
|---|---|
| **Integrador** | Diseña y configura proyectos: dispositivos, asociación de puntos, mimics, scripts de lógica y prueba, alarmas, documentación. Trabaja contra uno o varios Servers. |
| **cjhirashi** | Opera la instancia cloud de Studio; en v0.3, publica bloques SVG y plantillas al marketplace de Hub. |

No hay usuarios de operación (Operador, Visor) en Studio — esos usan Hira Server
directamente.

## Cómo se conecta

```
Hira Studio (cloud)
    │
    ├─► sesión de ingeniería ──────► Hira Server A (local del integrador)   [CT-engineering-session]
    ├─► sesión de ingeniería ──────► Hira Server B (producción, cliente X)  [CT-engineering-session]
    │       · lock exclusivo por proyecto · espejo Redis con TTL · heartbeat · 409 si ocupado
    │
    ├─► valida su licencia en ─────► Hira Hub   [CT-license]  (product: studio)
    └─► envía crash reports a ─────► Hira Hub   [CT-crash-report]
```

- Toda modificación de un proyecto pasa por una **sesión de ingeniería** contra el Server
  que lo aloja (`CT-engineering-session`, derivada de `SRV-ADR-016`). Solo una sesión
  activa por proyecto; un segundo intento recibe `409`.
- El **licenciamiento por puntos en línea** lo sigue fijando el Server destino
  (`SRV-ADR-018`) — Studio no relaja ese límite.
- Los cambios hechos desde Studio quedan operando de inmediato en el Server (no hay ciclo
  export/import). El paquete `.hira` sigue siendo mecanismo de migración entre Servers,
  no de sincronización con Studio.

## Relación con el resto del ecosistema

- **Hira Server** — el sistema sobre el que Studio opera. Ver `spec/hira-server/`.
- **Hira Hub** — licencia y crash reports de Studio; en v0.3, origen del catálogo de
  bloques SVG y del marketplace de plantillas `.hirat` que Studio consume.
- **Herencia de diseño** — gran parte del diseño de Studio se hereda de módulos ya
  especificados para Server. Índice en
  [`inherited-from-server.md`](inherited-from-server.md).

## Estado

Borrador. El diseño detallado de Studio arranca cerrando
[`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md) → primeros `STU-ADR-###`. Hasta entonces, Studio
no tiene sprint activo (el roadmap del ecosistema lo pone después de Server `v0.1` y
Hub `H0`).
