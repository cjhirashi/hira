---
id: SPEC-SRV-003
tipo: spec
feature: SRV-003-bacnet-adapter
estado: in-review
anchor_commit: ‹pendiente›
anchor_mode: advisory
covers:
  - hira-server/backend/**
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-14 }
  fase_2: pendiente
actualizado: 2026-09-14
---

# SPEC-SRV-003 · Adaptador BACnet — escaneo y candidatos

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Base: `SRV-ADR-012`
> (escaneo + candidatos, no asociación automática), `SRV-ADR-014` (simuladores, referencia
> de esquema `devices` — no implementados aquí), `AC-SRV-03` (subconjunto: 3.1 y 3.6-3.7
> parcial), `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md`.
> Primera de 4 features en que se partió `SRV-Sprint-3` (ROADMAP) — ver `memory/state.md`
> (2026-09-14). Construye sobre `SRV-002-auth-rbac` (`verified`).

## 1. Contexto del dominio
- Descubrir dispositivos BACnet en la red (Who-Is/I-Am vía BAC0), leer sus objetos, y
  persistir los puntos crudos como candidatos (`device_points_candidates`) — sin
  escritura, sin polling continuo, sin asociación explícita (feature posterior).
- Límites: BACnet/IP únicamente en este sprint (MSTP diferido). El Motor de Protocolos
  completo (lectura/escritura/polling de puntos *asociados*) no existe todavía — nace
  cuando llegue la feature de asociación explícita.

## 2. Alcance
### En alcance (propuesto)
- Tabla `devices` (mínima): id, nombre, protocolo (`bacnet`/`modbus`/`mqtt`, con
  `bacnet` como único valor usado en esta feature), dirección/instance number,
  `is_simulator BOOLEAN DEFAULT false` (columna ya presente para que Modbus/MQTT/
  Simuladores la reutilicen sin redisño, sin lógica que la use todavía).
- Tabla `device_points_candidates`: puntos crudos descubiertos, nunca promovidos a
  `points` automáticamente (`SRV-ADR-012`).
- Adaptador BACnet (BAC0): `scan()` — Who-Is broadcast, recibe I-Am, lee la lista de
  objetos de cada dispositivo respondiente, persiste dispositivo + candidatos.
- Endpoint(s) HTTP protegidos por RBAC (`SRV-002`) para disparar el escaneo y listar
  candidatos/dispositivos descubiertos.
- Detección de dispositivo sin respuesta durante el escaneo (marca/loguea, no bloquea
  el resto del escaneo).
- Verificación de integración real sin hardware: dos instancias BAC0 en la misma red
  local del test (una "dispositivo", otra escanea) — Who-Is/I-Am real por UDP, no
  mocks. No es el producto "Simuladores" (`SRV-ADR-014`, feature aparte) — es
  infraestructura de test de esta feature.
- RBAC: **Admin y Operador** pueden disparar un escaneo y ver candidatos/dispositivos
  (tarea de puesta en marcha/mantenimiento, no escritura crítica); Visor sin acceso.

### Fuera de alcance (decidido)
- Asociación explícita de puntos (`points`, `access_mode`, prioridad de escritura) —
  feature posterior, sobre este mismo modelo de candidatos.
- Escritura a dispositivos, polling continuo, `asyncio.Lock` por dispositivo
  (`VUL-SRV-005`) — sin operaciones concurrentes reales en esta feature (solo escaneo
  secuencial), se implementa cuando exista escritura/polling real.
- BACnet MSTP (puerto serial) — solo BACnet/IP en este sprint.
- Modbus, MQTT, Simuladores — features aparte (mismo grupo, orden a definir).
- Dashboard / UI de candidatos — esta feature es backend/contrato; la UI se
  especifica con `experto-ux-ui` cuando llegue el sprint de frontend correspondiente.

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `POST /devices/scan/bacnet` | entrada | REST | `hira-server/docs/openapi.yaml` (ampliar) |
| `GET /devices` | entrada | REST | ídem |
| `GET /devices/{id}/candidates` | entrada | REST | ídem |
| Red BACnet/IP | salida | adaptador BAC0 (Who-Is/I-Am, lectura de objetos) | interno, sin contrato externo |
| PostgreSQL (`devices`, `device_points_candidates`) | salida | repositorio de dominio (`Protocol`, mismo criterio que `UserRepositoryPort` de `SRV-002`) | interno |

**`devices`** (mínima, reutilizable por Modbus/MQTT/Simuladores):
`id`, `name`, `protocol` (`bacnet`/`modbus`/`mqtt` — solo `bacnet` usado aquí),
`address` (instance number + IP:puerto BACnet), `is_simulator BOOLEAN DEFAULT false`
(sin lógica que la use todavía), `last_seen_at` (actualizado en cada escaneo que lo
detecta), `created_at`, `updated_at`.

**`device_points_candidates`**: `id`, `device_id` (FK a `devices`), `object_type`
(tipo de objeto BACnet, p.ej. `analogInput`/`binaryOutput`), `object_instance`,
`object_name`, `present_value` (última lectura, nullable), `units` (si aplica,
nullable), `discovered_at`, `updated_at`. Único por `(device_id, object_type,
object_instance)` — un segundo escaneo actualiza, no duplica.

## 4. Criterios de aceptación (EARS)
> A partir de `AC-SRV-03.1`/`.6` (parcial), confirmado en la ronda de elicitación.

- **RF-001** — CUANDO Admin u Operador invoca `POST /devices/scan/bacnet`, el
  sistema DEBE emitir un Who-Is broadcast y esperar respuestas I-Am durante
  **3 segundos** antes de responder.
- **RF-002** — CUANDO el sistema recibe un I-Am durante el escaneo, DEBE leer la
  lista de objetos de ese dispositivo y persistir/actualizar un registro en
  `devices` (creándolo con `is_simulator=false` si no existe) y sus puntos crudos
  en `device_points_candidates` (actualiza `present_value`/`updated_at` si el
  candidato ya existía, no duplica).
- **RF-003** — SI un usuario con rol Visor invoca `POST /devices/scan/bacnet` o
  `GET /devices/{id}/candidates` ENTONCES el sistema DEBE responder 403.
- **RF-004** — CUANDO se invoca `GET /devices`, el sistema DEBE listar los
  dispositivos persistidos (protocolo, dirección, `is_simulator`, `last_seen_at`).
- **RF-005** — CUANDO se invoca `GET /devices/{id}/candidates`, el sistema DEBE
  listar los puntos crudos candidatos de ese dispositivo.
- **RF-006** — SI un dispositivo que respondió I-Am no responde a la lectura de
  objetos dentro de un timeout ENTONCES el sistema DEBE registrar el fallo (log)
  y continuar el escaneo con los demás dispositivos, sin abortar todo el proceso.
- **RF-007** — El sistema NUNCA DEBE promover automáticamente un candidato a una
  tabla de puntos operables (`SRV-ADR-012`) — vive en `device_points_candidates`
  hasta que exista la feature de asociación explícita.

## 5. Casos límite y manejo de errores
- **RF-008** — SI no se recibe ningún I-Am dentro de la ventana de escaneo
  ENTONCES el sistema DEBE responder 200 con una lista vacía (no es un error).
- **RF-009** — SI `GET /devices/{id}/candidates` recibe un `id` que no existe
  ENTONCES el sistema DEBE responder 404.
- **RF-010** — El timeout de lectura de objetos por dispositivo (RF-006) DEBE ser
  de **2 segundos** — mismo criterio ya usado en `/health` de `SRV-001`/`HUB-001`.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| `SRV-Sprint-3` partido en 4 features; esta es la primera (BACnet) | Dominio heterogéneo y grande (3 protocolos + simuladores); cada feature verificable de forma independiente | Una sola feature para todo el sprint | — (`memory/state.md`, 2026-09-14) |
| Asociación explícita de puntos diferida a feature posterior | `AC-SRV-03` mezcla escaneo con asociación; `ROADMAP.md` ya los separaba en Sprint 3/4 | Incluir `access_mode`/prioridad/polling ya aquí | `SRV-ADR-012`, `SRV-ADR-019` |
| `devices` (mínima, con `is_simulator`) se crea en esta feature | El escaneo no tiene dónde persistir un dispositivo descubierto sin ella; evita rediseño cuando lleguen Modbus/MQTT/Simuladores | Diferir `devices` a una feature de modelo de datos aparte | `SRV-ADR-014` |
| `asyncio.Lock` por dispositivo (`VUL-SRV-005`) diferido | Sin escritura/polling concurrente en esta feature — el escaneo ya es secuencial; anticipar el lock sería Art. 10 | Implementar el lock ya, solo para el escaneo | `VUL-SRV-005` |
| Solo BACnet/IP, MSTP diferido | Requiere hardware serial real para verificar con evidencia genuina; sin caso de uso concreto todavía | Soportar IP + MSTP desde el inicio | — |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — `POST /devices/scan/bacnet` NO DEBE tardar significativamente más
  que la ventana configurada (3s) más el tiempo de lectura de objetos de los
  dispositivos que sí respondieron (2s de timeout cada uno, en paralelo si es
  posible).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-14).
