---
id: SPEC-SRV-001
tipo: spec
feature: SRV-001-walking-skeleton
estado: verified
anchor_commit: b4248e749d6a9eceaa68b9f117b79116222c1eb9
anchor_mode: strict
covers:
  - hira-server/backend/**
  - hira-server/docs/**
  - hira-server/docker-compose*.yml
  - hira-server/.env.example
  - hira-server/mosquitto/**
  - hira-server/nginx/**
  - hira-server/frontend/**
  - hira-server/README.md
  - .harness/gate/services.txt
  - docs/hira-server/spec/implementation-guide/estructura-de-repositorio.md
  - docs/hira-server/spec/implementation-guide/guia-backend.md
  - docs/hira-server/spec/validation/vulnerabilities.md
  - docs/planning/SPRINT.md
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-13 }
  fase_2: { por: "Carlos", fecha: 2026-09-13 }
actualizado: 2026-09-13
---

# SPEC-SRV-001 · Walking Skeleton de Hira Server

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Punto de partida:
> `docs/planning/SPRINT.md` (detalle previo a la reestructuración del arnés) + `AC-SRV-01`
> (`docs/hira-server/spec/validation/acceptance-criteria.md`).

## 1. Contexto del dominio
- Levantar la infraestructura base de Hira Server (contenedores + API mínima) de forma
  que cualquier módulo posterior (auth, protocolos, alarmas…) tenga sobre qué construir,
  sin lógica de negocio todavía.
- Límites: `hira-server/` está vacío (solo stub). Se implementa desde cero. Dependencias
  de infraestructura: PostgreSQL/TimescaleDB, Redis, Mosquitto, Nginx — todas corren como
  contenedores del propio compose (no se asume nada externo).

## 2. Alcance
### En alcance
- Estructura de repo `backend/{core,adapters,routers,models,schemas,services,workers,websocket}`
  por puertos/adaptadores (`SRV-ADR-017`).
- `docker-compose.yml` (perfil producción) + `docker-compose.dev.yml` (hot reload):
  `backend` (FastAPI), `postgres` (TimescaleDB), `redis`, `mosquitto`, `nginx`.
- `core/logger.py` (JSON estructurado) y `core/config.py` (Pydantic Settings, falla
  explícita si falta una variable).
- `core/ports/` (`DatabasePort`, `CachePort`, `NotificationPort`) + adaptadores concretos
  mínimos (Postgres `SELECT 1`, Redis `ping`).
- `GET /health` con Correlation ID, agregando el estado real de los 3 servicios.
- `docs/openapi.yaml` inicial (Contract-First), solo `/health`.
- Tests de `AC-SRV-01` (1.1–1.4).

- Autenticación básica de Mosquitto (`VUL-SRV-001`): `allow_anonymous false` +
  `password_file` — **decidido, entra en este sprint** (2026-09-13).

### Fuera de alcance (decidido)
- Cualquier lógica de negocio (auth, protocolos, alarmas, motor de lógica).
- pgvector / esquema de datos de negocio (llega con `SRV-Sprint-2+`).
- Arranque verificado en Windows/WSL2 (`AC-SRV-01.2`) — diferido explícitamente; no
  bloquea el gate de cierre de este sprint (2026-09-13).

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `GET /health` | entrada | REST | `docs/openapi.yaml#/paths/~1health` |
| PostgreSQL | salida | `DatabasePort` | interno (Protocol, sin contrato externo) |
| Redis | salida | `CachePort` | interno (Protocol, sin contrato externo) |
| Mosquitto | salida | conexión MQTT | interno (sin publish/subscribe todavía) |

Payload de `GET /health` (confirmado, sin sobre RFC 9457 — es monitoreo, no negocio):
```json
{
  "status": "ok",
  "services": { "postgres": "ok", "redis": "ok", "mosquitto": "ok" },
  "version": "0.1.0",
  "trace_id": "..."
}
```

## 4. Criterios de aceptación (EARS)
> A partir de `AC-SRV-01`, confirmado en la ronda de elicitación (2026-09-13).

- **RF-001** — El sistema DEBE levantar los contenedores `backend`, `postgres`, `redis`,
  `mosquitto`, `nginx` mediante `docker compose up` y alcanzar estado `healthy` en cada
  uno en menos de 60s.
- **RF-002** — CUANDO se invoca `GET /health`, el sistema DEBE responder **HTTP 200**
  con el estado (`ok`/`error`) de PostgreSQL, Redis y Mosquitto individualmente y un
  estado agregado (`ok` si los tres están `ok`, `degraded` si al menos uno falla).
- **RF-003** — SI falta una variable de entorno requerida ENTONCES el sistema DEBE
  rechazar el arranque con un error que nombra la variable faltante (sin arranque parcial).
- **RF-004** — El sistema DEBE registrar cada log en JSON estructurado con `timestamp`,
  `level`, `service`, `module`, `trace_id`, `message` — cero `print()`.
- **RF-005** — El sistema DEBE propagar un `trace_id` (Correlation ID) por request,
  generándolo si el cliente no envía `X-Trace-ID`.
- **RF-006** — El sistema DEBE rechazar conexiones MQTT anónimas (Mosquitto con
  `allow_anonymous false` + `password_file`; el `backend` se conecta con credencial
  propia).

## 5. Casos límite y manejo de errores
- **RF-007** — SI PostgreSQL, Redis o Mosquitto no responden dentro de **2 segundos**
  al chequear `/health` ENTONCES el sistema DEBE marcar ese servicio como `error` sin
  colgar la respuesta.
- **RF-008** — SI el `backend` intenta conectar a Mosquitto con credencial inválida
  ENTONCES el sistema DEBE registrar el fallo (log JSON, `level: error`) y reflejarlo
  en `/health` como `mosquitto: error` — no debe reintentar indefinidamente sin backoff.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| Un solo perfil (Postgres+TimescaleDB), sin `HIRA_DEPLOY_MODE` | `E-ADR-001` retira el perfil `studio`/SQLite | Perfil dual server/studio | `E-ADR-001`, `SRV-ADR-015` |
| Estructura por puertos/adaptadores desde este sprint | `SRV-ADR-017` (Hexagonal) | Estructura por capas simple | `SRV-ADR-017` |
| Cierre de sesión usa `gate/check.sh` + `memory/history.md` | Esquema simplificado del arnés (`ADR-001` del arnés) reemplaza `registry.yaml` / `.harness/ci/run_all.sh` / `deviations/LOG.md` citados en el `SPRINT.md` original | Mantener el gate legacy | `.harness/decisions/ADR-001` |
| Auth de Mosquitto (`allow_anonymous false` + `password_file`) entra en este sprint | `VUL-SRV-001` es crítico y el compose de este sprint ya crea el contenedor — dejarlo abierto es riesgo desde el día 1 | Diferir a un sprint de seguridad de infra | `VUL-SRV-001` |
| Verificación de arranque en Windows/WSL2 (`AC-SRV-01.2`) diferida | No bloquear el Walking Skeleton por un segundo entorno de prueba; se valida Linux primero | Verificarlo en este mismo sprint | — |
| `GET /health` responde siempre HTTP 200 (detalle en el body) | Un healthcheck agregado no debe hacer que un load balancer saque el servicio completo por la falla de un servicio secundario | Responder 503 si cualquier servicio falla | — |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — Los contenedores DEBEN alcanzar `healthy` en < 60s desde `docker compose up` (de `AC-SRV-01.1`).
- **RNF-002** — El chequeo de cada servicio en `/health` DEBE tener timeout de 2s (no esperar indefinidamente).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-13).
