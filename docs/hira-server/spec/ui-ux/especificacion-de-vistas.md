---
origen_vault: "7.1 - Hira Server/7.1.4 - Diseño UI-UX/7.1.4.3 - Especificación de Vistas.md"
título: Especificación de Vistas — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño UI-UX
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, ui, vistas]
---

## 0. Biblioteca de Proyectos

**Propósito:** Selector y gestor de proyectos. Visible solo en instalaciones con licencia de integrador — la única que soporta multi-proyecto (ver SRV-ADR-020). En una instalación comercial (un solo proyecto por servidor), esta vista no existe: el usuario entra directo al Dashboard del único proyecto.

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Biblioteca de Proyectos          [+ Nuevo]  │
├─────────────────────────────────────────────┤
│  ┌───────────┐ ┌───────────┐ ┌───────────┐  │
│  │ Proyecto A│ │ Proyecto B│ │ Plantilla │  │
│  │ ● Activo  │ │ ○ Inactivo│ │  Base HVAC│  │
│  └───────────┘ └───────────┘ └───────────┘  │
├─────────────────────────────────────────────┤
│  Acciones por proyecto: Abrir · Exportar     │
│  .hira · Duplicar como plantilla · Eliminar  │
└─────────────────────────────────────────────┘
```

**Comportamiento:**
- Solo un proyecto puede estar activo (abierto) a la vez; cambiar de proyecto es instantáneo, sin reiniciar la aplicación
- El indicador de puntos en línea (ver SRV-ADR-018) se muestra por proyecto, contra el tope de la licencia de integrador
- "Exportar .hira" empaqueta el proyecto para moverlo a otra instalación (ver SRV-ADR-015) — uso típico: entregarlo a la instalación comercial del cliente
- "Duplicar como plantilla" genera una copia sin datos históricos ni configuración de red específica del cliente

---

## 1. Dashboard

**Propósito:** Vista principal de operación. Estado general del sistema en tiempo real.

**Layout:**
```
┌─────────────────────────────────────────────┐
│  KPI Cards (top): Dispositivos online · Alarmas activas · Puntos monitoreados  │
├─────────────────────────────────────────────┤
│  Widgets configurables por el integrador    │
│  (Grid drag-and-drop en modo configuración) │
│                                             │
│  Puede incluir: valores de puntos,          │
│  mini-gráficas, contadores, estado          │
│  de dispositivos                            │
└─────────────────────────────────────────────┘
```

**Comportamiento:**
- Valores se actualizan en tiempo real vía WebSocket sin reload (ver SRV-ADR-UI-03)
- Alarmas críticas activas muestran banner persistente en top
- En modo Visor: solo lectura, sin acceso a configuración de widgets

---

## 2. Mimics (Gráficos SVG animados)

**Propósito:** Representación gráfica del sistema de automatización con datos en tiempo real.

**Layout:**
```
┌────────────────────────────────────────────────┐
│  Selector de mimic · Modo [Ver | Editar]        │
├────────────────────────────────────────────────┤
│                                                │
│   Canvas React Flow — área de scroll libre     │
│                                                │
│   Componentes SVG:                             │
│   • Equipos animados (bomba, válvula,          │
│     ventilador, chiller…)                      │
│   • Líneas de conexión (tuberías, conductos)   │
│   • Labels de valor enlazados a puntos         │
│   • Indicadores de estado por color            │
│                                                │
├────────────────────────────────────────────────┤
│  Panel derecho (colapsable): lista de puntos   │
│  asociados enlazados en este mimic              │
└────────────────────────────────────────────────┘
```

**Modo Edición** (solo Integrador/Admin):
- Drag-and-drop de componentes SVG desde biblioteca lateral
- Click en componente → panel de enlace a un punto asociado (ver SRV-ADR-019)
- Guardar/descartar cambios

**Animaciones:**
- Bomba: rotor gira si punto `running = true`
- Válvula: abre/cierra según valor de apertura (0-100%)
- Ventilador: aspas giran con velocidad proporcional al setpoint
- Chiller: indicador de modo cooling/heating por color
- Temperatura: color de fondo del label en gradiente frío-caliente

---

## 3. Gestor de Alarmas

**Propósito:** Lista de alarmas activas y reconocimiento.

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Filtros: Severidad · Área · Estado · Rango de fechas  │
├──────┬──────┬──────────┬────────┬───────────┤
│ Sev  │ Área │ Punto    │ Valor  │ Disparada │
├──────┼──────┼──────────┼────────┼───────────┤
│ 🔴 C │ AHU1 │ temp-ret │ 28.5°C │ 14:32:05  │
│ 🟠 H │ CH01 │ pres-sal │ 4.2bar │ 14:18:40  │
│ 🟡 M │ ZONA │ co2-1    │ 1100pp │ 13:45:22  │
├──────┴──────┴──────────┴────────┴───────────┤
│  Botón: Reconocer seleccionadas             │
└─────────────────────────────────────────────┘
```

**Comportamiento:**
- Las alarmas críticas sin reconocer tienen fila con fondo ligeramente pulsante
- Click en fila → drawer lateral con detalle: histórico de la alarma, botón "Reconocer" con campo de nota obligatoria
- Tab "Historial" → alarmas resueltas con timestamps

---

## 4. Históricos

**Propósito:** Visualización de tendencias de puntos en el tiempo.

**Layout:**
```
┌─────────────────────────────────────────────┐
│  Selector de puntos asociados (multi-select) │
│  Rango de tiempo: [1h][8h][24h][7d][custom] │
├─────────────────────────────────────────────┤
│                                             │
│    Gráfica Plotly.js — líneas por punto     │
│    Zoom/pan con mouse · Tooltip al hover    │
│    Eje Y doble si unidades distintas        │
│                                             │
├─────────────────────────────────────────────┤
│  Botones: Exportar CSV · Exportar PNG       │
└─────────────────────────────────────────────┘
```

---

## 5. Motor de Lógica

**Propósito:** Crear y gestionar scripts de lógica continua en Python.

**Layout (split horizontal):**
```
┌──────────────────┬──────────────────────────┐
│  Lista de        │  Monaco Editor Python     │
│  scripts con     │                          │
│  estado:         │  # acceso solo a API     │
│  ■ activo        │  from hira import *      │
│  ◯ pausado       │                          │
│  ✗ error         │                          │
│                  ├──────────────────────────┤
│  Botones:        │  Panel ejecución:        │
│  Nuevo           │  Estado · Último run     │
│  Iniciar/Pausar  │  Log de salida           │
│  Eliminar        │  [Diagrama de flujo AST] │
└──────────────────┴──────────────────────────┘
```

---

## 6. Configurador

**Propósito:** Configurar dispositivos, puntos, mimics, áreas y roles. Solo accesible con permisos write/admin.

**Sub-módulos (tabs):**
- **Dispositivos:** tabla CRUD de dispositivos con columnas protocolo/dirección/estado + botón "Escanear red"
- **Puntos candidatos:** resultado del escaneo, pendientes de asociación (ver SRV-ADR-012, SRV-ADR-019)
- **Puntos asociados:** tabla CRUD de puntos Hira — cada uno con `access_mode` y, si es BACnet, prioridad de escritura; toggle log_enabled por punto
- **Mimics:** lista de mimics con thumbnails; botón "Nuevo" abre canvas de edición
- **Áreas:** gestión de áreas lógicas del proyecto
- **Roles y Permisos:** tabla de roles con permisos por módulo y área — usuarios de operación (por proyecto) y usuarios integrador (globales a la instancia), ver SRV-ADR-020

---

## 7. Agente IA

**Propósito:** Chat con el agente IA — integrador (construcción) o cliente (operación).

**Layout:**
```
┌───────────────────────────────────────────┐
│  Selector: [Agente Integrador] [Agente Cliente]  │
├───────────────────────────────────────────┤
│                                           │
│   Área de mensajes (scroll)               │
│   Burbujas usuario / agente               │
│   El agente puede citar puntos, alarmas   │
│   y datos del proyecto directamente       │
│                                           │
├───────────────────────────────────────────┤
│  [ Escribe tu mensaje...         ] [Enviar]│
│  Indicador: tokens usados / presupuesto   │
└───────────────────────────────────────────┘
```

Si el agente IA no está configurado (sin API key), la pantalla muestra un aviso con link a Configurador → Agente IA.

---

## Gate de Salida

- [x] Especificación de vistas completa, incluyendo Biblioteca de Proyectos (multi-proyecto, SRV-ADR-020)
- [ ] Revisado y aprobado por Charlie
