# schemas

Modelos Pydantic de request/response.

- `health.py` — `HealthResponse`, payload de respuesta de `GET /health`,
  traducción exacta de `hira-hub/docs/openapi.yaml#/paths/~1health`
  (Contract-First). Nace en un batch posterior (`tasks.md` T-015), fuera de
  alcance de este batch (T-001..T-012).
