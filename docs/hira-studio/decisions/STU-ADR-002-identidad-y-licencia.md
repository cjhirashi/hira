---
título: "STU-ADR-002 — Identidad del integrador y licenciamiento gestionado en Hub"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-09-03
resuelve: [SQ-1, SQ-7]
tags: [adr, hira-studio, hira-hub, identidad, licenciamiento]
---

## Contexto

SQ-1 (auth de Studio) y SQ-7 (licenciamiento de Studio) estaban abiertas. Decisión del
propietario: **el licenciamiento de Studio y de Server se gestiona en Hub**; en Studio hay
**un usuario por integrador** y a ese usuario se **enlaza la licencia de integrador**; en
Server la licencia se **asocia al Server** (a la instalación / hardware), no a un usuario.

## Decisión

### Modelo de identidad

- **Un `integrator_user` por integrador.** El registro del usuario vive en el **BFF de
  Studio** (`STU-ADR-001`): email, credencial (passkey o password bcrypt), `integrator_id`.
- Al crear la cuenta (o al vincular), el integrador aporta su **license key de integrador**
  (emitida por Hub, `product: studio`, `tier: integrator`). Studio la valida contra Hub por
  `CT-license` (`POST /api/licenses/activate` la primera vez, `/validate` en adelante) y la
  **enlaza** al `integrator_user` (guarda solo `key_prefix` + el `license_key_id` que
  devuelve Hub; nunca la key en claro).
- **Acceso a Studio = tener una licencia de integrador enlazada y `valid: true`.**
  Licencia expirada o revocada → Studio pasa a **solo lectura** (se pueden ver proyectos y
  sesiones, no editar ni publicar).

### Reparto de responsabilidades de licencia

| | Se emite en | Se enlaza a | Se valida por |
|---|---|---|---|
| Licencia de **integrador** (Studio) | Hub | el `integrator_user` de Studio | `CT-license` (Studio → Hub) |
| Licencia **comercial** (Server) | Hub | la instalación de Server (hardware fingerprint, tabla `license_activations`) | `CT-license` (Server → Hub) |

Hub es la **autoridad única de licencias** del ecosistema. Studio y Server son clientes de
`CT-license`; ninguno emite licencias.

### Sesión

El BFF de Studio emite su propio JWT de sesión (access corto + refresh en Redis, mismo
patrón que Server) tras validar credencial + licencia. El JWT lleva `integrator_id` — es
la clave de aislamiento multi-tenant (`STU-ADR-001`).

## Alternativas consideradas

- **Hub como IdP OIDC (store de usuarios en Hub).** Descartada por ahora: haría crecer el
  alcance de Hub (hoy su único frontend es el Panel Admin de cjhirashi) con un módulo de
  identidad de cara al integrador. Si más adelante se quiere identidad unificada
  (una cuenta para Hub + Studio + portal de ventas), se promueve con un ADR nuevo y Studio
  delega. La puerta queda abierta: Studio ya habla `CT-license` con Hub.
- **OIDC de terceros (Google).** Descartada: no unifica identidad con el ecosistema y
  añade dependencia de un IdP externo.
- **Suscripción cloud de Studio aparte.** Descartada: el licenciamiento se centraliza en
  Hub y se expresa como licencia de integrador; cualquier modelo de precio de esa licencia
  es una decisión de Hub, no un segundo flujo de facturación en Studio.

## Consecuencias

- Hub no cambia su modelo de datos: `license_keys` ya tiene `product: studio` y
  `integrator_email`. Studio guarda el vínculo `integrator_user ↔ license`.
- `CT-license` se usa tal cual (con `product: studio`). No hace falta contrato nuevo para
  esto.
- Revocar la licencia de un integrador en Hub → en la siguiente validación periódica,
  Studio degrada a ese usuario a solo lectura.
- Queda por definir (no bloquea v1): usuarios múltiples dentro de una **empresa
  integradora** (varios técnicos bajo una misma licencia). v1 = un usuario por licencia de
  integrador; el modelo de equipo se aborda con un ADR posterior.
