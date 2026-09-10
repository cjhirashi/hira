---
título: "E-ADR-001 — Hira Studio como producto cloud independiente"
componente: ecosystem
tipo: ADR
status: accepted
fecha_creación: 2026-09-02
supersede_parcialmente: [SRV-ADR-015, SRV-ADR-016, SRV-ADR-017]
tags: [adr, ecosystem, hira-studio, arquitectura, despliegue]
---

## Contexto

El diseño previo (`SRV-ADR-015`, `SRV-ADR-016`, `SRV-ADR-017`) definió **Hira Server y
Hira Studio como un solo producto, un solo instalador**: Studio era el conjunto de
herramientas de ingeniería (configurador, motor de lógica, motor de pruebas, mimics,
agente del integrador) accesible con credenciales de integrador *dentro de la misma
instancia de Server*, ya fuera local o conectada en remoto a otro Server vía sesión de
ingeniería. `HIRA_DEPLOY_MODE` distinguía perfil `server` (PostgreSQL) de perfil `studio`
(SQLite ligero) sobre el mismo código.

Por **logística de distribución y operación**, el ecosistema se reorganiza en tres
vertientes con una frontera clara nube / local:

- **Hira Hub** — nube (VPS de cjhirashi). Licencias, crash reports, versiones, ventas,
  marketplace.
- **Hira Studio** — nube. Herramientas de ingeniería y diseño de proyectos, hospedadas.
- **Hira Server** — local / on-premise, con instalador. Núcleo SCADA en la red del
  cliente.

Mantener Studio empaquetado dentro del instalador de Server obliga a cada integrador a
instalar y mantener un stack completo solo para diseñar, complica el pipeline de release
(un binario que sirve dos propósitos con perfiles divergentes) y ata la evolución de las
herramientas de ingeniería al ciclo de release del runtime de campo.

## Decisión

**Hira Studio es un producto cloud independiente**, con su propio repositorio
(`hira-studio/` en el monorepo), su propio ciclo de release y su propio despliegue en la
nube.

1. **Studio no se instala.** Se accede por navegador contra la instancia cloud de Studio.
2. **Studio no aloja proyectos.** Los proyectos siguen viviendo en un Hira Server (local
   del integrador o de producción del cliente). Studio es un cliente de ingeniería sobre
   esos Servers.
3. **Studio se conecta a uno o varios Servers remotos** mediante **sesión de ingeniería**
   (`CT-engineering-session`, derivada de `SRV-ADR-016`): lock exclusivo por proyecto,
   espejo en Redis con TTL, heartbeat, `409` si ya hay una sesión activa. Este mecanismo,
   que antes era "una de dos variantes" de Studio, pasa a ser **el único** modo de
   operación de Studio.
4. **Studio valida su propia licencia y envía sus crash reports a Hub** por los mismos
   contratos que Server (`CT-license`, `CT-crash-report`), con `product: studio`.
5. **El límite de negocio** lo sigue fijando el licenciamiento por puntos en línea del
   Server al que Studio se conecta (`SRV-ADR-018`) — no cambia.
6. **Hira Server deja de tener perfil `studio`.** `HIRA_DEPLOY_MODE` se retira; Server
   tiene un único perfil de despliegue (producción on-premise, PostgreSQL/TimescaleDB/
   pgvector). Las herramientas de ingeniería salen del frontend de Server.

### Qué queda por diseñar

Esta decisión abre preguntas de diseño que se resuelven antes de `STU-Sprint-1` y se
registran en `.harness/spec/hira-studio/OPEN-QUESTIONS.md` (modelo de auth de Studio
cloud, gestión de múltiples Servers por integrador, tenancy/hosting, qué backend necesita
Studio propio, cómo se ejecuta hoy el agente del integrador y el motor de lógica/pruebas
si el runtime está en Server).

## Qué supersede

| ADR | Antes | Ahora |
|---|---|---|
| `SRV-ADR-015` | "Un solo producto, un solo instalador Server/Studio." | Sigue vigente que **los proyectos viven en Server** y que `.hira` es mecanismo de migración, no de sincronización. **Deja de ser cierto** que Server y Studio son un solo instalable: Studio es cloud, Server es el instalable. |
| `SRV-ADR-016` | Sesión de ingeniería remota como una de dos variantes de conexión de Studio. | El mecanismo se conserva íntegro y se promueve a contrato de ecosistema `CT-engineering-session`. Pasa a ser el **único** modo de operación de Studio. |
| `SRV-ADR-017` | `adapters/factory.py` selecciona PostgreSQL o SQLite según `HIRA_DEPLOY_MODE` (`server` / `studio`). | La Arquitectura Hexagonal de Server **se mantiene**. Se retira el perfil `studio` y la variante SQLite; Server queda con un solo perfil. |

Los tres ADRs conservan un banner de supersesión parcial que apunta aquí. No se editan en
su cuerpo.

## Alternativas consideradas

- **Mantener Server/Studio como un solo instalable y "Studio cloud" = una instancia de
  Server hospedada en perfil `studio`.** Descartada: no elimina la duplicación de pipeline
  ni la carga de mantener SQLite + PostgreSQL sobre el mismo núcleo, y ata el ciclo de las
  herramientas de ingeniería al del runtime de campo.
- **No decidir aún y diseñar el harness neutral.** Descartada: retrasa el arranque de la
  vertiente Studio y deja tres ADRs en estado ambiguo.

## Consecuencias

- Tres repos de aplicación en el monorepo: `hira-server/`, `hira-hub/`, `hira-studio/`.
- Server se simplifica: un solo perfil de despliegue, sin SQLite, sin selector de modo,
  sin árbol de rutas de ingeniería en su frontend.
- `CT-engineering-session` se vuelve contrato de primera clase entre Studio y Server, con
  su propio gate de compatibilidad.
- El diseño de Studio (`spec/hira-studio/`) hereda gran parte de `spec/hira-server/`
  (configurador, modelo de lógica/pruebas, mimics, agente del integrador) — el índice de
  qué se hereda está en `spec/hira-studio/inherited-from-server.md`.
- Nuevas anclas de Studio (`STU-ADR-###`, `AC-STU-###`, `REQ-STU-###`) se abren en
  `registry.yaml` a medida que se cierra el diseño.
