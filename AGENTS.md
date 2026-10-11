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

Binding de Claude Code / Cursor, **obligatorio para continuar**. Manual de cada rol: `.harness/method.md §8`.

### Agentes Base (6)
- **`orquestador`** — Coordina features, asigna fases, delega roles
- **`autor-de-spec`** — Elicita Fase 1 (especificación interactiva con usuario)
- **`arquitecto`** — Redacta Fase 2 (Plan: componentes, contratos, secuenciación)
- **`implementador`** — Fase 3–4 (Tasks, código, tests, validación)
- **`revisor`** — QA, Gate, documentación, verificación `verified`
- **`explorador`** — Investigación, búsquedas en repo, mapeo de dependencias

### Especialistas (17)
- **`experto-ux-ui`** (`ADR-003`, activo) — diseña y revisa la UX/UI de los 3 productos. Toda feature de interfaz pasa por él antes de `verified`.
- **16 especialistas de módulo** — ver `.claude/agents/README.md` (nota: referencian rutas pre-ADR-001; refrescar antes de usar).

## 🔴 Regla Crítica — Código Ordenado y Profesional

**Código DEBE reflejar orden, comentarios y metodología — no aleatoriedad.**

**Comentarios:**
- Obligatorios donde la lógica no es obvia
- Explicar POR QUÉ, no QUÉ
- Una línea antes de la sección, breve

**Orden Visual:**
- Estructura clara y predecible
- Agrupación lógica de funciones
- Separación visual entre bloques (línea en blanco)
- Indentación consistente (2 espacios JS, 4 Python)

**Patrones Consistentes:**
- **Mismo tipo = mismo patrón en TODO el repo**
- Todos los servicios usan la misma estructura
- Todos los endpoints: ruta → validar → procesar → responder
- Todos los tests: arrange → act → assert

**Profesionalismo Visual:**
- Código que diga "personas ordenadas" de inmediato
- Quien lee entiende la arquitectura en 2 minutos
- Patrones visuales claros

**Checklist (pre-commit):**
- [ ] ¿Hay comentarios donde no es obvio?
- [ ] ¿Está ordenado por bloques lógicos?
- [ ] ¿Sigue el patrón de archivos similares?
- [ ] ¿Indentación consistente?

## 🔴 Regla Crítica — Resolver Desde la Raíz

**Ante fallas: NUNCA parches. SIEMPRE resolver desde la causa raíz.**

**Prohibido:**
- ❌ If temporales (`if os.getenv("TESTING")`)
- ❌ Comentarios `TODO`, `HACK`, `FIXME` sin fecha
- ❌ Skipear tests ("lo arreglamos después")
- ❌ Agregar defensas alrededor del error

**Método (resolver desde la raíz):**

1. **Investigar:** Stacktrace de abajo hacia arriba — ¿dónde se originó?
2. **Comprender:** ¿Qué asunción era incorrecta?
3. **Fixar:** Cambiar la causa raíz, no el síntoma
4. **Validar:** Tests que confirmen que el fix es permanente
5. **Limpiar:** Eliminar workarounds y code smells

**Ejemplo:**
- **Síntoma:** Endpoint GET `/vaults` retorna bóveda de otro usuario
- **Raíz:** No validar `current_user.id == vault.owner_id`
- **Fix:** Agregar validación en el query
- **Validar:** Test que asegure aislamiento

**Por qué:** Parches = deuda técnica + código frágil. Fix desde raíz = profesional + mantenible.

## 🔴 Regla Crítica — Respuestas Concisas

**Chat = directo al grano. Claro, conciso, sin relleno.**

**✅ Bien:** Una frase qué + resultado + próximo (3-4 líneas max)
**❌ Mal:** "Como te mencioné", contexto basura, redundancias

**Por qué:** Tokens = recursos. Respuestas largas = consumo innecesario.
