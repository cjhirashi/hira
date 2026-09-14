---
id: PLAN-SRV-003
tipo: plan
feature: SRV-003-bacnet-adapter
estado: approved
aprobaciones:
  fase_2: { por: "Carlos", fecha: 2026-09-14 }
actualizado: 2026-09-14
---

# PLAN-SRV-003 · Adaptador BACnet — escaneo y candidatos

> El *cómo*. Traduce cada `RF-001..RF-010`/`RNF-001` de `spec.md` al patrón
> **Hexagonal** (Constitución Art. 1–2, `SRV-ADR-017`), construyendo sobre
> `SRV-002-auth-rbac` (`verified`): reutiliza `core/security/dependencies.py`
> (`require_role`, sin reimplementarlo), `adapters/factory.py` (se amplía con 2
> puertos nuevos), `core/config.py::Settings`, `core/errors.py::ProblemDetailError`,
> `core/logger.py`, el estilo de `models/user_model.py`/`adapters/db/
> user_repository_adapter.py` (SQLAlchemy Core, sin ORM declarativo) y
> `alembic/` ya configurado (migración `0002`, sobre `0001` sin tocarla).
> Tercera feature real de `hira-server/backend/`; primera que integra un
> protocolo de campo (BACnet/IP vía `BAC0`).

## 0. Gates de simplicidad
- [x] **Simplicity** — 2 puertos nuevos (`BacnetTransportPort`,
      `DeviceRepositoryPort`), 2 tablas (`devices`, `device_points_candidates`),
      3 endpoints (`POST /devices/scan/bacnet`, `GET /devices`,
      `GET /devices/{id}/candidates`). Sin `asyncio.Lock` por dispositivo
      (`VUL-SRV-005`, diferido — sin escritura/polling concurrente en esta
      feature, `spec.md §2`/§6). Sin nuevas variables de entorno obligatorias:
      `Settings.bacnet_ip`/`bacnet_port` son opcionales con default `None`
      (BAC0 autodetecta la interfaz local si no se fija — comportamiento
      adecuado para un solo NIC on-premise, Art. 10: no anticipar).
- [x] **Anti-Abstraction** — `PostgreSQLDeviceRepository` usa SQLAlchemy Core
      (`Table`/`select`/`insert`/`update`, `ON CONFLICT` nativo de Postgres para
      los `upsert_*`), mismo estilo que `user_repository_adapter.py`; sin ORM
      declarativo para 2 tablas. `present_value`/`units` se persisten como
      `TEXT` homogéneo (no una columna tipada por tipo de objeto BACnet) — el
      dominio de esta feature es "candidato crudo mostrado tal cual", no
      cálculo numérico; tipar por tipo de objeto sin un caso de uso real que lo
      necesite sería abstracción especulativa. Una excepción declarada en §7
      (extracción de `metadata` compartida de `models/user_model.py` a
      `models/base.py`, toca un archivo `verified` de `SRV-002` sin cambiar su
      comportamiento).
- [x] **Integration-First** — `hira-server/docs/openapi.yaml` se amplía **antes**
      que `routers/devices.py` (paso 10 de §6); `core/ports/
      bacnet_transport_port.py` y `core/ports/device_repository_port.py`
      (`Protocol`) se definen antes que sus adaptadores concretos
      (`adapters/bacnet/bac0_adapter.py`, `adapters/db/
      device_repository_adapter.py`).

## 1. Cumplimiento constitucional
| Artículo | Cómo lo respeta este plan |
|---|---|
| Art. 1–2 (patrón) | Hexagonal puro: `services/device_scan_service.py` solo importa de `core/ports/` (`BacnetTransportPort`, `DeviceRepositoryPort`); `adapters/factory.py` inyecta `BAC0Adapter`/`PostgreSQLDeviceRepository`. Ningún router instancia un adaptador directamente (`SRV-ADR-017`, overlay de `hira-server/CLAUDE.md`: "si un módulo de `services/` importa... `BAC0`... viola la arquitectura"). |
| Art. 3 (testing) | Pruebas por zona (§5): núcleo (`core/bacnet_address.py`) sin mocks; coordinación (`services/device_scan_service.py`) con dobles de ambos puertos; adaptador BAC0 con **dos instancias reales de `BAC0` por UDP en localhost** (sin hardware, sin mocks — `spec.md §2`); adaptador de repositorio contra Postgres real con la migración `0002` aplicada; router con `TestClient`. |
| Art. 4 (persistencia) | `DeviceRepositoryPort` es el `StoragePort` de dominio para `devices`/`device_points_candidates` — distinto de `DatabasePort` (*liveness*-only) y de `UserRepositoryPort` (dominio de usuarios), mismo criterio ya fijado en `SRV-002-auth-rbac/plan.md` (Registro de decisiones). Segunda y tercera tabla de negocio del producto → migración Alembic `0002` (§3). |
| Art. 5 (seguridad) | RBAC ya cubierto por `SRV-002` (`require_role("admin", "operador")`, RF-003). Sin credenciales BACnet que proteger: BACnet/IP local no lleva autenticación en el protocolo estándar (`spec.md` no pide ninguna) — no se inventa un requisito de seguridad ausente del spec (Art. 10: no anticipar). |
| Art. 6 (contratos/errores) | Los 3 endpoints usan el sobre RFC 9457 solo donde hay error de negocio (`GET /devices/{id}/candidates` → 404 `device-not-found`, cualquiera de los 3 → 403 `insufficient-role` vía `require_role`, ya existente). Convención de `type` = `https://hira.dev/errors/<slug>` ya fijada por `E-ADR-003`; el catálogo de slugs de esta feature vive en §4 (el ADR no exige registro central, `E-ADR-003 §Decisión`). |
| Art. 10 (regla de raíz) | `DeviceRepositoryPort` nuevo (no forzar sus métodos en `DatabasePort`/`UserRepositoryPort`) — mismo razonamiento ya aplicado 2 veces en el ecosistema. `BacnetTransportPort` nuevo (no importar `BAC0` desde `services/`) — es la corrección de raíz exigida explícitamente por el overlay de `hira-server/CLAUDE.md`. |
| Art. 11 (documentación) | §8 de este plan — 1 fila, tarea `[doc]` en `tasks.md`. |

## Registro de decisiones de diseño (nuevas de este plan)
| Decisión | Justificación | Alternativa descartada |
|---|---|---|
| `BacnetTransportPort` nuevo en `core/ports/`, con value objects propios (`BacnetDeviceAnnouncement`, `BacnetObjectReading`, `BacnetReadTimeoutError`) — nunca un tipo de `BAC0`/`bacpypes3` cruza a `services/` | `SRV-ADR-017`/overlay `hira-server/CLAUDE.md`: "si un módulo de `services/` importa... `BAC0`... viola la arquitectura". `BAC0` (2026.7.25, verificado contra el wheel real — ver §2) expone objetos internos de `bacpypes3` (PDUs, `Point`) con atributos específicos de la librería; forzar a `services/` a conocerlos acoplaría el dominio a una librería de protocolo concreta, igual que se evitó con `psycopg2`/`asyncpg` en `DatabasePort` | Que `device_scan_service.py` importe `BAC0` directamente y opere sobre sus objetos |
| `DeviceRepositoryPort` nuevo, no reutilizar `DatabasePort` ni forzarlo en `UserRepositoryPort` | `DatabasePort` es *liveness*-only (`SRV-001`); `UserRepositoryPort` es un repositorio de un dominio distinto (usuarios). Un tercer dominio (dispositivos/candidatos) exige su propio `Protocol`, mismo razonamiento ya registrado en `SRV-002-auth-rbac/plan.md` (Registro de decisiones) y explícitamente pedido por la tarea | Añadir `upsert_device`/etc. a `DatabasePort` o a `UserRepositoryPort` |
| `devices.address` combina instance number + dirección de red BACnet en un solo `VARCHAR` (`spec.md §3`: "instance number + IP:puerto"), con formato fijo `"<instance_number>@<network_address>"` (p. ej. `"1234@192.168.1.50:47808"`), construido/parseado por 2 funciones puras nuevas en `core/bacnet_address.py` | El spec ya cerró una sola columna combinada (no 2 columnas separadas) — se necesita una convención de formato **determinista y probada de forma aislada** para no reinventarla ad-hoc en el servicio de coordinación ni en el adaptador; es la única regla de negocio pura de esta feature (parseo/validación de un value object), por eso vive en `core/` sin I/O, testeable sin mocks | Formatear el string ad-hoc dentro de `device_scan_service.py` (duplicaría la regla si `GET /devices` alguna vez necesitara decodificarla) o 2 columnas separadas en `devices` (contradice `spec.md §3` ya cerrado) |
| Constraint único `(protocol, address)` en `devices` (no solo `id` PK) | RF-002 exige "creándolo... si no existe" — necesita una clave natural para decidir *insert* vs *update* en cada escaneo; sin este único, un segundo escaneo del mismo dispositivo crearía una fila duplicada, violando RF-002 y el criterio de "un segundo escaneo actualiza, no duplica" ya fijado para `device_points_candidates` (`spec.md §3`) — se aplica el mismo criterio a `devices` por consistencia | Buscar por `address` con `SELECT` + rama `if/else` en el adaptador en vez de `ON CONFLICT` — más frágil ante una carrera entre 2 escaneos concurrentes (fuera de alcance evitarlo con locks, pero el `ON CONFLICT` es gratis y no añade complejidad) |
| `present_value`/`units` en `device_points_candidates` como `TEXT`, no tipado por tipo de objeto BACnet | El candidato es un valor crudo mostrado tal cual (`spec.md §2`: "sin escritura, sin polling") — no hay cálculo numérico sobre él en esta feature; tipar por tipo de objeto (analog=`FLOAT`, binary=`BOOLEAN`, multistate=`INTEGER`) es la abstracción correcta cuando exista la feature de asociación/polling real, no antes (Art. 10: no anticipar) | Columnas tipadas o una tabla de tipos de valor separada |
| `metadata` compartida extraída de `models/user_model.py` a `models/base.py` (import re-exportado, sin cambio de comportamiento) | `alembic/env.py::target_metadata` necesita ver **ambas** tablas nuevas (`devices`, `device_points_candidates`) además de `users` para que utilidades futuras (`metadata.create_all()` en tests, autogenerate si se usa algún día) las reconozcan todas bajo un único `MetaData()`; que `device_model.py` importara `metadata` directo de `user_model.py` acoplaría semánticamente "modelo de dispositivos" a "modelo de usuarios" sin motivo de dominio — la corrección de raíz es un módulo neutro (Art. 10) | `device_model.py` con su propio `MetaData()` independiente (2 metadatas — `alembic upgrade head` solo vería una según cuál importe `env.py`, riesgo real de una tabla que nunca se migra) o que `device_model.py` importe `from models.user_model import metadata` (acopla dispositivos a usuarios sin razón de dominio) |
| Lectura de objetos por dispositivo (RF-002) en paralelo con `asyncio.gather`, cada tarea con **su propio** manejo interno de `BacnetReadTimeoutError` (RF-006) — nunca `return_exceptions=True` en el `gather` | RNF-001 pide paralelismo "si es razonable"; RF-006 exige que un dispositivo sin respuesta no aborte el resto. Si cada corrutina captura su propio timeout y retorna `None` en vez de propagar, el `gather` nunca ve una excepción que gestionar — más simple y explícito que decidir caso por caso qué hacer con una lista mixta de resultados/excepciones de `return_exceptions=True` | `return_exceptions=True` + inspección posterior de qué elementos son `Exception` |
| `Settings.bacnet_ip`/`bacnet_port` opcionales (`str \| None = None`, `int \| None = None`), sin exigirlos en el arranque | `BAC0.lite(ip=None)` autodetecta la interfaz/IP local vía `HostIP()` (verificado en el código de `BAC0==2026.7.25`, `scripts/Lite.py`) — comportamiento correcto para el caso normal (un solo NIC en el host on-premise); fijarlos es un ajuste operativo excepcional (multi-NIC), no una variable obligatoria de cada despliegue | Añadir `bacnet_ip`/`bacnet_port` como campos requeridos de `Settings` |

## 2. Arquitectura de la feature *(Hexagonal)*

### Núcleo de negocio — sin I/O, sin ports/adapters, testeable sin mocks
- **`core/bacnet_address.py`** ← única regla de negocio pura de esta feature:
  `format_device_address(instance_number: int, network_address: str) -> str`
  (RF-002: construye `"<instance_number>@<network_address>"`, valida
  `instance_number >= 0` y `network_address` no vacío, lanza `ValueError` si no)
  y `parse_device_address(address: str) -> tuple[int, str]` (inverso — usado por
  `GET /devices` si algún consumidor futuro necesita descomponer la dirección
  sin volver a tocar el escaneo; se incluye ahora porque es el inverso trivial
  de la misma regla, no una anticipación de un caso de uso nuevo).
- **`core/errors.py`** (ya existe, `SRV-002`) — se reutiliza tal cual, sin
  cambios de contrato; esta feature solo añade **sitios de uso** nuevos
  (`routers/devices.py`) del slug `device-not-found` (404) — ver §4. No se crea
  un catálogo central de slugs (`E-ADR-003` ya decidió que vive distribuido por
  `plan.md`).

### Coordinación (casos de uso / fronteras de entrada)
- **`services/device_scan_service.py`**:
  - Constantes: `WHOIS_TIMEOUT_SECONDS = 3.0` (RF-001), `READ_TIMEOUT_SECONDS = 2.0` (RF-006, RF-010).
  - `scan_bacnet(transport: BacnetTransportPort, device_repo: DeviceRepositoryPort) -> list[DeviceRecord]` ← **RF-001, RF-002, RF-006, RF-008, RNF-001**:
    1. `announcements = await transport.who_is(WHOIS_TIMEOUT_SECONDS)` — Who-Is
       broadcast, espera 3s (RF-001). Si `announcements` está vacío, retorna
       `[]` sin tocar `device_repo` (RF-008 — 200 con lista vacía, no es error).
    2. Por cada `announcement`, dispara una corrutina `_scan_one(announcement)`
       en paralelo (`asyncio.gather`, RNF-001) que:
       a. `address = format_device_address(announcement.instance_number, announcement.address)` (`core/bacnet_address.py`).
       b. `device = await device_repo.upsert_device(name=f"BACnet {announcement.instance_number}", protocol="bacnet", address=address, is_simulator=False)` (RF-002 — crea o actualiza `last_seen_at`).
       c. `try: readings = await transport.read_device_objects(announcement.address, READ_TIMEOUT_SECONDS)` — si `BacnetReadTimeoutError`: `logger.warning(...)` (RF-006, incluye `device.id`/`address`) y **retorna sin lanzar** (el dispositivo queda persistido con `last_seen_at` actualizado, pero sin candidatos nuevos en este escaneo — no es un fallo del escaneo completo).
       d. Si la lectura tuvo éxito, por cada `reading` en `readings`: `await device_repo.upsert_candidate(device_id=device.id, object_type=reading.object_type, object_instance=reading.object_instance, object_name=reading.object_name, present_value=reading.present_value, units=reading.units)` (RF-002 — único por `(device_id, object_type, object_instance)`, actualiza si ya existía).
       e. Retorna `device` (o `None` si `upsert_device` en sí falló — no contemplado como caso normal, se deja propagar cualquier error de persistencia real, distinto de un timeout de red BACnet).
    3. Retorna la lista de `DeviceRecord` de los dispositivos tocados en este escaneo (para la respuesta HTTP de `POST /devices/scan/bacnet`).
  - **RF-007** (nunca promover un candidato a tabla operable) se cumple **por
    omisión de diseño**: este servicio no tiene ningún método que escriba en
    una tabla `points` (que ni siquiera existe todavía) — se verifica con un
    test de coordinación que confirma que ningún doble de un futuro
    `PointsRepositoryPort` es invocado (no existe tal puerto en este plan; el
    test documenta la ausencia explícitamente, no la infiere).

### Fronteras de salida
| Frontera | Para qué | Implementación concreta |
|---|---|---|
| Red BACnet/IP (Who-Is/I-Am, lectura de objetos) | Escaneo y lectura de dispositivos de campo | `adapters/bacnet/bac0_adapter.py::BAC0Adapter` implementa `BacnetTransportPort` con la librería `BAC0` real (`requirements.txt`, versión pineada `BAC0==2026.7.25`, con `bacpypes3` como dependencia transitiva ya fijada por `BAC0` — sin pinearla aparte salvo que un futuro conflicto lo exija) |
| PostgreSQL (`devices`, `device_points_candidates`) | Repositorio de dominio de dispositivos y candidatos | `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository` implementa `DeviceRepositoryPort` — SQLAlchemy Core (`Table`/`select`/`insert().on_conflict_do_update()`), mismo estilo que `user_repository_adapter.py` |

#### `core/ports/bacnet_transport_port.py` (nuevo)
```python
from dataclasses import dataclass
from typing import Protocol


class BacnetReadTimeoutError(Exception):
    """El dispositivo no respondió a la lectura de objetos dentro del timeout
    (RF-006, RF-010). Sin I/O — es una señal de dominio, no una excepción de
    red cruda de BAC0/bacpypes3."""


@dataclass(frozen=True)
class BacnetDeviceAnnouncement:
    """Un dispositivo que respondió I-Am durante un Who-Is (RF-001, RF-002)."""
    instance_number: int
    network_address: str  # dirección de red BACnet tal como la expone BAC0 (p. ej. "192.168.1.50:47808")


@dataclass(frozen=True)
class BacnetObjectReading:
    """Un objeto BACnet leído de un dispositivo (RF-002)."""
    object_type: str          # p. ej. "analogInput", "binaryOutput"
    object_instance: int
    object_name: str | None
    present_value: str | None  # serializado a texto — ver Registro de decisiones
    units: str | None


class BacnetTransportPort(Protocol):
    async def who_is(self, timeout_seconds: float) -> list[BacnetDeviceAnnouncement]:
        """Emite un Who-Is (broadcast en producción) y retorna los I-Am
        recibidos dentro de `timeout_seconds` (RF-001). Lista vacía si nadie
        responde (RF-008)."""
        ...

    async def read_device_objects(
        self, network_address: str, timeout_seconds: float
    ) -> list[BacnetObjectReading]:
        """Lee la lista de objetos del dispositivo en `network_address`
        (RF-002). Lanza `BacnetReadTimeoutError` si no responde dentro de
        `timeout_seconds` (RF-006, RF-010)."""
        ...
```

#### `core/ports/device_repository_port.py` (nuevo)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class DeviceRecord:
    id: str
    name: str
    protocol: str  # "bacnet" | "modbus" | "mqtt" — solo "bacnet" usado en esta feature
    address: str
    is_simulator: bool
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class DeviceCandidateRecord:
    id: str
    device_id: str
    object_type: str
    object_instance: int
    object_name: str | None
    present_value: str | None
    units: str | None
    discovered_at: datetime
    updated_at: datetime


class DeviceRepositoryPort(Protocol):
    async def upsert_device(
        self, *, name: str, protocol: str, address: str, is_simulator: bool = False
    ) -> DeviceRecord:
        """Crea o actualiza (único por `(protocol, address)`) un dispositivo,
        refrescando `last_seen_at` (RF-002)."""
        ...

    async def list_devices(self) -> list[DeviceRecord]:
        """RF-004."""
        ...

    async def get_device(self, device_id: str) -> DeviceRecord | None:
        """RF-009 — `None` si no existe (el router responde 404)."""
        ...

    async def upsert_candidate(
        self,
        *,
        device_id: str,
        object_type: str,
        object_instance: int,
        object_name: str | None,
        present_value: str | None,
        units: str | None,
    ) -> DeviceCandidateRecord:
        """Único por `(device_id, object_type, object_instance)` — actualiza
        `present_value`/`updated_at` si ya existía, no duplica (RF-002)."""
        ...

    async def list_candidates_for_device(self, device_id: str) -> list[DeviceCandidateRecord]:
        """RF-005."""
        ...
```

### Adaptadores de entrada
- `routers/devices.py`:
  - `POST /devices/scan/bacnet` — `require_role("admin", "operador")` (RF-003);
    invoca `services/device_scan_service.py::scan_bacnet` con
    `BacnetTransportPort`/`DeviceRepositoryPort` inyectados vía
    `Depends(adapters.factory.*)`; responde 200 con la lista de dispositivos
    tocados (`schemas/devices.py::DeviceOut`, puede ser `[]`, RF-008).
  - `GET /devices` — `require_role("admin", "operador")` (RF-003); lista todos
    los dispositivos persistidos (RF-004).
  - `GET /devices/{id}/candidates` — `require_role("admin", "operador")`
    (RF-003); `device_repo.get_device(id)` → `None` → `ProblemDetailError(404,
    "https://hira.dev/errors/device-not-found", "Dispositivo no encontrado",
    ...)` (RF-009); si existe, `device_repo.list_candidates_for_device(id)`
    (RF-005).
  - Ninguno instancia `BAC0Adapter`/`PostgreSQLDeviceRepository` directamente
    (`SRV-ADR-017`).
- `main.py` — se amplía: `app.include_router(devices_router)` (mismo patrón
  que `auth_router`/`monitor_router`, sin tocar el `lifespan` existente — esta
  feature no necesita una tarea de fondo nueva, a diferencia del suscriptor de
  invalidación de `SRV-002`).

### `adapters/factory.py` (se amplía)
- Nueva función `get_bacnet_transport_port() -> BacnetTransportPort`: nace en
  el **mismo paso** en que nace `routers/devices.py` (paso 11 de §6), con un
  **doble in-memory** (`_FakeBacnetTransport`, sin BAC0 real) — mismo patrón ya
  aplicado 2 veces en este ecosistema (`SRV-001` Directiva de Pausa §7,
  `SRV-002` proactivo con `get_user_repository_port`): el router necesita el
  punto de inyección desde que existe, `BAC0Adapter` real llega después (paso
  14) sin cambiar la firma.
- Nueva función `get_device_repository_port() -> DeviceRepositoryPort`: nace
  en el **mismo paso**, mismo criterio, con un doble in-memory
  (`_InMemoryDeviceRepository`) hasta que `PostgreSQLDeviceRepository` (paso
  16) reemplaza su cuerpo.
- Ambas cacheadas a nivel de módulo (singleton perezoso por proceso), mismo
  patrón que las 5 funciones ya existentes.

## 3. Modelo de datos
Segunda y tercera tabla de negocio del producto (tras `users` de `SRV-002`) —
segunda migración Alembic (`0002`, `down_revision = "0001"`, no reemplaza la
`0001` existente).

### Tabla `devices`
| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `UUID` | PK, default `uuid4()` (lado Python, mismo criterio que `users.id`) |
| `name` | `VARCHAR(255)` | `NOT NULL` |
| `protocol` | `VARCHAR(20)` | `NOT NULL`, `CHECK (protocol IN ('bacnet', 'modbus', 'mqtt'))` — solo `'bacnet'` usado en esta feature |
| `address` | `VARCHAR(255)` | `NOT NULL` — `"<instance_number>@<network_address>"` (`core/bacnet_address.py`) |
| `is_simulator` | `BOOLEAN` | `NOT NULL DEFAULT false` — columna presente para reutilización futura de Modbus/MQTT/Simuladores, sin lógica que la use todavía (`SRV-ADR-014`) |
| `last_seen_at` | `TIMESTAMPTZ` | `NULL` — se fija/actualiza en cada escaneo que detecta el dispositivo |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |

Índices: `UNIQUE (protocol, address)` (ver Registro de decisiones — clave de
*upsert* de RF-002).

### Tabla `device_points_candidates`
| Columna | Tipo | Restricciones |
|---|---|---|
| `id` | `UUID` | PK, default `uuid4()` |
| `device_id` | `UUID` | `NOT NULL`, `FK → devices.id ON DELETE CASCADE` |
| `object_type` | `VARCHAR(50)` | `NOT NULL` (p. ej. `analogInput`, `binaryOutput`) |
| `object_instance` | `INTEGER` | `NOT NULL` |
| `object_name` | `VARCHAR(255)` | `NULL` |
| `present_value` | `TEXT` | `NULL` — ver Registro de decisiones (sin tipar por tipo de objeto) |
| `units` | `VARCHAR(50)` | `NULL` |
| `discovered_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |

Índices: `UNIQUE (device_id, object_type, object_instance)` (RF-002: un
segundo escaneo actualiza, no duplica).

### Migraciones
- `hira-server/backend/alembic/versions/0002_create_devices_tables.py`
  (`revision = "0002"`, `down_revision = "0001"`, escrita a mano, mismo
  criterio que `0001` — 2 `CREATE TABLE` no justifican autogenerate). Crea
  `devices` y `device_points_candidates` en ese orden (la FK lo exige).
- `hira-server/backend/models/base.py` (nuevo) — `metadata = MetaData()`,
  único objeto compartido. `hira-server/backend/models/user_model.py` se
  **edita mínimamente** (import, sin cambio de comportamiento): `from
  models.base import metadata` en vez de declarar su propio `MetaData()` — ver
  Registro de decisiones. `hira-server/backend/models/device_model.py` (nuevo)
  — `devices_table`/`device_points_candidates_table` (`Table` Core) contra el
  mismo `metadata` importado de `models/base.py`.
- `hira-server/backend/alembic/env.py` — se amplía: importa
  `models.device_model` además de `models.user_model` (para que sus `Table`
  se registren en el `metadata` compartido antes de `target_metadata =
  models.base.metadata`); sin cambios en la lógica de conexión async ya
  existente.
- No se ejecuta automáticamente en el arranque del contenedor (mismo criterio
  ya documentado en `SRV-002-auth-rbac/plan.md §3` — paso operativo explícito
  `docker compose exec backend alembic upgrade head`).

## 4. Contratos
| Archivo en `contracts/` | Frontera | Gate(s) de CI |
|---|---|---|
| `.harness/specs/SRV-003-bacnet-adapter/contracts/openapi.yaml` — copia congelada al cierre de Fase 2/4; la fuente **viva** es `hira-server/docs/openapi.yaml` (se **amplía**, no se reemplaza — `/health` y `/auth/*` intactos) | `POST /devices/scan/bacnet`, `GET /devices`, `GET /devices/{id}/candidates` | `gate/check.sh` bloque 5 (Spectral lint, mismo warn conocido de tooling ya aceptado en `SRV-001`/`SRV-002`) |

### Sobre de error — RFC 9457 (reutiliza `ProblemDetail`, `E-ADR-003`)
| Endpoint | HTTP | `type` (slug) | `title` | Cuándo |
|---|---|---|---|---|
| Los 3 endpoints (vía `require_role`, ya existente) | 403 | `insufficient-role` | "Rol insuficiente" | Visor invoca cualquiera de los 3 (RF-003) — slug reutilizado de `SRV-002`, no se redefine |
| `GET /devices/{id}/candidates` | 404 | `device-not-found` | "Dispositivo no encontrado" | `id` no existe (RF-009) — slug **nuevo** de esta feature |

`POST /devices/scan/bacnet` y `GET /devices` no tienen una rama de error de
negocio propia en esta feature (RF-008: 0 dispositivos es 200, no error) —
solo heredan el 403 de `require_role`.

### Esquemas nuevos (`hira-server/docs/openapi.yaml` — extracto)
```yaml
DeviceOut:
  type: object
  required: [id, name, protocol, address, is_simulator, last_seen_at]
  properties:
    id: { type: string, format: uuid }
    name: { type: string }
    protocol: { type: string, enum: [bacnet, modbus, mqtt] }
    address: { type: string }
    is_simulator: { type: boolean }
    last_seen_at: { type: string, format: date-time, nullable: true }
DeviceCandidateOut:
  type: object
  required: [id, object_type, object_instance, object_name, present_value, units, discovered_at, updated_at]
  properties:
    id: { type: string, format: uuid }
    object_type: { type: string }
    object_instance: { type: integer }
    object_name: { type: string, nullable: true }
    present_value: { type: string, nullable: true }
    units: { type: string, nullable: true }
    discovered_at: { type: string, format: date-time }
    updated_at: { type: string, format: date-time }
```
`POST /devices/scan/bacnet` → `200: DeviceOut[]` (puede ser `[]`, RF-008).
`GET /devices` → `200: DeviceOut[]`. `GET /devices/{id}/candidates` → `200:
DeviceCandidateOut[]` | `404: ProblemDetail`.

## 5. Estrategia de pruebas (por zona del patrón)
| Zona | Qué se prueba | Herramienta |
|---|---|---|
| Núcleo (`core/bacnet_address.py`) | `format_device_address`/`parse_device_address` son inversos exactos; rechaza `instance_number < 0` y `network_address` vacío | unit puro, **sin mocks** — RF-002 |
| Coordinación (`services/device_scan_service.py`) | *Camino feliz*: 2 I-Am → 2 `upsert_device` + N `upsert_candidate` (RF-001, RF-002); *sin respuesta*: `who_is` retorna `[]` → `[]` sin tocar `DeviceRepositoryPort` (RF-008); *timeout parcial*: 1 de 2 dispositivos lanza `BacnetReadTimeoutError` en `read_device_objects` → el otro se persiste igual, el que falló se loguea y no aborta el `gather` (RF-006); *paralelismo*: verificar (con un doble que registra timestamps de entrada/salida) que las N llamadas a `read_device_objects` se solapan en el tiempo, no son estrictamente secuenciales (RNF-001); *RF-007*: ningún método de `services/device_scan_service.py` escribe en una tabla de puntos operables — verificado por inspección de imports del módulo (no importa nada de un futuro `PointsRepositoryPort`, que no existe) | unit + dobles (`Protocol` fakes) de `BacnetTransportPort`/`DeviceRepositoryPort` |
| Adaptador BAC0 (`adapters/bacnet/bac0_adapter.py`) — **verificación de integración real sin hardware** | Dos instancias reales de `BAC0.lite()` en `127.0.0.1` con puertos UDP distintos (p. ej. `47808`/`47809`, mismo host — sin broadcast real de LAN, ver nota abajo): una actúa de "dispositivo" (se le agregan 1-2 objetos locales reales, `bacpypes3.local.analog.AnalogValueObject`/`bacpypes3.local.binary.BinaryValueObject`, vía `<instancia>.this_application.app.add_object(obj)` — API confirmada contra el wheel real de `bacpypes3==0.0.106`, diseñada explícitamente "for sample applications"); la otra instancia (`BAC0Adapter` bajo prueba) ejecuta `who_is(timeout_seconds=...)` dirigido a esa dirección/puerto y `read_device_objects(...)` reales — Who-Is/I-Am y lectura de objetos por UDP real, sin mocks (`spec.md §2`). Verifica: I-Am recibido con el `instance_number` correcto (RF-001); objetos leídos coinciden con los creados en el "dispositivo" (RF-002); `BacnetReadTimeoutError` si se apaga el "dispositivo" tras el I-Am y antes de la lectura (RF-006/RF-010, timeout real de 2s) | integración — 2 procesos/instancias `BAC0` reales en la misma máquina de test, **no es el producto "Simuladores"** (`SRV-ADR-014`), es infraestructura de test de esta feature |
| Adaptador de repositorio (`PostgreSQLDeviceRepository`) | `upsert_device` crea y luego actualiza (mismo `protocol`+`address`) sin duplicar, refresca `last_seen_at`; `upsert_candidate` ídem por `(device_id, object_type, object_instance)`; `get_device` retorna `None` si no existe; `list_devices`/`list_candidates_for_device` reflejan lo persistido — contra Postgres real con la migración `0002` aplicada | integración — `docker compose up -d postgres` + `alembic upgrade head` + `pytest -m integration` |
| Router (`routers/devices.py`) | Contrato exacto de `openapi.yaml` (`TestClient`, con `BacnetTransportPort`/`DeviceRepositoryPort` in-memory del placeholder de `factory.py`) — 200 con lista (vacía y no vacía), 404 `device-not-found` con *shape* RFC 9457 exacto, 403 con Visor (reutiliza el mecanismo de `require_role` ya verificado en `SRV-002`, sin reprobar `require_role` en sí) | unit + `TestClient`, sin contenedores |
| Sistema (e2e) | `POST /devices/scan/bacnet` real (BAC0 real + Postgres real) → `GET /devices` refleja el dispositivo → `GET /devices/{id}/candidates` refleja sus objetos — un solo recorrido con las 2 instancias `BAC0` de la fila de adaptador de arriba, más el backend completo levantado | integración — contenedores reales del compose + las 2 instancias `BAC0` del test de adaptador |

> **Nota sobre "Who-Is broadcast" en el test de adaptador:** en producción,
> `who_is()` sin `address` es un broadcast local real (`spec.md §2`/RF-001). En
> el test, para no depender de que el broadcast UDP atraviese la red del
> entorno de CI (variable según el runner/contenedor), el "escáner" dirige el
> Who-Is a la dirección/puerto específico del "dispositivo" simulado
> (`who_is(address="127.0.0.1:<puerto>")`, parámetro `address` ya soportado
> por `BAC0.who_is`, verificado contra el wheel real) — sigue siendo Who-Is/
> I-Am real por UDP con el mismo códec del protocolo, cambia solo el modo de
> direccionamiento (unicast dirigido vs. broadcast), no la verificación de
> `BacnetTransportPort` en sí (que no distingue el modo, solo consume la
> respuesta). El broadcast real de RF-001 en producción **no** se re-verifica
> aquí; queda cubierto por el hecho de que `BAC0.who_is(address=None)` es la
> misma llamada de librería con un parámetro distinto, sin lógica propia de
> `BAC0Adapter` de por medio que dependa del modo de direccionamiento.

> **Duda abierta para Gate 2** (no bloquea el diseño, sí el primer *spike* de
> Fase 4): la investigación de este plan confirmó contra el código fuente real
> de `BAC0==2026.7.25`/`bacpypes3==0.0.106` (i) `bacnet.who_is(address=None,
> timeout=N) -> list[...]` como el método de escaneo, (ii) `await
> BAC0.device(address, device_id, bacnet_instance) -> Device` como el
> mecanismo de lectura de objetos de un dispositivo remoto (construye
> `.points` automáticamente), y (iii) `Application.add_object(obj)` +
> `bacpypes3.local.analog/binary.*Object` como el mecanismo estándar (citado en
> el propio código fuente como pensado "for sample applications") para crear
> el "dispositivo" mínimo del test. **No verificado con evidencia de
> ejecución real** (esta fase no ejecuta código): el nombre exacto de los
> atributos de cada `Point` devuelto por `BAC0.device(...)` (mapeo a
> `BacnetObjectReading.object_type`/`object_name`/`present_value`/`units`) y
> la forma exacta del objeto que retorna `who_is()` (para extraer
> `instance_number`/`network_address`). Se resuelve con un *spike* de una
> sesión al inicio de Fase 4 (antes de escribir `bac0_adapter.py` en firme),
> sin impacto en el contrato del puerto (`BacnetTransportPort` ya está fijado
> en value objects propios, agnósticos de esos detalles).

## 6. Secuenciación de archivos (tests antes que código)
1. `tests/test_bacnet_address.py` (falla) → `core/bacnet_address.py` — RF-002.
2. `core/ports/bacnet_transport_port.py` (`BacnetTransportPort`,
   `BacnetDeviceAnnouncement`, `BacnetObjectReading`, `BacnetReadTimeoutError`
   — `Protocol`, sin test propio, igual que `database_port.py`/
   `user_repository_port.py`).
3. `core/ports/device_repository_port.py` (`DeviceRepositoryPort`,
   `DeviceRecord`, `DeviceCandidateRecord` — `Protocol`, sin test propio).
4. `tests/test_device_scan_service.py` (dobles de ambos puertos, falla) →
   `services/device_scan_service.py::scan_bacnet` — RF-001, RF-002, RF-006,
   RF-007, RF-008, RNF-001.
5. `hira-server/docs/openapi.yaml` (Contract-First, antes del router) — amplía
   con los 3 endpoints, sin tocar `/health`/`/auth/*`.
6. `tests/test_devices_router.py` (`TestClient`, falla) → `routers/devices.py`
   + `schemas/devices.py` (`DeviceOut`, `DeviceCandidateOut`) +
   **`adapters/factory.py::get_bacnet_transport_port()`/
   `get_device_repository_port()`** (nacen aquí con dobles in-memory — mismo
   patrón que la Directiva de Pausa de `SRV-001`/proactivo de `SRV-002`: el
   router necesita el punto de inyección desde que existe) + registro en
   `main.py` (`include_router`) — RF-001, RF-003, RF-004, RF-005, RF-008,
   RF-009 vía HTTP con dobles in-memory.
7. `hira-server/backend/models/base.py` (nuevo, `metadata` compartida) +
   edición mínima de `hira-server/backend/models/user_model.py` (importa
   `metadata` de `models/base.py` en vez de declarar la suya — sin cambio de
   comportamiento, `tests/test_user_model.py`/suite de `SRV-002` debe seguir
   en verde sin modificar sus aserciones).
8. `hira-server/backend/models/device_model.py` (`devices_table`,
   `device_points_candidates_table`, Core `Table`) — soporta el modelo de
   datos de §3.
9. `hira-server/backend/alembic/env.py` (ampliar: importar
   `models.device_model`) + `alembic/versions/
   0002_create_devices_tables.py` (`down_revision="0001"`).
10. `tests/integration/test_bac0_adapter.py` (falla, requiere 2 instancias
    reales de `BAC0` — ver §5) → `adapters/bacnet/bac0_adapter.py::BAC0Adapter`
    + `BAC0==2026.7.25` en `requirements.txt` — reemplaza el **cuerpo** (no la
    firma) de `adapters/factory.py::get_bacnet_transport_port()` — RF-001,
    RF-002, RF-006, RF-010 (reales).
11. `tests/integration/test_device_repository_adapter.py` (falla, requiere
    Postgres real + migración `0002` aplicada) → `adapters/db/
    device_repository_adapter.py::PostgreSQLDeviceRepository` — reemplaza el
    **cuerpo** de `adapters/factory.py::get_device_repository_port()` — RF-002,
    RF-004, RF-005, RF-009.
12. `tests/integration/test_devices_scan_e2e.py` (contenedores reales +
    2 instancias `BAC0` reales) — recorrido completo `POST /devices/scan/
    bacnet` → `GET /devices` → `GET /devices/{id}/candidates` (RF-001, RF-002,
    RF-004, RF-005, RF-008, RF-009, RNF-001 medido con evidencia real).
13. `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` — nota
    `[doc]` de §8 (puede ejecutarse en paralelo desde el paso 1).
14. `hira-server/backend/adapters/bacnet/README.md`,
    `hira-server/backend/adapters/db/README.md` (ampliar, ya existe) —
    documentan las carpetas nuevas/ampliadas (regla de `hira-server/CLAUDE.md`:
    "cada carpeta que creas lleva su `README.md`").

> `.harness/gate/services.txt` ya declara `hira-server/backend:python`
> (`SRV-001`) — sin cambios necesarios, la suite nueva se integra en la misma
> suite de `pytest`.

## 7. Seguimiento de complejidad
| Excepción a la simplicidad | Justificación |
|---|---|
| `models/user_model.py` (archivo `verified` de `SRV-002`) se edita para importar `metadata` desde `models/base.py` nuevo, en vez de dejarlo intacto | Es la única forma de que `alembic/env.py` migre `users`, `devices` y `device_points_candidates` bajo un único `MetaData()` sin arriesgar que una tabla quede fuera del `target_metadata` real (Art. 10: la corrección va a la raíz — un módulo de metadata compartido — no a duplicar `MetaData()` por feature). El cambio es de una sola línea de import, sin alterar columnas/constraints/comportamiento de `users`; la suite existente de `SRV-002` debe seguir en verde sin relajar ninguna aserción (paso 7 de §6). |
| Constraint único `(protocol, address)` en `devices`, no pedido letra por letra en `spec.md §3` | `spec.md §3` fija las columnas pero no un índice único explícito; es una inferencia necesaria para que RF-002 ("creándolo si no existe") sea implementable sin duplicados — mismo criterio que el único ya fijado para `device_points_candidates`, que sí está explícito en el spec. No es una ampliación de alcance, es completar el modelo de datos al nivel de detalle que Fase 2 debe resolver. |

## 8. Impacto en documentación *(obligatorio — Constitución Art. 11)*
| Documento del mapa | Qué cambia | Acción |
|---|---|---|
| `docs/hira-server/spec/modules/dispositivos-protocolos-puntos.md` | La sección "Escaneo y descubrimiento" ya describe correctamente el mecanismo BACnet (Who-Is/I-Am, `device_points_candidates`) — **no queda obsoleta**, esta feature la implementa tal como está escrita. La frase "Solo opera sobre puntos asociados... nunca sobre candidatos crudos" (Responsabilidad, línea 17) sigue siendo cierta: esta feature no toca el Motor de Protocolos ni crea `points`. Lo que sí falta es una nota que **acote el alcance actual**: hoy el documento describe el módulo completo (incluye Modbus, MQTT, polling, escritura, `asyncio.Lock`, MSTP) como si ya existiera; tras esta feature, solo el escaneo BACnet/IP + candidatos es código real | `[doc]` añadir una nota al inicio del documento (bajo "Responsabilidad" o como aviso de estado): "Implementado a la fecha (`SRV-003-bacnet-adapter`): escaneo BACnet/IP (Who-Is/I-Am) y persistencia de candidatos. Modbus, MQTT, polling, escritura, `asyncio.Lock` por dispositivo, BACnet MSTP y Simuladores siguen siendo diseño, no código — ver `ROADMAP.md`/`.harness/specs/` para el estado real por sub-feature." Sin reescribir el resto del documento (sigue siendo el diseño válido de destino) |

`hira-server/docs/openapi.yaml` **no** es un doc del mapa Art. 11 — es el
contrato de producto de esta frontera, ya cubierto en §4 (se amplía, no se
reemplaza).

`docs/hira-server/spec/validation/acceptance-criteria.md` (`AC-SRV-03`) **no**
se toca: esta feature deja verificable `AC-SRV-03.1` (escaneo descubre
dispositivos) y una parte de `.6` (detección de "sin respuesta" durante el
escaneo mismo, RF-006) — no `.6` completo (detección de desconexión durante
*polling* continuo, que no existe todavía) ni `.2`-`.5`/`.7` (asociación,
escritura, polling, lock de escritura concurrente — features posteriores,
`spec.md §2` "Fuera de alcance"). Igual que `SRV-002-auth-rbac/plan.md §8`
decidió con `AC-SRV-02.3`/`.4`: no hay nada que quede obsoleto en ese
documento por este plan, se verificará por completo cuando lleguen esas
features.

`docs/hira-server/spec/validation/vulnerabilities.md::VUL-SRV-005` **no** se
toca: sigue 🔴 Abierto, sin cambio de estado — esta feature no implementa
escritura ni polling concurrente (`spec.md §2`/§6 ya lo diferenció
explícitamente), por lo que no aporta evidencia que mueva su estado.

## 9. Implementación por requisito

### Implementación de RF-001
- `core/ports/bacnet_transport_port.py::BacnetTransportPort.who_is`.
- `adapters/bacnet/bac0_adapter.py::BAC0Adapter.who_is` (Who-Is real, ventana 3s).
- `services/device_scan_service.py::scan_bacnet` (`WHOIS_TIMEOUT_SECONDS = 3.0`).
- `routers/devices.py::POST /devices/scan/bacnet`.
- `hira-server/docs/openapi.yaml#/paths/~1devices~1scan~1bacnet`.
- Tests: `tests/test_device_scan_service.py`, `tests/integration/test_bac0_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.
- `covers`: `hira-server/backend/core/ports/bacnet_transport_port.py`, `hira-server/backend/adapters/bacnet/bac0_adapter.py`, `hira-server/backend/services/device_scan_service.py`, `hira-server/backend/routers/devices.py`.

### Implementación de RF-002
- `core/bacnet_address.py::format_device_address`.
- `adapters/bacnet/bac0_adapter.py::BAC0Adapter.read_device_objects`.
- `core/ports/device_repository_port.py::DeviceRepositoryPort.upsert_device/upsert_candidate`.
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.upsert_device/upsert_candidate` (`ON CONFLICT`).
- `services/device_scan_service.py::scan_bacnet` (rama de éxito).
- Tests: `tests/test_bacnet_address.py`, `tests/test_device_scan_service.py`, `tests/integration/test_bac0_adapter.py`, `tests/integration/test_device_repository_adapter.py`, `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-003
- `core/security/dependencies.py::require_role("admin", "operador")` — **reutilizado tal cual** de `SRV-002`, sin cambios.
- `routers/devices.py` (los 3 endpoints, `Depends(require_role("admin", "operador"))`).
- Tests: `tests/test_devices_router.py` (403 con Visor), `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-004
- `core/ports/device_repository_port.py::DeviceRepositoryPort.list_devices`.
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.list_devices`.
- `routers/devices.py::GET /devices`, `schemas/devices.py::DeviceOut`.
- `hira-server/docs/openapi.yaml#/paths/~1devices`.
- Tests: `tests/test_devices_router.py`, `tests/integration/test_device_repository_adapter.py`.

### Implementación de RF-005
- `core/ports/device_repository_port.py::DeviceRepositoryPort.list_candidates_for_device`.
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.list_candidates_for_device`.
- `routers/devices.py::GET /devices/{id}/candidates`, `schemas/devices.py::DeviceCandidateOut`.
- `hira-server/docs/openapi.yaml#/paths/~1devices~1{id}~1candidates`.
- Tests: `tests/test_devices_router.py`, `tests/integration/test_device_repository_adapter.py`.

### Implementación de RF-006
- `core/ports/bacnet_transport_port.py::BacnetReadTimeoutError`.
- `adapters/bacnet/bac0_adapter.py::BAC0Adapter.read_device_objects` (`asyncio.wait_for`, `READ_TIMEOUT_SECONDS`).
- `services/device_scan_service.py::scan_bacnet` (captura por dispositivo, `logger.warning`, continúa el `gather`).
- Tests: `tests/test_device_scan_service.py` (timeout parcial), `tests/integration/test_bac0_adapter.py` (timeout real).

### Implementación de RF-007
- Ausencia de diseño verificada: `services/device_scan_service.py` no importa ni referencia ninguna tabla/puerto de `points`.
- Tests: `tests/test_device_scan_service.py` (test explícito que documenta la ausencia — inspección de imports del módulo).

### Implementación de RF-008
- `services/device_scan_service.py::scan_bacnet` (rama `announcements == []` → `[]`).
- `routers/devices.py::POST /devices/scan/bacnet` (200 con lista vacía, no 4xx/5xx).
- Tests: `tests/test_device_scan_service.py`, `tests/test_devices_router.py`, `tests/integration/test_devices_scan_e2e.py`.

### Implementación de RF-009
- `routers/devices.py::GET /devices/{id}/candidates` (rama `get_device(id) is None` → `ProblemDetailError(404, "device-not-found", ...)`).
- `core/ports/device_repository_port.py::DeviceRepositoryPort.get_device`.
- `adapters/db/device_repository_adapter.py::PostgreSQLDeviceRepository.get_device`.
- Tests: `tests/test_devices_router.py` (404 con `id` inexistente), `tests/integration/test_device_repository_adapter.py`.

### Implementación de RF-010
- `services/device_scan_service.py::READ_TIMEOUT_SECONDS = 2.0`.
- `adapters/bacnet/bac0_adapter.py::BAC0Adapter.read_device_objects` (aplica el timeout recibido, `asyncio.wait_for`).
- Tests: `tests/integration/test_bac0_adapter.py` (mide el timeout real ≈2s).

### Implementación de RNF-001
- `services/device_scan_service.py::scan_bacnet` (`asyncio.gather` — lecturas en paralelo, no secuenciales).
- Medición: `tests/test_device_scan_service.py` (paralelismo con dobles, timestamps solapados — evidencia rápida) y
  `tests/integration/test_devices_scan_e2e.py` (medición real de duración total del escaneo con N dispositivos simulados, contra Postgres/BAC0 reales — evidencia de terminal pegada, mismo criterio de Art. 3 "verificación real, nunca esperada").
