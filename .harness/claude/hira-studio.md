<!-- FUENTE del overlay de Hira Studio. Nuevo (E-ADR-001). -->

# Overlay — `hira-studio/`

Producto **cloud** de ingeniería y diseño de proyectos (`E-ADR-001`). Se accede por
navegador. **No se instala, no aloja proyectos, no es runtime SCADA.** Es un cliente de
ingeniería sobre uno o varios Hira Server remotos.

## Estado: diseño no cerrado

`hira-studio/` **no tiene sprint activo todavía.** Antes de implementar hay que resolver
`.harness/spec/hira-studio/OPEN-QUESTIONS.md` (SQ-1..SQ-8: auth cloud, conexión a
múltiples Servers, tenancy/hosting, backend propio, ejecución de lógica/Agente, multi-
proyecto en cloud, licenciamiento de Studio, modo offline/demos). Cada una se cierra con
un `STU-ADR-###` en `.harness/adr/hira-studio/`.

Si te piden implementar Studio y las OPEN-QUESTIONS relevantes siguen abiertas → dilo y
para. No improvises la arquitectura de Studio.

## Orden de lectura

1. `.harness/adr/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
2. `.harness/spec/hira-studio/context.md`
3. `.harness/spec/hira-studio/OPEN-QUESTIONS.md`
4. `.harness/spec/hira-studio/inherited-from-server.md` — qué diseño se hereda de Server.
5. `.harness/contracts/engineering-session.openapi.yaml` — `CT-engineering-session`.

## Contratos que consume

- `CT-engineering-session` (Studio → Server) — **único** camino para modificar un proyecto.
  Lock exclusivo por proyecto, heartbeat 60s, `409` si ocupado.
- `CT-license`, `CT-crash-report` (Studio → Hub) con `product: studio`.
- `CT-marketplace` (v0.3).

## Herencia de diseño

Configurador, edición de lógica/pruebas, mimics y Agente del Integrador se especifican
sobre la base de `.harness/spec/hira-server/` — ver el índice en
`inherited-from-server.md`. La **ejecución** de lógica/pruebas se queda en Server; Studio
edita y empuja vía la sesión de ingeniería (pendiente de cerrar SQ-5).

## Módulos para el commit (provisional — se afina con el diseño)

`INFRA` `BFF` `AUTH` `SERVERS` (gestión de conexiones a Servers) `CONFIGURATOR` `LOGIC`
`TESTS` `MIMICS` `AI` `PROJECTS` `CONTRACT` `FRONTEND`

## Reglas

Mismas transversales del ecosistema (`.harness/claude/ecosystem.md`): spec-first, anclas,
Contract-First, logger JSON, sin secrets en código, READMEs por carpeta, no editar ADRs
aceptados, no resolver contradicciones por tu cuenta.
