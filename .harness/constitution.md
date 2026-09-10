---
titulo: Constitución del arnés — ecosistema Hira
tipo: constitution
estado: approved
fecha: 2026-09-04
metodo: SDD Anchored (versión simplificada)
---

# Constitución — ecosistema Hira

Principios innegociables que toda `spec.md` y todo `plan.md` heredan y respetan. Se
valida **antes** de redactar cada spec. Cambiar un artículo exige un `ADR-`.

Separación estricta: `.harness/` = **cómo trabajamos** · `docs/` = **el producto**
(especificación, ADRs de producto, contratos, roadmap — ver Art. 11).

Monorepo de **3 productos** con un solo `.harness/` para todo el ecosistema:
`hira-server/`, `hira-studio/`, `hira-hub/` (aún sin código — fase de diseño).

---

## Artículo 1 · Arquitectura

**Los 3 productos son Hexagonal** — decisión del propietario del ecosistema
(`docs/decisions/ecosystem/E-ADR-002`), que prioriza consistencia y optionality entre
los 3 codebases sobre la simplicidad de un solo deployment target. Regla de oro
idéntica en los tres: `services/` **solo** importa de `core/ports/`, nunca de
`adapters/` directamente; `adapters/factory.py` selecciona la implementación concreta.
Cambiar el patrón de un producto exige un `ADR-` nuevo que supere al vigente.

- **`hira-server`** — Hexagonal desde origen (`docs/hira-server/decisions/SRV-ADR-017`).
  Múltiples adaptadores de protocolo (BACnet, Modbus, MQTT) y de storage
  (PostgreSQL+TimescaleDB en producción, SQLite en banco de pruebas del integrador).
- **`hira-studio`** — Hexagonal desde `E-ADR-002` (antes "directa",
  `docs/hira-studio/decisions/STU-ADR-001`, sección de arquitectura superseded).
- **`hira-hub`** — Hexagonal desde `E-ADR-002` (antes "directa",
  `docs/hira-hub/decisions/HUB-ADR-05`, superseded en su totalidad).

> Nota histórica: hasta el 2026-09-04 Studio y Hub eran "directa" por decisión propia,
> con un argumento igualmente válido bajo ese criterio (un solo deployment target no
> justifica puertos/adaptadores). `E-ADR-002` documenta el cambio de criterio.

## Artículo 2 · Perfil de arquitectura  *(registrado en la Génesis — decisiones ya tomadas por ADR)*

```yaml
estilo_aplicacion: monorepo-multiproducto      # 3 productos, ciclos de release independientes
productos:
  hira-server:
    estilo_despliegue: on-premise (instalador, un solo perfil de producción)
    patron_interno: hexagonal
    patron_interno_adr: docs/hira-server/decisions/SRV-ADR-017-arquitectura-hexagonal.md
    puertos: [ProtocolPort, StoragePort, NotificationPort]
    adaptadores_entrada: [FastAPI REST + WebSocket, CLI de administración]
    adaptadores_salida: [BACnet (BAC0), Modbus (pymodbus), MQTT (paho-mqtt),
                          PostgreSQL+TimescaleDB, SQLite (banco de pruebas), Redis Pub/Sub]
    topologia_agentes: dos-agentes-por-stakeholder   # Agente del Cliente / Agente del Integrador
    sustratos_integracion: [rest-http, websocket, ct-license, ct-crash-report, ct-engineering-session]
  hira-studio:
    estilo_despliegue: cloud multi-tenant (aislamiento lógico por integrator_id)
    patron_interno: hexagonal
    patron_interno_adr: docs/decisions/ecosystem/E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md
    componentes: [SPA (React+TS, MD3+Cyan), BFF (FastAPI + PostgreSQL propia + Redis)]
    puertos: [ProjectStoragePort, PairingPort, EngineeringSessionPort, LicensePort, SimulationPort]
    adaptadores_entrada: [BFF REST/WebSocket consumido por la SPA]
    adaptadores_salida: [PostgreSQL propia, Redis, cliente HTTP a Hub, cliente HTTP/WS a Server,
                          motor de simulación (sandbox RestrictedPython)]
    topologia_agentes: agente-integrador
    sustratos_integracion: [rest-http, ct-engineering-session (cliente), ct-license, ct-crash-report]
  hira-hub:
    estilo_despliegue: cloud single-tenant (VPS de cjhirashi)
    patron_interno: hexagonal
    patron_interno_adr: docs/decisions/ecosystem/E-ADR-002-arquitectura-hexagonal-para-los-3-productos.md
    stack: FastAPI + PostgreSQL + Redis   # mismo que Server (HUB-ADR-01)
    puertos: [LicenseStoragePort, CrashReportPort, UpdateDistributionPort, NotificationPort, PaymentPort (reservado)]
    adaptadores_entrada: [FastAPI REST — CT-license, CT-crash-report, CT-updates, CT-marketplace]
    adaptadores_salida: [PostgreSQL, Redis, SMTP/webhook, GHCR/S3, pasarela de pago (futuro)]
    sustratos_integracion: [ct-license, ct-crash-report, ct-updates, ct-marketplace]
capas_transversales: [observabilidad, auth]
sustratos_ecosistema:
  - contratos-compartidos   # docs/contracts/*.openapi.yaml — CT-license, CT-crash-report, CT-updates, CT-marketplace, CT-engineering-session
rutas:
  arnes: .harness/
  specs: .harness/specs/
  decisiones: .harness/decisions/     # decisiones DEL ARNÉS; las de producto van en docs/<producto>/decisions/
```

## Artículo 3 · Testing

- **TDD en la Fase 4** (test antes que código) — aplica igual en los 3 productos.
- Cobertura mínima **80 %** por módulo tocado; objetivo **90 %** para código nuevo.
- Pruebas **por zona del patrón hexagonal** en los 3 productos: núcleo/dominio (unit
  puro, sin mocks) · aplicación/casos de uso (unit + dobles de puertos) · adaptadores
  (integración contra la tecnología real) · sistema (e2e por un adaptador de entrada real).
- **Verificación real:** el servicio arranca, el endpoint responde. Evidencia = salida
  de terminal **pegada**, nunca "esperada". Aplica también a simuladores de `hira-server`
  (`docs/hira-server/decisions/SRV-ADR-014`): son adaptadores de primera clase, no un caso especial.

## Artículo 4 · Persistencia

- `hira-server`: PostgreSQL + TimescaleDB (series de tiempo, `SRV-ADR-004`) en
  producción; SQLite en banco de pruebas del integrador. Un `StoragePort` por backend.
- `hira-hub` y `hira-studio`: PostgreSQL propia + Redis cada uno (bases separadas, sin
  compartir esquema entre productos).

## Artículo 5 · Seguridad

- Secretos fuera del repo. RBAC dinámico en `hira-server` (`SRV-ADR-005`). Licenciamiento
  por puntos en línea (`SRV-ADR-018`) fija el límite de negocio para Server **y** Studio.
- Credenciales de emparejamiento Studio↔Server cifradas (`STU-ADR-003`).
- Crash reports opt-in y sanitizados antes de salir del producto (`HUB-ADR-04`).

## Artículo 6 · Contratos y errores

- Contratos **compartidos entre productos** en `docs/contracts/*.openapi.yaml`:
  `CT-license`, `CT-crash-report`, `CT-updates`, `CT-marketplace`, `CT-engineering-session`.
  Cambiarlos exige acuerdo entre los productos que los consumen (ADR de ecosistema si el
  cambio es incompatible).
- `CT-engineering-session` (Studio↔Server): lock exclusivo por proyecto, espejo en Redis
  con TTL, heartbeat, `409` si ya hay sesión activa (`SRV-ADR-016`, formalizado en `E-ADR-001`).
- Errores de API con formato **Problem Details (RFC 9457)**.

## Artículo 7 · Observabilidad

- Crash reports vía `CT-crash-report` hacia Hub, con `product: server|studio`.

## Artículo 8 · Gates y aprobaciones

- **Value Captain / Tech Lead:** el operador del ecosistema (cjhirashi). La IA **no
  autoaprueba**.
- 2 puntos de aprobación humana: tras **Specify** y tras **Plan**, por feature.
- **Toda feature que toque interfaz** de cualquiera de los 3 productos pasa por una
  **revisión de UX/UI** antes de `verified` — delegable al especialista `experto-ux-ui`
  (`ADR-003`), contra el sistema de diseño de `docs/hira-server/spec/ui-ux/`. La spec
  de una feature de frontend incluye su sección de UX o no está lista para el Gate 1.

## Artículo 9 · Convenciones

- IDs `RF-`/`RNF-`/`T-` por feature, `ADR-` para decisiones **del arnés**. Las decisiones
  **de producto** siguen su prefijo histórico y viven en `docs/`: `E-ADR-###` (ecosistema),
  `SRV-ADR-###` (server), `STU-ADR-###` (studio), `HUB-ADR-##` (hub) — **no se renumeran**.
- Carpetas de feature: `NNN-slug` kebab-case, prefijadas por producto cuando aplique
  (`SRV-003-alarmas-multicanal`, `STU-002-...`, `HUB-001-...`) para que convivan en un
  solo `specs/`.
- Commits: **Conventional Commits** + sufijo `(RF-NNN)`.

## Artículo 10 · Regla de raíz (prohibido el parche)

- Toda corrección ataca la **causa raíz**. Sin *workarounds*, sin `TODO`/`FIXME` sin
  ticket. Diferir es válido solo como `RF-`/`RNF-`/`ADR-` explícito.
- En `hira-server`: si una asunción de puertos/adaptadores resulta inviable, la
  corrección va al **puerto** (contrato), no a un parche en un adaptador concreto.

## Artículo 11 · Mapa de documentación del proyecto

| Documento | Ruta | Se actualiza cuando cambia… |
|---|---|---|
| Glosario del ecosistema | `docs/GLOSSARY.md` | términos de negocio nuevos |
| Visión, modelo de negocio, stakeholders, arquitectura C4 | `docs/ecosystem/spec/` | decisiones de ecosistema |
| ADRs de ecosistema | `docs/decisions/ecosystem/` (`E-ADR-`) | decisión que gobierna ≥2 productos |
| Spec de cada producto (arquitectura, módulos, UI/UX, operación, validación) | `docs/hira-server/spec/`, `docs/hira-studio/spec/`, `docs/hira-hub/spec/` | diseño del producto |
| ADRs de producto | `docs/<producto>/decisions/` (`SRV-`/`STU-`/`HUB-ADR-`) | decisión de arquitectura de ese producto |
| Contratos compartidos | `docs/contracts/*.openapi.yaml` + README | forma de un contrato entre productos |
| Roadmap y planificación | `docs/planning/` (ROADMAP, SPRINT, bitácoras) | prioridades, sprint activo |
| Histórico pre-simplificación | `docs/legacy/` (sistema de anclas, scripts de CI, plantillas, PROCESS/README viejos) | referencia; no se mantiene activamente |

> Las decisiones **del arnés** (cómo trabajamos) van en `.harness/decisions/`, nunca
> mezcladas con las de producto.

## Artículo 12 · Anti-hipersistema

1. **3 archivos por feature** (`spec.md`, `plan.md`, `tasks.md`) + `contracts/` si
   aplica. El método vive en `method.md` (1 archivo).
2. **Se retira el sistema de anclas paralelo** (`anchors/registry.yaml` + checksums +
   `check_traceability.py`): quedaba redundante con el anclaje simplificado (`covers` +
   `anchor_commit` en el front-matter de cada `spec.md`). Conservado en
   `docs/legacy/anchors-system/` por si hace falta consultar el histórico.
3. **Se retiran los gates de CI standalone** (`contract_gate.py`, `openapi_lint.py`,
   `traceability_gate.py`): se reintroducen como bloques de `gate/project.sh` **cuando
   haya contratos y código reales que validar** — no antes, para no fingir un gate verde
   sin nada que verificar. Conservados en `docs/legacy/ci-scripts/`.
4. **Se conserva `.harness/claude/`** (genera `AGENTS.md`/`CLAUDE.md` por producto vía
   `build_claude.py`) — es maquinaria del arnés, no documentación de producto. Pendiente:
   actualizar sus fuentes para que apunten a los `docs/` nuevos antes de regenerar.
5. **Un canon por hecho.** Cero duplicación entre `AGENTS.md`, esta Constitución y `docs/`.
6. **Rúbrica primero.** Lo trivial no toca el arnés.

---

## Historial de enmiendas

| Fecha | Artículo | Cambio | ADR |
|---|---|---|---|
| 2026-09-04 | — | Constitución inicial: reestructuración del arnés SDD-Anchored (sembrado 2026-09-02) al esquema simplificado. Perfiles de arquitectura de los 3 productos registrados tal como ya estaban decididos por sus ADRs. | ADR-001 (arnés) |
| 2026-09-04 | Art. 1, 2, 3 | **Homogeneizar a Hexagonal los 3 productos** (antes: Server hexagonal, Studio/Hub directa). Decisión del propietario del ecosistema: consistencia entre codebases sobre simplicidad de un solo deployment target. | `E-ADR-002` (producto) |
| 2026-09-10 | Art. 8 | Especialista `experto-ux-ui`: revisión de UX/UI obligatoria en features de frontend antes de `verified` | ADR-003 (arnés) |
