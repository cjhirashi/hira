# docs

Contratos de API internos de `hira-hub` (Contract-First).

- `openapi.yaml` — `GET /health` (RF-002), escrito antes del router
  (`backend/routers/monitor.py`, `tasks.md` T-013 → T-014/T-015). Payload
  exacto: `status`, `services.{postgres,redis}`, `version`, `trace_id`;
  siempre HTTP 200, sin sobre RFC 9457 (endpoint de monitoreo).

No confundir con `docs/hira-hub/` en la raíz del repo (documentación de
producto: specs, ADRs, criterios de aceptación) ni con `docs/contracts/`
(contratos compartidos entre productos).
