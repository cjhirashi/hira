---
id: PLAN-SRV-006
tipo: plan
feature: SRV-006-simuladores
estado: verified
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-10-15
---

# PLAN-SRV-006 · Simuladores de dispositivos (BACnet, Modbus, MQTT)

> El *cómo*. Traduce cada `RF-001..RF-015`/`RNF-001` de `spec.md` al patrón
> **Hexagonal** (Constitución Art. 1–2, `SRV-ADR-017`), construyendo sobre
> `SRV-003-bacnet-adapter`/`SRV-004-modbus-adapter`/`SRV-005-mqtt-scanning`
> (las 3 `verified`): **reutiliza sin recrear** `core/security/dependencies.py::
> require_role`, `core/errors.py::ProblemDetailError` (+ `schemas/errors.py`,
> `E-ADR-003`), `core/ports/device_repository_port.py::DeviceRepositoryPort` +
> `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository`
> (**se amplía**, no se recrea — nuevo método de lectura + corrección de
> `upsert_device`, RF-008), y `adapters/factory.py` (mismo patrón de 8
> funciones ya existentes). Cuarta y última feature del grupo de protocolos;
> primera que **arranca procesos reales** en vez de solo hablar con ellos —
> `services/` gana un estado en memoria del proceso (`SimulatorRegistryService`,
> nuevo, **no es un puerto**, mismo criterio ya registrado en
> `services/rbac_service.py::LocalPermissionsCache`) para trackear qué está
> corriendo (`spec.md §3`, ya decidido: el estado "en ejecución" no vive en
> `devices`).

## 0. Gates de simplicidad
- [x] **Simplicity** — 3 puertos nuevos, uno por protocolo, cada uno con
      exactamente 2 métodos (`start`/`stop`) — el mínimo necesario para
      modelar "arrancar un proceso real, pararlo" (RF-001/002/003, RF-009).
      1 tabla nueva: **cero** (reutiliza `devices`/`device_points_candidates`).
      1 método nuevo en `DeviceRepositoryPort`
      (`get_device_by_address`, necesario para el chequeo de conflicto de
      RF-006/RF-007 **antes** de escribir — ver Registro de decisiones). 1
      corrección de causa raíz en `upsert_device` (RF-008). 1 servicio nuevo
      de estado en memoria (`SimulatorRegistryService`) con un único
      `asyncio.Lock` (no uno por dispositivo — ver Registro de decisiones).
      1 router nuevo (`routers/simulators.py`, justificado por RBAC mixto —
      ver Registro de decisiones). Sin variables de entorno nuevas
      obligatorias: `bacnet_simulator_port_range_start` es **opcional** con
      default (`47900`), mismo criterio que `bacnet_ip`/`bacnet_port`
      (`SRV-003`).
- [x] **Anti-Abstraction** — Cada puerto de simulador tiene exactamente
      `start()`/`stop()` — no se exponen `pause()`/`resume()`/`configure()`
      sin un caso de uso real que los pida (`spec.md` no los pide). El
      `token: str` opaco que retorna `start()` es la única forma de
      referenciar una instancia en ejecución — el puerto no expone el tipo
      concreto de la librería (`BAC0.lite()`, `ModbusTcpServer`,
      `mqtt.Client`) a `services/` (`SRV-ADR-017`). Un único `asyncio.Lock`
      global en `SimulatorRegistryService`, no uno por `device_id`/protocolo
      — arrancar/detener simuladores es una operación de administración de
      baja frecuencia (Admin, no el *hot path* de cada request como
      `LocalPermissionsCache`), serializarla por completo es la solución más
      simple que corrige la condición de carrera real (ver Registro de
      decisiones) sin la complejidad de locks granulares que ningún caso de
      uso actual requiere.
- [x] **Integration-First** — `hira-server/docs/openapi.yaml` se amplía
      **antes** que `routers/simulators.py` (paso 6 de §6); los 3 puertos de
      `core/ports/` se definen antes que sus adaptadores. El comportamiento
      real de las 3 librerías en **modo servidor/publicador** se verificó con
      **ejecución real** en esta fase (no se asumió nada, mismo estándar que
      `SRV-003`/`004`/`005`) — ver §5, nota de investigación: `BAC0.lite(...,
      deviceId=...)` como dispositivo BACnet/IP real que responde a Who-Is
      con un `device_instance` elegido y expone objetos leíbles por un
      cliente BACnet real; `pymodbus.simulator.SimData`/`SimDevice` +
      `ModbusTcpServer.serve_forever()` como tarea de fondo (ya usado como
      infraestructura de test en `SRV-004`, aquí se convierte en el
      **producto**); `paho-mqtt` publicando en un bucle `asyncio` periódico,
      sin bloquear el *event loop*, con validación síncrona de `topic`/
      `payload` en `client.publish()` (mismo patrón de `ValueError` síncrono
      ya verificado en `client.subscribe()` de `SRV-005`). Ninguna duda de
      API queda abierta para Fase 4.

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/simulator_service.py` y `services/simulator_registry_service.py` solo importan de `core/ports/` (`BacnetSimulatorPort`/`ModbusSimulatorPort`/`MqttPublisherPort` nuevos, `DeviceRepositoryPort` ampliado) + `core/bacnet_address.py`/`core/modbus_address.py`/`core/errors.py`/`core/logger.py` (todos `core/`); `adapters/factory.py` inyecta los 3 adaptadores reales. Ningún router instancia un adaptador directamente (`SRV-ADR-017`, overlay `hira-server/CLAUDE.md`). |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo (`core/bacnet_address.py::format_simulator_device_address`) sin mocks; `SimulatorRegistryService` sin mocks (estructura en memoria, prueba su propia serialización con 2 corutinas reales); coordinación (`services/simulator_service.py`) con dobles de los 3 puertos + `DeviceRepositoryPort`; los 3 adaptadores con la **librería real en modo servidor** (BAC0.lite() real, `ModbusTcpServer` real, `paho-mqtt` real contra Mosquitto real del compose) — verificados con un **cliente real** del mismo protocolo (mismo rigor que `SRV-003`/`004`/`005`, ahora el simulador es el producto bajo prueba, no infraestructura de test, `spec.md §1`); router con `TestClient` + dobles propios; sistema (e2e) con Postgres + Mosquitto reales. |
| Art. 4 (persistencia) | `DeviceRepositoryPort` (`SRV-003`, `verified`) sigue siendo el `StoragePort` de dominio — se **amplía** con `get_device_by_address` (lectura, RF-006/RF-007) y se **corrige** `upsert_device` (RF-008), sin tabla nueva. |
| Art. 5 (seguridad) | `POST`/`DELETE /simulators/*` → `require_role("admin")` (RF-004, "arranca procesos y listeners de red reales, más sensible que un escaneo de 3s de solo lectura", `spec.md §6`); `GET /simulators` → `require_role("admin", "operador")` (RF-005, mismo criterio que `GET /devices`). `MqttPublisherAdapter` se conecta **siempre** autenticado (`mqtt_user`/`mqtt_password`), mismo criterio que `MqttScanAdapter`/`MosquittoAdapter` (`VUL-SRV-001`, ya resuelto — esta feature refuerza el cierre, no lo reabre). |
| Art. 6 (contratos/errores) | 5 endpoints nuevos con sobre RFC 9457 donde hay error de negocio: 403 `insufficient-role` (reutilizado), 409 `simulator-address-conflict`/`simulator-already-running` (RF-006, slugs **nuevos**), 404 `simulator-not-running` (RF-012, slug **nuevo**), 400 `mqtt-invalid-publish` (RF-014, slug **nuevo** — distinto de `mqtt-invalid-topic-pattern` de `SRV-005`: valida `publish()`, no `subscribe()`), 400 `mqtt-invalid-interval` (RF-015, slug **nuevo**). `type` = `https://hira.dev/errors/<slug>` (`E-ADR-003`). |
| Art. 10 (regla de raíz) | RF-008 corrige `upsert_device` en el **adaptador/SQL** (causa raíz: `ON CONFLICT DO UPDATE` sobrescribía incondicionalmente `is_simulator`), no con un parche en `services/` que "vuelva a poner" el flag después. Los 3 puertos de simulador son **nuevos**, no forzados en `BacnetTransportPort`/`ModbusTransportPort`/`MqttScanTransportPort` (dominios y ciclos de vida de conexión distintos — cliente efímero de solo-lectura vs. servidor/publicador persistente hasta `DELETE`) — mismo razonamiento ya aplicado 2 veces en el ecosistema (`MqttScanAdapter` vs. `MosquittoAdapter`, `plan.md` de `SRV-005`). |
| Art. 11 (documentación) | §8 de este plan — 1 fila, tarea `[doc]` (cierra la nota de estado de `dispositivos-protocolos-puntos.md` que desde `SRV-003` dice "Simuladores... siguen siendo diseño, no código"). |

## Registro de decisiones de diseño (nuevas de este plan)

| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| **3 puertos nuevos por protocolo** (`BacnetSimulatorPort`, `ModbusSimulatorPort`, `MqttPublisherPort`), **no** se reutilizan/amplían `BacnetTransportPort`/`ModbusTransportPort`/`MqttScanTransportPort` | Verificado con ejecución real (§5): un simulador BACnet es una instancia **`BAC0.lite(deviceId=...)`** independiente (rol de *servidor*, responde a Who-Is) — el `BAC0Adapter` existente es un **cliente** (`who_is`/`read_device_objects`, rol *cliente*, ephemeral por escaneo). Mismo caso con `pymodbus` (`AsyncModbusTcpClient` cliente vs. `ModbusTcpServer` servidor — APIs de la librería completamente distintas) y `paho-mqtt` (`MqttScanAdapter` suscribe+acumula en una ventana de 3s y desconecta; el publicador vive hasta `DELETE`, ciclo de vida indefinido). Forzar ambos roles en un solo `Protocol` obligaría a métodos opcionales/no usados en un lado (Anti-Abstraction). Mismo criterio ya cerrado 2 veces en este ecosistema: `MqttScanAdapter` vs. `MosquittoAdapter` (`SRV-005/plan.md §1`) | Ampliar `BacnetTransportPort` con `start_simulator()`/`stop_simulator()` — mezclaría un contrato de *cliente de solo lectura* con uno de *servidor con estado persistente*, forzando a cualquier implementación futura de `BacnetTransportPort` (p. ej. un doble de test) a soportar ambos roles |
| Cada puerto de simulador retorna un **token opaco (`str`)** en `start()`, recibido de vuelta en `stop(token)` — no expone el objeto concreto de la librería (`BAC0.lite()`, `ModbusTcpServer`, `mqtt.Client`) a `services/` | `SRV-ADR-017`: `services/` no puede depender de un tipo de `BAC0`/`pymodbus`/`paho-mqtt`. El adaptador mantiene internamente `dict[token, instancia_real]` — el mismo patrón ya usado implícitamente por `PostgreSQLDeviceRepository` (mantiene su propio `AsyncEngine`, expone solo `DeviceRecord`) | Retornar el `device_id` como identificador y que el adaptador mantenga `dict[device_id, instancia]` — descartado: acoplaría el adaptador a la noción de `device_id` (concepto de `DeviceRepositoryPort`, otro puerto), cuando el adaptador no necesita saber nada de `devices`; el token opaco mantiene los puertos desacoplados entre sí |
| **Identidad del simulador BACnet = `device_instance` puro** (`core/bacnet_address.py::format_simulator_device_address(device_instance) -> str`, retorna `str(device_instance)`, validado `0 <= device_instance <= 4194303`) — **no** el formato `"<instance>@<network_address>"` de `format_device_address` (`SRV-003`, dispositivos reales) | RF-007 exige que reanudar el **mismo** simulador tras un reinicio reutilice el mismo `device_id` — el lookup por identidad debe ser **calculable solo a partir del cuerpo del request** (`device_instance`), sin conocer de antemano en qué puerto UDP local corrió la instancia anterior (el puerto se asigna de nuevo, fresco, en cada arranque — ver siguiente fila). Si la identidad incluyera el puerto, un reinicio nunca podría recomputar la misma dirección para encontrar la fila existente. Es coherente con el propio protocolo BACnet: un integrador real descubre dispositivos por Who-Is/I-Am (por `device_instance`), no por IP:puerto memorizado — el propio `BacnetTransportPort.who_is()` ya re-resuelve `network_address` en cada llamada, nunca lo cachea como identidad permanente | Reusar `format_device_address(device_instance, f"{ip}:{port}")` con el mismo formato que dispositivos reales — se descartó tras verificar que rompía RF-007 (un reinicio produciría una dirección nueva, `upsert_device` crearía una fila **duplicada** en vez de reanudar la existente) |
| El puerto UDP local que ocupa cada instancia `BAC0.lite()` simulada se **asigna de forma efímera** en cada `start()` (contador incremental desde `Settings.bacnet_simulator_port_range_start`, default `47900`, liberado en `stop()`), **no** se persiste ni se deriva de `device_instance` | Consecuencia directa de la fila anterior: si la identidad ya es restart-safe por sí sola (`device_instance` puro), el puerto de transporte puede ser efímero sin comprometer RF-007 — simplifica el adaptador (sin necesidad de una tabla de reserva de puertos) y evita colisión con el puerto ya ocupado por el `BAC0Adapter` cliente existente (`get_bacnet_transport_port()`, `settings.bacnet_port`) | Un puerto fijo por `device_instance` (p. ej. `47900 + device_instance % N`) — descartado: riesgo de colisión entre 2 `device_instance` distintos mapeados al mismo puerto módulo N, sin beneficio real (nada depende de que el puerto sea estable entre reinicios, ver fila anterior) |
| **Consecuencia aceptada**: un escaneo real posterior (`POST /devices/scan/bacnet`) que descubra el simulador en su `network_address` real (`"<instance>@<ip real>:<puerto efímero>"`) creará/actualizará una fila **distinta** en `devices` a la del simulador (`"<instance>"`, sin `@`) — no colisionan en `(protocol, address)`, así que RF-008 no se dispara para *esta* combinación específica en BACnet (sí se sigue disparando, y sigue siendo necesaria, para Modbus/MQTT, donde la identidad del simulador y la dirección que produce el escaneo **sí** son el mismo string — ver filas de abajo) | Documentado explícitamente para Gate 2 — es una consecuencia de diseño no trivial de la decisión de identidad restart-safe de arriba, no un descuido. `spec.md §2` ya declara que el escaneo posterior es **opcional**, "no es requisito" ver el simulador en `GET /devices` sin él — el simulador ya aparece por su propio registro inmediato (RF-001..003); el escaneo adicional simplemente añadiría una segunda fila (real, con `is_simulator=false` en su fila propia — correcto, porque *esa fila* en efecto describe lo que un escaneo real vería en la red, no el simulador administrado) | Forzar que el escaneo y el registro del simulador coincidan en una sola fila para BACnet — exigiría exponer el puerto UDP efímero al llamador del escaneo o volver el puerto determinista (ambas descartadas arriba) |
| **Identidad del simulador Modbus = `format_modbus_address(host, port, unit_id)`** (`core/modbus_address.py`, `SRV-004`, **reutilizada tal cual, sin cambios**) | A diferencia de BACnet, `host`/`port` los especifica el propio Admin en el body (RF-002) — no hay puerto efímero que asignar, la dirección ya es 100 % restart-safe y **coincide exactamente** con la que produciría un escaneo real (`scan_modbus`, `SRV-004`) sobre la misma dirección — aquí sí se ejercita el fix de RF-008 en la práctica | — (reutilización directa, sin alternativa a evaluar) |
| **Identidad del simulador MQTT = el propio `topic`** (concreto, sin wildcard — `spec.md §3`, ya decidido) | Coincide con el campo `address` que ya usa `scan_mqtt` (`SRV-005`, `address=topic_pattern`) — si un escaneo con un patrón sin wildcard coincide exactamente con el topic del simulador, el fix de RF-008 aplica igual que en Modbus | — |
| `get_device_by_address(protocol, address) -> DeviceRecord | None` — método **nuevo** en `DeviceRepositoryPort` (contrato ampliado, no un adaptador parcheado, Art. 10) | RF-006 exige rechazar con 409 **sin escribir nada** si la dirección ya es un dispositivo real o un simulador en ejecución — eso requiere una **lectura** previa a cualquier `upsert_device`; `upsert_device` (una escritura con `ON CONFLICT DO UPDATE`) no puede servir como "find-or-reject" sin el riesgo de escribir primero y decidir después (ventana insegura: un `upsert_device` con `is_simulator=true` sobre una fila real, incluso corregido por el fix de RF-008 — que solo protege *cuando ya es simulador*, no evita marcar como simulador algo que **era** real) | Usar `list_devices()` y filtrar en `services/` — descartado: trae **todas** las filas a memoria por cada arranque de simulador, sin índice, cuando ya existe el índice único `(protocol, address)` que hace la consulta puntual trivial |
| `upsert_device` — el `ON CONFLICT DO UPDATE` ahora fija `is_simulator = devices_table.c.is_simulator OR excluded.is_simulator` (antes: `is_simulator = excluded.is_simulator`, sobrescritura incondicional) | RF-008, causa raíz: una vez que una fila es simulador, **debe seguir siéndolo para siempre** salvo un mecanismo explícito de "des-flag" que esta feature no construye (`spec.md §2`/§6, `AC-SRV-05.5` diferido) — el `OR` booleano en SQL es exactamente esa regla ("una vez `true`, siempre `true`"), aplicada de forma atómica en la misma sentencia, sin *round-trip* de lectura previa. Corrige tanto el camino nuevo de esta feature (aunque, por diseño, `services/simulator_service.py` ya rechaza antes de llegar aquí vía `get_device_by_address`, ver fila de arriba) como, sobre todo, el camino **ya existente** de `scan_bacnet`/`scan_modbus`/`scan_mqtt` (`SRV-003`/`004`/`005`, que siempre pasan `is_simulator=False` literal) | Leer el estado actual antes de cada `upsert_device` y decidir en Python qué `is_simulator` enviar — descartado: reintroduce la ventana de carrera que el propio `INSERT ... ON CONFLICT` evita por diseño (atomicidad de una sola sentencia SQL, mismo criterio ya usado por el resto de `upsert_device`/`upsert_candidate`) |
| `SimulatorRegistryService` — estado en memoria del proceso, **no es un puerto** (mismo criterio ya registrado en `services/rbac_service.py::LocalPermissionsCache`, `SRV-002`) | `spec.md §3`, ya decidido en Fase 1: el estado "en ejecución" vive en memoria del proceso de Hira Server, no en `devices` — no hay ningún sistema externo que este objeto hable, es una estructura de datos (`dict[device_id, RunningSimulator]`) interna. Vive en su propio archivo (`services/simulator_registry_service.py`, no inline en `simulator_service.py` como hace `rbac_service.py` con su caché) porque aquí **3** funciones de arranque (una por protocolo) más `stop`/`list` convergen sobre el **mismo** registro — separarlo aclara que es un componente compartido, no propiedad de una sola función | Definir `SimulatorRegistryService` dentro de `simulator_service.py` (mismo archivo, como `LocalPermissionsCache` en `rbac_service.py`) — válido también, pero con 3 protocolos convergiendo se prefirió el archivo propio por claridad, sin que esto cambie el criterio "no es un puerto" |
| **Un único `asyncio.Lock`** en `SimulatorRegistryService` (no uno por `device_id`/protocolo), que envuelve la sección crítica completa "verificar conflicto (RF-006) → arrancar el proceso real → registrar" en `services/simulator_service.py` — no solo la mutación del `dict` | Sin el lock, 2 requests concurrentes para la **misma identidad** podrían pasar ambos la verificación de `get_device_by_address`/`is_running` antes de que cualquiera registre en el `dict`, arrancando **2 procesos reales duplicados** (mismo `device_instance`/`host:port` escuchando dos veces — el segundo `BAC0.lite()`/`ModbusTcpServer` fallaría al bindear el mismo puerto, o el simulador MQTT publicaría duplicado). Mantener el lock durante los `await` de arranque **no** viola RNF-001: no bloquea el *event loop* (otras rutas siguen respondiendo), solo serializa entre sí las llamadas a `start_*_simulator`/`stop_simulator` — una operación de administración de baja frecuencia, no el *hot path* de cada request (a diferencia de `LocalPermissionsCache`, que si tuviera un lock global sí degradaría RNF-001 de `SRV-002`) | Lock por `device_id` (`dict[device_id, asyncio.Lock]`) — más "escalable" en teoría, pero el `device_id` de una identidad **nueva** todavía no existe cuando se necesita el lock (la condición de carrera es justo sobre "¿esta identidad ya tiene un `device_id`?") — requeriría una segunda estructura de locks por *identidad de request* (`protocol+address`) antes de saber el `device_id`, complejidad sin beneficio real dado el volumen de esta operación |
| `routers/simulators.py` — router **nuevo**, separado de `routers/devices.py` | `routers/devices.py` aplica `require_role("admin", "operador")` a **nivel de router** (`dependencies=[Depends(...)]` del `APIRouter`, uniforme en sus 5 rutas) — esta feature necesita **RBAC mixto** (`POST`/`DELETE` solo Admin, `GET` Admin+Operador, RF-004/RF-005), que un único router-level `dependencies=` no puede expresar sin duplicar la verificación por ruta de forma confusa. Separar el router también refleja la separación de dominio de `spec.md §1`: gestión de **ciclo de vida** de simuladores vs. **escaneo/listado** de dispositivos — aunque ambos comparten `DeviceRepositoryPort` | Añadir las 5 rutas a `routers/devices.py` con `dependencies=[Depends(require_role("admin"))]` explícito por ruta además del `require_role("admin","operador")` de nivel de router — técnicamente funciona (ambas dependencias corren, el resultado es el más restrictivo) pero mezcla 2 políticas RBAC distintas en un único archivo/router, menos claro para quien lo lea después |
| Objetos BACnet soportados en `POST /simulators/bacnet`: `object_type` restringido a un `Literal` de 6 valores (`analog-value`, `analog-input`, `analog-output`, `binary-value`, `binary-input`, `binary-output`) en `schemas/simulators.py` — rechazo 422 estándar de Pydantic/FastAPI para cualquier otro valor, **no** un 400 RFC 9457 | `spec.md` no define una rama de error de negocio para "tipo de objeto no soportado" (a diferencia de RF-014/RF-015, que sí son RF explícitos) — restringir a nivel de schema (Contract-First: el `enum` queda documentado en `openapi.yaml`) es la validación más simple que existe hoy sin inventar un RF nuevo (Art. 10). Los 6 tipos son los que `bacpypes3.local.{analog,binary}` exponen como objetos "locales" (escribibles en memoria, ya usados por el helper de test de `SRV-003`, `tests/integration/test_bac0_adapter.py`) — `multistate`/`schedule`/etc. quedan fuera, sin evidencia de necesidad (Art. 10) | Aceptar cualquier string y fallar en tiempo de ejecución dentro del adaptador con una excepción no controlada (500) — descartado: peor experiencia para el llamador sin necesidad, cuando FastAPI ya ofrece 422 estructurado gratis vía `Literal` |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks
- **`core/bacnet_address.py`** (ya existe, `SRV-003`, **se amplía, no se
  modifica lo existente**): función nueva
  `format_simulator_device_address(device_instance: int) -> str` — retorna
  `str(device_instance)`; lanza `ValueError` si `device_instance` está fuera
  de `[0, 4194303]` (rango real de *instance number* BACnet). RF-001,
  RF-007 (ver Registro de decisiones).
- **`core/modbus_address.py`**, **`core/errors.py`** (ya existen,
  reutilizados tal cual — Modbus/MQTT no necesitan una función de identidad
  nueva, ver Registro de decisiones).

### Coordinación (casos de uso / fronteras de entrada)
- **`services/simulator_registry_service.py`** (nuevo — estado en memoria,
  no es un puerto, ver Registro de decisiones):
  - `RunningSimulator` (`@dataclass(frozen=True)`): `device_id`, `protocol`,
    `address`, `token`, `started_at` — RF-010.
  - `SimulatorRegistryService`: `dict[device_id, RunningSimulator]` +
    `asyncio.Lock` público (`self.lock`, usado por
    `services/simulator_service.py` para la sección crítica completa, ver
    Registro de decisiones); métodos síncronos `get`/`is_running`/
    `register`/`unregister`/`list_running` (sin `await` propio — las
    mutaciones del `dict` no necesitan ser `async`, el `Lock` protege la
    *secuencia* de operaciones de quien lo usa, no cada método individual).
  - `get_simulator_registry()` — *singleton* de módulo (`_default_registry`),
    inyectado vía `Depends()` en `routers/simulators.py` (mismo mecanismo
    de FastAPI que los puertos reales de `adapters/factory.py`, aunque este
    objeto vive en `services/`, no en `adapters/` — no es infraestructura
    intercambiable).
- **`services/simulator_service.py`** (nuevo):
  - `start_bacnet_simulator(*, device_instance, objects, transport, device_repo, registry) -> RunningSimulator` — **RF-001, RF-006, RF-007, RNF-001**:
    1. `address = format_simulator_device_address(device_instance)`.
    2. `async with registry.lock:`
    3. `existing = await device_repo.get_device_by_address("bacnet", address)`.
    4. Si `existing` no es `None` y `not existing.is_simulator`:
       `raise ProblemDetailError(409, .../simulator-address-conflict, ...)` — **RF-006**.
    5. Si `existing` no es `None` y `registry.is_running(existing.id)`:
       `raise ProblemDetailError(409, .../simulator-already-running, ...)` — **RF-006**.
    6. `token = await transport.start(device_instance=device_instance, objects=objects)` — **RF-001** (arranca la instancia real; sin validación de negocio adicional que capturar aquí, a diferencia de MQTT).
    7. `try:` `device = await device_repo.upsert_device(name=f"Simulador BACnet {device_instance}", protocol="bacnet", address=address, is_simulator=True)`; por cada `obj` en `objects`: `await device_repo.upsert_candidate(device_id=device.id, object_type=obj.object_type, object_instance=obj.object_instance, object_name=None, present_value=obj.present_value, units=None)` — **RF-001** (crea o, en el camino de reanudación, refresca la fila ya existente — **RF-007**). `except Exception: await transport.stop(token); raise` — limpieza defensiva: si la persistencia falla tras arrancar el proceso real, no deja un simulador huérfano sin forma de detenerlo vía la API (ver nota de resiliencia, §7).
    8. `entry = RunningSimulator(device_id=device.id, protocol="bacnet", address=address, token=token, started_at=utcnow())`; `registry.register(entry)`; `return entry`.
  - `start_modbus_simulator(*, host, port, unit_id, registers, transport, device_repo, registry) -> RunningSimulator` — **RF-002, RF-006, RF-007, RNF-001**: misma estructura; `address = format_modbus_address(host, port, unit_id)` (`SRV-004`, reutilizada); `device_repo.upsert_candidate` por cada `ModbusSimulatedRegisterSpec` (`object_type=spec.register_type.value`, `object_instance=spec.address`, `present_value=str(spec.value)`).
  - `start_mqtt_simulator(*, topic, payload, interval_seconds, transport, device_repo, registry) -> RunningSimulator` — **RF-003, RF-006, RF-007, RF-014, RF-015, RNF-001**:
    1. `if interval_seconds <= 0: raise ProblemDetailError(400, .../mqtt-invalid-interval, ...)` — **RF-015**, antes de tocar el registro o arrancar nada.
    2. `async with registry.lock:` conflicto (igual que arriba, `protocol="mqtt"`, `address=topic`).
    3. `try: token = await transport.start(topic=topic, payload=payload, interval_seconds=interval_seconds)` `except MqttInvalidPublishError as exc: raise ProblemDetailError(400, .../mqtt-invalid-publish, ...) from exc` — **RF-014**, antes de escribir en `devices` (sin fila "fantasma" si la librería rechaza el primer publish).
    4. `device = await device_repo.upsert_device(name=f"Simulador MQTT {topic}", protocol="mqtt", address=topic, is_simulator=True)` — sin candidatos (MQTT no tiene "puntos" en el sentido de RF-002/BACnet, `spec.md §3`).
    5. Registra y retorna, igual que los otros 2.
  - `stop_simulator(*, device_id, registry, bacnet_transport, modbus_transport, mqtt_transport) -> None` — **RF-009, RF-012**:
    1. `async with registry.lock:`
    2. `entry = registry.get(device_id)`; si `None`: `raise ProblemDetailError(404, .../simulator-not-running, ...)` — **RF-012** (cubre los 3 sub-casos del RF de una sola vez: no existe, es `is_simulator=false`, o ya está detenido — ninguno está en el registro).
    3. Despacha al puerto correcto por `entry.protocol` (`{"bacnet": bacnet_transport, "modbus": modbus_transport, "mqtt": mqtt_transport}[entry.protocol]`); `await transport.stop(entry.token)`.
    4. `registry.unregister(device_id)` — **RF-009** (no toca `devices`/`device_points_candidates`, ver diseño de omisión abajo).
  - **RF-009** ("no elimina el dispositivo ni sus candidatos") se cumple por
    **omisión de diseño**: `stop_simulator` no importa ni referencia
    `device_repo.delete_*` (no existe tal método en `DeviceRepositoryPort` —
    nunca se añadió, `spec.md §2` Fuera de alcance).
  - **RF-011** ("sin mecanismo para quitar `is_simulator`") se cumple por
    **omisión de diseño**: ningún método de `services/simulator_service.py`
    ni de `DeviceRepositoryPort` pone `is_simulator=False` sobre una fila
    existente — el único lugar que escribe `is_simulator` es
    `upsert_device`, y solo con `True` (arranque) o con el valor ya
    protegido por el `OR` de RF-008 (escaneo).
  - **RF-013** ("reinicio detiene todos los simuladores, `devices`/
    candidatos intactos") se cumple por **omisión de diseño**:
    `SimulatorRegistryService` es un `dict` en memoria del proceso —
    `main.py` no lo persiste ni lo restaura en `lifespan`; un reinicio lo
    deja vacío sin código adicional. Ningún RF pide auto-rearranque
    (`spec.md §2` Fuera de alcance, ya decidido).
  - **RNF-001**: cada `start_*`/`stop_simulator` mantiene el `Lock` durante
    sus `await`, pero nunca ejecuta código bloqueante de forma síncrona
    dentro del *event loop* — los 3 adaptadores delegan el trabajo
    bloqueante de sus librerías a una tarea de fondo (`asyncio.create_task`)
    o a un hilo (`run_in_executor`), medido en §5.

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| Red BACnet/IP local (UDP) — instancia servidora real | Simulador BACnet responde a Who-Is con `device_instance`, expone objetos reales (RF-001) | `adapters/bacnet/bacnet_simulator_adapter.py::BacnetSimulatorAdapter` implementa `BacnetSimulatorPort` con `BAC0.lite(deviceId=...)` real |
| Red Modbus TCP local — servidor real | Simulador Modbus responde en `host:port` con `unit_id`, expone registros reales (RF-002) | `adapters/modbus/modbus_simulator_adapter.py::ModbusSimulatorAdapter` implementa `ModbusSimulatorPort` con `pymodbus.server.ModbusTcpServer` + `pymodbus.simulator.{SimData,SimDevice}` reales |
| Mosquitto (broker real ya autenticado de `SRV-001`) — publicación periódica | Simulador MQTT publica `payload` en `topic` cada `interval_seconds` (RF-003) | `adapters/mqtt/mqtt_publisher_adapter.py::MqttPublisherAdapter` implementa `MqttPublisherPort` con `paho-mqtt==2.1.0` real |
| PostgreSQL (`devices`, `device_points_candidates`) | Repositorio de dominio, ampliado | `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository` (`SRV-003`, **ampliado**: `get_device_by_address` nuevo, `upsert_device` corregido — RF-006/RF-007/RF-008) |

#### `core/ports/bacnet_simulator_port.py` (nuevo)
```python
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class BacnetSimulatedObjectSpec:
    """Un objeto BACnet inicial del simulador (RF-001). `object_type` ∈ los 6
    valores soportados (`schemas/simulators.py::BacnetSimulatedObjectIn`,
    validados en el borde HTTP, `plan.md §1` Registro de decisiones).
    `present_value` en texto — el adaptador lo convierte al tipo BACnet real
    (float para analog-*, "active"/"inactive" para binary-*)."""

    object_type: str
    object_instance: int
    present_value: str


class BacnetSimulatorPort(Protocol):
    async def start(
        self, *, device_instance: int, objects: list[BacnetSimulatedObjectSpec]
    ) -> str:
        """Arranca una instancia BACnet/IP real (RF-001) que responde a
        Who-Is con `device_instance` y expone `objects` como objetos BACnet
        reales, leíbles por cualquier cliente BACnet real (incl.
        `BacnetTransportPort`, `SRV-003`). No bloquea el *event loop*
        (RNF-001 — mismo patrón ya `verified` de `BAC0Adapter`, construcción
        síncrona de `BAC0.lite()`, `plan.md §5`). Retorna un token opaco que
        identifica esta instancia, para pasar a `stop()`."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene la instancia identificada por `token` (RF-009), liberando
        su socket UDP local."""
        ...
```

#### `core/ports/modbus_simulator_port.py` (nuevo)
```python
from dataclasses import dataclass
from typing import Protocol

from core.ports.modbus_transport_port import ModbusRegisterType


@dataclass(frozen=True)
class ModbusSimulatedRegisterSpec:
    """Un registro inicial del simulador Modbus (RF-002). Reutiliza
    `ModbusRegisterType` de `modbus_transport_port.py` (`SRV-004`) — mismo
    vocabulario de tipo de registro que el escaneo, sin duplicarlo."""

    register_type: ModbusRegisterType
    address: int
    value: bool | int


class ModbusSimulatorPort(Protocol):
    async def start(
        self,
        *,
        host: str,
        port: int,
        unit_id: int,
        registers: list[ModbusSimulatedRegisterSpec],
    ) -> str:
        """Arranca un servidor Modbus TCP real (RF-002) en `host:port` que
        responde con `unit_id` como *device id*, cargado con `registers`.
        No bloquea el *event loop* (RNF-001 — tarea de fondo,
        `ModbusTcpServer.serve_forever()`, `plan.md §5`). Retorna un token
        opaco."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene el servidor identificado por `token` (RF-009)."""
        ...
```

#### `core/ports/mqtt_publisher_port.py` (nuevo)
```python
from typing import Protocol


class MqttInvalidPublishError(Exception):
    """`topic`/`payload` rechazado por la librería MQTT al publicar
    (RF-014) — señal de dominio, no la excepción cruda de `paho-mqtt` (mismo
    criterio que `MqttInvalidTopicPatternError`, `SRV-005`)."""


class MqttPublisherPort(Protocol):
    async def start(self, *, topic: str, payload: str, interval_seconds: float) -> str:
        """Arranca un publicador MQTT real (RF-003) que publica `payload` en
        `topic` cada `interval_seconds` segundos, en un bucle de fondo
        (RNF-001, `plan.md §5`). Lanza `MqttInvalidPublishError` si
        `topic`/`payload` es rechazado por la librería al intentar el primer
        publish (RF-014) — **antes** de arrancar el bucle periódico. Retorna
        un token opaco."""
        ...

    async def stop(self, token: str) -> None:
        """Detiene el publicador identificado por `token` (RF-009)."""
        ...
```

### `DeviceRepositoryPort` — ampliación (`core/ports/device_repository_port.py`)
- Método nuevo: `get_device_by_address(self, protocol: str, address: str) -> DeviceRecord | None` — RF-006, RF-007 (lectura puntual por el índice único `(protocol, address)` ya existente, `SRV-003`).
- `upsert_device` — **el contrato no cambia de firma**, pero su docstring se
  amplía con la garantía nueva (RF-008): "una vez que una fila tiene
  `is_simulator=true`, ninguna llamada posterior con `is_simulator=false`
  la revierte — `is_simulator` solo se apaga por un mecanismo explícito que
  esta versión del contrato no expone (RF-011)".

### Adaptadores de entrada
- **`routers/simulators.py`** (nuevo, prefix `/simulators`, sin
  `dependencies=` a nivel de router — RBAC mixto, ver Registro de
  decisiones):
  - `POST /simulators/bacnet` — `Depends(require_role("admin"))` (RF-004).
    Body: `StartBacnetSimulatorRequest`. Invoca `start_bacnet_simulator` con
    `BacnetSimulatorPort`/`DeviceRepositoryPort`/`SimulatorRegistryService`
    inyectados. Responde `201` con `SimulatorOut`.
  - `POST /simulators/modbus` — ídem, `ModbusSimulatorPort`. `201`.
  - `POST /simulators/mqtt` — ídem, `MqttPublisherPort`. `201`.
  - `GET /simulators` — `Depends(require_role("admin", "operador"))`
    (RF-005). `registry.list_running()` mapeado a `list[SimulatorOut]` —
    lectura directa del registro (mismo criterio que `GET /devices` lee
    `device_repo.list_devices()` directo, sin una función de `services/`
    dedicada solo para esto). `200`.
  - `DELETE /simulators/{device_id}` — `Depends(require_role("admin"))`
    (RF-004). Invoca `stop_simulator` con los 3 puertos +
    `SimulatorRegistryService` inyectados (necesita los 3 para poder
    despachar al protocolo correcto según lo que diga el registro, ver
    `services/simulator_service.py::stop_simulator`). `204` sin cuerpo.
  - `ProblemDetailError` (403/404/409/400) propaga sin captura explícita —
    el `exception_handler` ya registrado en `main.py` la traduce a HTTP
    (reutilizado, sin cambios).
  - No instancia ningún adaptador directamente (`SRV-ADR-017`).

### `adapters/factory.py` (se amplía)
- `get_bacnet_simulator_port() -> BacnetSimulatorPort`: singleton,
  `BacnetSimulatorAdapter(ip=settings.bacnet_ip, port_range_start=settings.bacnet_simulator_port_range_start)`
  — mismo `bacnet_ip` que `get_bacnet_transport_port()` (interfaz local), un
  rango de puertos **distinto** para no colisionar con el puerto fijo del
  cliente de escaneo.
- `get_modbus_simulator_port() -> ModbusSimulatorPort`: singleton,
  `ModbusSimulatorAdapter()` — sin estado de `Settings` (mismo criterio que
  `get_modbus_transport_port()`: `host`/`port` llegan por parámetro en cada
  llamada).
- `get_mqtt_publisher_port() -> MqttPublisherPort`: singleton,
  `MqttPublisherAdapter(host=settings.mqtt_broker_host, port=1883, user=settings.mqtt_user, password=settings.mqtt_password)`
  — mismas credenciales que `get_mqtt_scan_transport_port()`, función
  **independiente** (mismo criterio ya registrado: ciclo de vida de
  conexión distinto — aquí, indefinido hasta `DELETE`, no por ventana).
- `Settings` (`core/config.py`) — campo nuevo, opcional:
  `bacnet_simulator_port_range_start: int = 47900` (mismo criterio que
  `bacnet_ip`/`bacnet_port`, `SRV-003`: ajuste operativo excepcional, no
  obligatorio).

## 3. Modelo de datos
**Sin migración nueva.** Reutiliza `devices`/`device_points_candidates`
(`SRV-003`, `verified`). El `CHECK (protocol IN ('bacnet', 'modbus',
'mqtt'))` ya admite los 3 protocolos que usa esta feature — sin protocolo
nuevo que registrar. `devices.is_simulator` (existente desde `SRV-003`, sin
productor hasta ahora) recibe su primer escritor real (`upsert_device(...,
is_simulator=True)`).

`devices.address` para cada protocolo de simulador (ver Registro de
decisiones para el razonamiento completo):
- BACnet: `str(device_instance)` (`core/bacnet_address.py::
  format_simulator_device_address`) — **distinto** del formato
  `"<instance>@<network>"` que usan los dispositivos reales de `SRV-003`.
- Modbus: `"<host>:<port>:<unit_id>"` (`core/modbus_address.py::
  format_modbus_address`, **idéntico** al que usa `scan_modbus`, `SRV-004`).
- MQTT: el `topic` concreto tal cual (**idéntico** semánticamente al
  `address=topic_pattern` que usa `scan_mqtt`, `SRV-005`, cuando el patrón
  escaneado no lleva wildcard).

`device_points_candidates` para simuladores BACnet/Modbus: mismo esquema
que sus escaneos respectivos (`object_type`, `object_instance` entero,
`present_value` texto, `units=NULL`) — sin candidatos para simuladores MQTT
(RF-003 no los define; MQTT no tiene "puntos" en `device_points_candidates`
en esta feature, ni siquiera vía escaneo, `SRV-005`).

**Migración de índice: ninguna.** `get_device_by_address` reutiliza el
índice único ya existente `uq_devices_protocol_address` — consulta puntual,
sin `EXPLAIN` sorpresa.

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-006-simuladores/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** es `hira-server/docs/openapi.yaml` (se **amplía**, no se reemplaza — los 13 paths existentes intactos) | `POST /simulators/{bacnet,modbus,mqtt}`, `GET /simulators`, `DELETE /simulators/{device_id}` | `gate/check.sh` bloque 5 (Spectral lint, mismo warn conocido de tooling ya aceptado en `SRV-001`..`005`) |

### Sobre de error — RFC 9457 (reutiliza `ProblemDetail`, `E-ADR-003`)
| Endpoint | HTTP | `type` (slug) | `title` | Cuándo |
|---|---|---|---|---|
| `POST`/`DELETE /simulators/*` | 403 | `insufficient-role` | "Rol insuficiente" | Operador/Visor invoca `POST`/`DELETE` (RF-004) — slug reutilizado |
| `GET /simulators` | 403 | `insufficient-role` | "Rol insuficiente" | Visor invoca el listado (RF-005) — slug reutilizado |
| `POST /simulators/*` | 409 | `simulator-address-conflict` | "Dirección ya registrada" | La dirección/identidad ya corresponde a un dispositivo real (RF-006) — slug **nuevo** |
| `POST /simulators/*` | 409 | `simulator-already-running` | "Simulador ya en ejecución" | La dirección/identidad ya tiene un simulador corriendo (RF-006) — slug **nuevo** |
| `DELETE /simulators/{device_id}` | 404 | `simulator-not-running` | "Simulador no encontrado" | `device_id` sin simulador actualmente en ejecución (RF-012) — slug **nuevo** |
| `POST /simulators/mqtt` | 400 | `mqtt-invalid-publish` | "Publicación MQTT inválida" | `topic`/`payload` rechazado por `paho-mqtt` al publicar (RF-014) — slug **nuevo**, distinto de `mqtt-invalid-topic-pattern` (`SRV-005`, valida `subscribe()`, no `publish()`) |
| `POST /simulators/mqtt` | 400 | `mqtt-invalid-interval` | "Intervalo inválido" | `interval_seconds <= 0` (RF-015) — slug **nuevo** |

### Esquemas nuevos (`hira-server/docs/openapi.yaml` — extracto)
```yaml
BacnetSimulatedObjectIn:
  type: object
  required: [object_type, object_instance, present_value]
  additionalProperties: false
  properties:
    object_type:
      type: string
      enum: [analog-value, analog-input, analog-output, binary-value, binary-input, binary-output]
    object_instance:
      type: integer
      minimum: 0
    present_value:
      type: string
      description: >
        Texto — analog-*: parseable a número; binary-*: "active"/"inactive".

StartBacnetSimulatorRequest:
  type: object
  required: [device_instance]
  additionalProperties: false
  properties:
    device_instance:
      type: integer
      minimum: 0
      maximum: 4194303
    objects:
      type: array
      items:
        $ref: "#/components/schemas/BacnetSimulatedObjectIn"

ModbusRegisterValueIn:
  type: object
  required: [address, value]
  additionalProperties: false
  properties:
    address:
      type: integer
      minimum: 0
    value:
      oneOf: [{type: boolean}, {type: integer}]

StartModbusSimulatorRequest:
  type: object
  required: [host, port, unit_id]
  additionalProperties: false
  properties:
    host: {type: string, minLength: 1}
    port: {type: integer, minimum: 1, maximum: 65535}
    unit_id: {type: integer, minimum: 0, maximum: 255}
    coils: {type: array, items: {$ref: "#/components/schemas/ModbusRegisterValueIn"}}
    discrete_inputs: {type: array, items: {$ref: "#/components/schemas/ModbusRegisterValueIn"}}
    holding_registers: {type: array, items: {$ref: "#/components/schemas/ModbusRegisterValueIn"}}
    input_registers: {type: array, items: {$ref: "#/components/schemas/ModbusRegisterValueIn"}}

StartMqttSimulatorRequest:
  type: object
  required: [topic, payload, interval_seconds]
  additionalProperties: false
  properties:
    topic: {type: string, minLength: 1}
    payload: {type: string}
    interval_seconds:
      type: number
      description: >
        Sin `minimum` a propósito — RF-015 exige 400 RFC 9457, no el 422
        genérico de Pydantic (mismo criterio que `ModbusRangeIn.count`, `SRV-004`).

SimulatorOut:
  type: object
  required: [device_id, protocol, address, started_at]
  additionalProperties: false
  properties:
    device_id: {type: string, format: uuid}
    protocol: {type: string, enum: [bacnet, modbus, mqtt]}
    address: {type: string}
    started_at: {type: string, format: date-time}
```
`POST /simulators/{bacnet,modbus,mqtt}` → `201: SimulatorOut` | `400`
(RF-014/RF-015, solo MQTT) | `403` (RF-004) | `409` (RF-006).
`GET /simulators` → `200: SimulatorOut[]` (puede ser `[]`) | `403` (RF-005).
`DELETE /simulators/{device_id}` → `204` (sin cuerpo) | `403` (RF-004) |
`404` (RF-012).

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`core/bacnet_address.py::format_simulator_device_address`) | Determinista, `str(device_instance)` exacto; rechaza `< 0` y `> 4194303` | unit puro, **sin mocks** — RF-001/RF-007 |
| Estado en memoria (`services/simulator_registry_service.py`) | `register`/`get`/`is_running`/`unregister`/`list_running` sobre el `dict`; el `Lock` serializa 2 corutinas reales que intentan `async with registry.lock` a la vez (una espera a que la otra libere — verificado con orden de ejecución real, `asyncio.gather`, sin mocks) | unit, **sin mocks** — RF-010 |
| Coordinación (`services/simulator_service.py`) | Por cada protocolo: *camino feliz* (arranca, persiste device+candidatos, registra); *RF-006 dispositivo real*: `get_device_by_address` doble retorna `is_simulator=false` → 409 antes de invocar `transport.start`; *RF-006 ya corriendo*: `registry` doble con la entrada ya presente → 409 antes de invocar `transport.start`; *RF-007 reanudación*: `get_device_by_address` retorna un simulador existente no corriendo → mismo `device_id` reutilizado, sin segundo `upsert_device` con `is_simulator` distinto; *RF-014* (solo MQTT): doble de `transport.start` lanza `MqttInvalidPublishError` → 400, sin `upsert_device` invocado; *RF-015* (solo MQTT): `interval_seconds<=0` → 400, sin invocar `transport`/`device_repo`; *RF-009/RF-012* (`stop_simulator`): `device_id` en el registro → despacha al puerto correcto y desregistra; `device_id` ausente → 404; *limpieza defensiva*: `device_repo.upsert_device` doble que lanza → `transport.stop(token)` invocado antes de propagar | unit + dobles (`Protocol` fakes) de los 3 puertos + `DeviceRepositoryPort` + `SimulatorRegistryService` real (no doble — es puro, sin I/O, se usa tal cual en estos tests) |
| Adaptador BACnet (`adapters/bacnet/bacnet_simulator_adapter.py`) — **verificación de integración real, contra un cliente BACnet real (`BAC0.lite()`, sin `BAC0Adapter`/mocks)** | (a) `start(device_instance=999123, objects=[...])` → un cliente BACnet real (`BAC0.lite()`) hace Who-Is unicast y recibe I-Am con `instance_number == 999123` (mismo patrón de `test_bac0_adapter.py`, pero el simulador ahora es el "dispositivo" bajo prueba, no infraestructura de test); (b) el cliente lee `presentValue` de un objeto `analog-value` inicial y obtiene el valor real cargado; (c) `stop(token)` libera el puerto UDP — un segundo `start()` puede reutilizar el mismo rango sin colisión; (d) 2 simuladores concurrentes (`device_instance` distintos) conviven sin colisión de puerto (`bacnet_simulator_port_range_start` incremental) | integración — BAC0 real (`BAC0==2026.7.25`), sin contenedores, UDP en loopback |
| Adaptador Modbus (`adapters/modbus/modbus_simulator_adapter.py`) — **verificación de integración real, contra un cliente Modbus real (`AsyncModbusTcpClient`, sin `PymodbusAdapter`/mocks)** | (a) `start(host="127.0.0.1", port=..., unit_id=1, registers=[...])` → un cliente Modbus real lee los registros y obtiene los valores reales cargados (holding/input → int, coil/discrete → bool); (b) `stop(token)` cierra el servidor — un cliente posterior no puede conectar | integración — `ModbusTcpServer`/`SimData`/`SimDevice` reales (mismas clases ya usadas como infraestructura de test en `SRV-004`, aquí como producto), sin contenedores, TCP en loopback |
| Adaptador MQTT (`adapters/mqtt/mqtt_publisher_adapter.py`) — **verificación de integración real, contra el Mosquitto real del compose de `SRV-001`, con un segundo cliente `paho-mqtt` como suscriptor de prueba** | (a) `start(topic=..., payload=..., interval_seconds=1.0)` → un suscriptor real recibe **≥ 3** mensajes con el `payload` esperado en una ventana de 3.5s (cadencia ~1s medida, `time.monotonic()`, evidencia real — ver nota de investigación); (b) *RF-014*: `topic` con wildcard (`"edificio/#"`) o vacío → `MqttInvalidPublishError` inmediato (`< 1s`, sin arrancar el bucle) — mismo patrón `ValueError` síncrono de `client.publish()` verificado en esta fase; (c) `stop(token)` detiene el bucle — el suscriptor no recibe más mensajes tras `stop()` | integración — Mosquitto real del compose + un segundo cliente `paho-mqtt` como suscriptor de prueba |
| Adaptador de repositorio (`PostgreSQLDeviceRepository`, ampliado) | `get_device_by_address`: existente vs. inexistente, distingue por `protocol` (mismo `address`, protocolos distintos, no colisiona); **`upsert_device` preserva `is_simulator=true`**: fila ya simulador → segundo `upsert_device(..., is_simulator=False)` (simulando un escaneo real posterior) → `is_simulator` sigue `true` tras la llamada (test **nuevo**, verifica RF-008 directamente contra Postgres real) | integración — Postgres real (`SRV-003`, contenedor ya existente) |
| Router (`routers/simulators.py`) | Contrato exacto de `openapi.yaml` (`TestClient`, dobles vía `app.dependency_overrides` de los 3 puertos + `DeviceRepositoryPort` + `SimulatorRegistryService`) — 201 con `SimulatorOut` (los 3 protocolos), 403 con Operador en `POST`/`DELETE` y con Visor en los 3 endpoints, 403 reservado también sobre Operador+`GET` **no** aplica (Operador sí puede `GET`, verificado en positivo), 409 (RF-006, ambas variantes), 404 (RF-012), 400 (RF-014/RF-015, *shape* RFC 9457 exacto), 204 sin cuerpo en `DELETE` exitoso | unit + `TestClient`, sin contenedores |
| Sistema (e2e) | `POST /simulators/bacnet` real → un cliente BACnet real confirma el I-Am → `GET /simulators` lo lista → `GET /devices` también lo lista (`is_simulator=true`) → `DELETE /simulators/{id}` → `GET /simulators` ya no lo lista, `GET /devices` **sigue** listándolo (RF-009) → repetir flujo abreviado para Modbus y MQTT; `POST /devices/scan/modbus` sobre la misma dirección del simulador Modbus en ejecución confirma que `is_simulator` sigue `true` tras el escaneo (RF-008, evidencia end-to-end) | integración — Postgres + Mosquitto reales del compose + clientes reales de cada protocolo |

> **Nota de investigación (ejecutada en esta fase, con evidencia real —
> mismo estándar que `SRV-003`/`004`/`005/plan.md §5`):**
> 1. **BACnet como servidor real** (`BAC0==2026.7.25`, `bacpypes3==0.0.106`):
>    `BAC0.lite(ip="127.0.0.1", port=48100, deviceId=999123, ping=False)`
>    arranca un dispositivo BACnet/IP real cuyo *Boid* (identificador
>    interno) refleja el `deviceId` pasado. Un cliente BACnet real separado
>    (`BAC0.lite(...)`, sin `deviceId`) que hace `who_is(address="127.0.0.1:
>    48100", timeout=3.0)` recibe exactamente 1 I-Am con
>    `iAmDeviceIdentifier == ("device", 999123)`. Un objeto
>    `AnalogValueObject` añadido dinámicamente con
>    `sim.this_application.app.add_object(...)` (mismo mecanismo ya
>    `verified` en `tests/integration/test_bac0_adapter.py::
>    _make_simulated_device`, `SRV-003`) es leíble por el cliente real:
>    `client.read("127.0.0.1:48100 analogValue 1 presentValue")` retorna
>    `42.0` (el valor real cargado). Confirma que `BAC0.lite(deviceId=...)`
>    es la implementación correcta de `BacnetSimulatorPort.start()` — sin
>    duda de API abierta para Fase 4.
> 2. **Modbus como servidor real** (`pymodbus==3.15.0`): ya verificado como
>    infraestructura de test en `SRV-004-modbus-adapter/plan.md §5`
>    (`ModbusTcpServer` + `SimData`/`SimDevice`, API "clásica" rota en esta
>    versión, confirmado en su momento) — esta feature reutiliza el mismo
>    mecanismo exacto, ahora como el **adaptador de producto**
>    (`ModbusSimulatorAdapter`), no como *fixture* de un archivo de test.
>    Sin nueva duda de API: el comportamiento ya está verificado con
>    ejecución real y sigue siendo el mismo en esta sesión.
> 3. **MQTT publicando periódicamente** (`paho-mqtt==2.1.0`, contra el
>    Mosquitto real del compose de `SRV-001`, `docker compose -f
>    docker-compose.yml -f docker-compose.dev.yml up -d mosquitto`): un
>    bucle `asyncio` (`while not stop_event.is_set(): client.publish(...);
>    await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)`)
>    publicó 4 mensajes en 3.5s con `interval_seconds=1.0` (cadencia medida:
>    ~1.000-1.002s entre publicaciones, `time.monotonic()`), recibidos
>    íntegros por un segundo cliente `paho-mqtt` (suscriptor de prueba) — sin
>    bloquear el *event loop* (el hilo de red de `paho-mqtt`,
>    `loop_start()`, corre aparte; el `asyncio.wait_for` cede el control
>    entre publicaciones). `client.publish(topic, payload)` valida el
>    *topic* de forma **síncrona** (`ValueError`, sin *round-trip* al
>    broker) para topics con wildcard (`"edificio/#"` →
>    `"Publish topic cannot contain wildcards."`) o vacíos (`""` →
>    `"Invalid topic."`) — mismo patrón de validación síncrona ya verificado
>    en `client.subscribe()` (`SRV-005`). Confirma que un bucle
>    `asyncio`/`paho-mqtt` simple es la implementación correcta de
>    `MqttPublisherPort.start()` — sin duda de API abierta para Fase 4.
>
> Este plan no deja ninguna duda abierta de API de `BAC0`/`pymodbus`/
> `paho-mqtt` en modo servidor/publicador para Fase 4.

## 6. Secuenciación de archivos (tests antes que código)
1. `tests/test_bacnet_address.py` (se amplía, falla) →
   `core/bacnet_address.py::format_simulator_device_address` — RF-001,
   RF-007.
2. `tests/test_simulator_registry_service.py` (falla) →
   `services/simulator_registry_service.py::RunningSimulator`,
   `SimulatorRegistryService`, `get_simulator_registry` — RF-010.
3. `core/ports/bacnet_simulator_port.py`, `core/ports/
   modbus_simulator_port.py`, `core/ports/mqtt_publisher_port.py`
   (`Protocol`, sin test propio, igual que los puertos de transporte de
   `SRV-003`/`004`/`005`).
4. `core/ports/device_repository_port.py` (se amplía: `get_device_by_address`
   añadido al `Protocol`, docstring de `upsert_device` actualizado con la
   garantía de RF-008 — sin test propio, es una interfaz).
5. `tests/test_simulator_service.py` (falla) →
   `services/simulator_service.py::start_bacnet_simulator/
   start_modbus_simulator/start_mqtt_simulator/stop_simulator` — RF-001,
   RF-002, RF-003, RF-006, RF-007, RF-009, RF-012, RF-014, RF-015, RNF-001.
6. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) —
   amplía con los 5 paths + 6 schemas nuevos, sin tocar los 13 endpoints
   existentes.
7. `tests/test_simulators_router.py` (falla) → `routers/simulators.py` +
   `schemas/simulators.py` + **`adapters/factory.py::
   get_bacnet_simulator_port()/get_modbus_simulator_port()/
   get_mqtt_publisher_port()`** (nacen aquí con placeholders in-memory —
   mismo patrón ya aplicado 5 veces: el router necesita el punto de
   inyección desde que existe) — RF-001..RF-015 vía HTTP con dobles
   in-memory del propio archivo de test. `main.py` registra
   `routers/simulators.py` (`app.include_router`) — sin cambios al
   `lifespan` (RF-013: el registro nace vacío, sin restaurar nada).
8. `tests/integration/test_device_repository_adapter.py` (se amplía, falla)
   → `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository`
   (`get_device_by_address` nuevo, `upsert_device` corregido — el `OR`
   booleano) — RF-006, RF-007, RF-008.
9. `tests/integration/test_bacnet_simulator_adapter.py` (falla, requiere
   `BAC0` real) → `adapters/bacnet/bacnet_simulator_adapter.py::
   BacnetSimulatorAdapter` — reemplaza el **cuerpo** (no la firma) de
   `get_bacnet_simulator_port()` — RF-001, RNF-001 (reales).
10. `tests/integration/test_modbus_simulator_adapter.py` (falla, requiere
    `pymodbus` real) → `adapters/modbus/modbus_simulator_adapter.py::
    ModbusSimulatorAdapter` — reemplaza el cuerpo de
    `get_modbus_simulator_port()` — RF-002, RNF-001 (reales).
11. `tests/integration/test_mqtt_publisher_adapter.py` (falla, requiere el
    Mosquitto real del compose) → `adapters/mqtt/mqtt_publisher_adapter.py::
    MqttPublisherAdapter` — reemplaza el cuerpo de
    `get_mqtt_publisher_port()` — RF-003, RF-014, RNF-001 (reales).
12. `tests/integration/test_simulators_e2e.py` (nuevo — contenedores reales
    + clientes reales de cada protocolo) — recorrido completo descrito en
    §5, fila "Sistema (e2e)" — RF-001..RF-015, RNF-001 medido con evidencia
    real.
13. `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` —
    nota `[doc]` de §8, cierra la nota de estado ya dejada por `SRV-003`/
    `004`/`005` (puede ejecutarse en paralelo desde el paso 1).
14. READMEs ampliados (carpetas ya existentes, sin carpeta nueva que
    crear): `hira-server/backend/adapters/bacnet/README.md` (añade
    `bacnet_simulator_adapter.py`); `hira-server/backend/adapters/modbus/
    README.md` (añade `modbus_simulator_adapter.py`);
    `hira-server/backend/adapters/mqtt/README.md` (añade
    `mqtt_publisher_adapter.py`, junto a `mosquitto_adapter.py`/
    `mqtt_scan_adapter.py`); `hira-server/backend/adapters/README.md`
    (añade las 3 funciones nuevas de `factory.py`, 11 en total);
    `hira-server/backend/core/ports/README.md` (añade los 3 puertos +
    la ampliación de `device_repository_port.py`);
    `hira-server/backend/services/README.md` (añade
    `simulator_registry_service.py`, `simulator_service.py`);
    `hira-server/backend/routers/README.md` (añade `simulators.py`);
    `hira-server/backend/schemas/README.md` (añade `simulators.py`).

> `.harness/gate/services.txt` ya declara `hira-server/backend:python`
> (`SRV-001`) — sin cambios necesarios, la suite nueva se integra en la
> misma suite de `pytest`.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `services/simulator_service.py::start_*_simulator` envuelve la persistencia (`upsert_device`/`upsert_candidate`) en un `try/except Exception: await transport.stop(token); raise` — limpieza defensiva sin transacción cruzada real entre el proceso real (BAC0/pymodbus/paho) y PostgreSQL | Arrancar un proceso real y escribir en una base de datos son 2 sistemas sin transacción conjunta posible — un fallo de Postgres **después** de `transport.start()` exitoso, sin esta limpieza, dejaría un simulador corriendo sin ningún `device_id`/entrada de registro para detenerlo vía la API (huérfano hasta el próximo reinicio de Hira Server, RF-013). El `try/except` es la mitigación más simple sin inventar un mecanismo de dos fases (Art. 10: no hay evidencia de que Postgres falle con la frecuencia suficiente para justificar más que esto) — riesgo residual documentado: si el propio `transport.stop(token)` de limpieza también falla, el huérfano persiste hasta el reinicio; sin evidencia de que valga la pena un reintento adicional aquí. |
| Identidad de simulador BACnet (`str(device_instance)`) usa un formato de `address` **distinto** al de dispositivos reales BACnet (`"<instance>@<network>"`, `SRV-003`) dentro de la misma columna `devices.address` | Ver Registro de decisiones §2 — es la única forma de que RF-007 (reanudación restart-safe) sea implementable sin depender de un puerto UDP efímero estable entre reinicios. Marcado explícitamente para confirmación en Gate 2, mismo criterio que la excepción análoga de `SRV-005-mqtt-scanning/plan.md §7` (`topic_instance_key`). |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` | La nota de estado ya añadida por `SRV-003`/`004`/`005` ("Polling, escritura, `asyncio.Lock` por dispositivo, BACnet MSTP, Modbus RTU y Simuladores siguen siendo diseño, no código") queda **desactualizada** en la parte de Simuladores tras esta feature: arrancar/detener simuladores BACnet/Modbus/MQTT pasa a ser código real. La sección "Simuladores" (líneas ya existentes, escritas en `SRV-ADR-014`) sigue siendo correcta tal como está redactada — esta feature la implementa, sin contradecirla | `[doc]` editar la nota de estado (no crear una nueva): "Implementado a la fecha (`SRV-003-bacnet-adapter`, `SRV-004-modbus-adapter`, `SRV-005-mqtt-scanning`, `SRV-006-simuladores`): escaneo BACnet/IP (Who-Is/I-Am), escaneo de rangos Modbus TCP, suscripción wildcard MQTT y simuladores de los 3 protocolos (arrancar/detener, registro inmediato en `devices` con `is_simulator=true`, estado de ejecución en memoria del proceso). Polling, escritura, `asyncio.Lock` por dispositivo, BACnet MSTP y Modbus RTU siguen siendo diseño, no código — ver `ROADMAP.md`/`.harness/specs/` para el estado real por sub-feature." |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es el
contrato de producto de esta frontera, ya cubierto en §4 (se amplía, no se
reemplaza).

`docs/hira-server/spec/validation/acceptance-criteria.md` **no** se toca:
`spec.md` de esta feature ya declara qué `AC-SRV-05` cubre (5.1–5.4; 5.5
diferido) en su encabezado — sin un `AC-SRV-0X` dedicado nuevo que redactar.

`docs/hira-server/spec/validation/vulnerabilities.md::VUL-SRV-001` **no**
se toca: sigue 🟢 Resuelto (`SRV-001`) — `MqttPublisherAdapter` refuerza ese
cierre (siempre autenticado, nunca anónimo, `plan.md §5`) sin cambiar su
estado.

## 9. Implementación por requisito

### Implementación de RF-001
- `core/bacnet_address.py::format_simulator_device_address`.
- `core/ports/bacnet_simulator_port.py::BacnetSimulatorPort.start` (+ `BacnetSimulatedObjectSpec`).
- `adapters/bacnet/bacnet_simulator_adapter.py::BacnetSimulatorAdapter.start`.
- `services/simulator_service.py::start_bacnet_simulator`.
- `routers/simulators.py::POST /simulators/bacnet`.
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1bacnet`.
- Tests: `tests/test_bacnet_address.py`, `tests/test_simulator_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_bacnet_simulator_adapter.py`, `tests/integration/test_simulators_e2e.py`.
- `covers`: `hira-server/backend/core/bacnet_address.py`, `hira-server/backend/core/ports/bacnet_simulator_port.py`, `hira-server/backend/adapters/bacnet/bacnet_simulator_adapter.py`, `hira-server/backend/services/simulator_service.py`, `hira-server/backend/routers/simulators.py`.

### Implementación de RF-002
- `core/modbus_address.py::format_modbus_address` (`SRV-004`, reutilizado tal cual).
- `core/ports/modbus_simulator_port.py::ModbusSimulatorPort.start` (+ `ModbusSimulatedRegisterSpec`).
- `adapters/modbus/modbus_simulator_adapter.py::ModbusSimulatorAdapter.start`.
- `services/simulator_service.py::start_modbus_simulator`.
- `routers/simulators.py::POST /simulators/modbus`.
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1modbus`.
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_modbus_simulator_adapter.py`, `tests/integration/test_simulators_e2e.py`.
- `covers`: `hira-server/backend/core/ports/modbus_simulator_port.py`, `hira-server/backend/adapters/modbus/modbus_simulator_adapter.py`.

### Implementación de RF-003
- `core/ports/mqtt_publisher_port.py::MqttPublisherPort.start`.
- `adapters/mqtt/mqtt_publisher_adapter.py::MqttPublisherAdapter.start`.
- `services/simulator_service.py::start_mqtt_simulator`.
- `routers/simulators.py::POST /simulators/mqtt`.
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1mqtt`.
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_mqtt_publisher_adapter.py`, `tests/integration/test_simulators_e2e.py`.
- `covers`: `hira-server/backend/core/ports/mqtt_publisher_port.py`, `hira-server/backend/adapters/mqtt/mqtt_publisher_adapter.py`.

### Implementación de RF-004
- `core/security/dependencies.py::require_role` — **reutilizado tal cual** de `SRV-002`, aplicado por ruta (no a nivel de router) en `routers/simulators.py`.
- Tests: `tests/test_simulators_router.py` (403 con Operador/Visor en `POST`/`DELETE`), `tests/integration/test_simulators_e2e.py`.

### Implementación de RF-005
- `core/security/dependencies.py::require_role("admin", "operador")` en `routers/simulators.py::GET /simulators`.
- Tests: `tests/test_simulators_router.py` (403 con Visor, 200 con Admin y con Operador).

### Implementación de RF-006
- `core/ports/device_repository_port.py::DeviceRepositoryPort.get_device_by_address` (nuevo).
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.get_device_by_address`.
- `services/simulator_registry_service.py::SimulatorRegistryService.is_running`.
- `services/simulator_service.py::_check_conflict_and_resolve_device_id` (helper interno de los 3 `start_*_simulator`).
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_device_repository_adapter.py`.
- `covers`: `hira-server/backend/core/ports/device_repository_port.py`, `hira-server/backend/services/simulator_registry_service.py`.

### Implementación de RF-007
- `core/bacnet_address.py::format_simulator_device_address` (identidad restart-safe).
- `services/simulator_service.py::start_*_simulator` (rama de reanudación: `existing.id` reutilizado).
- Tests: `tests/test_simulator_service.py` (doble de `get_device_by_address` retorna un simulador existente no corriendo → mismo `device_id`), `tests/integration/test_simulators_e2e.py`.

### Implementación de RF-008
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.upsert_device` (el `OR` booleano en `ON CONFLICT DO UPDATE`).
- `core/ports/device_repository_port.py::DeviceRepositoryPort.upsert_device` (docstring ampliado con la garantía).
- Tests: `tests/integration/test_device_repository_adapter.py` (test nuevo, directo contra Postgres real), `tests/integration/test_simulators_e2e.py` (evidencia end-to-end: escaneo real posterior a un simulador en ejecución no resetea el flag).
- `covers`: `hira-server/backend/adapters/db/device_repository_adapter.py`.

### Implementación de RF-009
- `services/simulator_service.py::stop_simulator`.
- `routers/simulators.py::DELETE /simulators/{device_id}`.
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py` (204, `devices`/candidatos no tocados — inspección de que `stop_simulator` no importa ningún método de borrado), `tests/integration/test_simulators_e2e.py`.

### Implementación de RF-010
- `services/simulator_registry_service.py::SimulatorRegistryService.list_running`, `RunningSimulator`.
- `routers/simulators.py::GET /simulators`.
- Tests: `tests/test_simulator_registry_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_simulators_e2e.py`.

### Implementación de RF-011
- Ausencia de diseño verificada: ningún método de `DeviceRepositoryPort`/`services/simulator_service.py` escribe `is_simulator=False` sobre una fila existente.
- Tests: `tests/test_simulator_service.py` (inspección: los 3 `start_*_simulator` solo llaman `upsert_device(..., is_simulator=True)`), `tests/integration/test_device_repository_adapter.py` (RF-008 ya lo prueba desde el otro lado).

### Implementación de RF-012
- `services/simulator_service.py::stop_simulator` (404 si `registry.get(device_id) is None`).
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1{device_id}` (respuesta 404).
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py` (*shape* RFC 9457 exacto).

### Implementación de RF-013
- Ausencia de diseño verificada: `services/simulator_registry_service.py` no tiene persistencia; `main.py::lifespan` no lo referencia.
- Tests: `tests/test_simulator_registry_service.py` (un `SimulatorRegistryService()` nuevo siempre nace vacío — equivalente verificable de "un reinicio lo vacía").

### Implementación de RF-014
- `core/ports/mqtt_publisher_port.py::MqttInvalidPublishError`.
- `adapters/mqtt/mqtt_publisher_adapter.py::MqttPublisherAdapter.start` (captura el `ValueError` síncrono de `paho-mqtt` en `client.publish()`, lo traduce).
- `services/simulator_service.py::start_mqtt_simulator` (`try/except MqttInvalidPublishError` → `ProblemDetailError(400, .../mqtt-invalid-publish)`).
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1mqtt` (respuesta 400).
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py`, `tests/integration/test_mqtt_publisher_adapter.py` (patrones/tópicos inválidos reales, tiempo medido `<1s`).

### Implementación de RF-015
- `services/simulator_service.py::start_mqtt_simulator` (`interval_seconds <= 0` → `ProblemDetailError(400, .../mqtt-invalid-interval)`, antes de `transport.start`).
- `hira-server/docs/openapi.yaml#/paths/~1simulators~1mqtt` (respuesta 400, `interval_seconds` sin `minimum` en el schema).
- Tests: `tests/test_simulator_service.py`, `tests/test_simulators_router.py`.

### Implementación de RNF-001
- `services/simulator_service.py::start_*_simulator/stop_simulator` (el `asyncio.Lock` no bloquea el *event loop*, solo serializa entre sí las llamadas de gestión de simuladores).
- `adapters/bacnet/bacnet_simulator_adapter.py` (construcción síncrona de `BAC0.lite()`, mismo patrón ya `verified` de `BAC0Adapter`, sin operación bloqueante de larga duración).
- `adapters/modbus/modbus_simulator_adapter.py` (`asyncio.create_task(server.serve_forever())` — tarea de fondo).
- `adapters/mqtt/mqtt_publisher_adapter.py` (`asyncio.create_task` del bucle de publicación + `run_in_executor` para el `connect()` bloqueante, mismo patrón que `MqttScanAdapter`).
- Medición: `tests/integration/test_simulators_e2e.py` (con simuladores en ejecución, `GET /health`/`GET /devices` siguen respondiendo con normalidad — evidencia de terminal pegada, Art. 3).
