---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.25 - ADR-021 - Modelo IA interno embebido con Ollama como fallback.md"
título: SRV-ADR-021 — Modelo IA interno embebido con Ollama como fallback
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-08-03
tags: [adr, arquitectura, hira-server, ia, docker]
---

## Contexto

SRV-ADR-006 ya establece que el módulo IA es opcional y que el sistema opera al 100% sin él, mencionando "soporte de Ollama como alternativa local" entre sus consecuencias — pero sin especificarlo como componente formal de la instalación. SRV-ADR-013 define dos agentes independientes (Integrador y Cliente), cada uno configurable con Claude, OpenAI u Ollama externo, a elección y costo de cada stakeholder.

En la práctica, muchas instalaciones — sobre todo instancias comerciales en sitios sin garantía de conectividad, o integradores que aún no configuraron una API key — se quedan sin ningún asistente disponible. Un modelo pequeño corriendo dentro del propio despliegue de Docker resuelve ese vacío sin depender de internet ni de una API key de terceros.

## Decisión

Hira Server incluye, como parte estándar de su `docker-compose` (no opcional, no requiere configuración), un contenedor Ollama con un modelo ligero (por defecto `llama3.2:3b`, configurable vía variable de entorno `HIRA_LOCAL_AI_MODEL`) que actúa como modelo IA interno.

Reglas de uso:

- **Prioridad:** si el agente (Integrador o Cliente) tiene una API externa configurada (Claude, OpenAI, u Ollama externo — ver SRV-ADR-013), esa es la que se usa. El modelo interno solo entra en juego si no hay ninguna API externa configurada para esa instancia, o si la llamada externa falla (timeout, sin conexión).
- **Alcance:** aplica a ambos agentes — Integrador y Cliente — como fallback de menor capacidad, nunca como reemplazo de un modelo externo ya configurado.
- **Transparencia:** el panel indica siempre qué modelo respondió (interno o externo) en cada mensaje, para que el usuario entienda que está hablando con un modelo de menor capacidad.
- **Alcance funcional del modelo interno:** conserva el mismo conjunto de tools que su agente (Integrador o Cliente, ver SRV-ADR-013) y el mismo RAG sobre `document_embeddings` (ver SRV-ADR-011) — la diferencia es la capacidad de razonamiento del modelo, no las herramientas disponibles. Tareas complejas de razonamiento largo pueden degradarse; el panel lo señala si detecta baja confianza en la respuesta.

## Alternativas consideradas

- No incluir modelo interno — dejar el sistema sin asistente si no hay API externa configurada (statu quo de SRV-ADR-006/SRV-ADR-013, insuficiente para instalaciones sin internet)
- Requerir que el integrador instale Ollama por separado, fuera del `docker-compose` de Hira (más fricción de instalación, mayor probabilidad de que quede sin configurar)
- Modelo interno como único agente disponible, sin posibilidad de usar Claude/OpenAI (contradice SRV-ADR-013 y limita la capacidad para quien sí quiere pagar por un modelo mayor)

## Consecuencias

- El sistema garantiza asistencia IA básica desde la instalación, sin configuración ni costo adicional, incluso sin internet
- Consumo adicional de recursos del host (CPU/RAM) por el contenedor Ollama, presente aunque no se use activamente — mitigado eligiendo un modelo en el rango de 1B–3B parámetros
- El modelo por defecto es configurable — un integrador con hardware más capaz puede subir a un modelo mayor (ej. `phi4-mini` 3.8B) sin cambiar arquitectura, solo la variable de entorno
- Se añade un nuevo contenedor al `docker-compose` y un nuevo componente en el diagrama de contenedores (ver `.harness/spec/hira-server/architecture/general.md`)
- Las métricas de uso (`ai_usage_log`, ver `.harness/spec/hira-server/modules/agente-ia.md`) deben distinguir si la interacción fue atendida por el modelo interno o por uno externo, para que el integrador entienda cuándo el sistema está operando en modo degradado
