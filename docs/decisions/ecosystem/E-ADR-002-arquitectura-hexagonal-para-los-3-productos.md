---
título: "E-ADR-002 — Arquitectura Hexagonal para los 3 productos del ecosistema"
componente: ecosystem
tipo: ADR
status: accepted
fecha_creación: 2026-09-04
supersede_parcialmente: [STU-ADR-001]
supersede: [HUB-ADR-05]
tags: [adr, ecosystem, arquitectura, hexagonal]
---

> **Decisión del propietario del ecosistema.** Homogeniza el patrón interno de los 3
> productos a Hexagonal. Cambia el criterio de decisión frente a `HUB-ADR-05` y la
> sección de arquitectura de `STU-ADR-001`: **consistencia y optionality del
> ecosistema priman sobre la simplicidad de un solo deployment target.**

## Contexto

`SRV-ADR-017` adoptó Hexagonal para `hira-server` por su variabilidad real de
adaptadores (protocolos de campo, storage por perfil). `HUB-ADR-05` y `STU-ADR-001`
adoptaron arquitectura **directa** para `hira-hub` y `hira-studio` con un argumento
igualmente válido bajo su criterio original: *un solo deployment target no justifica
la capa de puertos/adaptadores* — es superficie de mantenimiento sin beneficio
inmediato para un operador único.

El propietario del ecosistema decide **no mantener esa asimetría**: quiere Hexagonal
en los 3 productos.

## Decisión

**`hira-hub` y `hira-studio` adoptan Arquitectura Hexagonal**, con el mismo criterio
que `hira-server` (`services/` solo importa de `core/ports/`, nunca de `adapters/`
directamente; `adapters/factory.py` selecciona la implementación concreta).

### `hira-hub` — núcleo y adaptadores

- **Núcleo:** licenciamiento (activación, validación, grace period — `HUB-ADR-03`),
  crash reports (recepción y saneamiento — `HUB-ADR-04`), catálogo de versiones/updates,
  y el futuro marketplace/ventas (v0.2/v0.3).
- **Puertos:** `LicenseStoragePort` · `CrashReportPort` · `UpdateDistributionPort` ·
  `NotificationPort` (alertas de licencia/crash) · `PaymentPort` (reservado, ventas/marketplace).
- **Adaptadores primarios (entrada):** FastAPI REST — `CT-license`, `CT-crash-report`,
  `CT-updates`, `CT-marketplace`.
- **Adaptadores secundarios (salida):** PostgreSQL (storage), Redis (cache/rate-limit),
  SMTP/webhook (notificaciones), GHCR/S3 (distribución de binarios), pasarela de pago
  (futuro, detrás de `PaymentPort`).

### `hira-studio` — núcleo y adaptadores

- **Núcleo:** proyectos de diseño offline (borradores), emparejamiento con Servers
  remotos, mediación de sesión de ingeniería, Agente del Integrador.
- **Puertos:** `ProjectStoragePort` (borradores) · `PairingPort` (credenciales de
  emparejamiento, cifradas — `STU-ADR-003`) · `EngineeringSessionPort` (media hacia
  `CT-engineering-session` de un Server) · `LicensePort` (valida vía `CT-license` en
  Hub) · `SimulationPort` (motor de simulación offline / sandbox RestrictedPython —
  swappable, `STU-ADR-004`).
- **Adaptadores primarios:** BFF REST/WebSocket consumido por la SPA.
- **Adaptadores secundarios:** PostgreSQL propia, Redis, cliente HTTP a Hub, cliente
  HTTP/WebSocket a Server, motor de simulación concreto.

**`hira-server` no cambia** — sigue gobernado por `SRV-ADR-017`.

## Alternativas consideradas

- **Mantener la asimetría** (Server hexagonal, Hub/Studio directa) — la recomendación
  original por criterio de simplicidad para un solo deployment target. Descartada por
  decisión explícita del propietario: prioriza consistencia entre los 3 codebases
  (mismo vocabulario, mismo patrón de testing, más fácil de mantener siendo un solo
  desarrollador) y la optionality de swappear adaptadores más adelante (proveedor de
  pago del marketplace, canal de notificaciones, motor de simulación) sin refactor
  estructural.

## Consecuencias

- **Buenas:** vocabulario y estructura idénticos en los 3 repos (`core/`, `core/ports/`,
  `adapters/`) — menor carga cognitiva al cambiar de proyecto. Los tests de dominio de
  Hub y Studio corren sin BD real, igual que Server. Cambiar de proveedor de pago,
  canal de notificación o motor de simulación no toca el núcleo.
- **Coste (aceptado explícitamente):** Hub y Studio ganan superficie de mantenimiento
  (interfaces de puerto + al menos un adaptador concreto por puerto) que, bajo el
  criterio original de `HUB-ADR-05`/`STU-ADR-001`, no se justificaba por sí sola —
  se acepta a cambio de la consistencia de ecosistema.
- `HUB-ADR-05` queda **superseded** en su totalidad. `STU-ADR-001` queda
  **parcialmente superseded**: su decisión de hosting/tenancy (multi-tenant único
  junto a Hub) y de stack (FastAPI + PostgreSQL + Redis) **se mantienen**; solo cambia
  "arquitectura directa" → hexagonal.

## Enlaces

- Afecta a: `.harness/constitution.md` Art. 1–2 (perfil de arquitectura).
- Supersede: `docs/hira-hub/decisions/HUB-ADR-05-arquitectura-directa.md` (completo),
  `docs/hira-studio/decisions/STU-ADR-001-cloud-multitenant-spa-bff.md` (sección de
  arquitectura interna únicamente).
- Relacionado: `docs/hira-server/decisions/SRV-ADR-017-arquitectura-hexagonal.md`
  (patrón de referencia).
