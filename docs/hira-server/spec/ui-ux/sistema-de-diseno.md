---
origen_vault: "7.1 - Hira Server/7.1.4 - Diseño UI-UX/7.1.4.1 - Sistema de Diseño.md"
título: Sistema de Diseño — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño UI-UX
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, ui, ux, diseño-visual]
---

## Alcance

Diseño visual y de experiencia de usuario del frontend de **Hira Server/Studio** — la única aplicación web del producto, presente en toda instalación: la del integrador (local, multi-proyecto) y la del cliente (comercial, un proyecto). La diferencia de experiencia entre un usuario de operación y un integrador es de acceso por rol, no de aplicación distinta.

**Usuarios:** Operador, Visor/Supervisor, Integrador (con acceso a las herramientas de ingeniería integradas — configurador, lógica, pruebas)
**Stack frontend:** React + TypeScript, Vite, Tailwind CSS, React Flow, Plotly.js, Monaco Editor, Socket.io, SVG animado

---

## Principios de Diseño

| Principio | Descripción |
|---|---|
| **Control visual** | El operador debe ver el estado completo del sistema de un vistazo. Sin ruido visual. |
| **Jerarquía de alarmas** | El color y la posición comunican urgencia — nunca texto solo. |
| **Tiempo real implícito** | Los datos se actualizan sin que el usuario haga nada. Sin botones de "refrescar". |
| **Rol diferenciado** | Un operador y un integrador ven interfaces distintas según sus permisos RBAC. |
| **Densidad de información** | Pantallas de control justifican alta densidad. Pantallas de configuración priorizan claridad. |
| **Offline-first perceptual** | Si hay pérdida de conexión al backend, la UI debe comunicarlo con un banner — no quedar congelada en silencio. |

---

## Sistema de Diseño Visual

**Base:** Material Design 3 (MD3) — ver SRV-ADR-UI-01
**Color semilla:** Cyan — `#00BCD4`
**Generación del esquema:** Material Theme Builder (https://m3.material.io/theme-builder) usando Cyan como seed. Los valores hex exactos NO se hardcodean aquí — el builder genera el archivo de tokens (CSS custom properties / JSON) que se consume en el proyecto.

### Roles de Color MD3

MD3 define roles semánticos, no valores fijos. El esquema Light y Dark se generan automáticamente del seed:

| Rol MD3 | Uso en Hira Server |
|---|---|
| `primary` | Botones principales, FAB, selección activa en sidebar, links |
| `onPrimary` | Texto/íconos sobre `primary` |
| `primaryContainer` | Fondo de chips, badges de selección, item activo de sidebar |
| `onPrimaryContainer` | Texto/íconos sobre `primaryContainer` |
| `secondary` | Elementos secundarios, chips de filtro |
| `tertiary` | Acentos informativos, badges de notificación |
| `surface` | Fondo de cards, panels, Navigation Drawer |
| `onSurface` | Texto principal, íconos |
| `surfaceVariant` | Headers de tabla, fondos alternativos, input fields |
| `outline` | Bordes de inputs, separadores, dividers |
| `error` | Mapea a `alarm-critical` dentro del esquema MD3 |

### Control de Tema: Claro / Oscuro / Sistema

Ver SRV-ADR-UI-01. Implementación: CSS custom properties (`--md-sys-color-*`) conmutadas con atributo `data-theme="light|dark"` en el root del DOM. El toggle se persiste en `localStorage` y se aplica antes del primer render (evitar flash). Posición del toggle: menú de perfil de usuario (topbar) → opción "Tema".

### Tokens de Alarma (Hira — encima de MD3)

MD3 no cubre semántica industrial. Se añaden tokens propios que conviven con el esquema MD3 y son **estables en ambos temas** (no cambian con Light/Dark — la consistencia de color en alarmas es crítica para seguridad operativa):

| Token | Hex | Uso |
|---|---|---|
| `--hira-alarm-critical` | `#EF4444` | Alarma crítica — parpadeo animado permitido |
| `--hira-alarm-high` | `#F97316` | Alarma alta |
| `--hira-alarm-medium` | `#EAB308` | Alarma media |
| `--hira-alarm-low` | `#3B82F6` | Alarma baja |
| `--hira-status-ok` | `#22C55E` | Punto/dispositivo online |
| `--hira-status-offline` | `#6B7280` | Dispositivo desconectado, punto sin dato |
| `--hira-status-warning` | `#EAB308` | Umbral próximo, latencia alta |
| `--hira-status-writing` | `#A78BFA` | Punto en proceso de escritura pendiente |

**Semáforo de escritura:** al escribir un valor a un punto asociado (ver SRV-ADR-019), el punto parpadea en `--hira-status-writing` hasta confirmación del backend.

### Tipografía

Inter como typeface (compatible con MD3 — permite override de fuente). JetBrains Mono para datos técnicos. Mapeado al MD3 Type Scale:

| Rol MD3 | Typeface | Tamaño | Peso | Uso en Hira Server |
|---|---|---|---|---|
| Title Large | Inter | 22px | 600 | Nombre de vista activa |
| Title Medium | Inter | 16px | 500 | Encabezados de sección, headers de tabla |
| Body Large | Inter | 16px | 400 | Texto principal, body |
| Body Medium | Inter | 14px | 400 | Labels, descripciones, sidebar items |
| Body Small | Inter | 12px | 400 | Metadata, timestamps, tooltips |
| Label Large | Inter | 14px | 500 | Botones, tabs, nombres de alarma |
| Label Medium | JetBrains Mono | 14px | 500 | Valores numéricos de puntos |
| Label Small | JetBrains Mono | 13px | 400 | Monaco Editor, código Python |

Los valores numéricos van siempre en fuente monoespaciada para alinear decimales en tablas.

### Espaciado, Forma y Elevación

- **Grid base MD3:** 4dp
- **Espaciado estándar:** 4, 8, 12, 16, 24, 32, 48dp
- **Shape Scale MD3:** Extra Small (4dp) para chips/badges → Small (8dp) → Medium (12dp) → Large (16dp) para cards y modales
- **Elevación MD3:** Surface Tones — no sombras, sino tint de `primary` sobre `surface` en niveles 0–5. Profundidad expresada con color, no con shadow.

### Componentes Base

| Componente | Descripción |
|---|---|
| `<PointValue>` | Valor + unidad de un punto asociado. Color de texto/fondo según token de alarma activo. Parpadeo animado si alarma crítica. |
| `<AlarmBadge>` | MD3 Badge con color de alarma. Parpadea si no reconocida. |
| `<DeviceStatusDot>` | Indicador circular MD3 de 8dp con token de estado: ok/offline/warning. |
| `<LiveIndicator>` | Punto pulsante en color `primary` — confirma que WebSocket está activo. |
| `<ConnectionBanner>` | MD3 Banner en `error` al perder conexión al backend. |
| `<SvgMimic>` | Canvas React Flow con componentes SVG animados. |
| `<TrendChart>` | Wrapper Plotly.js — tema sigue el tema activo (Light/Dark). |
| `<MonacoEditor>` | Editor Python — tema sigue el tema activo del sistema. Ver SRV-ADR-UI-04. |

---

## Gate de Salida

- [x] Sistema de diseño definido (tokens, tipografía, componentes base)
- [ ] Revisado y aprobado por Charlie
