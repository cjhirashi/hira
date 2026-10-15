---
título: "HUB-ADR-06 — Propiedad de proyecto y vinculación de integradores"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-10-15
resuelve: [pregunta abierta de E-ADR-001 sobre control de acceso externo a proyectos]
tags: [adr, hira-hub, hira-studio, hira-server, seguridad, propiedad, licenciamiento]
---

## Contexto

`STU-ADR-003` resolvió cómo Studio se autentica ante un Server (token de emparejamiento),
pero no resolvió **quién decide qué integrador puede llegar a qué proyecto**. El
propietario del ecosistema identificó el riesgo: los Servers viven en la red de sus
clientes finales — una vulneración de ese control de acceso es un problema de negocio
para él, no solo técnico.

Decisión del propietario (2026-10-15): un proyecto tiene un **dueño** (el integrador que
lo crea, o el cliente final una vez entregado). El dueño decide qué otros integradores
pueden vincularse. Al entregar el proyecto, el integrador **cede la propiedad al
cliente**, que desde ese momento controla el acceso.

Este control de acceso es sobre **quién puede llegar desde afuera** (Studio → Server), no
sobre operación interna del Server — por eso vive en Hub, no en el RBAC del Server
(`SRV-002-auth-rbac`, ya `verified`, no se reabre).

## Decisión

### Modelo de datos (Hub)

Nueva tabla `project_ownership`:

| Campo | Qué es |
|---|---|
| `project_ref` | Referencia única al par `(server_pairing_id, project_id)` — el proyecto tal como vive en un Server emparejado (`STU-ADR-004`) |
| `owner_account_id` | Cuenta de Hub (integrador o cliente) que es dueña hoy |
| `created_at` / `transferred_at` | Trazabilidad de cuándo se creó y cuándo cambió de dueño |

Nueva tabla `project_linked_integrators`:

| Campo | Qué es |
|---|---|
| `project_ref` | Mismo proyecto |
| `integrator_account_id` | Cuenta de integrador con acceso otorgado |
| `granted_by` | Cuenta que otorgó el acceso (debe ser el `owner_account_id` vigente en ese momento) |
| `granted_at` / `revoked_at` | Trazabilidad |

### Reglas

1. **Solo el dueño vigente** puede otorgar o revocar vinculaciones de `project_linked_integrators`.
2. **Transferencia de propiedad** (`transfer_ownership`): el dueño vigente mueve
   `owner_account_id` a otra cuenta. Si el destinatario (típicamente el cliente final) no
   tiene cuenta en Hub, se genera una invitación; la transferencia queda pendiente hasta
   que la acepta. Al completarse, el dueño anterior **no** queda automáticamente vinculado
   — si quiere seguir con acceso, el nuevo dueño debe vincularlo explícitamente.
3. **Cuentas de Hub para clientes finales:** un cliente final necesita una cuenta de Hub
   para administrar vinculaciones de su proyecto, pero **no** necesita licencia de Studio
   (`CT-license, product: studio`) — esa licencia solo la necesitan los integradores que
   diseñan. Una cuenta "cliente" sin licencia de Studio activa puede entrar a Hub
   únicamente a gestionar propiedad/vinculaciones de sus proyectos, no a abrir Studio.
4. **Listado de proyectos en Studio:** al autenticarse, Studio le pide a Hub (no al
   Server) la lista de proyectos donde la cuenta es `owner_account_id` o aparece en
   `project_linked_integrators` sin `revoked_at`. Cada entrada ya trae resuelto el par
   `(Server, proyecto)` de `STU-ADR-004`.
5. **Auditoría:** cada alta/baja de vinculación y cada transferencia se registra con
   quién y cuándo — necesario si hay una disputa de acceso entre integrador y cliente.

### Qué no cambia

- El Server sigue sin saber nada de esto — su RBAC (`Admin`/`Operador`/`Visor`/
  `integrador`, `SRV-002-auth-rbac`) sigue siendo exclusivamente sobre operación interna
  del Server, no sobre quién puede llegar desde Studio.
- Los borradores de diseño offline de Studio (`STU-ADR-004`) no pasan por este modelo —
  solo los proyectos ya vinculados a un Server real.

## Alternativas consideradas

- **Dejar el control de acceso solo en el rol `integrador` del Server (como hoy).**
  Descartada: el Server no tiene visibilidad de cuentas de Studio/Hub ni de a quién
  pertenece el negocio del proyecto; mezclaría control de acceso externo con RBAC
  operativo interno y forzaría a reabrir una spec `verified`.
- **Modelar propiedad/vinculación dentro de Studio en vez de Hub.** Descartada: Studio es
  stateless respecto a identidad/licencias de negocio — Hub ya es la fuente de verdad de
  cuentas (`CT-license`, `HUB-ADR-02`); es más natural extenderla ahí.

## Consecuencias

- Hub gana 2 tablas nuevas + endpoints: listar mis proyectos, otorgar/revocar
  vinculación, transferir propiedad, aceptar invitación.
- `STU-ADR-006` (conectividad Studio↔Server) usa este modelo como gate de autorización
  antes de abrir cualquier sesión de ingeniería: revocar aquí también debe cortar el
  acceso de red de ese integrador a ese Server.
- Pendiente de diseñar en el siguiente ciclo: UI de Hub para gestionar vinculaciones/
  transferencias (fuera de alcance de este ADR, es solo el modelo).
