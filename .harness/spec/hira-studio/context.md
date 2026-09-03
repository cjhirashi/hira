---
título: Contexto — Hira Studio (producto cloud)
componente: hira-studio
tipo: Especificación
status: activo
última_actualización: 2026-09-03
ancla_origen: E-ADR-001
decisiones: [STU-ADR-001, STU-ADR-002, STU-ADR-003, STU-ADR-004, STU-ADR-005]
---

## Qué es Hira Studio

Hira Studio es la **vertiente cloud de ingeniería** del ecosistema Hira: el entorno donde
el integrador diseña, configura, prueba y documenta proyectos SCADA, sin instalar nada.
Se accede por navegador contra la instancia cloud de Studio operada por cjhirashi.

Formalizado en `E-ADR-001` — supersede parcialmente `SRV-ADR-015/016/017`.

## Qué NO es

- **No aloja el proyecto que opera.** El proyecto **autoritativo y en operación** vive en
  un Hira Server, al que Studio lo publica (`STU-ADR-004`). Studio sí guarda **borradores
  de diseño** offline (con dispositivos como simuladores) hasta que se publican.
- **No es un runtime SCADA de producción.** No hace polling de dispositivos reales, no
  evalúa alarmas operativas, no ejecuta lógica continua 24/7. Sí ejecuta lógica y pruebas
  **contra simuladores, en modo diseño offline**, para validar el proyecto antes de
  publicarlo (`STU-ADR-004`).
- **No se instala.** No hay `docker compose` para el integrador, no hay perfil
  `HIRA_DEPLOY_MODE=studio`. (El integrador sí puede instalar un **Hira Server** propio
  como banco de pruebas y emparejarlo con Studio.)

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

## Diseño resuelto (SQ-1..SQ-8)

Las 8 preguntas abiertas se cerraron el 2026-09-03 (ver
[`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md) para el detalle y `.harness/adr/hira-studio/`):

| Tema | Decisión | ADR |
|---|---|---|
| Hosting / tenancy | Instancia multi-tenant única junto a Hub, aislamiento por `integrator_id` | `STU-ADR-001` |
| Arquitectura | SPA + BFF (FastAPI) con BD PostgreSQL propia + Redis; estructura directa | `STU-ADR-001` |
| Identidad | Un `integrator_user` por integrador (store en el BFF de Studio); JWT de sesión con `integrator_id` | `STU-ADR-002` |
| Licenciamiento | Gestionado en Hub. La licencia de integrador (de Hub) se enlaza al usuario de Studio y se valida por `CT-license`. Sin licencia válida → solo lectura | `STU-ADR-002` |
| Conexión a Servers | Emparejamiento por token generado en el Server; credencial rotable, cifrada en Studio | `STU-ADR-003` |
| Ejecución de lógica/pruebas | Offline en Studio contra simuladores (validación de diseño); en línea siempre en el Server | `STU-ADR-004` |
| Publicación | Studio serializa el proyecto (formato `.hira` extendido) y lo carga al Server por la sesión de ingeniería; los simuladores se mapean a dispositivos reales por escaneo | `STU-ADR-004` |
| Multi-proyecto | Biblioteca de Studio = borradores offline + pares `(Server, proyecto)` emparejados. Multi-proyecto sigue siendo capacidad del Server (`SRV-ADR-020`) | `STU-ADR-004` |
| Agente del Integrador | Corre en el BFF de Studio con la API key del integrador; tools offline/online/Hub. El Agente del Cliente se queda en Server | `STU-ADR-005` |

## Estado

Diseño de plataforma cerrado. Falta la **spec por módulo** de Studio
(`spec/hira-studio/` — configurador, motor offline, publicación, agente, emparejamiento,
biblioteca) y sembrar los `AC-STU-*` correspondientes. En el roadmap, la vertiente Studio
va después de que Server exponga `CT-engineering-session` ampliado
(`.harness/coordination/ROADMAP.md`, track STU).
