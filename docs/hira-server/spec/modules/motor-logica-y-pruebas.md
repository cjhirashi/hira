---
origen_vault: "7.1 - Hira Server/7.1.5 - Diseño por Módulo/7.1.5.7 - Motor de Lógica y Motor de Pruebas.md"
título: Motor de Lógica y Motor de Pruebas — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño por Módulo
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, motor-de-lógica, motor-de-pruebas]
---

## Motor de Lógica (operación continua)

**Responsabilidad:** ejecutar scripts Python de operación continua sobre puntos asociados.

- Editor: Monaco Editor con tema oscuro y autocompletado del API `hira` (ver SRV-ADR-UI-04)
- API interna disponible dentro del sandbox: `hira.read(point)`, `hira.write(point, value)`, `hira.subscribe(point)`
- Ejecución: Celery, cola `normal`, ciclo indefinido hasta que el integrador lo detiene
- Un worker que muere es reiniciado automáticamente por Celery en menos de 30s
- Toda escritura respeta RBAC y `access_mode` del punto (ver SRV-ADR-019)

## Motor de Pruebas (ejecución única o acotada)

**Responsabilidad:** ejecutar scripts de prueba funcional y comisionamiento con prioridad sobre la lógica continua.

- Ejecución: Celery, cola `high` — prioridad sobre la cola `normal`
- Al iniciar, registra en Redis los puntos que usará (`lock:point:{id}`, TTL 3600s, refrescado cada 60s mientras corre)
- Los workers de lógica continua consultan el lock antes de escribir — si el punto está bloqueado, saltan la escritura sin error
- Al finalizar la prueba (o expirar el TTL si el worker muere), los locks se liberan y la lógica continua se reanuda automáticamente — sin intervención manual
- Secuencia típica de un script de prueba: `hira.write()` + `hira.read()` + `hira.wait()`
- Resultados → tabla `script_executions` (`result_json`) → Módulo de Análisis (reportes PDF/CSV)
- Los scripts de prueba se guardan como plantillas reutilizables por proyecto (`template_name`)

## Sandbox

Ver `.harness/spec/hira-server/modules/auth-rbac-seguridad.md` — RestrictedPython, sin acceso a filesystem, red, subprocess ni imports arbitrarios en ninguno de los dos motores.

---

## Gate de Salida

- [x] Dos capas de ejecución documentadas con mecanismo de prioridad y locks (SRV-ADR-009)
- [x] Sandbox referenciado sin duplicar contenido de seguridad
- [ ] Revisado y aprobado por Charlie
