# adapters/bacnet

Implementa `core/ports/bacnet_transport_port.py::BacnetTransportPort` contra la
librería `BAC0`/`bacpypes3` real (`SRV-003-bacnet-adapter`, T-013/T-014,
`plan.md §2`). Único módulo del backend que importa `BAC0`/`bacpypes3`
(`SRV-ADR-017`) — `services/device_scan_service.py` solo conoce el `Protocol`.

- `bac0_adapter.py::BAC0Adapter` — `who_is(timeout_seconds)` (Who-Is/I-Am,
  RF-001) y `read_device_objects(network_address, timeout_seconds)` (lee
  `objectList` del dispositivo y cada objeto que no sea `device`/
  `network-port` — RF-002; `BacnetReadTimeoutError` real vía
  `asyncio.wait_for` si no responde a tiempo — RF-006/RF-010). Constructor
  con `ip`/`port` opcionales (`None` → `BAC0.lite()` autodetecta la interfaz
  local) y `target_address` (**solo tests** — dirige el Who-Is a una
  dirección unicast en vez de broadcast, ver docstring del módulo y
  `plan.md §5`).
- Verificado con `tests/integration/test_bac0_adapter.py` — 2 instancias
  reales de `BAC0.lite()` en `127.0.0.1` (UDP real, sin mocks, sin hardware):
  I-Am con `instance_number` correcto, objetos leídos coinciden con los
  creados en el "dispositivo" simulado, `BacnetReadTimeoutError` real (~2s) si
  el dispositivo se desconecta entre el I-Am y la lectura.

`BAC0==2026.7.25` en `requirements.txt` (trae `bacpypes3==0.0.106` como
dependencia transitiva).
