---
título: "HUB-ADR-02 — License keys opacas, validadas contra hash"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-07-24
origen_vault: "7.2 - Hira Hub/7.2.3 - Diseño Conceptual.md (ADR-H02)"
tags: [adr, hira-hub, seguridad, licenciamiento]
---

## Contexto

Las license keys viajan en requests desde instalaciones de campo. No deben revelar
información interna ni ser predecibles.

## Decisión

Keys aleatorias de formato `HIRA-XXXX-XXXX-XXXX-XXXX` generadas con `secrets.token_hex`.
Almacenadas como hash bcrypt en BD. La validación compara el hash — la key en claro nunca
se almacena ni se loguea; en logs solo aparece `key_prefix` (`HIRA-XXXX`). La key se
muestra **una sola vez** al emitirse.

## Alternativas consideradas

- Keys con metadata codificada (estilo Stripe `sk_live_...`) — descartada: filtra
  estructura interna y complica la revocación.

## Consecuencias

Seguridad por defecto; si la BD se filtra, las keys no son recuperables; si el integrador
pierde la key, se emite una nueva (no se puede "recuperar"). Contrato de validación:
`CT-license`.
