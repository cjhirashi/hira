---
tipo: memoria
subtipo: state
actualizado: 2026-09-14
---

# Estado del arnés — ecosistema Hira

## ⚠️ Correcciones del usuario (leer SIEMPRE — no borrar)

### [2026-09-10] Toda feature de frontend pasa por el especialista `experto-ux-ui`
- **Qué pasó:** el usuario quiere que las interfaces de los 3 productos estén siempre
  bien diseñadas, profesionales y con excelente UX.
- **Corrección:** especialista `experto-ux-ui` añadido (`ADR-003`). Complementa a
  `hira-frontend` (que implementa): `experto-ux-ui` diseña y **revisa** la UX/UI.
  Interviene en Fase 1/2 (flujos, estados, `RF-` de UX contra el sistema de diseño
  `docs/hira-server/spec/ui-ux/`) y en Fase 4 (revisión contra estándar: WCAG AA,
  consistencia MD3+Cyan, accesibilidad, responsive, microcopy). Constitución Art. 8.
- **Cómo aplicar:** feature que toque interfaz → delega en `experto-ux-ui`; sin su
  sección de UX la spec no pasa el Gate 1. No escribe código de producción.

### [2026-09-04] Los 3 productos son Hexagonal, no solo hira-server
- **Qué pasó:** al confirmar la restructuración del arnés, el usuario aclaró que
  quiere Hexagonal en **los 3 productos**, no solo en `hira-server` (que ya lo era
  por `SRV-ADR-017`). `hira-studio` y `hira-hub` tenían "directa" por sus propios ADR
  (`STU-ADR-001`, `HUB-ADR-05`), con un argumento válido bajo ese criterio.
- **Corrección:** `E-ADR-002` homogeneiza a Hexagonal los 3 productos; supersede
  `HUB-ADR-05` (completo) y la sección de arquitectura de `STU-ADR-001` (el hosting/
  stack de esa decisión se mantiene). `constitution.md` Art. 1–2 actualizado con
  puertos/adaptadores para Studio y Hub.
- **Cómo aplicar:** cualquier `plan.md` de Studio o Hub debe diseñar por puertos
  (`core/ports/`), igual que Server — no "directa".

### [2026-09-04] Forzar la Fase 1 (corrección propagada desde cjhirashi-career)
- **Qué pasó:** en `cjhirashi-career` el arnés no forzaba Fase 1 ante "corrige esta
  falla" — faltaba el hook `Stop`, `CLAUDE.md` sin reglas duras, rúbrica sin rama para
  "esto es un rediseño". Ver `ADR-002`.
- **Cómo aplicar aquí:** añadido `.claude/settings.json` (hook Stop → gate), reglas
  duras en `CLAUDE.md`, y las dos ramas nuevas en `method.md §2`. Relevante en `hira`
  porque casi todo está "sin ancla" (fase de diseño) — eso no es luz verde.

### [2026-09-02] Studio es un producto cloud independiente, no un perfil de Server
- **Qué pasó:** el diseño previo (`SRV-ADR-015/016/017`) definía Server y Studio como un
  solo producto/instalador con `HIRA_DEPLOY_MODE=server|studio`.
- **Corrección del usuario:** Studio se reorganiza en 3 vertientes con frontera nube/local
  clara — Hub (nube), Studio (nube), Server (on-premise, con instalador).
- **Cómo aplicar:** `E-ADR-001` es la fuente de verdad; los 3 ADRs quedan con banner de
  supersesión parcial. `HIRA_DEPLOY_MODE` se retira de Server (un solo perfil de producción).

### [2026-09-04] El patrón de arquitectura no es uniforme entre productos
- **Qué pasó:** al reestructurar el arnés se confirmó con el usuario que **sí habrá
  arquitectura hexagonal** en este repo.
- **Corrección / matiz:** es **`hira-server`** el que es hexagonal (`SRV-ADR-017`, ya
  decidido desde julio). `hira-studio` y `hira-hub` usan arquitectura **directa**, por
  decisión propia y justificada (`STU-ADR-001`, `HUB-ADR-05`): un solo deployment target
  no justifica puertos/adaptadores.
- **Cómo aplicar:** no uniformar el patrón entre productos. El perfil de arquitectura de
  cada uno vive por separado en `constitution.md` Art. 2.

## Estado del backlog

- **Reestructuración del arnés al esquema simplificado** (2026-09-04, `ADR-001`) y
  refresco de rutas (2026-09-13, `ADR-004`) — completos. Convención de commits:
  Conventional Commits + `(RF-NNN)` (corregido un overlay que aún decía el formato
  histórico con corchetes).
- **`SRV-001-walking-skeleton` — `estado: implemented`.** Primera feature real del
  ecosistema, ciclo completo Fase 1→4 (30/30 tareas, `T-001..T-030`), verificada por
  el `revisor` en cada batch, ancla movida a `b4248e749d6a9eceaa68b9f117b79116222c1eb9`.
  Incluyó 2 Directivas de Pausa (secuenciación de `adapters/factory.py`; wiring de
  `MosquittoAdapter.connect()` en el `lifespan`) y un fix genérico al arnés
  (`.harness/gate/check.sh` excluye `-m integration` del bloque 5 por defecto).
  Detalle completo: entrada Session-End `[2026-09-13]` en `memory/history.md` y
  tabla de Cobertura de `tasks.md` — no se repite aquí (`method.md §10`).
- `docs/planning/SPRINT.md` (el sprint pre-reestructuración) lleva banner de
  superseded — ya no es fuente viva, la reemplazó `SRV-001-walking-skeleton`.
- **Bitácoras previas** (pre-reestructuración): `docs/planning/sprint-history.md`,
  `docs/planning/hira-{server,hub}-bitacora.md`, `docs/planning/hira-hub-sprint-plan.md`.

## Obstáculos y desviaciones abiertas

- **Fuera de alcance de `ADR-004`:** el corpus de `docs/<producto>/spec/` (~40 archivos)
  tiene enlaces internos cruzados que siguen citando rutas pre-`ADR-001`. `ADR-001` ya
  decidió no reescribir ese corpus — es documentación de producto cerrada, no
  maquinaria del arnés. 404 en uno de esos enlaces = doc de producto desactualizada,
  no un problema del arnés; backlog de higiene separado, no se parchea el arnés.
- Ninguno abierto — `SRV-001-walking-skeleton` y `SRV-002-auth-rbac` `verified`;
  `HUB-001-walking-skeleton` `implemented` (pendiente confirmación `verified`).

## Próximo paso concreto

- Antes de tocar nada: `bash .harness/gate/check.sh`.
- **`SRV-001-walking-skeleton`** y **`SRV-002-auth-rbac`**: `estado: verified`
  (Carlos, Gate 4). Detalle en sus entradas Session-End de `memory/history.md`.
- **`HUB-001-walking-skeleton`**: `estado: verified` (Carlos, Gate 4). 25/25
  tareas, ancla en `4d180449ae41c30e402bf88eb7c36cded5592eea`. 1 rebote real
  del revisor (credenciales de Redis no usadas, corregido de raíz). Ambos
  servicios (`hira-server`, `hira-hub`) corren ya su suite real en el mismo
  `gate/check.sh`. Detalle en su entrada Session-End de `memory/history.md`.
- **`SRV-Sprint-3` (ROADMAP) partido en 4 features del arnés** (decisión
  2026-09-14): BACnet, Modbus, MQTT-scanning, Simuladores — dominio demasiado
  heterogéneo para un solo ciclo. Asociación explícita de puntos (`points`,
  `access_mode`, prioridad, polling, `asyncio.Lock` de `VUL-SRV-005`) diferida
  a una feature aparte, posterior a las 4 (coherente con la propia separación
  Sprint 3/4 de `ROADMAP.md` — ver detalle en `SRV-003-bacnet-adapter/spec.md
  §6`). `ROADMAP.md` cita `VUL-SRV-001` como ancla de este sprint — ya
  resuelto en `SRV-001`, referencia obsoleta, no bloquea.
- **`SRV-003-bacnet-adapter`** (BACnet) y **`SRV-004-modbus-adapter`** (Modbus)
  — ambas `estado: verified` (Carlos, Gate 4), sobre el mismo modelo `devices`/
  `device_points_candidates` (`SRV-003` lo creó, `SRV-004` lo reutiliza sin
  migración nueva). Detalle en sus entradas Session-End de `memory/history.md`.
- **`SRV-005-mqtt-scanning`** (MQTT, tercera del grupo de protocolos) —
  `estado: implemented`, ancla en `d93243a`. 13/13 tareas, ciclo completo
  Fase 1→4, 1 rebote real del revisor (tabla de Cobertura con fila RF-005
  `Pendiente` pese a verificable — mismo bug recurrente de `SRV-001/003/004`,
  corregido). Sin Directiva de Pausa formal, pero sí un hallazgo real
  documentado de raíz (orden `disconnect()`/`loop_stop()` en
  `MqttScanAdapter` — bloqueo de hasta ~1s en el hilo de red de paho-mqtt,
  sin violar ningún RF-/RNF-). Decisión de dominio: sin identidad fija de
  "dispositivo" — un `device` MQTT = el patrón de suscripción completo;
  `crc32` del topic real en `object_instance`, topic completo en
  `object_name`. Verificado contra el Mosquitto real ya autenticado de
  `SRV-001` (sin broker de prueba aparte). 234/234 tests, gate verde.
  Pendiente confirmación humana de Gate 4 (`verified`). Detalle completo:
  entrada Session-End `[2026-09-14]` en `memory/history.md`.
- **Próximo paso:** confirmar `verified` de `SRV-005-mqtt-scanning` (Gate 4,
  pendiente de respuesta del usuario). Después, decidir entre: (a)
  `Simuladores` — 4ª y última feature del grupo de protocolos, permitiría
  probar BACnet/Modbus/MQTT sin hardware (aunque las 3 ya se verificaron sin
  él, con infraestructura de prueba ad-hoc); (b) cambiar de frente a
  `HUB-H1` (gestión de licencias); (c) la feature de "asociación explícita
  de puntos" — diferida explícitamente por las 3 features de protocolos, ver
  `SRV-003-bacnet-adapter/spec.md §6`.
