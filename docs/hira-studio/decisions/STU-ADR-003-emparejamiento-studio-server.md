---
título: "STU-ADR-003 — Emparejamiento Studio ↔ Server por token"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-09-03
resuelve: [SQ-2]
tags: [adr, hira-studio, hira-server, seguridad, emparejamiento]
---

> **Extendido por [STU-ADR-006](STU-ADR-006-conectividad-studio-server-tunel-inverso.md).**
> Este documento sigue vigente para la mecánica de credencial de emparejamiento. La
> conectividad de red (cómo Studio alcanza un Server sin IP pública, sin exponer la red
> del cliente) y el gate de autorización por propiedad del proyecto (`HUB-ADR-06`) se
> diseñaron por separado, en `STU-ADR-006`.

## Contexto

Studio (cloud) necesita un canal autenticado hacia cada Hira Server remoto para abrir
sesiones de ingeniería (`CT-engineering-session`) y publicar proyectos. SQ-2 preguntaba
cómo se registra un Server en Studio y cómo se autentica Studio ante él.

## Decisión

**Emparejamiento por token generado en el Server.**

1. En el panel de administración del Server (rol integrador), el integrador genera un
   **código de emparejamiento** de un solo uso y vida corta (p. ej. 10 min).
2. En Studio, el integrador registra un Server nuevo pegando ese código + una URL/host
   alcanzable del Server.
3. El BFF de Studio llama a `POST /api/v1/engineering/pair` del Server con: el código, el
   `integrator_id` y el `key_prefix` de la licencia de integrador de Studio (para que el
   Server registre quién se emparejó).
4. El Server valida el código, comprueba que hay un usuario con rol integrador, y devuelve
   una **credencial de emparejamiento** de larga duración y **rotable** (un secreto
   opaco). El Server la guarda en su BD (`studio_pairings`: id, `integrator_id`,
   `key_prefix`, hash de la credencial, `created_at`, `last_used_at`, `revoked`).
5. Studio guarda la credencial **cifrada** en su BD (`STUDIO_PAIRING_ENCRYPTION_KEY`) y la
   usa en el header de todas las llamadas de `CT-engineering-session` y de publicación de
   proyecto a ese Server.
6. Cualquiera de los dos lados puede **revocar**: el integrador desde el panel del Server
   (lista de Studios emparejados) o desde Studio (quitar el Server).

## Alternativas consideradas

- **Reutilizar las credenciales de usuario integrador del Server.** Descartada: guardar
  el password del Server del cliente en un producto cloud es inaceptable.
- **Certificado mutuo (mTLS).** Descartada para v1: operativamente pesado para
  instalaciones on-premise de integradores no expertos en PKI.
- **Credencial de integrador delegada por Hub.** Aplazada: requeriría que Hub firme
  tokens de acceso a Servers (Hub como broker de acceso). Es una evolución posible si en
  el futuro Hub se vuelve IdP (`STU-ADR-002`, alternativa aplazada). El token de
  emparejamiento local no depende de que Hub esté en línea.

## Consecuencias

- **Contrato:** `CT-engineering-session` se amplía con `POST /engineering/pair` y la
  cabecera de credencial de emparejamiento; se añade un endpoint de listado/revocación de
  emparejamientos. Se registra como cambio de contrato pendiente en
  `.harness/contracts/engineering-session.openapi.yaml`.
- **Server:** nueva tabla `studio_pairings` y UI en el panel para generar código y listar
  Studios emparejados (module `ENGINEERING`).
- El Server sigue siendo el que decide quién lo puede modificar; Hub no participa en el
  runtime de la conexión.
- El grace period de licencia (`HUB-ADR-03`) es independiente del emparejamiento: un
  Server sin conexión a Hub sigue aceptando sesiones de ingeniería de un Studio emparejado.
