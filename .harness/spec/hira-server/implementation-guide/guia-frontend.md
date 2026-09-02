---
origen_vault: "7.1 - Hira Server/7.1.6 - Guías de Implementación/7.1.6.3 - Guía Frontend.md"
título: Guía Frontend — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Guías de Implementación
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, frontend, mimics]
---

## Estructura del Frontend

```
frontend/
├── Dockerfile
├── package.json
├── vite.config.ts
├── tsconfig.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── layout/          # Shell, sidebar, topbar — ver .harness/spec/hira-server/ui-ux/navegacion-y-responsividad.md
    │   ├── dashboard/        # Canvas mimics, paneles de control
    │   ├── alarms/           # Lista, reconocimiento, historial
    │   ├── historicals/      # Plotly charts, selector de rango
    │   ├── logic/            # Monaco Editor, lista de scripts
    │   ├── configurator/     # Forms: dispositivos, puntos candidatos, puntos asociados, áreas
    │   ├── projects/         # Biblioteca de proyectos — solo instancia multi-proyecto (SRV-ADR-020)
    │   ├── ai/                # Chat de los agentes Integrador y Cliente
    │   └── common/            # Botones, modales, tablas reutilizables
    ├── hooks/
    │   ├── useWebSocket.ts    # Conexión Socket.io
    │   ├── usePoints.ts       # Lectura de puntos asociados en tiempo real
    │   └── useAlarms.ts
    ├── services/
    │   └── api.ts             # Cliente HTTP hacia FastAPI
    ├── store/                 # Estado global (Zustand)
    └── svg/
        └── hvac/               # Componentes SVG animados HVAC
            ├── Fan.tsx
            ├── Damper.tsx
            ├── Valve.tsx
            ├── Chiller.tsx
            ├── AHU.tsx         # Air Handling Unit
            └── Sensor.tsx       # Temperatura, humedad, CO2, presión
```

El sistema de diseño (tokens, tipografía, componentes base) y la especificación de cada vista están en `.harness/spec/hira-server/ui-ux/` — esta guía cubre solo la organización del código, no el diseño visual.

## Decisiones de Implementación

### Zustand para estado global

Opción ligera y directa para React, sin la verbosidad de Redux. El estado de Hira es relativamente simple: puntos en tiempo real (manejado por el hook de WebSocket) + estado de UI. Zustand cubre el estado de UI sin sobre-diseñar.

## Esquema JSON de Mimics

Contrato entre los datos de un mimic y los componentes SVG que lo renderizan (`src/svg/hvac/`). Los componentes deben leer este formato — es el mismo esquema que consume tanto la edición asistida por formulario como el editor visual drag-and-drop (ver `.harness/spec/hira-server/ui-ux/especificacion-de-vistas.md`, vista Mimics).

```json
{
  "schema_version": "1.0",
  "id": "mimic-uuid",
  "name": "Sala de Máquinas Piso 3",
  "canvas": {
    "width": 1200,
    "height": 800,
    "background": "#1a1a2e"
  },
  "elements": [
    {
      "id": "el-uuid",
      "type": "Fan",
      "position": { "x": 200, "y": 150 },
      "size": { "width": 80, "height": 80 },
      "label": "Ventilador AHU-01",
      "bindings": {
        "running":  { "point_id": 42, "true_when": "value == 1" },
        "speed_pct": { "point_id": 43 },
        "fault":    { "point_id": 44, "true_when": "value == 1" }
      },
      "style": {
        "color_normal": "#00ff88",
        "color_fault":  "#ff4444",
        "color_off":    "#888888"
      }
    },
    {
      "id": "el-uuid-2",
      "type": "Sensor",
      "sensor_type": "temperature",
      "position": { "x": 400, "y": 200 },
      "label": "Temperatura Retorno",
      "bindings": { "value": { "point_id": 51 } },
      "display": { "unit": "°C", "decimals": 1, "min": 10, "max": 40 }
    },
    {
      "id": "el-uuid-3",
      "type": "Setpoint",
      "position": { "x": 500, "y": 300 },
      "label": "SP Temperatura",
      "bindings": { "value": { "point_id": 55 }, "writable": true },
      "display": { "unit": "°C", "decimals": 1, "min": 16, "max": 28 }
    }
  ],
  "connections": [
    { "id": "conn-uuid", "from": "el-uuid", "to": "el-uuid-2", "style": "pipe" }
  ]
}
```

**Tipos de elementos:** `Fan`, `Damper`, `Valve`, `Chiller`, `AHU`, `Sensor`, `Setpoint`, `Label`, `StatusIndicator`

**Bindings:** cada propiedad visual puede vincularse a un `point_id` — siempre un punto **asociado** (ver SRV-ADR-019), nunca un candidato crudo. El frontend resuelve el valor actual desde el estado en tiempo real (WebSocket). `true_when` es una expresión simple evaluada en el cliente.

---

## Gate de Salida

- [x] Estructura de frontend detallada
- [x] Esquema JSON de mimics documentado como contrato estable
- [ ] Revisado y aprobado por Charlie
