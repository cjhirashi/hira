---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.8 - Agente IA.md"
título: Agente IA — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-08-03
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, agente-ia, rag]
---

## Responsabilidad

Dos instancias independientes de LangChain (ver SRV-ADR-013): Agente del Integrador (construcción del proyecto) y Agente del Cliente (operación, con RAG sobre la documentación del proyecto). Cada una con su propia API key y su propio conjunto de tools.

## Configuración

- `ai_config` por proyecto e instancia (`integrator | client`), proveedor (`claude | openai | ollama`), modelo, API key cifrada (`AI_ENCRYPTION_KEY`)
- El sistema opera al 100% sin ningún agente activo (ver SRV-ADR-006) — si no hay API key configurada, el panel muestra "no configurado" sin errores

## Modelo Interno (fallback) — ver SRV-ADR-021

- Contenedor Ollama incluido siempre en el `docker-compose`, con un modelo ligero por defecto (`llama3.2:3b`, configurable vía `HIRA_LOCAL_AI_MODEL`) — no requiere configuración ni API key
- Se usa automáticamente cuando la instancia (Integrador o Cliente) no tiene API externa configurada, o cuando la llamada externa falla (timeout, sin conexión) — nunca compite con un modelo externo ya configurado, solo cubre su ausencia
- Mismo conjunto de tools y mismo RAG que el agente externo (ver tabla de tools abajo) — la diferencia es la capacidad de razonamiento del modelo, no las herramientas disponibles
- El panel indica en cada respuesta si fue atendida por el modelo interno o por uno externo, para que el usuario sepa que está operando en modo de menor capacidad

## RAG (Agente del Cliente)

- Fuente: `document_embeddings` — chunks de la documentación del proyecto (fichas técnicas, lista de puntos asociados, diagramas de flujo de scripts, resultados de pruebas, históricos), indexados con pgvector (ivfflat) — ver SRV-ADR-011
- El agente consulta el índice antes de responder, recuperando solo los fragmentos relevantes a la pregunta — evita inyectar la lista completa de puntos en cada conversación (relevante en proyectos grandes, > 500 puntos)

## Tools por agente

| Agente | Tools |
|---|---|
| Integrador | Configurador, Motor de Lógica, Motor de Pruebas, Documentación, editor de mimics |
| Cliente | Monitoreo, Alarmas, Históricos, Análisis, generación de reportes |

Toda escritura que el agente ejecute como tool respeta RBAC y `access_mode` del punto, igual que una escritura manual.

## Métricas y presupuesto

- `ai_usage_log` registra tokens de entrada/salida, costo estimado, duración, sesión y **origen** (`interno | externo`, ver SRV-ADR-021) por cada interacción — retención 90 días rolling
- Métricas derivadas para Prometheus: `hira_ai_tokens_total`, `hira_ai_cost_usd_total`, `hira_ai_requests_total`, `hira_ai_latency_ms`, `hira_ai_tokens_per_session`
- Alertas de presupuesto configurables por agente (umbral de tokens/día o USD/mes); al superarse, notificación en panel — no bloquea la operación salvo que se configure explícitamente para desactivar el agente

---

## Gate de Salida

- [x] Dos agentes independientes documentados con tools diferenciados
- [x] RAG y estrategia de contexto documentados
- [x] Métricas y presupuesto de tokens documentados
- [x] Modelo interno de fallback (SRV-ADR-021) documentado
- [ ] Revisado y aprobado por Charlie
