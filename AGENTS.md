# AGENTS.md — mapa del ecosistema Hira

> **Punto de entrada** para cualquier agente que trabaje en este repo. Es un **mapa**,
> no una biblia: lee sólo lo que necesites.
>
> **Cómo trabajamos:** arnés **SDD Anchored** (spec viva anclada al código). El método
> completo está en **`.harness/method.md`** (léelo por secciones). Los principios
> innegociables (incluidos los perfiles de arquitectura de los 3 productos) en
> **`.harness/constitution.md`**.
>
> **Separación estricta:** `.harness/` = cómo operamos · **`docs/` = el producto**
> (especificación, ADRs, contratos, roadmap — ver `docs/README.md`).

## Antes de empezar (en orden)

1. **`bash .harness/gate/check.sh`**. Si cierra la compuerta, **DETENTE** y reporta.
2. Lee **`.harness/memory/state.md`** completo (correcciones del usuario arriba).
3. Ojea **`.harness/specs/`** — vacío por ahora (fase de diseño, sin código todavía).

## Qué es el ecosistema

Monorepo de **3 productos**, sin código todavía (fase de diseño, F0 cerrada
2026-09-03 — ver `docs/planning/`):

| Carpeta | Qué es | Corre en | Patrón interno |
|---|---|---|---|
| `hira-server/` | Núcleo SCADA: protocolos (BACnet/Modbus/MQTT), alarmas, históricos, motor de lógica, tiempo real, Agente del Cliente/Integrador | Local / on-premise, con instalador | **Hexagonal** (`docs/hira-server/decisions/SRV-ADR-017`) |
| `hira-studio/` | Ingeniería y diseño de proyectos: configurador, motor de lógica/pruebas (edición offline), mimics, Agente del Integrador, biblioteca de proyectos | Nube, multi-tenant | **Hexagonal** (`docs/decisions/ecosystem/E-ADR-002`) |
| `hira-hub/` | Licencias, crash reports, versiones, ventas, marketplace | Nube (VPS) | **Hexagonal** (`docs/decisions/ecosystem/E-ADR-002`) |

**Los 3 productos son Hexagonal** desde el 2026-09-04 (`E-ADR-002` homogeneizó el
patrón; antes Studio/Hub eran "directa"). Detalle de puertos/adaptadores por producto:
`.harness/constitution.md` Art. 1–2.

**Frontera:** Hub y Studio en la nube, Server local/on-premise (`docs/decisions/ecosystem/E-ADR-001`).
Los proyectos de ingeniería siempre viven en un Hira Server; Studio es un cliente de
ingeniería sobre uno o varios Servers remotos (`CT-engineering-session`).

Detalle de cada perfil de arquitectura (puertos, adaptadores, stack):
`.harness/constitution.md` Art. 1–2.

## Contratos compartidos

`docs/contracts/*.openapi.yaml`: `CT-license`, `CT-crash-report`, `CT-updates`,
`CT-marketplace`, `CT-engineering-session`. Cambiarlos exige acuerdo entre los
productos que los consumen.

## Convenciones

- IDs de feature nueva: `RF-`/`RNF-`/`T-` por feature, `ADR-` del arnés. Los IDs de
  producto **históricos** no se renumeran: `E-ADR-`, `SRV-ADR-`, `STU-ADR-`, `HUB-ADR-`.
- Carpetas de feature: `.harness/specs/<PRODUCTO>-NNN-slug/` (`SRV-`/`STU-`/`HUB-` prefijo).
- Commits de features nuevas: **Conventional Commits** + sufijo `(RF-NNN)`. *(Los commits
  previos a esta reestructuración usan `[<COMP>-Sprint-N][TIPO][MÓDULO] …` — convención
  histórica, no se retroactiva.)*
- Criterios de aceptación en **EARS** (`method.md §4`) para features nuevas.

## Mapa de documentación (producto)

Ver `docs/README.md` para el índice completo (spec por producto, ADRs, contratos,
roadmap, glosario, legacy). Tabla con "se actualiza cuando cambia…":
`.harness/constitution.md` Art. 11.

## Bindings de herramienta — `.claude/agents/`

Binding de Claude Code, **opcional**. Manual de cada rol: `.harness/method.md §8`.

- **Base:** `orquestador` · `autor-de-spec` · `arquitecto` · `implementador` ·
  `revisor` · `explorador`.
- **`experto-ux-ui`** (`ADR-003`, activo) — diseña y revisa la UX/UI de los frontends
  de los 3 productos; complementa a `hira-frontend`. Toda feature de interfaz pasa por
  él antes de `verified` (Constitución Art. 8).
- **16 especialistas de módulo pre-diseñados** (`hira-*`, `hub-*`) — ver
  `.claude/agents/README.md`. **Referencian rutas retiradas; refrescar antes de usarlos**
  (ver `memory/state.md`).

`.harness/claude/` genera `AGENTS.md`/`CLAUDE.md` por producto (`build_claude.py`);
sus fuentes también necesitan actualizarse a los `docs/` nuevos antes de regenerar.
