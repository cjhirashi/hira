---
título: Arquitectura del ecosistema (C4 nivel 1) — Hira
componente: ecosystem
tipo: Especificación
status: activo
última_actualización: 2026-09-02
deriva_de: ["spec/hira-server/architecture/general.md", "spec/hira-hub/conceptual-design.md", "E-ADR-001"]
---

## Diagrama de contexto — post `E-ADR-001`

```mermaid
flowchart TB
    subgraph DEV["cjhirashi — Desarrollo"]
        A0[Desarrollador]
    end
    subgraph INT["Integrador"]
        A1[Integrador / Admin]
    end
    subgraph CLI["Cliente Final"]
        A2[Operador]
        A3[Técnico / Supervisor]
    end

    subgraph CLOUD["NUBE"]
        subgraph HUB["Hira Hub — VPS (hub.hira.cjhirashi.com)"]
            HB[Licencias · Crash Reports · Versiones\nVentas v0.2 · Marketplace v0.3]
        end
        subgraph STU["Hira Studio — cloud"]
            ST[Configurador · Motor de Lógica/Pruebas (edición)\nMimics · Agente del Integrador · Biblioteca de proyectos]
        end
    end

    subgraph LOCAL["LOCAL / ON-PREMISE"]
        subgraph SRV_INT["Hira Server — banco de pruebas del integrador (opcional)"]
            SV0[Simuladores · diseño/demo]
        end
        subgraph SRV["Hira Server — producción, sitio del cliente"]
            SV[SCADA: Protocolos · Alarmas · Históricos\nLógica/Pruebas (runtime) · Tiempo real · Agente del Cliente]
        end
        subgraph RED["Red local del cliente"]
            D1[BACnet — HVAC]
            D2[Modbus — variadores/medidores]
            D3[MQTT — IoT]
        end
    end

    subgraph EXT["Internet (opcional)"]
        I1[Claude API / OpenAI]
    end

    A0 -->|administra| HB
    A1 -->|diseña e ingeniería| ST
    A2 & A3 -->|operan SCADA| SV

    ST -->|"sesión de ingeniería  [CT-engineering-session]"| SV
    ST -->|"sesión de ingeniería"| SV0
    ST -->|"valida licencia  [CT-license]  (product: studio)"| HB
    ST -->|"crash reports  [CT-crash-report]"| HB
    ST -.->|"catálogo bloques / plantillas .hirat  [CT-marketplace] (v0.3)"| HB

    SV -->|"valida licencia  [CT-license]  (product: server)"| HB
    SV -->|"crash reports  [CT-crash-report]"| HB
    SV -->|"consulta versión  [CT-updates]"| HB

    SV <-->|BACnet / Modbus / MQTT| D1 & D2 & D3
    SV <-->|IA externa, opcional| I1
    ST <-->|Agente del Integrador, opcional| I1

    note["Server y Studio incluyen su propio modelo IA interno\n(Ollama embebido, SRV-ADR-021) como fallback"]
```

**Diagrama interactivo de conectividad** (post `STU-ADR-006`/`HUB-ADR-06`):
[`diagrams/arquitectura-conectividad-server-hub-studio.html`](../diagrams/arquitectura-conectividad-server-hub-studio.html)
— túnel inverso self-hosted, licenciamiento y gate de propiedad de proyecto.

## Fronteras

| Frontera | Regla |
|---|---|
| Nube vs local | Hub y Studio en la nube; Server on-premise, con instalador (`E-ADR-001`). |
| Dónde viven los proyectos | Siempre en un Hira Server. Studio los edita vía sesión de ingeniería; nunca los aloja (`SRV-ADR-015` en su parte vigente). |
| Runtime SCADA | Solo Server: polling, alarmas, históricos, ejecución de lógica/pruebas, tiempo real, Agente del Cliente. |
| Herramientas de ingeniería | Solo Studio: configurador, edición de lógica/pruebas, mimics, Agente del Integrador. |
| Núcleo sin internet | El SCADA de Server opera 100% local (`SRV-ADR-001`); la capa de servicios (licencia, updates, crash, IA externa, notificaciones) requiere conectividad, con grace period de 72h para licencia (`HUB-ADR-03`). |

## Contratos entre componentes

| Contrato | Entre | Origen |
|---|---|---|
| `CT-license` | Server → Hub · Studio → Hub | `HUB-ADR-02`, `spec/hira-hub/detailed-design.md` |
| `CT-crash-report` | Server → Hub · Studio → Hub | `HUB-ADR-04`, `VUL-SRV-012` |
| `CT-updates` | Server → Hub · Studio → Hub | `spec/hira-hub/conceptual-design.md` |
| `CT-engineering-session` | Studio ↔ Server | `SRV-ADR-016` (promovido por `E-ADR-001`) |
| `CT-marketplace` | Studio ↔ Hub · Server ← Hub | Hub v0.3 (`VUL-SRV-015`) — placeholder |

Detalle en `.harness/contracts/`.

## Arquitectura interna por componente

- **Hira Server** — Hexagonal (`SRV-ADR-017`), un solo perfil de despliegue tras
  `E-ADR-001`. Ver `spec/hira-server/architecture/general.md`.
- **Hira Hub** — directa, sin puertos/adaptadores (`HUB-ADR-05`). Ver
  `spec/hira-hub/conceptual-design.md`.
- **Hira Studio** — por definir (ver `spec/hira-studio/OPEN-QUESTIONS.md` SQ-4).
