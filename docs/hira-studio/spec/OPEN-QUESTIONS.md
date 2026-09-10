---
título: Preguntas de diseño de Hira Studio — resueltas
componente: hira-studio
tipo: Registro de decisiones
status: cerrado
última_actualización: 2026-09-03
---

Las 8 preguntas que abría `E-ADR-001` se resolvieron el **2026-09-03** con decisión del
propietario. Cada una quedó en un `STU-ADR-###` en `.harness/adr/hira-studio/`.

| # | Pregunta | Decisión | ADR |
|---|---|---|---|
| SQ-1 | Auth de Studio cloud | Un `integrator_user` por integrador, store en el BFF de Studio; JWT de sesión con `integrator_id`. Hub-como-IdP queda como evolución posible, no v1. | `STU-ADR-002` |
| SQ-2 | Conexión y auth a Servers | Emparejamiento por token generado en el Server → credencial de larga duración rotable, cifrada en Studio. Revocable desde cualquiera de los dos lados. | `STU-ADR-003` |
| SQ-3 | Tenancy / hosting | Instancia **multi-tenant única junto a Hub**; aislamiento lógico por `integrator_id`. Self-host y per-integrador: fuera de v1. | `STU-ADR-001` |
| SQ-4 | Backend propio de Studio | **SPA + BFF (FastAPI) con BD PostgreSQL + Redis**, arquitectura directa (como `HUB-ADR-05`). Persiste borradores, emparejamientos, preferencias, historial, caché de catálogo. | `STU-ADR-001` |
| SQ-5 | Ejecución de lógica/pruebas y Agente del Integrador | **Offline en Studio** (motor de simulación + sandbox RestrictedPython) para validar el diseño; **en línea siempre en el Server**. Agente del Integrador en el BFF de Studio con la API key del integrador; Agente del Cliente sigue en Server. | `STU-ADR-004`, `STU-ADR-005` |
| SQ-6 | Multi-proyecto en cloud | Biblioteca de Studio = borradores offline + pares `(Server emparejado, proyecto)`. Multi-proyecto sigue siendo capacidad del Server, exclusiva de licencia de integrador (`SRV-ADR-020` se conserva, con banner). | `STU-ADR-004` |
| SQ-7 | Licenciamiento de Studio | **Gestionado en Hub.** La licencia de integrador (Hub, `product: studio`) se enlaza al `integrator_user` y se valida por `CT-license`. Sin licencia válida → Studio en solo lectura. Server: la licencia se asocia a la instalación (hardware). | `STU-ADR-002` |
| SQ-8 | Offline / demos sin Server | El **diseño offline con simuladores** ES el flujo sin Server. Para arrancar rápido: plantillas `.hirat` de Hub (v0.3). Para correr en línea hace falta un Server real (del cliente o un banco de pruebas del integrador). Sin "Server efímero en cloud". | `STU-ADR-004` |

## Consecuencias transversales pendientes (no bloquean, se recogen en el roadmap)

- **Ampliar `CT-engineering-session`** con: `POST /engineering/pair` + cabecera de
  credencial de emparejamiento (`STU-ADR-003`); operación de **publicar/actualizar
  proyecto** (`STU-ADR-004`); endpoints de consulta que necesitan las tools *en línea* del
  Agente del Integrador (`STU-ADR-005`).
- **Formato de paquete de proyecto** de Studio → Server: `.hira` extendido; converge con
  `VUL-SRV-009` (compatibilidad de versiones) y `VUL-SRV-015` (esquema `.hirat`).
- **Server:** tabla `studio_pairings` + UI de emparejamiento en el panel; import de
  proyecto por la sesión de ingeniería reutilizando la lógica de import de `.hira`.
- **Modelo de equipo** (varios técnicos de una empresa integradora bajo una licencia):
  fuera de v1, ADR posterior.
