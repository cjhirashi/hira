---
origen_vault: "7.2 - Hira Hub/7.2.4 - Diseño UI-UX.md"
título: Diseño UI/UX — Hira Hub
proyecto: Hira Hub
dominio: Productos de Software
fase: 04 — Diseño UI/UX
fecha_creación: 2026-07-24
última_actualización: 2026-07-24
tipo: Documento de Proyecto
status: en-proceso
github: ""
tags: [proyecto, productos-software, hira-hub, ui, ux, diseño-visual]
ecosistema: Hira
---

## Alcance y Versiones

Hira Hub tiene **tres capas de UI con propósitos y audiencias distintas**. Este documento cubre el diseño de las tres:

| Capa | Versión | Audiencia | Propósito |
|---|---|---|---|
| **Panel Admin** | v0.1 | cjhirashi (interno) | Gestión operativa: licencias, crash reports, versiones |
| **Portal de Ventas** | v0.2 | Integradores (público) | Compra de licencias Server/Studio con Stripe |
| **Marketplace** | v0.3 | Integradores / Fabricantes (público) | Catálogo y compra de plantillas `.hirat` |

Las tres capas comparten el mismo sistema de diseño base (MD3 con seed Cyan), diferenciadas por patrones de layout y densidad según su audiencia.

---

## Sistema de Diseño Base (compartido por las tres capas)

**Base:** Material Design 3 (MD3)
**Color semilla:** Cyan — `#00BCD4`
**Generación del esquema:** Material Theme Builder (https://m3.material.io/theme-builder). El output del builder genera los tokens como CSS custom properties que se importan en el proyecto. No se hardcodean hex en este documento.

### Roles de Color MD3

| Rol MD3 | Uso en Hira Hub |
|---|---|
| `primary` | Botones principales, CTAs, links, elementos de marca Hira |
| `onPrimary` | Texto/íconos sobre `primary` |
| `primaryContainer` | Fondos de cards seleccionadas, badges de plan "Más popular" |
| `onPrimaryContainer` | Texto/íconos sobre `primaryContainer` |
| `secondary` | Elementos de apoyo, chips de filtro, tabs secundarias |
| `tertiary` | Acentos decorativos, badges de estado |
| `surface` | Fondo de cards, panels, tablas, navbar |
| `onSurface` | Texto principal, íconos |
| `surfaceVariant` | Headers de tabla, secciones alternas, fondos de filtros |
| `outline` | Bordes de inputs, separadores |
| `error` | Acciones destructivas (revocar licencia), estados de error |
| `onError` | Texto/íconos sobre error |

### Control de Tema

| Opción | Comportamiento |
|---|---|
| **Claro** | Light Color Scheme de MD3 |
| **Oscuro** | Dark Color Scheme de MD3 |
| **Sistema** | Sigue `prefers-color-scheme` del SO |

La preferencia se persiste en `localStorage`. Para el Panel Admin (acceso interno), el default es **Sistema**. Para el Portal de Ventas y Marketplace (cara pública), el default es **Claro** — se ofrece toggle en la navbar.

### Diferenciación entre capas (encima de MD3)

Las tres capas comparten el mismo seed y color scheme. La diferenciación se expresa mediante:

| Aspecto | Panel Admin | Portal de Ventas | Marketplace |
|---|---|---|---|
| **Densidad** | Alta (tablas, datos) | Media (landing, pricing) | Media (grid de cards) |
| **Tipografía** | Body Medium 14px base | Title Large/Headline para heroes | Body Medium + price labels |
| **Hero** | Sin hero — directo al dashboard | Hero oscuro (surface inverse) | Header con buscador |
| **Navegación** | Sidebar con Navigation Drawer | Navbar horizontal top | Navbar + panel de filtros lateral |
| **Layout** | Expanded siempre (escritorio) | Responsive: compact/medium/expanded | Responsive: compact/medium/expanded |

### Responsividad

**MD3 Adaptive breakpoints:**

| Breakpoint | Rango | Patrón de navegación |
|---|---|---|
| **Compact** | 0–599dp | Navigation Bar (bottom) para Portal/Marketplace; Panel Admin no soporta compact |
| **Medium** | 600–1239dp | Navigation Rail (lateral) |
| **Expanded** | ≥ 1240dp | Navigation Drawer permanente |

**Panel Admin:** solo Expanded — es herramienta interna de escritorio.
**Portal de Ventas y Marketplace:** responsive completo — los integradores pueden llegar desde móvil.

### Tipografía

Inter como typeface en todos los roles MD3. Compatible con MD3 (override de fuente permitido).

| Rol MD3 | Tamaño | Peso | Uso |
|---|---|---|---|
| Display Large | 57px | 400 | — (no usado en Hira Hub) |
| Headline Large | 32px | 700 | Heroes de Portal y Marketplace |
| Headline Medium | 28px | 600 | Títulos de sección |
| Title Large | 22px | 600 | Encabezados de página, nombres de plantillas |
| Title Medium | 16px | 500 | Headers de tabla, labels de plan |
| Body Large | 16px | 400 | Copy del Portal, descripciones de plantilla |
| Body Medium | 14px | 400 | Contenido del Panel Admin, texto secundario |
| Label Large | 14px | 500 | Botones, CTAs |
| Label Medium | 12px | 500 | Badges, estados de licencia |

---

## Capa 1: Panel Admin (v0.1)

### Propósito y contexto de uso

Herramienta interna de cjhirashi. No tiene que vender ni impresionar — tiene que ser funcional y eficiente. Un solo usuario activo a la vez. Acceso solo desde dispositivos de confianza via JWT.

### Principios de diseño — Panel Admin

| Principio | Descripción |
|---|---|
| **Funcional sobre estético** | Densidad de información alta. No hay marketing, solo datos. |
| **Acciones directas** | Las operaciones más frecuentes (revocar licencia, marcar report como revisado) son accesibles en una sola acción desde la tabla. |
| **Auditabilidad** | Cada acción muestra quién la hizo y cuándo. Timestamps en todas las tablas. |

### Sistema de diseño — Panel Admin

Hereda el **Sistema de Diseño Base MD3** (ver sección al inicio de este documento). Particularidades de esta capa:

- **Densidad:** alta — Body Medium 14px base, tablas compactas
- **Layout:** solo Expanded (≥ 1240dp), herramienta de escritorio exclusivamente
- **Tema default:** Sistema (sigue preferencia del SO de cjhirashi)
- **Roles semánticos adicionales:** `error` → revocar licencia / estado revocada; `tertiary` → crash reports sin revisar; `primary` → acciones principales (emitir licencia, marcar revisado)

### Arquitectura de navegación — Panel Admin

```
Sidebar oscura (izquierda, fija):
  ─────────────────
  Dashboard
  ─────────────────
  Licencias
  Crash Reports    ← badge con no revisados
  Versiones
  ─────────────────
  Configuración
```

### Especificación de vistas — Panel Admin

**Dashboard:**
```
┌────────────────────────────────────────────┐
│  KPI Cards:                                │
│  Licencias activas · Nuevos crash reports  │
│  · Servers en campo · Última versión       │
├────────────────────────────────────────────┤
│  Actividad reciente (últimas 24h):         │
│  Nuevas validaciones, crash reports        │
│  recibidos, licencias emitidas             │
└────────────────────────────────────────────┘
```

**Licencias:**
```
┌──────────────────────────────────────────────────────────────┐
│  Botón: "Emitir nueva licencia"                              │
├──────────┬────────────┬────────────┬──────────┬─────────────┤
│ Prefijo  │ Integrador │ Producto   │ Tier     │ Estado      │
├──────────┼────────────┼────────────┼──────────┼─────────────┤
│ HIRA-A1B2│ email@     │ Server     │ Pro      │ ✅ Activa   │
│ HIRA-C3D4│ otro@      │ Studio     │ —        │ ⚠️ Vence 7d │
│ HIRA-E5F6│ test@      │ Server     │ Starter  │ ❌ Revocada │
├──────────┴────────────┴────────────┴──────────┴─────────────┤
│  Click en fila → drawer: detalle de activaciones por hardware│
│  Acciones: Revocar · Emitir nueva · Ver historial            │
└──────────────────────────────────────────────────────────────┘
```

**Crash Reports:**
```
┌─────────────────────────────────────────────────────┐
│  Filtros: Producto · Versión · Sin revisar          │
├────────┬─────────┬──────────────┬────────┬──────────┤
│ Prod   │ Versión │ Módulo       │ Ocurr. │ Último   │
├────────┼─────────┼──────────────┼────────┼──────────┤
│ Server │ 0.1.2   │ bacnet.adpt  │ 14     │ 14:32    │
│ Studio │ 0.1.0   │ export.hira  │  3     │ 12:10    │
├────────┴─────────┴──────────────┴────────┴──────────┤
│  Click en fila → drawer con stack trace completo    │
│  Acciones: Marcar revisado · Abrir issue GitHub     │
└─────────────────────────────────────────────────────┘
```

---

## Capa 2: Portal de Ventas (v0.2)

### Propósito y contexto de uso

Área pública de hub.hira.cjhirashi.com donde el integrador llega, entiende los planes, compra una licencia con Stripe, y recibe la key por email. Es la cara comercial del ecosistema — tiene que transmitir confianza y claridad.

### Principios de diseño — Portal de Ventas

| Principio | Descripción |
|---|---|
| **Claridad de precio** | El precio de cada plan visible sin hacer scroll. Sin "contactar para precio". |
| **Proceso de compra corto** | Máx 3 pasos: elegir plan → datos + pago → confirmación con key. |
| **Confianza técnica** | El copy habla en lenguaje de integrador de automatización, no de consumidor. |
| **Marca Hira** | Primera impresión del ecosistema para muchos integradores. Debe ser consistente con la marca. |

### Sistema de diseño — Portal de Ventas

Hereda el **Sistema de Diseño Base MD3** (ver sección al inicio de este documento). Particularidades de esta capa:

- **Densidad:** media — Headline Large para hero, Body Large para copy
- **Layout:** responsive completo — compact/medium/expanded
- **Tema default:** Claro — cara pública, contexto de compra
- **Hero:** `inverseSurface` (superficie oscura MD3) para el hero y footer — efecto contraste sin salir del esquema MD3
- **Badge "Más popular":** `primaryContainer` con texto `onPrimaryContainer`
- **Roles semánticos adicionales:** `primary` → todos los CTAs de compra; `outline` → cards de plan no seleccionadas; `primaryContainer` → card de plan seleccionada/recomendada

### Arquitectura de navegación — Portal de Ventas

```
Navbar:
  Logo Hira  |  Precios  |  Marketplace (link a v0.3)  |  [Iniciar sesión Panel Admin]

Páginas:
  /          → Landing con hero, propuesta de valor, resumen de planes
  /precios   → Pricing page con comparativa de plans
  /checkout  → Formulario de compra (Stripe Elements)
  /gracias   → Confirmación post-pago, instrucciones de uso de la key
```

### Especificación de vistas — Portal de Ventas

**Landing (/)**
```
┌─────────────────────────────────────────────────────┐
│  HERO (fondo oscuro):                               │
│  "Tu plataforma SCADA. Tu marca."                   │
│  Subtítulo: ecosistema para integradores            │
│  CTA: [Ver planes]                                  │
├─────────────────────────────────────────────────────┤
│  Propuesta de valor: 3 columnas                     │
│  Sin CAPEX alto · BACnet+Modbus+MQTT · IA incluida  │
├─────────────────────────────────────────────────────┤
│  Resumen de planes (3 cards) → link a /precios      │
├─────────────────────────────────────────────────────┤
│  Cómo funciona: 4 pasos del ecosistema              │
│  Studio → .hira → Server → Hub                      │
└─────────────────────────────────────────────────────┘
```

**Pricing (/precios)**
```
┌──────────────────┬──────────────────┬──────────────────┐
│    Starter       │  Professional    │   Enterprise     │
│    $399          │     $999  ⭐     │    $2,499        │
│    por instalac. │    Más popular   │    por instalac. │
├──────────────────┼──────────────────┼──────────────────┤
│  Puntos: hasta   │  Puntos: hasta   │  Puntos:         │
│  500 tags        │  2,000 tags      │  ilimitados      │
│  BACnet + Modbus │  BACnet + Modbus │  Todos protocolos│
│  MQTT            │  MQTT            │  + soporte prior.│
│  Alarmas         │  Alarmas         │                  │
│  Históricos      │  Históricos      │                  │
│  —               │  Motor de Lógica │  Motor de Lógica │
│  —               │  —               │  IA incluida     │
├──────────────────┼──────────────────┼──────────────────┤
│  [Comprar]       │  [Comprar]       │  [Comprar]       │
└──────────────────┴──────────────────┴──────────────────┘
   + Módulo IA: +$199 por instalación (add-on disponible en Pro/Starter)
```

**Checkout (/checkout)**
```
┌───────────────────────────────────┐
│  Resumen: Plan seleccionado       │
│  Precio total con impuestos       │
├───────────────────────────────────┤
│  Datos del integrador:            │
│  Nombre · Email · Empresa         │
│  (estos datos van en la licencia) │
├───────────────────────────────────┤
│  Stripe Elements (card input)     │
├───────────────────────────────────┤
│  [Confirmar compra — $X]          │
│  Candado SSL · "Key llega al      │
│  email en < 2 minutos"            │
└───────────────────────────────────┘
```

**Confirmación (/gracias)**
```
✅ ¡Compra completada!
Tu license key fue enviada a email@.

Próximos pasos:
1. Descarga Hira Studio en hira.cjhirashi.com/studio
2. Diseña tu proyecto (tutorial en docs)
3. Activa tu licencia en Hira Server desde el panel de Licencia
```

---

## Capa 3: Marketplace (v0.3)

### Propósito y contexto de uso

Catálogo público de pre-ingenierías `.hirat`. El integrador navega, filtra por tipo de equipo o protocolo, compra o descarga plantillas, y las importa en Studio. Es el tercer eje de ingresos del ecosistema y el que genera efectos de red.

### Principios de diseño — Marketplace

| Principio | Descripción |
|---|---|
| **Descubrimiento** | El integrador debe poder encontrar "plantilla de Fan Coil Unit BACnet" en menos de 30 segundos. |
| **Confianza en calidad** | Las plantillas oficiales cjhirashi tienen badge diferenciado. Reviews visibles. |
| **Proceso de descarga/compra claro** | Plantilla gratuita → descarga directa. Pago → Stripe → descarga. |
| **Preview útil** | Cada plantilla muestra qué dispositivos incluye, qué puntos, screenshot del mimic. |

### Sistema de diseño — Marketplace

Hereda el **Sistema de Diseño Base MD3** (ver sección al inicio de este documento). Particularidades de esta capa:

- **Densidad:** media — grid de cards con imagen, nombre, precio, rating
- **Layout:** responsive completo. En compact: filtros colapsables (drawer). En medium/expanded: panel de filtros lateral fijo.
- **Tema default:** Claro (mismo que Portal de Ventas — son parte del mismo sitio)
- **Badges de plantilla** usando roles MD3:

| Badge | Rol MD3 | Uso |
|---|---|---|
| "Oficial cjhirashi" | `primary` bg + `onPrimary` | Plantillas oficiales cjhirashi |
| "Premium" | `secondaryContainer` bg + `onSecondaryContainer` | Plantillas de pago |
| "Gratuito" | `tertiaryContainer` bg + `onTertiaryContainer` | Plantillas gratuitas |
| "Marca oficial" | `primaryContainer` bg + `onPrimaryContainer` | Fabricantes verificados |

### Arquitectura de navegación — Marketplace

```
Navbar (hereda de Portal de Ventas):
  Logo Hira  |  Precios  |  Marketplace  |  [Publicar plantilla]  |  [Mi cuenta]

Páginas:
  /marketplace           → Catálogo con filtros y búsqueda
  /marketplace/[id]      → Detalle de plantilla
  /marketplace/publicar  → Formulario de publicación (integradores)
  /marketplace/cuenta    → Mis compras, mis plantillas publicadas
```

### Especificación de vistas — Marketplace

**Catálogo (/marketplace)**
```
┌────────────────────┬────────────────────────────────┐
│  FILTROS           │  Grid de plantillas (3 cols)   │
│  ─────────         │                                │
│  Tipo de equipo:   │  ┌──────┐ ┌──────┐ ┌──────┐  │
│  □ HVAC            │  │[img] │ │[img] │ │[img] │  │
│  □ Lighting        │  │FCU   │ │Chiller│ │AHU  │  │
│  □ Plumbing        │  │BACnet│ │BACnet │ │Modbus│  │
│  □ IoT/Smart Home  │  │$29   │ │GRATIS │ │$49  │  │
│                    │  │⭐ 4.8 │ │⭐ 4.5 │ │⭐ 4.9│  │
│  Protocolo:        │  └──────┘ └──────┘ └──────┘  │
│  □ BACnet          │                                │
│  □ Modbus          │  ...más plantillas...          │
│  □ MQTT            │                                │
│                    │                                │
│  Precio:           │                                │
│  □ Gratuito        │                                │
│  □ De pago         │                                │
│                    │                                │
│  Autor:            │                                │
│  □ Oficial cjhir.  │                                │
│  □ Comunidad       │                                │
│  □ Marca oficial   │                                │
└────────────────────┴────────────────────────────────┘
```

**Detalle de plantilla (/marketplace/[id])**
```
┌──────────────────────────────────────────────────────┐
│  [Screenshot del mimic]   │  Nombre: FCU BACnet v2   │
│                           │  Autor: cjhirashi ✅      │
│                           │  Protocolo: BACnet        │
│                           │  Tipo: HVAC               │
│                           │  Puntos incluidos: 24     │
│                           │  Precio: $29              │
│                           │  [Comprar / Descargar]    │
├──────────────────────────────────────────────────────┤
│  Descripción: qué incluye la plantilla               │
│  Lista de puntos BACnet que mapea                    │
│  Capturas de: mimic + configurador precargado        │
├──────────────────────────────────────────────────────┤
│  Reviews: ⭐⭐⭐⭐⭐ (12 reviews)                       │
└──────────────────────────────────────────────────────┘
```

---

## Flujos Críticos de Usuario

### Flujo: Compra de licencia (Portal de Ventas)

1. Integrador llega a `/precios`
2. Selecciona plan Professional → click "Comprar"
3. Completa formulario en `/checkout` (datos + Stripe card)
4. Stripe procesa → webhook confirma pago a Hub
5. Hub emite license key + envía email al integrador
6. Integrador llega a `/gracias` con instrucciones
7. Integrador recibe email con key `HIRA-XXXX-XXXX-XXXX-XXXX`

**Tiempo objetivo: < 3 minutos desde selección de plan hasta recibir email.**

### Flujo: Descarga de plantilla gratuita (Marketplace)

1. Integrador filtra por "FCU + BACnet + Gratuito"
2. Click en plantilla → página de detalle
3. Click "Descargar" → se descarga archivo `.hirat`
4. Integrador importa el `.hirat` en Hira Studio

### Flujo: Compra de plantilla premium (Marketplace)

1. Integrador selecciona plantilla premium ($29)
2. Si tiene sesión → directo a Stripe Checkout
3. Si no tiene sesión → crear cuenta o continuar como invitado
4. Pago → archivo `.hirat` descargable inmediatamente y enviado por email

---

## ADRs UI/UX

### ADR-UI-H01 — Material Design 3 unificado con diferenciación por layout y densidad

- **Contexto:** Panel Admin, Portal de Ventas y Marketplace sirven a audiencias y propósitos muy distintos, pero forman parte del mismo ecosistema Hira
- **Decisión:** Sistema de diseño base único: MD3 con seed Cyan, soporte Light/Dark/Sistema, responsive MD3 breakpoints. La diferenciación entre capas se expresa mediante densidad de información, patrones de navegación (Drawer en Admin, Navbar en público) y el uso de `inverseSurface` para heros en Portal/Marketplace — sin paletas separadas por capa.
- **Por qué:** Un seed único en MD3 genera coherencia de color automáticamente en todas las variantes (light, dark, containers, variants). Mantener tres paletas separadas con tokens propios generaba divergencia sin beneficio real. La diferenciación visual que importa (admin vs. público) se consigue con layout y densidad, no con colores distintos.
- **Consecuencias:** Un solo archivo de tokens MD3 (generado por Material Theme Builder). Las tres capas comparten los mismos `--md-sys-color-*`. Los ajustes por capa son en layout y tipografía, no en color.

### ADR-UI-H02 — Portal de Ventas no requiere cuenta para comprar

- **Contexto:** Reducir fricción en el proceso de compra es crítico para conversión
- **Decisión:** El integrador puede comprar una licencia sin crear cuenta — solo email para recibir la key. La cuenta es opcional (sirve para historial de compras y Marketplace)
- **Por qué:** Cada paso adicional de registro reduce la conversión. La key se envía por email de todas formas.
- **Consecuencias:** Hub debe manejar "compras sin cuenta" y asociarlas al email como identificador

### ADR-UI-H03 — Marketplace usa reviews como señal de calidad

- **Contexto:** El integrador no puede probar la plantilla antes de comprar
- **Decisión:** Todas las plantillas tienen reviews con puntuación. Las plantillas nuevas sin reviews muestran "Nueva" en lugar de puntuación vacía.
- **Por qué:** Reviews reducen la incertidumbre de compra; son el principal mecanismo de confianza en un marketplace
- **Consecuencias:** Se necesita un sistema de reviews ligero — puntuación 1-5 + comentario opcional, solo por compradores verificados

---

## Gate de Salida

- [x] Sistema de diseño definido para las tres capas (tokens, tipografía)
- [x] Arquitectura de navegación de las tres capas documentada
- [x] Especificación de vistas del Panel Admin (v0.1) — completa para Sprint H0-H1
- [x] Especificación de Portal de Ventas (v0.2) — completa para cuando inicie Sprint H2
- [x] Especificación de Marketplace (v0.3) — completa para cuando inicie Sprint H3
- [x] Flujos críticos de compra documentados
- [x] ADRs UI/UX registrados
- [ ] Revisado y aprobado por Charlie
