---
título: "STU-ADR-005 — Agente del Integrador en el BFF de Studio"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-09-03
resuelve: [SQ-5]
tags: [adr, hira-studio, ia]
---

## Contexto

`SRV-ADR-013` define dos agentes IA independientes: **Integrador** (construcción del
proyecto) y **Cliente** (operación). Con `E-ADR-001`, la construcción del proyecto pasa a
Studio. Falta decidir dónde corre el Agente del Integrador.

## Decisión

**El Agente del Integrador corre en el BFF de Studio**, con la **API key del integrador**
(cifrada en la BD de Studio con `AI_ENCRYPTION_KEY`-equivalente). El Agente del **Cliente
se queda íntegramente en el Server** (`SRV-ADR-013` sin cambios para ese lado).

- **Tools del Agente del Integrador:**
  - *Offline*: operan sobre el proyecto de diseño en Studio (crear/editar dispositivos
    simulados, puntos, scripts, mimics; ejecutar una prueba en el motor offline).
  - *En línea*: cuando hay sesión de ingeniería activa, además operan sobre el Server
    conectado (leer estado real, listar dispositivos escaneados, proponer asociaciones).
  - *Hub*: buscar plantillas / bloques en el marketplace (v0.3).
- **Modelo interno:** aplica el mismo criterio de `SRV-ADR-021` — si el integrador no
  configuró API externa, Studio usa un modelo interno de fallback (Ollama en el
  despliegue de Studio, o el del Server conectado; a afinar en la spec de módulo).
- **RAG de diseño:** el Agente del Integrador indexa la documentación del proyecto de
  diseño (borrador) y, en línea, la del Server conectado (`SRV-ADR-011`).
- **Métricas de uso** (`ai_usage_log`, `SRV-ADR-021`): Studio lleva su propio registro de
  consumo/costo del Agente del Integrador, separado del de los agentes del Server.

## Alternativas consideradas

- **Agente del Integrador en el Server, Studio solo proxya.** Descartada: el integrador
  necesita el asistente también **offline** (sin Server), y el contexto de edición vive en
  Studio.
- **Un solo agente compartido.** Descartada: contradice `SRV-ADR-013` (costos y tools
  separados por stakeholder).

## Consecuencias

- Studio necesita un módulo `AI` en su BFF: orquestación del agente (LangChain o
  equivalente), cifrado de la API key, `ai_usage_log` propio, y el conjunto de tools
  offline/online descrito arriba.
- Para las tools *en línea*, el Server debe exponer por la sesión de ingeniería los
  endpoints de lectura/consulta que el agente necesita → se recoge en la ampliación de
  `CT-engineering-session` (`STU-ADR-003`, `STU-ADR-004`).
- El costo de IA del diseño lo asume el integrador con su propia key — sin cambio respecto
  del modelo comercial (`business-model.md`).
