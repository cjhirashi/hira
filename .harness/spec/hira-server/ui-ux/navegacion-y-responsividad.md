---
origen_vault: "7.1 - Hira Server/7.1.4 - Diseño UI-UX/7.1.4.2 - Navegación y Responsividad.md"
título: Navegación y Responsividad — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño UI-UX
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, ui, navegación, responsividad, accesibilidad]
---

## Arquitectura de Navegación

### Layout principal

```
┌─────────────────────────────────────────────────────────┐
│  TOPBAR: Logo Hira · Nombre del proyecto activo · Alarmas activas (badge) · Usuario · LiveIndicator  │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ SIDEBAR  │           ÁREA DE CONTENIDO                 │
│  (nav)   │                                             │
│          │                                              │
└──────────┴──────────────────────────────────────────────┘
```

En la instalación local del integrador (licencia de integrador, multi-proyecto — ver SRV-ADR-020), el topbar incluye además el selector de proyecto activo (ver `.harness/spec/hira-server/ui-ux/especificacion-de-vistas.md`, vista Biblioteca de Proyectos).

### Sidebar — estructura de navegación

La sidebar muestra solo los módulos a los que el usuario tiene acceso según RBAC (ver SRV-ADR-UI-02).

```
─────────────────
  Dashboard
  Mimics
─────────────────
  Alarmas        ← badge con cantidad de alarmas activas
  Históricos
─────────────────
  Lógica         ← solo Integrador (write/admin en módulo logic)
  Pruebas        ← solo Integrador
  Análisis
─────────────────
  Documentación
─────────────────
  Configurador   ← solo Admin/Integrador
  Usuarios       ← solo Admin
─────────────────
  Agente IA
─────────────────
  Monitoreo      ← solo Admin/Integrador
  Licencia
─────────────────
```

**Regla:** si el usuario no tiene acceso a un módulo, ese item simplemente no aparece en sidebar. No aparece bloqueado ni en gris (ver SRV-ADR-UI-02). El backend igualmente rechaza requests no autorizados — la ocultación en UI es UX, no seguridad.

---

## Responsividad

**Sistema:** MD3 Adaptive Design — 3 breakpoints con patrones de navegación adaptativos.

| Breakpoint MD3 | Rango | Patrón de navegación | Acceso funcional |
|---|---|---|---|
| **Compact** | 0–599dp | Navigation Bar (bottom, hasta 5 ítems) | Solo lectura: Dashboard, Mimics, Alarmas |
| **Medium** | 600–1239dp | Navigation Rail (lateral, iconos + label) | Acceso completo excepto Monaco Editor |
| **Expanded** | ≥ 1240dp | Navigation Drawer permanente (sidebar completo) | Experiencia completa — layout principal |

**Restricciones por breakpoint:**

- **Compact:** Configurador y Lógica no disponibles — requieren precisión de cursor. Si se intenta acceder, banner informativo: "Esta función requiere pantalla de escritorio". Monaco Editor no carga en móvil.
- **Medium:** Monaco Editor muestra aviso "Abre en escritorio para editar lógica" — el resto de funciones disponibles.
- **Expanded:** experiencia sin restricciones — layout idéntico al diseño original de sala de control.

---

## Accesibilidad

- Contraste mínimo: ratio 4.5:1 para texto sobre fondos oscuros
- Todos los estados de alarma tienen icono además del color (no solo semáforo)
- Navegación por teclado: Tab entre módulos del sidebar, Enter para seleccionar
- Los valores numéricos en tiempo real NO usan ARIA live regions (demasiado ruido) — solo las alarmas nuevas anuncian vía `role="alert"`

---

## Gate de Salida

- [x] Arquitectura de navegación validada con todos los módulos
- [x] Responsividad y accesibilidad documentadas
- [ ] Revisado y aprobado por Charlie
