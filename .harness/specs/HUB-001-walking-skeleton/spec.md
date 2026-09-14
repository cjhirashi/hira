---
id: SPEC-HUB-001
tipo: spec
feature: HUB-001-walking-skeleton
estado: in-review
anchor_commit: ‹pendiente›
anchor_mode: advisory
covers:
  - hira-hub/backend/**
  - hira-hub/docs/**
  - hira-hub/docker-compose*.yml
  - hira-hub/.env.example
  - hira-hub/nginx/**
  - .harness/gate/services.txt
  - docs/hira-hub/spec/conceptual-design.md
  - docs/hira-hub/spec/detailed-design.md
  - docs/hira-hub/spec/dev-guide.md
  - docs/hira-hub/spec/validation.md
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-14 }
  fase_2: pendiente
actualizado: 2026-09-14
---

# SPEC-HUB-001 · Walking Skeleton de Hira Hub

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Punto de partida:
> `docs/hira-hub/spec/validation.md` (Sprint H0), `HUB-ADR-01` (mismo stack que Server),
> `E-ADR-002` (Hexagonal, supersede `HUB-ADR-05` "directa"). Primera feature real de
> Hira Hub — sin dependencia de `SRV-*`, puede correr en paralelo.

## 1. Contexto del dominio
- Levantar la infraestructura base de Hira Hub (contenedores + API mínima) de forma
  que licencias/crash-reports/updates (H1/H2/H3) tengan sobre qué construir, sin
  lógica de negocio todavía.
- Límites: `hira-hub/` está vacío. Se implementa desde cero. Dependencias de
  infraestructura: PostgreSQL, Redis, Nginx — todas corren como contenedores del
  propio compose. **A diferencia de `hira-server`: sin Mosquitto/MQTT** (Hub no
  habla protocolos de campo).

## 2. Alcance
### En alcance (propuesto)
- Estructura de repo por puertos/adaptadores (`E-ADR-002`, Hexagonal — mismo patrón
  que `hira-server`, aunque Hub es un solo perfil de despliegue).
- `docker-compose.yml` (perfil producción) + `docker-compose.dev.yml` (hot reload):
  `backend` (FastAPI), `postgres`, `redis`, `nginx`.
- `core/logger.py` (JSON estructurado) y `core/config.py` (Pydantic Settings, falla
  explícita si falta una variable) — mismo diseño que `hira-server` (`SRV-001`),
  reimplementado para Hub (repos separados, sin código compartido en este sprint).
- `core/ports/` (`DatabasePort`, `CachePort`) + adaptadores concretos mínimos
  (Postgres `SELECT 1`, Redis `ping`).
- `GET /health` con Correlation ID, agregando el estado real de Postgres + Redis
  (sin Mosquitto — solo 2 servicios, no 3).
- `hira-hub/docs/openapi.yaml` inicial (Contract-First), solo `/health`.
- Tests del criterio de aceptación de Sprint H0.

### Fuera de alcance (decidido)
- Cualquier lógica de negocio (licencias, crash reports, updates, Panel Admin) — H1/H2/H3.
- Despliegue de producción real: VPS, dominio `hub.hira.cjhirashi.com`, HTTPS/Let's
  Encrypt/Certbot (`docs/hira-hub/spec/deployment.md`) — decidido (2026-09-13): H0 es
  el walking skeleton local/dev, igual que hizo `SRV-001`. El despliegue real a VPS es
  un sprint operativo posterior.

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `GET /health` | entrada | REST | `hira-hub/docs/openapi.yaml#/paths/~1health` |
| PostgreSQL | salida | `DatabasePort` | interno (Protocol, sin contrato externo) |
| Redis | salida | `CachePort` | interno (Protocol, sin contrato externo) |

Payload de `GET /health` (confirmado, mismo criterio que `SRV-001` — sin sobre RFC
9457, es monitoreo):
```json
{
  "status": "ok",
  "services": { "postgres": "ok", "redis": "ok" },
  "version": "0.1.0",
  "trace_id": "..."
}
```

## 4. Criterios de aceptación (EARS)
> A partir de `docs/hira-hub/spec/validation.md` Sprint H0, confirmado en la ronda
> de elicitación (2026-09-14).

- **RF-001** — El sistema DEBE levantar los contenedores `backend`, `postgres`,
  `redis`, `nginx` mediante `docker compose up` y alcanzar estado `healthy` en cada
  uno en menos de 60s.
- **RF-002** — CUANDO se invoca `GET /health`, el sistema DEBE responder **HTTP
  200** con el estado (`ok`/`error`) de PostgreSQL y Redis individualmente y un
  estado agregado (`ok` si ambos están `ok`, `degraded` si al menos uno falla).
- **RF-003** — SI falta una variable de entorno requerida ENTONCES el sistema DEBE
  rechazar el arranque con un error que nombra la variable faltante (sin arranque
  parcial).
- **RF-004** — El sistema DEBE registrar cada log en JSON estructurado con
  `timestamp`, `level`, `service`, `module`, `trace_id`, `message` — cero `print()`.
- **RF-005** — El sistema DEBE propagar un `trace_id` (Correlation ID) por request,
  generándolo si el cliente no envía `X-Trace-ID`.
- **RF-006** — Nginx DEBE servir correctamente como proxy reverso hacia `backend`
  (verificado localmente — sin dominio/TLS real, fuera de alcance de este sprint).

## 5. Casos límite y manejo de errores
- **RF-007** — SI PostgreSQL o Redis no responden dentro de **2 segundos** al
  chequear `/health` ENTONCES el sistema DEBE marcar ese servicio como `error` sin
  colgar la respuesta.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| Hexagonal desde este sprint | `E-ADR-002` homogeneiza los 3 productos; supersede `HUB-ADR-05` ("directa") | Arquitectura directa (`HUB-ADR-05`, superseded) | `E-ADR-002` |
| Sin Mosquitto en el compose | Hub no habla protocolos de campo — solo Postgres+Redis+Nginx (`HUB-ADR-01`) | Incluir Mosquitto "por si acaso" | `HUB-ADR-01` |
| Despliegue de producción (VPS/dominio/TLS) fuera de este sprint | H0 es el walking skeleton local/dev; `docs/hira-hub/spec/deployment.md` es un sprint operativo posterior | Configurar HTTPS/dominio real ya en H0 | — |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — Los contenedores DEBEN alcanzar `healthy` en < 60s desde
  `docker compose up` (de Sprint H0).
- **RNF-002** — El chequeo de cada servicio en `/health` DEBE tener timeout de 2s
  (no esperar indefinidamente).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-14).
