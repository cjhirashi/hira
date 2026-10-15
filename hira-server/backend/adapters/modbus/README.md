# adapters/modbus

Implementa `core/ports/modbus_transport_port.py::ModbusTransportPort` contra la
librería `pymodbus` real (`SRV-004-modbus-adapter`, T-009/T-010, `plan.md §2`).
Único módulo del backend que importa `pymodbus` (`SRV-ADR-017`) —
`services/device_scan_service.py` solo conoce el `Protocol`.

- `pymodbus_adapter.py::PymodbusAdapter` — `read_range(host, port, unit_id,
  register_type, start, count, timeout_seconds)` abre una conexión TCP
  (`AsyncModbusTcpClient(..., timeout=timeout_seconds, retries=0)`, una sola
  vez por llamada, reutilizada para las `count` direcciones del rango —
  RNF-001) y lee cada dirección individualmente (RF-001; nunca en batch, para
  que una dirección fallida no aborte las demás). Un único método despacha
  internamente a `read_coils`/`read_discrete_inputs`/
  `read_holding_registers`/`read_input_registers` según `register_type`
  (Anti-Abstraction). Cada dirección resuelve a `ModbusRegisterReading`
  (éxito) o `ModbusReadFailure` (RF-005 — `ExceptionResponse` real del
  servidor, o `ModbusException`/timeout real; **no** es una excepción de
  Python que aborte el rango).
- `retries=0` explícito — imprescindible para que el timeout real de una
  dirección sin respuesta sea `timeout_seconds` (RF-008, 1s) y no lo
  multiplique por reintentos (valor por defecto de `pymodbus`, `retries=3`,
  produciría ~4s).
- Verificado con `tests/integration/test_pymodbus_adapter.py` — servidor
  Modbus TCP real (`pymodbus.server.ModbusTcpServer` +
  `pymodbus.simulator.SimDevice`/`SimData`, API nueva de `pymodbus==3.15.0`,
  **no** la API "clásica" `ModbusServerContext`/`ModbusDeviceContext` —
  verificado con ejecución real que esa combinación está rota/vestigial en
  esta versión, devuelve incondicionalmente `ExcCodes.DEVICE_BUSY`) en
  `127.0.0.1`, sin mocks, sin hardware: los 4 tipos de registro devuelven
  exactamente los valores cargados; dirección fuera de rango y `unit_id`
  incorrecto responden con `ExceptionResponse` real (`ModbusReadFailure`,
  sin excepción de Python); timeout real medido ≈1.0-1.1s contra un servidor
  TCP crudo que acepta la conexión pero nunca responde (`retries=0`,
  RF-008).

`pymodbus==3.15.0` en `requirements.txt` (última versión disponible en PyPI
al fijarla).

- `modbus_simulator_adapter.py::ModbusSimulatorAdapter` — implementa
  `ModbusSimulatorPort` (`SRV-006-simuladores`, T-023, `plan.md §2`/§5).
  Cada `start(host, port, unit_id, registers)` levanta un `ModbusTcpServer`
  real con un `SimDevice` (API `SimData`/`SimDevice` de `pymodbus==3.15.0`,
  la misma ya verificada como infraestructura de test en `SRV-004`, aquí
  como producto) cargado con los registros pedidos y lo sirve en una tarea
  de fondo (`asyncio.create_task(server.serve_forever())`, RNF-001 — no
  bloquea el *event loop*). Soporta los 4 tipos de registro: `coil`/
  `discrete_input` (bool, `DataType.BITS`) y `holding_register`/
  `input_register` (int, `DataType.UINT16`). Direcciones no configuradas
  responden con `ILLEGAL_ADDRESS` (mismo comportamiento que un PLC real).
  `stop(token)` llama a `server.shutdown()` y espera la tarea con
  `asyncio.wait_for`. Retorna un token opaco `str` (UUID hex).
  Verificado con `tests/integration/test_modbus_simulator_adapter.py` —
  cliente `AsyncModbusTcpClient` real lee los valores cargados; `stop`
  cierra el servidor.
