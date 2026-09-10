---
id: ADR-003
tipo: adr
estado: accepted
fecha: 2026-09-10
---

# ADR-003 · Especialista de UX/UI en el arnés

## Contexto y planteamiento del problema

El ecosistema Hira tiene interfaz de peso en los 3 productos: `hira-server` (SCADA
con MD3 + Cyan, mimics React Flow, Monaco editor — `SRV-ADR-UI-0{1..4}`),
`hira-studio` (SPA de ingeniería) y `hira-hub` (panel cloud). Ya hay un sistema de
diseño especificado (`docs/hira-server/spec/ui-ux/`) y un agente `hira-frontend` que
**implementa** el código de frontend. Falta un especialista que vele por la **calidad
de UX/UI** — diseño y revisión, no implementación — para que las interfaces sean
profesionales y con buena experiencia de usuario de forma consistente.

`.claude/agents/README.md` fija que un especialista nuevo se añade **vía un `ADR-`**.

## Decisión

Se añade el especialista **`experto-ux-ui`** a `.claude/agents/`:

- **Delegable** en cualquier feature que toque interfaz de cualquiera de los 3 productos.
- **Fase 1/2:** aporta flujos, estados por vista, componentes del sistema de diseño a
  reutilizar y `RF-` de UX medibles.
- **Fase 4:** revisa la UI construida contra el estándar (jerarquía, espaciado,
  tipografía, contraste **WCAG AA**, consistencia con el sistema de diseño,
  accesibilidad, responsive, microcopy, movimiento) antes de que cierre el `revisor`.
- **Complementa a `hira-frontend`**, no lo reemplaza: `experto-ux-ui` diseña y revisa;
  `hira-frontend` construye. La fuente de verdad del sistema de diseño sigue siendo
  `docs/hira-server/spec/ui-ux/`; cambiarlo es un `SRV-ADR-UI-` nuevo.
- **No escribe código de producción** ni aprueba nada `verified`.

Se añade a `.harness/constitution.md` Art. 8 la cláusula: **toda feature que toque
interfaz de un frontend pasa por la revisión de UX/UI** antes de `verified`.

## Consecuencias

- **Buenas:** estándar de UX/UI explícito y revisión dedicada en los 3 productos;
  accesibilidad como requisito, no como extra.
- **Coste:** un paso de revisión por feature de frontend (rápido si la spec ya trae la
  sección de UX). Opcional — features sin interfaz no lo tocan.

## Enlaces

- Agente: `.claude/agents/experto-ux-ui.md`.
- Sistema de diseño: `docs/hira-server/spec/ui-ux/sistema-de-diseno.md` y hermanos.
- Afecta a: `.harness/constitution.md` Art. 8, `.claude/agents/README.md`, `AGENTS.md`.
- Relacionado: `ADR-001` (adopción del arnés), `E-ADR-002` (hexagonal en los 3 productos).
