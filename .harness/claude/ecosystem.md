<!-- FUENTE. Editar aquí, no en AGENTS.md/CLAUDE.md (se generan con build_claude.py). -->

# Ecosistema Hira — instrucciones base

Monorepo con tres componentes y un harness SDD-Anchored. **Antes de tocar código, lee
`.harness/method.md §2` (rúbrica) y `.harness/constitution.md`.**

## Los tres componentes

| Carpeta | Qué es | Corre en | Arquitectura |
|---|---|---|---|
| `hira-server/` | Núcleo SCADA (protocolos, alarmas, históricos, lógica, tiempo real) | Local / on-premise, con instalador | Hexagonal (`docs/hira-server/decisions/SRV-ADR-017`) |
| `hira-studio/` | Ingeniería y diseño de proyectos (configurador, lógica/pruebas, mimics, Agente Integrador) | Nube | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |
| `hira-hub/` | Licencias, crash reports, versiones, ventas, marketplace | Nube (VPS) | Hexagonal (`docs/decisions/ecosystem/E-ADR-002`) |

Frontera: **Hub y Studio en la nube, Server local** (`E-ADR-001`). Los proyectos viven
siempre en un Hira Server.

## Reglas transversales (todas las apps)

1. **Spec-first.** Solo se implementa lo que está especificado (`docs/<producto>/spec/`
   para el diseño ya cerrado; `.harness/specs/<PRODUCTO>-NNN-slug/spec.md` para features
   nuevas). Lo no especificado → Directiva de Pausa (`.harness/method.md §5`) y se espera.
   No inventes diseño.
2. **Anclas.** Toda tarea cita las anclas que toca (`RF-`/ADR de producto) y los
   `AC-<COMP>-*` que deja verificables. Cada carpeta que creas lleva su `README.md`.
3. **Contract-First.** Endpoint nuevo → primero al contrato (`docs/contracts/` si es
   entre componentes, `<app>/docs/openapi.yaml` si es interno), luego el router.
4. **Observabilidad.** Logger JSON estructurado desde `core/logger.py`. Cero `print()` en
   producción. Todo log de un request lleva `trace_id` (middleware Correlation ID,
   header `X-Trace-ID`).
5. **Seguridad.** Secrets solo en variables de entorno. Nada de SQL por concatenación
   (ORM con parámetros). Ver el registro de vulnerabilidades de cada componente.
6. **READMEs.** Cada carpeta que creas lleva su `README.md` en el mismo paso.
7. **No edites un ADR aceptado.** Se supersede con uno nuevo.
8. **No resuelvas contradicciones de diseño por tu cuenta.** Directiva de Pausa
   (`.harness/method.md §5`) y esperar revisión humana.

## Commits

```
[<COMP>-Sprint-N][TIPO][MÓDULO] qué se hizo en imperativo · Anchors: <lista>
```

`<COMP>` = `SRV` | `HUB` | `STU`.
TIPO ∈ `CREA` `IMPL` `CONTRACT` `CONFIG` `TEST` `README` `FIX` `REFACTOR` `SECURITY` `SPEC` `ADR`.
Catálogo de MÓDULO por componente en su sección de abajo.
Fin del commit: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

## Definition of Done

Anclas citadas · contrato actualizado antes del router · cada `AC-*` con test que lo cita
y pasa · `.harness/gate/check.sh` en verde · tabla de cobertura de `tasks.md` al día ·
READMEs de las carpetas nuevas.

## Equipo de agentes

El orquestador (sesión principal) reparte a los especialistas de `.claude/agents/`, cada
uno dueño de un módulo con su rango de anclas como límite. Detalle:
`.harness/claude/ORCHESTRATION.md`.
