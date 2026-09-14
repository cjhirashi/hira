---
id: SPEC-SRV-004
tipo: spec
feature: SRV-004-modbus-adapter
estado: verified
anchor_commit: 089b1e0d59d455a0dd71ab769b6c1fd9a682ed2b
anchor_mode: strict
covers:
  - hira-server/backend/**
  - hira-server/docs/openapi.yaml
  - docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md
aprobaciones:
  fase_1: { por: "Carlos", fecha: 2026-09-14 }
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# SPEC-SRV-004 · Adaptador Modbus — escaneo y candidatos

> Producida en Fase 1 por elicitación interactiva (`method.md §3`). Base:
> `SRV-ADR-012` (escaneo + candidatos), `docs/hira-server/spec/modules/
> dispositivos-protocolos-puntos.md` ("Modbus: escaneo de rangos de registros
> configurables, pymodbus, TCP/RTU"). **Sin `AC-SRV-0X` dedicado** (a diferencia
> de BACnet con `AC-SRV-03`) — se construye desde cero, siguiendo el mismo patrón
> ya `verified` en `SRV-003-bacnet-adapter`. Segunda de 4 features en que se
> partió `SRV-Sprint-3` — ver `memory/state.md` (2026-09-14). Construye sobre
> `SRV-003-bacnet-adapter` (`verified`): reutiliza `devices`/
> `device_points_candidates` ya existentes, no las recrea.

## 1. Contexto del dominio
- Escanear un rango de registros Modbus configurable en un dispositivo (host:puerto
  + unit_id), y persistir los puntos crudos como candidatos — mismo modelo de
  `devices`/`device_points_candidates` ya creado en `SRV-003`, sin asociación
  explícita (feature posterior, igual que BACnet).
- Diferencia clave con BACnet: **Modbus no tiene descubrimiento nativo** (sin
  Who-Is). El integrador debe indicar host:puerto + unit_id + rango de
  direcciones a probar — el "escaneo" es sondear ese rango, no descubrir la red.

## 2. Alcance
### En alcance (decidido)
- Adaptador Modbus TCP (pymodbus): dado host+puerto+unit_id y, por cada uno de
  los **4 tipos de registro** (coils, discrete inputs, holding registers, input
  registers), un rango `start`/`count`, lee cada dirección del rango y persiste
  como candidato los registros que responden.
- Reutiliza `devices`/`device_points_candidates` de `SRV-003` — filas nuevas con
  `protocol='modbus'`. **`GET /devices` y `GET /devices/{id}/candidates` ya son
  protocolo-agnósticos (`SRV-003`) — no se tocan en esta feature**, solo se
  amplía con `POST /devices/scan/modbus`.
- `devices.address` para Modbus: `"<host>:<port>:<unit_id>"` (mismo criterio de
  columna combinada que BACnet, formato propio por protocolo).
- Verificación de integración real sin hardware: servidor Modbus TCP real de
  `pymodbus` (`pymodbus.server`) en el propio test, con registros de prueba
  cargados — TCP real, no mocks. No es el producto "Simuladores" (feature
  aparte) — es infraestructura de test de esta feature, mismo criterio que las
  2 instancias BAC0 de `SRV-003`.
- RBAC: Admin y Operador (mismo criterio que `SRV-003`), reutiliza
  `require_role` de `SRV-002`.
- Límite de rango: **máximo 125 direcciones por tipo de registro** por request
  (límite estándar de un mensaje Modbus) — un rango mayor se rechaza con 400.

### Fuera de alcance (decidido, mismo criterio que BACnet)
- Asociación explícita de puntos, escritura, polling continuo, lock por
  dispositivo — diferidos, igual que en `SRV-003`.
- Modbus RTU (serial) — solo TCP en este sprint, igual razón que MSTP en BACnet
  (requiere hardware serial real para verificar con evidencia genuina).
- Dashboard/UI — backend/contrato únicamente.

## 3. Modelo de datos y contratos de E/S
| Frontera | Dirección | Tipo | Contrato |
|---|---|---|---|
| `POST /devices/scan/modbus` | entrada | REST | `hira-server/docs/openapi.yaml` (ampliar) |
| `GET /devices`, `GET /devices/{id}/candidates` | entrada | REST | ya existen (`SRV-003`), sin cambios |
| Red Modbus TCP | salida | adaptador pymodbus | interno, sin contrato externo |
| PostgreSQL (`devices`, `device_points_candidates`) | salida | `DeviceRepositoryPort` (`SRV-003`, reutilizado) | interno |

**Request de `POST /devices/scan/modbus`**: `host`, `port`, `unit_id`, y un rango
`{start, count}` opcional por cada tipo de registro (`coils`, `discrete_inputs`,
`holding_registers`, `input_registers`) — un tipo sin rango no se escanea.

**Mapeo a `device_points_candidates`** (reutilizado de `SRV-003`, sin cambio de
esquema): `object_type` = uno de `coil`/`discrete_input`/`holding_register`/
`input_register`; `object_instance` = dirección del registro (string);
`present_value` = valor leído; `units` = `NULL` (Modbus no expone unidades).

## 4. Criterios de aceptación (EARS)
> Sin `AC-SRV-0X` previo — construidos desde cero, confirmados en la ronda de
> elicitación (2026-09-14), mismo patrón que `SRV-003`.

- **RF-001** — CUANDO Admin u Operador invoca `POST /devices/scan/modbus` con
  `host`/`port`/`unit_id` y al menos un rango por tipo de registro, el sistema
  DEBE leer cada dirección del rango especificado, por cada tipo indicado.
- **RF-002** — CUANDO una dirección responde con un valor, el sistema DEBE
  persistir/actualizar `devices` (`protocol='modbus'`, dirección
  `"<host>:<port>:<unit_id>"`, creándolo si no existe) y el candidato
  correspondiente en `device_points_candidates` (actualiza si ya existía, no
  duplica).
- **RF-003** — SI un usuario con rol Visor invoca `POST /devices/scan/modbus`
  ENTONCES el sistema DEBE responder 403.
- **RF-004** — SI el rango solicitado para cualquier tipo de registro excede
  **125 direcciones** ENTONCES el sistema DEBE rechazar la solicitud con 400,
  sin ejecutar ninguna lectura.
- **RF-005** — SI una dirección del rango no responde (timeout o excepción
  Modbus) ENTONCES el sistema DEBE registrar el fallo (log) y continuar con las
  demás direcciones del rango, sin abortar el resto del escaneo.
- **RF-006** — El sistema NUNCA DEBE promover automáticamente un candidato a
  una tabla de puntos operables (`SRV-ADR-012`) — mismo criterio que `SRV-003`.

## 5. Casos límite y manejo de errores
- **RF-007** — SI ninguna dirección del rango responde ENTONCES el sistema
  DEBE responder 200 con una lista vacía de candidatos nuevos (no es un error).
- **RF-008** — El timeout de lectura por dirección DEBE ser de **1 segundo**.

## 6. Registro de decisiones y descartes
| Decisión | Justificación | Alternativa descartada | ADR |
|---|---|---|---|
| Sin descubrimiento nativo — el usuario indica host/puerto/rango | Modbus no tiene un equivalente a Who-Is; es una limitación real del protocolo, no una decisión de producto | Intentar "descubrir" dispositivos Modbus en la red | — |
| Reutiliza `devices`/`device_points_candidates` de `SRV-003`, sin tabla nueva | Mismo modelo ya diseñado para ser multi-protocolo (`protocol` column); evita duplicar esquema | Tabla `modbus_points_candidates` separada | `SRV-003-bacnet-adapter/spec.md §3` |
| Solo Modbus TCP, RTU diferido | Igual razón que BACnet MSTP: requiere hardware serial real para verificar con evidencia genuina | Soportar TCP+RTU desde el inicio | — |
| Los 4 tipos de registro desde el inicio | `pymodbus` los soporta con el mismo esfuerzo (4 llamadas de lectura sobre el mismo cliente); acotar no simplifica la implementación | Solo holding/input registers | — |
| Límite de 125 direcciones por tipo de registro, rechazado con 400 | Límite estándar de un mensaje Modbus; pedir más exigiría lectura en bloques que esta feature no necesita | Sin límite explícito | — |
| Timeout de 1s por dirección (no 2s como BACnet) | Modbus TCP local es típicamente más rápido que BACnet/UDP broadcast | Reusar 2s por consistencia | — |
| `GET /devices`/`GET /devices/{id}/candidates` no se tocan | Ya son protocolo-agnósticos desde `SRV-003` (columna `protocol` en `devices`) | Crear endpoints específicos de Modbus | `SRV-003-bacnet-adapter` |

## 7. Requisitos no funcionales (RNF)
- **RNF-001** — `POST /devices/scan/modbus` NO DEBE tardar significativamente
  más que la suma de lecturas del rango solicitado (timeout 1s × direcciones
  que no respondan, mínimo para las que sí responden).

## Marcadores abiertos
- `[NEEDS CLARIFICATION] = 0`. Usuario confirmó "así es" (2026-09-14).
