---
título: GLOSSARY — Términos del ecosistema Hira
tipo: Referencia
status: activo
última_actualización: 2026-09-02
---

# Glosario

## Ecosistema

| Término | Definición |
|---|---|
| **Ecosistema Hira** | Los tres componentes juntos: Hira Server, Hira Studio y Hira Hub. |
| **Hira Server** | Plataforma SCADA que corre **local / on-premise** en el servidor del cliente (o en la PC del integrador). Con instalador. Núcleo: protocolos, alarmas, históricos, lógica, tiempo real. |
| **Hira Studio** | Producto **cloud** de ingeniería y diseño de proyectos (configurador, motor de lógica, motor de pruebas, mimics, agente del integrador). Se conecta a uno o varios Hira Server remotos vía sesión de ingeniería y a Hira Hub para licencia. Ver `E-ADR-001`. |
| **Hira Hub** | Backend **cloud** (VPS) que opera cjhirashi: validación de licencias, crash reports, versiones/actualizaciones, portal de ventas (v0.2), marketplace de plantillas (v0.3). |
| **Integrador** | Empresa/técnico que compra licencias, diseña proyectos en Studio y despliega Servers en instalaciones de clientes. |
| **Cliente final** | Propietario del edificio/instalación donde corre un Hira Server. |
| **Operador** | Usuario que monitorea y opera un Hira Server día a día. |

## Datos y protocolos

| Término | Definición |
|---|---|
| **Punto** | Variable unificada que vive en el Server, independiente del protocolo. Puede estar enlazada a un punto real de un controlador (BACnet/Modbus/MQTT) o ser una variable interna sin controlador. Ver `SRV-ADR-019`. |
| **Punto candidato** | Punto crudo descubierto por escaneo de dispositivos (`device_points_candidates`). **No** es utilizable en línea: no se pollea, no se historiza, no dispara alarmas, no lo ve el RAG. Ver `SRV-ADR-012`. |
| **Asociación explícita** | Acto de convertir un candidato en un punto de Hira usable, definiendo `access_mode` (`read` / `read_write`) y, en BACnet, `bacnet_write_priority`. Solo tras la asociación el punto entra en línea. Ver `SRV-ADR-012`, `SRV-ADR-019`. |
| **Punto en línea** | Punto activo, recibiendo/enviando datos en tiempo real. El límite de licencia se mide en puntos en línea simultáneos. Ver `SRV-ADR-018`. |
| **`access_mode`** | Capacidad de acceso de una asociación: `read` o `read_write`. Una escritura a un punto `read` se rechaza. |
| **`bacnet_write_priority`** | Prioridad del priority array de BACnet con la que Hira escribe a un punto asociado (solo protocolo BACnet). |
| **Simulador** | Dispositivo virtual registrado en `devices` con el mismo esquema que uno real (flag/clase diferenciador). Recorre el mismo pipeline que hardware real. Ver `SRV-ADR-014`. |
| **Motor de Protocolos** | Componente que hace polling y escritura BACnet / Modbus / MQTT y publica a Redis. |
| **Motor de Lógica** | Scripts Python de operación **continua** (`hira.read/write/subscribe`), cola Celery `normal`. Ver `SRV-ADR-007`, `SRV-ADR-009`. |
| **Motor de Pruebas** | Scripts Python de ejecución **única o acotada**, cola Celery `high`. Bloquea en Redis los puntos que usa (`lock:point:<id>`). Ver `SRV-ADR-009`. |

## Licencia y portabilidad

| Término | Definición |
|---|---|
| **Licencia de integrador** | Instala Server en la PC del integrador. Escaneo/creación de puntos sin límite; puntos **en línea** limitados a un tope de demo. Multi-proyecto. Ver `SRV-ADR-018`, `SRV-ADR-020`. |
| **Licencia comercial** | Instalación de producción en el servidor del cliente. Tope de puntos en línea según tier (Starter / Professional / Enterprise). Un solo proyecto por servidor. |
| **Tier** | Nivel de licencia comercial: Starter ($399), Professional ($999), Enterprise ($2,499). Define `license.max_points`. |
| **`.hira`** | Paquete de exportación/importación de un proyecto completo (JSON serializado por ORM + checksum). Mecanismo de migración/respaldo, **no** el flujo principal de sincronización. Ver `SRV-ADR-015`. |
| **`.hirat`** | Plantilla de proyecto (Hira Template): subconjunto de un `.hira` sin datos históricos, config de red ni credenciales. Se publica y descarga en el marketplace de Hub. Ver `VUL-SRV-015`. |
| **Sesión de ingeniería** | Conexión con lock exclusivo de Studio a un Server remoto (`engineering_sessions`, espejo Redis TTL 300s, heartbeat 60s, `409` si ya hay una activa). Único camino por el que Studio modifica un proyecto que no corre en su propia máquina. Ver `SRV-ADR-016`, `CT-engineering-session`. |
| **Grace period** | 72h que un Server sigue operando si no puede validar licencia contra Hub. Ver `HUB-ADR-03`. |

## Harness

| Término | Definición |
|---|---|
| **Ancla** | ID estable que aparece a la vez en la spec y en el código/tests que la realizan. Ver `anchors/SCHEMA.md`. |
| **Contrato (`CT-*`)** | Especificación OpenAPI de una API/evento entre componentes. Fuente única en `contracts/`. |
| **Gate** | Script de CI que falla el build ante deriva spec↔código. |
| **Desviación (`DEV-*`)** | Registro de "no se pudo implementar como se especifica". Va a `deviations/LOG.md`. |
| **Overlay** | Fragmento de instrucciones específico de un componente (`.harness/claude/<comp>.md`) que se ensambla en su `AGENTS.md`/`CLAUDE.md`. |
