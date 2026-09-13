"""`main.py::lifespan` — arranque validado (RF-003, `spec.md`).

Wiring de `Settings()` en el `lifespan` de FastAPI: si falta una variable de entorno
requerida, `pydantic.ValidationError` se captura, se loguea en JSON (`level: error`)
nombrando el/los campo(s) faltante(s) vía `core/logger.py`, y el arranque se aborta
(`sys.exit(1)`) — nunca arranque parcial (`plan.md §2`, `tasks.md` T-012).

Wiring de `MosquittoAdapter.connect()` en el mismo `lifespan` (RF-006/RF-008,
`plan.md §7` Directiva de Pausa #2, `tasks.md` T-022 ampliada): a diferencia del
error de `Settings()`, un fallo de conexión a Mosquitto **no** aborta el arranque
— se loguea y el estado queda para que `/health` lo refleje vía `ping()` (RF-007).
Los tests de esta sección usan un doble (`AsyncMock`) de `MosquittoAdapter.connect`
para no depender de un broker real ni de los 7s de backoff (1s/2s/4s) — el backoff
en sí ya está probado de forma aislada contra un contenedor real en
`tests/integration/test_adapters.py` (T-021/T-022); lo que se verifica aquí es
que el proceso real de arranque **invoca** `connect()`, no que el backoff funcione.

Ampliado en T-036/T-037 (`plan.md §10`, resolución de RNF-001): el `lifespan`
también arranca `services/rbac_service.py::run_invalidation_subscriber` como
tarea de fondo (`asyncio.create_task`), junto al `connect()` de Mosquitto, y la
cancela limpio (`task.cancel()` + `await task` sin excepción sin capturar) en el
*shutdown*. Se usa un doble de `CachePort.subscribe` controlado por el test
(nunca produce mensajes) para no depender de Redis real.
"""
import asyncio
import json
from unittest.mock import AsyncMock

import pytest

import adapters.factory as factory
import main as main_module
from adapters.mqtt.mosquitto_adapter import MosquittoAdapter
from main import app, lifespan

REQUIRED_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://hira:hira@postgres:5432/hiradb",
    "REDIS_URL": "redis://redis:6379/0",
    "MQTT_BROKER_HOST": "mosquitto",
    "MQTT_USER": "hira",
    "MQTT_PASSWORD": "s3cret",
    "SECRET_KEY": "x" * 32,
    "CORS_ORIGINS": "http://localhost:5173",
}


def _set_env(monkeypatch, remove=None):
    remove = remove or []
    for key, value in REQUIRED_ENV.items():
        if key in remove:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)


@pytest.fixture(autouse=True)
def _reset_notification_port_singleton(monkeypatch):
    """`adapters/factory.py::get_notification_port` cachea un singleton por proceso
    (patrón ya documentado en `factory.py`) — se resetea entre tests para que cada
    uno reciba una instancia fresca de `MosquittoAdapter`."""
    monkeypatch.setattr(factory, "_notification_port", None)
    yield
    monkeypatch.setattr(factory, "_notification_port", None)


@pytest.mark.asyncio
async def test_lifespan_starts_when_all_required_vars_present(monkeypatch):
    _set_env(monkeypatch)
    # Sin doble real de Mosquitto disponible en este entorno de test: se sustituye
    # `connect()` para no pagar los ~7s de backoff (1s/2s/4s) de un intento real
    # contra un host ("mosquitto") que no resuelve fuera de la red del compose.
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))

    async with lifespan(app):
        pass  # no debe abortar ni lanzar


@pytest.mark.asyncio
async def test_lifespan_aborts_with_json_error_when_var_missing(monkeypatch, capsys):
    _set_env(monkeypatch, remove=["MQTT_PASSWORD"])

    with pytest.raises(SystemExit) as exc_info:
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    assert exc_info.value.code == 1

    captured = capsys.readouterr()
    lines = [line for line in captured.out.strip().splitlines() if line]
    record = json.loads(lines[-1])
    assert record["level"] == "ERROR"
    assert "mqtt_password" in record["message"].lower()


@pytest.mark.asyncio
async def test_lifespan_no_partial_startup_names_all_missing_vars(monkeypatch, capsys):
    """RF-003: sin arranque parcial — nombra TODAS las variables faltantes, no solo una."""
    for key in REQUIRED_ENV:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(SystemExit):
        async with lifespan(app):
            pass  # pragma: no cover - no debe llegar aquí

    captured = capsys.readouterr()
    record = json.loads(captured.out.strip().splitlines()[-1])
    assert record["level"] == "ERROR"
    for key in REQUIRED_ENV:
        assert key.lower() in record["message"].lower()


@pytest.mark.asyncio
async def test_lifespan_invokes_mosquitto_connect_and_does_not_abort_on_failure(
    monkeypatch, capsys
):
    """RF-008 — Mosquitto real apagado / credencial inválida: `connect()` agota su
    backoff interno y se rinde (`is_connected=False`) sin lanzar; a diferencia del
    error de `Settings()`, el `lifespan` **no** aborta el arranque (`plan.md §7`
    Directiva de Pausa #2)."""
    _set_env(monkeypatch)
    notification_port = factory.get_notification_port()

    async def _fails_after_backoff() -> None:
        # Simula el comportamiento real de `MosquittoAdapter.connect()` tras agotar
        # el backoff (1s/2s/4s, ver `mosquitto_adapter.py`): loguea y se rinde sin
        # lanzar excepción. No se re-ejecuta el backoff real aquí (sería lento y
        # redundante con `tests/integration/test_adapters.py`); solo se verifica
        # que el `lifespan` invoca `connect()` y tolera este resultado.
        notification_port._connected = False

    connect_spy = AsyncMock(side_effect=_fails_after_backoff)
    monkeypatch.setattr(notification_port, "connect", connect_spy)

    async with lifespan(app):
        pass  # no debe abortar ni lanzar SystemExit aunque Mosquitto no conecte

    connect_spy.assert_awaited_once()
    assert factory.get_notification_port() is notification_port
    assert notification_port.is_connected is False

    # RF-007: `/health` (vía `ping()`) sigue siendo quien refleja el estado en
    # cada chequeo — el `lifespan` no necesita loguear él mismo el detalle del
    # backoff, ese log ya lo emite `MosquittoAdapter.connect()`. Aquí solo se
    # confirma que el arranque no quedó bloqueado ni logueó un error fatal propio.
    captured = capsys.readouterr()
    assert "Arranque abortado" not in captured.out


@pytest.mark.asyncio
async def test_lifespan_invokes_mosquitto_connect_and_reflects_success(monkeypatch):
    """RF-006/RF-008 — con credencial válida, `connect()` es invocado por el
    `lifespan` y deja `is_connected=True`."""
    _set_env(monkeypatch)
    notification_port = factory.get_notification_port()

    async def _succeeds() -> None:
        notification_port._connected = True

    connect_spy = AsyncMock(side_effect=_succeeds)
    monkeypatch.setattr(notification_port, "connect", connect_spy)

    async with lifespan(app):
        pass

    connect_spy.assert_awaited_once()
    assert notification_port.is_connected is True


class _NeverEndingCache:
    """Doble de `CachePort` cuyo `subscribe` nunca produce mensajes — permite
    verificar que el `lifespan` arranca la tarea de fondo (registrando el
    canal) y la cancela limpio en el *shutdown*, sin depender de Redis real
    (RF-006, `plan.md §2`/§10, T-036)."""

    def __init__(self) -> None:
        self.subscribed_channels: list[str] = []
        self.cancelled = False

    async def subscribe(self, channel: str):
        self.subscribed_channels.append(channel)
        try:
            while True:
                await asyncio.sleep(3600)
                yield "unreachable"  # pragma: no cover
        except asyncio.CancelledError:
            self.cancelled = True
            raise


@pytest.mark.asyncio
async def test_lifespan_starts_invalidation_subscriber_and_cancels_it_cleanly(
    monkeypatch,
):
    """T-036/T-037 — el `lifespan` arranca `run_invalidation_subscriber` como
    tarea de fondo al iniciar (junto al `connect()` de Mosquitto) y la cancela
    limpio (`CancelledError` capturado, sin *warning* de tarea huérfana) al
    apagar."""
    _set_env(monkeypatch)
    monkeypatch.setattr(MosquittoAdapter, "connect", AsyncMock(return_value=None))
    fake_cache = _NeverEndingCache()
    monkeypatch.setattr(main_module, "get_cache_port", lambda: fake_cache)

    async with lifespan(app):
        # Deja correr un tick del loop para que la tarea de fondo arranque y
        # se registre en el canal simulado.
        await asyncio.sleep(0)
        assert fake_cache.subscribed_channels == ["rbac:invalidations"]

    # Tras salir del `async with` (shutdown), la tarea debió cancelarse limpio
    # — si `lifespan` no la hubiera esperado (`await task`), esta aserción no
    # reflejaría la cancelación real (una tarea sin `await`ear no garantiza
    # haber corrido su bloque `except CancelledError` todavía).
    assert fake_cache.cancelled is True
