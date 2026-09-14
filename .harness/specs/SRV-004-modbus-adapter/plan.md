---
id: PLAN-SRV-004
tipo: plan
feature: SRV-004-modbus-adapter
estado: implemented
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# PLAN-SRV-004 · Adaptador Modbus — escaneo de rangos y candidatos

> El *cómo*. Traduce cada `RF-001..RF-008`/`RNF-001` de `spec.md` al patrón
> **Hexagonal** (Constitución Art. 1–2, `SRV-ADR-017`), construyendo sobre
> `SRV-003-bacnet-adapter` (`verified`): **reutiliza sin tocar**
> `core/security/dependencies.py::require_role`, `core/errors.py::
> ProblemDetailError` (+ `schemas/errors.py`, `E-ADR-003`), `core/ports/
> device_repository_port.py::DeviceRepositoryPort` (ya soporta cualquier
> `protocol`), `adapters/db/device_repository_adapter.py::
> PostgreSQLDeviceRepository` (ya persiste en `devices`/
> `device_points_candidates`, **sin migración nueva** — `protocol='modbus'`
> ya está en el `CHECK` de `models/device_model.py` desde `SRV-003`),
> `adapters/factory.py::get_device_repository_port()` (se usa tal cual) y
> `routers/devices.py` (`GET /devices`, `GET /devices/{id}/candidates` ya
> protocolo-agnósticos — **no se tocan**). Cuarta feature real de
> `hira-server/backend/`; segundo adaptador de protocolo de campo tras BACnet,
> primero **sin descubrimiento nativo** (`spec.md §1`).

## 0. Gates de simplicidad
- [x] **Simplicity** — 1 puerto nuevo (`ModbusTransportPort`), 0 tablas nuevas
      (reutiliza `devices`/`device_points_candidates`), 1 endpoint nuevo
      (`POST /devices/scan/modbus`). Lecturas **secuenciales** dentro de un
      escaneo (no `asyncio.gather` como BACnet) — ver Registro de decisiones,
      justificado por RNF-001 y por ser un único dispositivo físico (no N
      dispositivos independientes como en BACnet). Sin variables de entorno
      nuevas en `Settings` — host/puerto/unit_id vienen en el body de cada
      request, no hay nada que configurar al arranque (a diferencia de
      `bacnet_ip`/`bacnet_port`, que fijan la interfaz local del propio
      backend).
- [x] **Anti-Abstraction** — Un único método de puerto (`read_range`) cubre
      los 4 tipos de registro (mismo patrón de llamada Modbus, difiere solo
      en qué método de `pymodbus` se invoca) — no 4 métodos casi idénticos.
      Fallos de dirección (`ModbusReadFailure`) se modelan como **valor de
      retorno**, no como excepción — ver Registro de decisiones (difiere a
      propósito de `BacnetReadTimeoutError` de `SRV-003`, con justificación
      explícita). `present_value` sigue siendo `TEXT` sin tipar (ya decidido
      en `SRV-003-bacnet-adapter/plan.md`, sin reabrir esa decisión).
- [x] **Integration-First** — `hira-server/docs/openapi.yaml` se amplía
      **antes** que `routers/devices.py` (paso 4 de §6); `core/ports/
      modbus_transport_port.py` se define antes que `adapters/modbus/
      pymodbus_adapter.py`. La API real de `pymodbus==3.15.0` (cliente,
      servidor de test, excepciones) se **verificó con ejecución real** en
      esta fase (ver §5, nota de investigación) — no es una duda abierta
      para Fase 4, a diferencia de lo que `SRV-003-bacnet-adapter/plan.md`
      dejó pendiente para BAC0.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/device_scan_service.py` solo importa de `core/ports/` (`ModbusTransportPort`, `DeviceRepositoryPort` ya existente) + `core/errors.py`/`core/logger.py`/`core/modbus_address.py` (todos `core/`); `adapters/factory.py` inyecta `PymodbusAdapter`. Ningún router instancia un adaptador directamente (`SRV-ADR-017`, overlay `hira-server/CLAUDE.md`: "si un módulo de `services/` importa... `pymodbus`... viola la arquitectura"). |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo (`core/modbus_address.py`) sin mocks; coordinación (`services/device_scan_service.py::scan_modbus`) con dobles de `ModbusTransportPort`/`DeviceRepositoryPort`; adaptador `pymodbus` con **un servidor Modbus TCP real** (`pymodbus.server.ModbusTcpServer` + `pymodbus.simulator.SimDevice`/`SimData`) en localhost, con valores de prueba cargados en los 4 tipos de registro — sin mocks, sin hardware (`spec.md §2`); un segundo servidor TCP "silencioso" (`asyncio.start_server` crudo, sin responder) para el timeout real de 1s (RF-008); router con `TestClient`; sistema (e2e) con el servidor `pymodbus` real + Postgres real. |
| Art. 4 (persistencia) | `DeviceRepositoryPort` (`SRV-003`, ya `verified`) es el `StoragePort` de dominio para `devices`/`device_points_candidates` — esta feature no crea un puerto de persistencia nuevo, añade filas con `protocol='modbus'` al mismo esquema multi-protocolo (`CHECK (protocol IN ('bacnet','modbus','mqtt'))` ya lo permite). |
| Art. 5 (seguridad) | RBAC ya cubierto por `SRV-002`/reutilizado tal cual de `SRV-003` (`require_role("admin", "operador")`, RF-003). Modbus TCP estándar no lleva autenticación en el protocolo — `spec.md` no pide ninguna, no se inventa un requisito de seguridad ausente (Art. 10: no anticipar), mismo criterio que `SRV-003-bacnet-adapter/plan.md` con BACnet/IP. |
| Art. 6 (contratos/errores) | `POST /devices/scan/modbus` usa el sobre RFC 9457 solo donde hay error de negocio: 403 `insufficient-role` (reutilizado de `SRV-002`, vía `require_role`) y 400 `modbus-range-too-large` (slug **nuevo** de esta feature, RF-004). `type` = `https://hira.dev/errors/<slug>` (`E-ADR-003`, catálogo distribuido por `plan.md`, ya decidido). |
| Art. 10 (regla de raíz) | `ModbusTransportPort` nuevo (no forzar sus métodos en `BacnetTransportPort`, que es un contrato de un protocolo distinto con semántica de descubrimiento que Modbus no tiene) — mismo razonamiento ya aplicado 3 veces en el ecosistema (`DeviceRepositoryPort` vs. `DatabasePort`/`UserRepositoryPort` en `SRV-002`/`SRV-003`). |
| Art. 11 (documentación) | §8 de este plan — 1 fila, tarea `[doc]` en `tasks.md` (actualiza la nota de estado ya dejada por `SRV-003`, no crea una sección nueva). |

## Registro de decisiones de diseño (nuevas de este plan)
| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| `ModbusTransportPort` con **un solo método** (`read_range`) que cubre los 4 tipos de registro (`ModbusRegisterType`), no 4 métodos `read_coils`/`read_discrete_inputs`/`read_holding_registers`/`read_input_registers` | La única diferencia real entre los 4 tipos es qué método de `pymodbus` invoca el adaptador internamente (`client.read_coils` vs. `client.read_holding_registers`, etc.) — el contrato de dominio (leer un rango de un tipo dado, dirección por dirección) es idéntico en los 4 casos; 4 métodos casi idénticos en el `Protocol` sería duplicación especulativa (Anti-Abstraction, `plan.md §0`) | 4 métodos separados en el puerto, uno por tipo de registro |
| Fallos de dirección (`ModbusReadFailure`) modelados como **valor de retorno** de `read_range` (mezclado con `ModbusRegisterReading` en la misma lista), no como excepción (`raise`) | A diferencia de BACnet (`BacnetReadTimeoutError`, donde un dispositivo sin respuesta es la excepción — la mayoría de los I-Am recibidos sí responden a la lectura de objetos), en un escaneo de rango Modbus **la mayoría de las direcciones no responden** — es el caso normal esperado de "sondear un rango a ciegas" (`spec.md §1`: "el 'escaneo' es sondear ese rango, no descubrir la red"). Usar excepciones para el caso común de control de flujo es un antipatrón; un tipo de resultado (éxito/fallo) por dirección es más explícito y evita que `services/` tenga que envolver cada dirección individual en `try/except` (RF-001 exige leer *cada* dirección, no abortar en la primera que falle) | Una excepción `ModbusReadTimeoutError` por dirección, capturada una a una en `services/` (mismo patrón que BACnet) — viable pero fuerza 125×4 bloques `try/except` en el caso peor, y trata como "excepcional" lo que aquí es el resultado más común |
| `read_range` recibe `host`/`port`/`unit_id`/`register_type`/`start`/`count`/`timeout_seconds` y devuelve la lista completa de resultados de ese rango (una conexión TCP por llamada, reutilizada internamente para las `count` direcciones) | RNF-001 ("no debe tardar significativamente más que la suma de lecturas") se satisface de forma trivial con este diseño: como máximo 4 conexiones por escaneo (una por tipo de registro presente en la solicitud), cada una reutilizada para hasta 125 lecturas secuenciales — evita el costo de reconectar por cada una de las hasta 500 direcciones sin añadir la complejidad de exponer un objeto de "sesión"/"handle" de conexión a través del puerto | (a) `read_register` de una sola dirección, reconectando en cada llamada (hasta 500 conexiones/escaneo — overhead innecesario); (b) exponer un `ModbusConnectionHandle` opaco con `open()`/`close()` separados en el puerto — más flexible pero sin un caso de uso real que lo necesite (esta feature nunca reutiliza una conexión entre tipos de registro distintos, `spec.md §2`) |
| Las 4 lecturas de rango (una por tipo de registro presente en la solicitud) se ejecutan **secuencialmente** en `services/device_scan_service.py::scan_modbus`, no en paralelo (`asyncio.gather`, a diferencia de `scan_bacnet`) | BACnet paraleliza sobre **N dispositivos físicos independientes** (RNF-001 de `SRV-003` lo pedía explícitamente). Aquí las 4 lecturas apuntan al **mismo** dispositivo físico — muchos esclavos Modbus TCP embebidos (el tipo de hardware real que integra este producto) solo toleran una conexión TCP concurrente; abrir 4 conexiones simultáneas al mismo dispositivo es un riesgo real de fallo sin beneficio claro, y RNF-001 de *esta* feature no pide paralelismo, solo acota el tiempo total a la suma de las lecturas — que ya se cumple con ejecución secuencial (`plan.md §0`, Gate Simplicity) | `asyncio.gather` sobre las 4 lecturas de rango, mismo patrón que BACnet |
| Servidor Modbus TCP de prueba con `pymodbus.server.ModbusTcpServer` + `pymodbus.simulator.SimDevice`/`SimData` (API nueva de `pymodbus==3.15.0`) — **no** con `pymodbus.datastore.ModbusServerContext`/`ModbusDeviceContext`/`ModbusSequentialDataBlock` (API "clásica" de versiones anteriores, todavía documentada en tutoriales antiguos) | Verificado con ejecución real contra el código fuente de `pymodbus==3.15.0` (ver §5, nota de investigación): `ModbusServerContext.async_getValues()` con un `ModbusDeviceContext` clásico devuelve **incondicionalmente `ExcCodes.DEVICE_BUSY`** en esta versión — esa combinación está rota/vestigial en 3.15.0, solo `ModbusSimulatorContext` (compat antiguo) o `SimDevice`/`SimData` (API nueva, recomendada por la propia librería — `ModbusServerContext` emite `Log.warning("...deprecated and will be removed in v4...")`) funcionan de verdad. Usar la API clásica habría producido un servidor de test que siempre responde con una excepción Modbus, invalidando la verificación de RF-001/RF-002 (lectura exitosa) | `ModbusServerContext`/`ModbusDeviceContext`/`ModbusSequentialDataBlock` (API clásica, documentada en la mayoría de tutoriales de `pymodbus` pre-4.0, pero no funcional para lecturas reales en la versión pineada) |
| `retries=0` explícito al construir `AsyncModbusTcpClient` en el adaptador (`adapters/modbus/pymodbus_adapter.py`), además de `timeout=timeout_seconds` | Verificado con ejecución real (§5): con `retries=0`, una dirección sin respuesta lanza `ModbusIOException` a los **≈1.002s** exactos (medido, `timeout=1.0`). El valor por defecto de `pymodbus` es `retries=3`, que habría multiplicado el timeout real por cada dirección fallida (~4s en vez de 1s), violando RF-008 ("timeout de lectura por dirección DEBE ser de 1 segundo") | Dejar `retries` en su valor por defecto (3) — mediría ~4s por dirección sin respuesta en el peor caso, no 1s |
| `present_value` se serializa con `str(value)` tal cual lo devuelve `pymodbus` — `"True"`/`"False"` para coils/discrete inputs (`bool` de Python), el entero como texto para holding/input registers (`0`-`65535`) | `spec.md §3` no exige un formato específico ("`present_value` = valor leído"); mismo criterio de simplicidad que `SRV-003` con `present_value`/`units` sin tipar — no hay cálculo numérico sobre el candidato en esta feature (Art. 10: no anticipar un formato que nadie consume todavía) | Serializar a `"true"`/`"false"` en minúscula (más "JSON-like") — posible pero es una convención no pedida por el spec, se deja para cuando exista un consumidor real que la necesite |
| `core/modbus_address.py::format_modbus_address(host, port, unit_id) -> str` — función pura nueva, mismo patrón que `core/bacnet_address.py::format_device_address` de `SRV-003` | `spec.md §3` fija el formato `"<host>:<port>:<unit_id>"` como convención explícita — necesita una regla determinista y probada de forma aislada, igual razón que BACnet. Valida `host` no vacío, `1 <= port <= 65535`, `0 <= unit_id <= 255` (límite real de `pymodbus.simulator.SimDevice.id`, verificado en el código fuente — no un límite inventado) | Formatear el string ad-hoc dentro de `scan_modbus` (duplicaría la regla si otro consumidor la necesitara) |
| Sin función `parse_modbus_address` (inversa) | A diferencia de BACnet (`SRV-003` la incluyó como "inverso trivial, no anticipación"), aquí **ningún** consumidor de esta feature necesita descomponer la dirección — `GET /devices`/`GET /devices/{id}/candidates` no se tocan y no la usan. Añadirla sin un caso de uso real sería anticipación (Art. 10) | Incluirla "por si acaso", como en `SRV-003` |
| Validación del límite de 125 direcciones (RF-004) vive en `services/device_scan_service.py::scan_modbus`, no en un módulo `core/` dedicado ni en el schema Pydantic del router | Es una comparación de dominio de una sola línea por rango (`count > 125`) ligada a la semántica del protocolo Modbus (tamaño máximo de un mensaje), no a la forma del JSON de entrada — encaja como regla de coordinación junto al resto de la orquestación del escaneo, igual que `WHOIS_TIMEOUT_SECONDS`/`READ_TIMEOUT_SECONDS` de `SRV-003` viven como constantes de `services/`. `ProblemDetailError` (definida en `core/errors.py`) ya se lanza desde `core/security/dependencies.py` en el ecosistema — lanzarla desde `services/` (que también importa solo de `core/`) no viola `SRV-ADR-017` | Un `core/modbus_range.py` dedicado para una sola comparación (over-engineering); o validar en el schema Pydantic con `Field(le=125)` por rango — technically viable pero produce un 422 genérico de FastAPI, no el 400 con sobre RFC 9457 que RF-004 exige explícitamente |
| Respuesta de `POST /devices/scan/modbus` = `list[DeviceCandidateOut]` (reutilizado de `SRV-003`, sin schema nuevo) — **no** `list[DeviceOut]` como BACnet | RF-007 lo dice explícitamente: "responde 200 con una lista vacía **de candidatos nuevos**" — a diferencia de BACnet (que descubre N dispositivos y responde con la lista de dispositivos tocados), Modbus escanea **un solo** dispositivo ya conocido por el llamador (host/puerto/unit_id vienen en el request) — lo que aporta valor en la respuesta son los puntos descubiertos, no confirmar un dispositivo que el propio cliente ya especificó | `list[DeviceOut]` (mismo shape que BACnet) — no reflejaría lo que RF-007 pide verificar, y el cliente ya conoce el dispositivo que pidió escanear |
| `scan_modbus` vive en el **mismo módulo** `services/device_scan_service.py` que `scan_bacnet` (`SRV-003`), no en un archivo separado | Mismo dominio de coordinación ("escanear un dispositivo y persistir candidatos"), misma dependencia (`DeviceRepositoryPort`), mismo estilo de función async con puerto(s) inyectado(s) por parámetro — separarlo en `services/modbus_scan_service.py` sería duplicar el patrón sin una razón de dominio real (Anti-Abstraction); el archivo sigue siendo pequeño (2 funciones de escaneo + sus helpers privados) | `services/modbus_scan_service.py` separado — organización por protocolo en vez de por caso de uso, sin beneficio real dado que ambas funciones son estructuralmente análogas |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks
- **`core/modbus_address.py`** ← única regla de negocio pura de esta feature:
  `format_modbus_address(host: str, port: int, unit_id: int) -> str` (RF-002:
  construye `"<host>:<port>:<unit_id>"`, valida `host` no vacío,
  `1 <= port <= 65535`, `0 <= unit_id <= 255`, lanza `ValueError` si no).
- **`core/errors.py`** (ya existe, `SRV-002`) — reutilizado tal cual; esta
  feature añade un sitio de uso nuevo (`services/device_scan_service.py`) del
  slug **nuevo** `modbus-range-too-large` (400, RF-004) — ver §4.

### Coordinación (casos de uso / fronteras de entrada)
- **`services/device_scan_service.py`** (ya existe de `SRV-003`, se amplía
  con una segunda función de escaneo, mismo módulo — ver Registro de
  decisiones):
  - Constantes nuevas: `MODBUS_MAX_RANGE_ADDRESSES = 125` (RF-004),
    `MODBUS_READ_TIMEOUT_SECONDS = 1.0` (RF-008).
  - `scan_modbus(*, host: str, port: int, unit_id: int, ranges: dict[ModbusRegisterType, tuple[int, int]], transport: ModbusTransportPort, device_repo: DeviceRepositoryPort) -> list[DeviceCandidateRecord]` ← **RF-001, RF-002, RF-004, RF-005, RF-006, RF-007, RNF-001**:
    1. **RF-004** — por cada `(register_type, (start, count))` en `ranges`,
       si `count > MODBUS_MAX_RANGE_ADDRESSES`: `raise ProblemDetailError(400, ".../modbus-range-too-large", "Rango de registros demasiado grande", ...)` — **antes de cualquier lectura** (ni siquiera se construye `address` ni se toca `transport`/`device_repo`).
    2. `address = format_modbus_address(host, port, unit_id)` (`core/modbus_address.py`).
    3. `device: DeviceRecord | None = None` — **no** se crea todavía (RF-002:
       solo se persiste cuando al menos una dirección responde).
    4. Por cada `(register_type, (start, count))` en `ranges`, **secuencial**
       (RNF-001, ver Registro de decisiones):
       a. `results = await transport.read_range(host=host, port=port, unit_id=unit_id, register_type=register_type, start=start, count=count, timeout_seconds=MODBUS_READ_TIMEOUT_SECONDS)`.
       b. Por cada `result` en `results` (`RF-001` — recorre las `count`
          direcciones del rango, en orden):
          - Si `isinstance(result, ModbusReadFailure)`: `logger.warning(...)` (RF-005, incluye `register_type`/`address`/`reason`) y continúa con la siguiente dirección — **no aborta el rango ni el escaneo**.
          - Si `isinstance(result, ModbusRegisterReading)`: si `device is None`, `device = await device_repo.upsert_device(name=f"Modbus {address}", protocol="modbus", address=address, is_simulator=False)` (RF-002, solo la primera vez que responde algo en todo el escaneo); `candidate = await device_repo.upsert_candidate(device_id=device.id, object_type=result.register_type.value, object_instance=result.address, object_name=None, present_value=str(result.value), units=None)` (RF-002); `candidates.append(candidate)`.
    5. Retorna `candidates` — `[]` si ninguna dirección de ningún rango
       respondió (RF-007, 200 con lista vacía, no es un error; `device_repo`
       nunca se tocó en ese caso).
  - **RF-006** (nunca promover un candidato a tabla operable) se cumple por
    **omisión de diseño**, igual que `scan_bacnet`: `services/
    device_scan_service.py` no tiene ningún método que escriba en una tabla
    `points` (que no existe todavía) — verificado por inspección de imports
    del módulo en el test de coordinación.

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| Red Modbus TCP (lectura de coils/discrete inputs/holding registers/input registers) | Sondeo de rangos de registros de un dispositivo Modbus TCP | `adapters/modbus/pymodbus_adapter.py::PymodbusAdapter` implementa `ModbusTransportPort` con la librería `pymodbus` real (`requirements.txt`, versión pineada `pymodbus==3.15.0` — última disponible en PyPI al momento de este plan, instalada y verificada con ejecución real, ver §5) |
| PostgreSQL (`devices`, `device_points_candidates`) | Repositorio de dominio de dispositivos y candidatos | `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository` (`SRV-003`, **ya existe, sin cambios**) |

#### `core/ports/modbus_transport_port.py` (nuevo)
```python
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ModbusRegisterType(str, Enum):
    """Los 4 tipos de registro Modbus soportados (`spec.md §2`). El valor de
    cada miembro es el `object_type` persistido en `device_points_candidates`
    (`spec.md §3`)."""

    COIL = "coil"
    DISCRETE_INPUT = "discrete_input"
    HOLDING_REGISTER = "holding_register"
    INPUT_REGISTER = "input_register"


@dataclass(frozen=True)
class ModbusRegisterReading:
    """Una dirección que respondió dentro del timeout (RF-001, RF-002)."""

    register_type: ModbusRegisterType
    address: int
    value: bool | int  # bool para coil/discrete_input, int (0-65535) para holding/input registers


@dataclass(frozen=True)
class ModbusReadFailure:
    """Una dirección que no respondió — timeout o excepción Modbus (RF-005).

    No es una excepción de Python (`raise`): en un escaneo de rango, "no
    responde" es el resultado esperado para la mayoría de direcciones — se
    modela como dato, no como control de flujo (`plan.md §1`, Registro de
    decisiones)."""

    register_type: ModbusRegisterType
    address: int
    reason: str  # mensaje de diagnóstico, para el log de `services/`


class ModbusTransportPort(Protocol):
    async def read_range(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        register_type: ModbusRegisterType,
        start: int,
        count: int,
        timeout_seconds: float,
    ) -> list[ModbusRegisterReading | ModbusReadFailure]:
        """Abre una conexión TCP a `host:port` (una sola vez, reutilizada
        para las `count` direcciones de este rango — RNF-001) y lee, una
        dirección a la vez (RF-001; nunca en batch, para que una dirección
        fallida no aborte las demás), cada dirección de `start` a
        `start + count - 1` del `register_type` indicado, con `unit_id`
        como Modbus device id. Cada dirección se resuelve a
        `ModbusRegisterReading` (éxito) o `ModbusReadFailure` (timeout o
        excepción Modbus dentro de `timeout_seconds` — RF-005). La lista
        retornada tiene siempre `count` elementos, uno por dirección, en
        orden ascendente."""
        ...
```

### Adaptadores de entrada
- `routers/devices.py` (ya existe, `SRV-003`, se amplía con un endpoint
  nuevo — los 3 endpoints existentes **no se tocan**):
  - `POST /devices/scan/modbus` — `require_role("admin", "operador")` (RF-003,
    ya cubierto por la `dependencies=[Depends(require_role(...))]` del
    `APIRouter`, sin cambios); valida el body con
    `schemas/devices.py::ScanModbusRequest`; construye
    `ranges: dict[ModbusRegisterType, tuple[int, int]]` a partir de los
    campos opcionales presentes en el body (`coils`/`discrete_inputs`/
    `holding_registers`/`input_registers` — "un tipo sin rango no se
    escanea", `spec.md §3`); invoca
    `services/device_scan_service.py::scan_modbus` con
    `ModbusTransportPort`/`DeviceRepositoryPort` inyectados vía
    `Depends(adapters.factory.*)`; responde 200 con
    `list[DeviceCandidateOut]` (puede ser `[]`, RF-007). `ProblemDetailError`
    (400, RF-004) propaga sin captura explícita — el `exception_handler` ya
    registrado en `main.py` (`SRV-002`) la traduce a HTTP.
  - No instancia `PymodbusAdapter`/`PostgreSQLDeviceRepository` directamente
    (`SRV-ADR-017`).

### `adapters/factory.py` (se amplía)
- Nueva función `get_modbus_transport_port() -> ModbusTransportPort`: nace en
  el **mismo paso** en que nace el endpoint del router (paso 5 de §6), con un
  **doble in-memory** (`_PlaceholderModbusTransport`, `read_range` siempre
  retorna `count` `ModbusReadFailure` — sin `pymodbus` real) — mismo patrón
  ya aplicado 3 veces en este ecosistema (`SRV-001` Directiva de Pausa §7,
  `SRV-002` proactivo, `SRV-003` con `get_bacnet_transport_port()`):
  `PymodbusAdapter` real llega después (paso 6) sin cambiar la firma.
- Cacheada a nivel de módulo (singleton perezoso por proceso), mismo patrón
  que las 6 funciones ya existentes. `get_device_repository_port()` **no se
  toca** — se reutiliza tal cual.

## 3. Modelo de datos
**Sin migración nueva.** Reutiliza `devices`/`device_points_candidates`
(`hira-server/backend/models/device_model.py`, `alembic/versions/
0002_create_devices_tables.py`, ambas de `SRV-003-bacnet-adapter`, ya
`verified`). El `CHECK (protocol IN ('bacnet', 'modbus', 'mqtt'))` de
`devices` ya admite `'modbus'` desde que se escribió (`SRV-003` diseñó el
esquema como multi-protocolo desde el origen — ver `SRV-003-bacnet-adapter/
plan.md §3`). Esta feature solo añade **filas** con `protocol='modbus'`, sin
tocar `models/device_model.py`, `models/base.py` ni `alembic/env.py`.

`devices.address` para Modbus: `"<host>:<port>:<unit_id>"`
(`core/modbus_address.py::format_modbus_address`, §2) — mismo criterio de
columna combinada por protocolo que `"<instance_number>@<network_address>"`
de BACnet, formato propio, ambos caben en el mismo `VARCHAR(255)`.

`device_points_candidates` para Modbus: `object_type` ∈
`{coil, discrete_input, holding_register, input_register}` (RF-002/§3 de
`spec.md`, ya dentro del `VARCHAR(50)` existente, sin `CHECK` — igual que
BACnet, que tampoco restringe `object_type` con `CHECK`); `object_instance`
= dirección del registro (`INTEGER`, ya el tipo de la columna); `units` =
siempre `NULL` para Modbus (Modbus no expone unidades, `spec.md §3`).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-004-modbus-adapter/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** es `hira-server/docs/openapi.yaml` (se **amplía**, no se reemplaza — `/health`, `/auth/*`, `/devices/scan/bacnet`, `/devices`, `/devices/{id}/candidates` intactos) | `POST /devices/scan/modbus` | `gate/check.sh` bloque 5 (Spectral lint, mismo warn conocido de tooling ya aceptado en `SRV-001`/`SRV-002`/`SRV-003`) |

### Sobre de error — RFC 9457 (reutiliza `ProblemDetail`, `E-ADR-003`)
| Endpoint | HTTP | `type` (slug) | `title` | Cuándo |
|---|---|---|---|---|
| `POST /devices/scan/modbus` | 403 | `insufficient-role` | "Rol insuficiente" | Visor invoca el escaneo (RF-003) — slug reutilizado de `SRV-002`/`SRV-003`, no se redefine |
| `POST /devices/scan/modbus` | 400 | `modbus-range-too-large` | "Rango de registros demasiado grande" | Cualquier rango solicitado excede 125 direcciones (RF-004) — slug **nuevo** de esta feature |

`POST /devices/scan/modbus` no tiene una rama de error de negocio propia para
"ninguna dirección respondió" (RF-007: 0 candidatos es 200, no error).

### Esquemas nuevos (`hira-server/docs/openapi.yaml` — extracto)
```yaml
ModbusRegisterRange:
  type: object
  required: [start, count]
  additionalProperties: false
  properties:
    start:
      type: integer
      minimum: 0
    count:
      type: integer
      minimum: 1
      maximum: 125
      description: Máximo 125 direcciones por tipo de registro (RF-004).
ScanModbusRequest:
  type: object
  required: [host, port, unit_id]
  additionalProperties: false
  properties:
    host:
      type: string
      minLength: 1
    port:
      type: integer
      minimum: 1
      maximum: 65535
    unit_id:
      type: integer
      minimum: 0
      maximum: 255
    coils:
      $ref: "#/components/schemas/ModbusRegisterRange"
      nullable: true
    discrete_inputs:
      $ref: "#/components/schemas/ModbusRegisterRange"
      nullable: true
    holding_registers:
      $ref: "#/components/schemas/ModbusRegisterRange"
      nullable: true
    input_registers:
      $ref: "#/components/schemas/ModbusRegisterRange"
      nullable: true
```
`POST /devices/scan/modbus` → `200: DeviceCandidateOut[]` (reutilizado de
`SRV-003`, puede ser `[]`, RF-007) | `400: ProblemDetail` (RF-004) |
`403: ProblemDetail` (RF-003). El `maximum: 125` del schema es una
validación de **forma** adicional (defensa en profundidad, produce un 422 de
FastAPI antes de llegar al servicio) — la validación de **negocio** que
exige RF-004 (400 con sobre RFC 9457) la hace `scan_modbus` explícitamente
(§2), no se depende únicamente del schema.

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`core/modbus_address.py`) | `format_modbus_address` construye `"<host>:<port>:<unit_id>"`; rechaza `host` vacío, `port` fuera de `[1, 65535]`, `unit_id` fuera de `[0, 255]` | unit puro, **sin mocks** — RF-002 |
| Coordinación (`services/device_scan_service.py::scan_modbus`) | *Camino feliz*: 2 tipos de registro con valores → 1 `upsert_device` (la primera vez que algo responde) + N `upsert_candidate`, retorna N candidatos (RF-001, RF-002); *rango > 125*: `ProblemDetailError(400)` **antes** de invocar `transport`/`device_repo` (verificado con un doble que falla el test si se llama, RF-004); *ninguna dirección responde*: `[]`, `device_repo.upsert_device` nunca invocado (RF-007); *fallo parcial*: mezcla de `ModbusRegisterReading`/`ModbusReadFailure` en la misma lista → las direcciones fallidas se loguean y se omiten, las exitosas se persisten igual (RF-005); *RF-006*: ningún método de `services/device_scan_service.py` escribe en una tabla de puntos operables — verificado por inspección de imports (igual criterio que `scan_bacnet`) | unit + dobles (`Protocol` fakes) de `ModbusTransportPort`/`DeviceRepositoryPort` |
| Adaptador `pymodbus` (`adapters/modbus/pymodbus_adapter.py`) — **verificación de integración real sin hardware** | (a) *Camino feliz*: `pymodbus.server.ModbusTcpServer` real en `127.0.0.1:<puerto>` con `pymodbus.simulator.SimDevice(id=<unit_id>, simdata=(<coils>, <discrete>, <holding>, <input>))` (4 bloques independientes, `SimData` por tipo) — `read_range` para cada uno de los 4 tipos devuelve los valores exactos cargados (RF-001, RF-002); (b) *dirección fuera de rango* y *unit_id incorrecto*: ambos devuelven `ExceptionResponse` real (`isError() == True`) del servidor `pymodbus` → `ModbusReadFailure` (RF-005, rama "excepción Modbus"); (c) *timeout real*: un segundo servidor TCP "silencioso" (`asyncio.start_server` crudo, acepta la conexión y nunca responde) → `ModbusIOException` real a **≈1.0s** (`retries=0`, RF-005 rama "timeout"/RF-008, medido) | integración — servidor `pymodbus` real + servidor TCP crudo, **no es el producto "Simuladores"** (`SRV-ADR-014`), es infraestructura de test de esta feature |
| Adaptador de repositorio (`PostgreSQLDeviceRepository`, `SRV-003`) | **Sin test nuevo** — el contrato ya está verificado (`tests/integration/test_device_repository_adapter.py`, `SRV-003`); esta feature solo ejercita `upsert_device`/`upsert_candidate` con `protocol='modbus'`, ya cubierto por el `CHECK` genérico del esquema, sin comportamiento nuevo que probar en el adaptador | — (reutilizado) |
| Router (`routers/devices.py`) | Contrato exacto de `openapi.yaml` (`TestClient`, con `ModbusTransportPort`/`DeviceRepositoryPort` in-memory del placeholder de `factory.py`) — 200 con lista de candidatos (vacía y no vacía), 400 `modbus-range-too-large` con *shape* RFC 9457 exacto, 403 con Visor (reutiliza `require_role` ya verificado) | unit + `TestClient`, sin contenedores |
| Sistema (e2e) | `POST /devices/scan/modbus` real (`pymodbus` real + Postgres real) → `GET /devices` refleja el dispositivo Modbus (`protocol='modbus'`) → `GET /devices/{id}/candidates` refleja sus candidatos — recorrido completo con el servidor `pymodbus` real de la fila de adaptador de arriba, más el backend completo levantado | integración — contenedores reales del compose + servidor `pymodbus` real |

> **Nota de investigación (ejecutada en esta fase, con evidencia real —
> resuelve por adelantado lo que `SRV-003-bacnet-adapter/plan.md` dejó como
> "duda abierta para Gate 2" con BAC0):** se instaló `pymodbus==3.15.0` en un
> entorno aislado y se ejecutó un round-trip real cliente↔servidor en
> `127.0.0.1`. Hallazgos verificados con ejecución (no solo lectura de
> código):
> 1. `pymodbus.datastore.ModbusServerContext` combinado con
>    `ModbusDeviceContext` (API "clásica") está **roto** en 3.15.0:
>    `async_getValues()` devuelve incondicionalmente `ExcCodes.DEVICE_BUSY`
>    para esa combinación — confirmado leyendo el código fuente
>    (`pymodbus/datastore/context.py`). La API correcta y funcional en esta
>    versión es `pymodbus.simulator.SimDevice`/`SimData` (`ModbusTcpServer`
>    la acepta directamente como `context=`).
> 2. Round-trip real con `SimDevice(id=1, simdata=(coils, discrete, holding,
>    input))` (4 bloques independientes) + `AsyncModbusTcpClient`: los 4
>    `read_coils`/`read_discrete_inputs`/`read_holding_registers`/
>    `read_input_registers` devolvieron exactamente los valores cargados
>    (`.bits[0]`/`.registers[0]` para una lectura de `count=1`).
> 3. Una dirección fuera del rango configurado → `ExceptionResponse` real
>    (`isError() == True`), **no** una excepción Python ni un timeout.
> 4. Un `unit_id`/`device_id` no configurado en el `SimDevice` → también
>    `ExceptionResponse` real (`isError() == True`) — mismo tratamiento que
>    (3), sin caso especial en el adaptador.
> 5. Con `AsyncModbusTcpClient(..., timeout=1.0, retries=0)` contra un
>    servidor TCP que acepta la conexión pero nunca responde: `read_holding_registers(...)` lanzó `ModbusIOException` a los **1.002s**
>    medidos (`time.monotonic()`), confirmando que `retries=0` es
>    imprescindible para que el timeout real sea 1s y no ~4s (RF-008).
>
> Este plan no deja ninguna duda abierta de API de `pymodbus` para Fase 4 —
> a diferencia de `SRV-003`, que sí dejó pendiente el mapeo exacto de
> atributos de `BAC0.device(...).points` para un *spike* inicial.

## 6. Secuenciación de archivos (tests antes que código)
1. `tests/test_modbus_address.py` (falla) → `core/modbus_address.py` — RF-002.
2. `core/ports/modbus_transport_port.py` (`ModbusTransportPort`,
   `ModbusRegisterType`, `ModbusRegisterReading`, `ModbusReadFailure` —
   `Protocol`, sin test propio, igual que `bacnet_transport_port.py`/
   `device_repository_port.py`).
3. `tests/test_device_scan_service.py` (se amplía con los casos de
   `scan_modbus`, dobles de ambos puertos, falla) → `services/
   device_scan_service.py::scan_modbus` (+ `MODBUS_MAX_RANGE_ADDRESSES`,
   `MODBUS_READ_TIMEOUT_SECONDS`) — RF-001, RF-002, RF-004, RF-005, RF-006,
   RF-007, RNF-001.
4. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) —
   amplía con `POST /devices/scan/modbus` + `ScanModbusRequest`/
   `ModbusRegisterRange`, sin tocar los 5 endpoints existentes.
5. `tests/test_devices_router.py` (se amplía, `TestClient`, falla) →
   `routers/devices.py` (nuevo endpoint) + `schemas/devices.py`
   (`ScanModbusRequest`, `ModbusRangeIn`) +
   **`adapters/factory.py::get_modbus_transport_port()`** (nace aquí con
   placeholder in-memory — mismo patrón que `get_bacnet_transport_port()`
   de `SRV-003`: el router necesita el punto de inyección desde que existe)
   — RF-001, RF-003, RF-004, RF-007 vía HTTP con dobles in-memory.
6. `tests/integration/test_pymodbus_adapter.py` (falla, requiere el servidor
   `pymodbus` real + el servidor TCP "silencioso" — ver §5) →
   `adapters/modbus/pymodbus_adapter.py::PymodbusAdapter` +
   `pymodbus==3.15.0` en `requirements.txt` — reemplaza el **cuerpo** (no la
   firma) de `adapters/factory.py::get_modbus_transport_port()` — RF-001,
   RF-002, RF-005, RF-008 (reales).
7. `tests/integration/test_devices_scan_e2e.py` (se amplía — contenedores
   reales + servidor `pymodbus` real) — recorrido completo
   `POST /devices/scan/modbus` → `GET /devices` → `GET /devices/{id}/
   candidates` (RF-001, RF-002, RF-003, RF-004, RF-005, RF-007, RNF-001
   medido con evidencia real).
8. `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` — nota
   `[doc]` de §8, actualiza la ya existente de `SRV-003` (puede ejecutarse
   en paralelo desde el paso 1).
9. `hira-server/backend/adapters/modbus/README.md` (nuevo — carpeta nueva,
   regla de `hira-server/CLAUDE.md`: "cada carpeta que creas lleva su
   `README.md`"); `hira-server/backend/adapters/README.md` (ampliar, ya
   existe — añade la 7ª/8ª función de `factory.py` a su historial).

> `.harness/gate/services.txt` ya declara `hira-server/backend:python`
> (`SRV-001`) — sin cambios necesarios, la suite nueva se integra en la
> misma suite de `pytest`.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `ModbusReadFailure` como valor de retorno en vez de excepción — único puerto del ecosistema que no usa el patrón `raise <Algo>TimeoutError` ya establecido por `BacnetTransportPort` | Ver Registro de decisiones §1: en Modbus, "no responde" es el resultado más común de un escaneo por rango (a diferencia de BACnet, donde un dispositivo entero sin respuesta es la excepción tras un I-Am recibido) — modelarlo como excepción forzaría a `services/` a un `try/except` por cada una de hasta 500 direcciones para lo que es, estructuralmente, el caso esperado. No es una duplicación de patrón sin razón: es la traducción correcta de una semántica de dominio distinta a la de BACnet. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` | La nota de estado ya añadida por `SRV-003-bacnet-adapter` ("Implementado a la fecha: escaneo BACnet/IP... Modbus, MQTT, polling, escritura... siguen siendo diseño, no código") queda **desactualizada** en la parte de Modbus tras esta feature: el escaneo de rangos Modbus/TCP y la persistencia de candidatos pasan a ser código real. La tabla "Escaneo y descubrimiento" (fila Modbus: "Escaneo de rangos de registros configurables (pymodbus, TCP/RTU)") sigue siendo correcta tal como está escrita — esta feature la implementa (solo TCP, RTU queda fuera de alcance, ya declarado en `spec.md §2`) | `[doc]` editar la nota de estado (no crear una nueva): "Implementado a la fecha (`SRV-003-bacnet-adapter`, `SRV-004-modbus-adapter`): escaneo BACnet/IP (Who-Is/I-Am) y escaneo de rangos Modbus TCP (coils, discrete inputs, holding registers, input registers), ambos con persistencia de candidatos. MQTT, polling, escritura, `asyncio.Lock` por dispositivo, BACnet MSTP, Modbus RTU y Simuladores siguen siendo diseño, no código — ver `ROADMAP.md`/`.harness/specs/` para el estado real por sub-feature." |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es el
contrato de producto de esta frontera, ya cubierto en §4 (se amplía, no se
reemplaza).

`docs/hira-server/spec/validation/acceptance-criteria.md` **no** se toca:
`spec.md` de esta feature declara explícitamente que no hay un `AC-SRV-0X`
dedicado a Modbus (a diferencia de BACnet con `AC-SRV-03`) — "se construye
desde cero, siguiendo el mismo patrón ya `verified` en
`SRV-003-bacnet-adapter`" (`spec.md`, encabezado). Nada que quede obsoleto
ahí por este plan.

`docs/hira-server/spec/validation/vulnerabilities.md::VUL-SRV-005` **no** se
toca: sigue 🔴 Abierto — esta feature tampoco implementa escritura ni
polling concurrente sobre un dispositivo (mismo criterio que `SRV-003-bacnet-
adapter/plan.md §8`).

## 9. Implementación por requisito

### Implementación de RF-001
- `core/ports/modbus_transport_port.py::ModbusTransportPort.read_range`.
- `adapters/modbus/pymodbus_adapter.py::PymodbusAdapter.read_range` (lectura dirección por dirección, nunca en batch).
- `services/device_scan_service.py::scan_modbus` (itera cada tipo de registro presente en la solicitud, secuencial).
- `routers/devices.py::POST /devices/scan/modbus`.
- `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1modbus`.
- Tests: `tests/test_device_scan_service.py`, `tests/integration/test_pymodbus_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.
- `covers`: `hira-server/backend/core/ports/modbus_transport_port.py`, `hira-server/backend/adapters/modbus/pymodbus_adapter.py`, `hira-server/backend/services/device_scan_service.py`, `hira-server/backend/routers/devices.py`.

### Implementación de RF-002
- `core/modbus_address.py::format_modbus_address`.
- `core/ports/device_repository_port.py::DeviceRepositoryPort.upsert_device/upsert_candidate` (`SRV-003`, ya existente, sin cambios).
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.upsert_device/upsert_candidate` (`SRV-003`, ya existente, sin cambios).
- `services/device_scan_service.py::scan_modbus` (rama de éxito — `upsert_device` solo la primera vez que responde algo).
- Tests: `tests/test_modbus_address.py`, `tests/test_device_scan_service.py`, `tests/integration/test_pymodbus_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.
- `covers`: `hira-server/backend/core/modbus_address.py`.

### Implementación de RF-003
- `core/security/dependencies.py::require_role("admin", "operador")` — **reutilizado tal cual** de `SRV-002`, ya aplicado al `router` completo de `routers/devices.py` desde `SRV-003`, sin cambios.
- Tests: `tests/test_devices_router.py` (403 con Visor), `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-004
- `services/device_scan_service.py::scan_modbus` (`MODBUS_MAX_RANGE_ADDRESSES = 125`, validación antes de cualquier lectura).
- `core/errors.py::ProblemDetailError` (reutilizado) — slug `modbus-range-too-large` (400).
- `schemas/devices.py::ModbusRangeIn` (`Field(le=125)`, defensa en profundidad de forma).
- `hira-server/docs/openapi.yaml#/components/schemas/ModbusRegisterRange` (`maximum: 125`).
- Tests: `tests/test_device_scan_service.py` (rango > 125, sin tocar `transport`/`device_repo`), `tests/test_devices_router.py` (400 con *shape* RFC 9457).

### Implementación de RF-005
- `core/ports/modbus_transport_port.py::ModbusReadFailure`.
- `adapters/modbus/pymodbus_adapter.py::PymodbusAdapter.read_range` (captura `ModbusException`/`isError()` por dirección, retorna `ModbusReadFailure`, `retries=0`).
- `services/device_scan_service.py::scan_modbus` (`logger.warning` por cada `ModbusReadFailure`, continúa con la siguiente dirección/rango).
- Tests: `tests/test_device_scan_service.py` (fallo parcial con dobles), `tests/integration/test_pymodbus_adapter.py` (excepción Modbus real + timeout real).

### Implementación de RF-006
- Ausencia de diseño verificada: `services/device_scan_service.py` no importa ni referencia ninguna tabla/puerto de `points` (mismo criterio que `SRV-003`, módulo compartido).
- Tests: `tests/test_device_scan_service.py` (test explícito, inspección de imports del módulo — cubre `scan_bacnet` y `scan_modbus` a la vez).

### Implementación de RF-007
- `services/device_scan_service.py::scan_modbus` (retorna `[]` si ninguna dirección respondió en ningún rango, `device_repo` nunca tocado).
- `routers/devices.py::POST /devices/scan/modbus` (200 con lista vacía, no 4xx/5xx).
- Tests: `tests/test_device_scan_service.py`, `tests/test_devices_router.py`, `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-008
- `services/device_scan_service.py::MODBUS_READ_TIMEOUT_SECONDS = 1.0`.
- `adapters/modbus/pymodbus_adapter.py::PymodbusAdapter.read_range` (`AsyncModbusTcpClient(..., timeout=timeout_seconds, retries=0)` — `retries=0` imprescindible, ver §5 nota de investigación).
- Tests: `tests/integration/test_pymodbus_adapter.py` (mide el timeout real, ≈1.0s, evidencia de terminal pegada).

### Implementación de RNF-001
- `services/device_scan_service.py::scan_modbus` (ejecución secuencial por tipo de registro, una conexión TCP reutilizada por `read_range` para las `count` direcciones del rango — ver Registro de decisiones §1).
- Medición: `tests/integration/test_devices_scan_e2e.py` (duración total del escaneo con rangos conocidos, contra Postgres/`pymodbus` reales, evidencia de terminal pegada — Art. 3 "verificación real, nunca esperada").
