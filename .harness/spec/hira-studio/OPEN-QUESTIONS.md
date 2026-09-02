---
título: Preguntas abiertas de diseño — Hira Studio
componente: hira-studio
tipo: Registro de decisiones pendientes
status: abierto
última_actualización: 2026-09-02
---

`E-ADR-001` establece que Studio es un producto cloud independiente pero deja abiertas las
decisiones de abajo. Cada una se cierra con un `STU-ADR-###` (o una edición de spec) antes
de `STU-Sprint-1`. Mientras estén abiertas, Studio no tiene sprint activo.

| # | Pregunta | Por qué importa | Candidatas |
|---|---|---|---|
| SQ-1 | **Auth de Studio cloud.** ¿Cómo inicia sesión el integrador en Studio? ¿Cuenta propia de Studio, cuenta federada con Hub, o la license key? | Studio es multi-integrador y multi-Server. Necesita identidad propia. | Cuenta Studio con SSO a Hub · OIDC · magic link |
| SQ-2 | **Gestión de conexiones a Servers.** ¿Cómo registra un integrador sus Servers en Studio? ¿Cómo se autentica Studio ante cada Server para abrir la sesión de ingeniería? | Un integrador tiene N Servers (local + varios clientes). La sesión de ingeniería (`CT-engineering-session`) necesita un canal autenticado Studio→Server. | Token de emparejamiento generado en el Server · certificado mutuo · credencial de integrador delegada por Hub |
| SQ-3 | **Tenancy / hosting.** ¿Una instancia de Studio multi-tenant para todos los integradores, o una por integrador? ¿Dónde se hospeda (VPS de cjhirashi junto a Hub, u otro)? | Define el modelo de datos, el aislamiento y el costo operativo. | Multi-tenant única · namespace por integrador · self-host opcional |
| SQ-4 | **Backend propio de Studio.** ¿Qué backend necesita Studio más allá de proxyar al Server? (preferencias de usuario, catálogo local de bloques, borradores no publicados, historial de sesiones). | Determina si `hira-studio/` tiene su propia BD o es solo frontend + BFF fino. | Frontend + BFF sin estado · BFF con BD ligera (Postgres) |
| SQ-5 | **Ejecución de lógica/pruebas y Agente del Integrador.** Los scripts se editan en Studio pero corren en Server. ¿Studio empuja el script y el Server lo ejecuta/valida, o Studio tiene un sandbox de validación propio? ¿El Agente del Integrador corre en Studio (con su API key) o Studio proxya al `/ai/integrator` del Server? | Afecta qué endpoints expone Server a la sesión de ingeniería y dónde vive el costo de IA. | Ejecución siempre en Server vía `CT-engineering-session` · Studio valida sintaxis/RestrictedPython localmente, ejecuta en Server · Agente Integrador en Studio |
| SQ-6 | **Multi-proyecto en el modelo cloud.** `SRV-ADR-020` daba multi-proyecto a la instalación local del integrador. En cloud, ¿"biblioteca de proyectos" = lista de (Server, proyecto) a los que el integrador tiene acceso? ¿Sigue existiendo el concepto de instalación local del integrador con licencia de integrador? | `SRV-ADR-018/020` asumían una instancia local multi-proyecto del integrador. Con Studio cloud eso cambia. | Studio lista (Server,proyecto) · se conserva un "Server local del integrador" como banco de pruebas · licencia de integrador pasa a habilitar Studio |
| SQ-7 | **Licenciamiento de Studio.** ¿Studio se licencia aparte (suscripción cloud), o el acceso a Studio va incluido con la licencia de integrador emitida por Hub? | Hub emite `product: studio` en `license_keys` (`HUB` detailed-design). Falta el modelo comercial. | Suscripción cloud mensual · incluido con licencia de integrador · freemium |
| SQ-8 | **Offline / demos sin Server.** Antes el integrador podía diseñar en su PC sin depender del cliente. Si Studio es cloud y no aloja proyectos, ¿cómo hace demos o diseño especulativo sin un Server? | Caso de uso `CU-11` del diseño de Server. | Server local del integrador como banco de pruebas · Studio con un "Server efímero" en cloud · plantillas `.hirat` como punto de partida |

## Proceso

Cada `SQ-N` que se resuelve:
1. Se decide (con el usuario) y se redacta un `STU-ADR-###` en `.harness/adr/hira-studio/`.
2. Se actualiza `spec/hira-studio/context.md` y, si toca, los ADRs de Server con banner de
   supersesión.
3. Se marca aquí `Resuelta → STU-ADR-###`.
4. Se abre la spec de módulo correspondiente en `spec/hira-studio/`.
