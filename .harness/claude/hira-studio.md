<!-- FUENTE del overlay de Hira Studio. -->

# Overlay — `hira-studio/`

Producto **cloud** de ingeniería y diseño de proyectos (`E-ADR-001`). Se accede por
navegador. **No se instala.** Guarda **borradores de diseño offline**; el proyecto que
opera vive en un Hira Server, al que Studio lo **publica**.

## Diseño de plataforma — CERRADO (`STU-ADR-001..005`, 2026-09-03)

| Tema | Decisión | ADR |
|---|---|---|
| Hosting | Instancia multi-tenant única junto a Hub; aislamiento por `integrator_id` | `STU-ADR-001` |
| Arquitectura | SPA (React/TS, MD3+Cyan) + BFF FastAPI con PostgreSQL + Redis; **Hexagonal** (homogeneizada por `E-ADR-002`, supersede la sección de arquitectura de `STU-ADR-001`) | `STU-ADR-001`, `E-ADR-002` |
| Identidad | Un `integrator_user` por integrador (store en el BFF); JWT de sesión con `integrator_id` | `STU-ADR-002` |
| Licencia | Gestionada en Hub. Licencia de integrador (`product: studio`) enlazada al usuario, validada por `CT-license`. Sin licencia válida → **solo lectura** | `STU-ADR-002` |
| Conexión a Servers | **Emparejamiento por token** generado en el Server → credencial rotable, **cifrada** en Studio (`STUDIO_PAIRING_ENCRYPTION_KEY`) | `STU-ADR-003` |
| Ejecución | **Offline en Studio** (motor de simulación + sandbox RestrictedPython) para validar el diseño; **en línea siempre en el Server** | `STU-ADR-004` |
| Publicación | Serializar el borrador (`.hira` extendido) y cargarlo al Server por la sesión de ingeniería; simuladores → mapeo a dispositivos reales por escaneo | `STU-ADR-004` |
| Agente del Integrador | En el BFF de Studio, con la API key del integrador; tools offline/online/Hub; `ai_usage_log` propio. El Agente del Cliente se queda en Server | `STU-ADR-005` |

## Estado de implementación

**Falta la spec por módulo** (`docs/hira-studio/spec/` — auth, servers/pairing, projects,
configurator, offline-runner, publish, ai) y los `AC-STU-*` detallados (grupos
`AC-STU-01..06`, ver `tasks.md` de cada feature). Y falta que SRV exponga
`CT-engineering-session` **ampliado** (`REQ-CT-engsession-v2`: pair + publish +
consultas). Ver `docs/planning/ROADMAP.md`, track STU.

No arranques una feature de Studio hasta que exista la spec por módulo. Si un cambio
necesita tocar el contrato de la sesión de ingeniería y la ampliación aún no está,
Directiva de Pausa (`.harness/method.md §5`).

## Orden de lectura

1. `docs/decisions/ecosystem/E-ADR-001-studio-producto-cloud-independiente.md`
2. `docs/hira-studio/spec/context.md` y `architecture.md`
3. `docs/hira-studio/decisions/STU-ADR-001..005`
4. `docs/hira-studio/spec/inherited-from-server.md` — qué diseño se hereda de Server.
5. `docs/contracts/engineering-session.openapi.yaml` — `CT-engineering-session` (+ ampliación pendiente).

## Contratos que consume

- `CT-engineering-session` (Studio → Server) — **único** canal hacia un Server: sesión con
  lock por proyecto, emparejamiento, publicación de proyecto, consultas del agente.
- `CT-license`, `CT-crash-report` (Studio → Hub) con `product: studio`.
- `CT-marketplace` (v0.3).

## Herencia de diseño

Configurador, modelo de puntos/asociaciones, API `hira` de scripts y formato de mimic se
**especifican en `spec/hira-server/`**; Studio los **implementa**, no los redefine. El
`offline-runner` implementa el mismo contrato de la API `hira` y las mismas restricciones
de RestrictedPython que el Server. Índice: `inherited-from-server.md`.

## Módulos para el commit

`INFRA` `CORE` `AUTH` `SERVERS` `PROJECTS` `CONFIGURATOR` `OFFLINE-RUNNER` `PUBLISH`
`AI` `MIMICS` `CONTRACT` `FRONTEND`

## Reglas

Transversales del ecosistema (`.harness/claude/ecosystem.md`). Además:
- Todo acceso a datos del BFF filtra por `integrator_id` del JWT — es la frontera de
  aislamiento (`AC-STU-02`). No hay endpoint que devuelva datos de otro integrador.
- Credenciales de emparejamiento: cifradas en reposo, nunca en logs, nunca al SPA.
- El `offline-runner` nunca toca un Server ni un dispositivo real.
