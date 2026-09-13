---
título: "E-ADR-003 — Convención de `type` para el sobre de error RFC 9457"
componente: ecosystem
tipo: ADR
status: accepted
fecha_creación: 2026-09-13
tags: [adr, ecosystem, contratos, errores, rfc9457]
---

> Fija cómo se construye el campo `type` del sobre RFC 9457 (ya exigido por
> Constitución Art. 6 en los 3 productos), para que cada feature futura no lo
> reinvente ni elija un formato distinto. Nace en `SRV-002-auth-rbac` (primer uso
> real en el ecosistema); se formaliza aquí para que aplique a Server, Hub y Studio
> por igual.

## Contexto

La Constitución (Art. 6) exige el sobre RFC 9457 (`application/problem+json`) para
errores de negocio en los 3 productos, pero no fijaba cómo construir `type` — el
único campo de la RFC sin un formato canónico impuesto (la RFC solo exige que sea
un URI, con `about:blank` como valor por defecto si no se quiere dar más detalle).
`SRV-001-walking-skeleton` no necesitó decidirlo (`/health` es monitoreo, no usa el
sobre). `SRV-002-auth-rbac` es el primer endpoint de negocio real del ecosistema y
necesitó un catálogo de `type` para sus 8 causas de error (`invalid-credentials`,
`token-expired`, etc.).

## Decisión

`type` es un URI **estable, con esquema `https://`, que no necesita resolver a una
página real**: `https://hira.dev/errors/<slug>`, con `<slug>` en `kebab-case`,
estable una vez publicado (no se renombra un slug ya usado — se agrega uno nuevo si
el significado cambia).

- `<slug>` identifica la **causa**, no el código HTTP (varios `type` pueden compartir
  `status`; p. ej. `token-expired` y `token-invalid` son ambos 401 pero causas
  distintas que un cliente puede querer distinguir).
- Cada producto mantiene su propio catálogo de slugs en el `plan.md` de la feature
  que los introduce (como hace `SRV-002-auth-rbac §4`) — no hay un registro central
  de slugs en este ADR; el URI compartido (`https://hira.dev/errors/`) es lo único
  que se fija aquí.
- `title` es fijo por slug (resumen legible); `detail` es específico de la instancia
  y **nunca** debe filtrar información que ayude a enumerar recursos (p. ej. el 401
  de login usa el mismo `title`/`detail` genérico sin importar la causa real —
  `SRV-002-auth-rbac RF-002`).

## Alternativas consideradas

- **`type: "about:blank"` para todo (default de la RFC).** Descartada: pierde el
  valor de que un cliente (frontend, integración) distinga causas por `type` sin
  parsear `detail` (texto libre, no debe usarse para lógica de negocio en el cliente).
- **URI que sí resuelve a documentación real** (p. ej. un endpoint que sirve HTML
  describiendo el error). Descartada por ahora: over-engineering para el volumen
  actual de tipos de error; se reconsiderará si el catálogo crece mucho o si un
  consumidor externo (Studio, integraciones) lo pide explícitamente.

## Consecuencias

- **Buenas:** ningún producto reinventa el formato de `type` en su primera feature
  con errores de negocio; un cliente puede hacer `switch` sobre `type` de forma
  estable entre versiones.
- **Neutras:** el catálogo de slugs vive distribuido en los `plan.md` de cada
  feature, no centralizado — aceptable mientras el volumen sea manejable; si crece
  mucho, un `docs/contracts/errors-catalog.md` compartido es la evolución natural
  (no se crea preventivamente, Art. 10).

## Enlaces

- Constitución Art. 6 (exige RFC 9457).
- Primer uso real: `SRV-002-auth-rbac/plan.md §4` (catálogo de 8 slugs).
