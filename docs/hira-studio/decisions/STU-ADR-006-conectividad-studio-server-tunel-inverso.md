---
título: "STU-ADR-006 — Conectividad Studio↔Server por túnel inverso self-hosted; instalación desde Hub"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-10-15
resuelve: [SQ-2 — parte de red, no cubierta por STU-ADR-003]
extiende: [STU-ADR-003]
depende_de: [HUB-ADR-06]
tags: [adr, hira-studio, hira-server, hira-hub, seguridad, red, instalación]
---

## Contexto

`STU-ADR-003` resolvió **la autenticación** del emparejamiento Studio↔Server (token de
emparejamiento, credencial rotable), pero asumió tácitamente que Studio dispone de "una
URL/host alcanzable" del Server, sin diseñar cómo se logra esa alcanzabilidad.

En la práctica, los Servers de Hira viven en la red de los **clientes finales** de los
integradores — casi nunca con IP pública, casi siempre detrás de firewall corporativo.
El propietario del ecosistema fijó una restricción de negocio explícita: **el mecanismo
de conectividad no puede exponer la red del cliente**; una vulneración ahí es un
problema de negocio para él, no solo un incidente técnico.

## Decisión

### 1. Túnel inverso iniciado por el Server (self-hosted)

El Server corre un cliente de túnel (`frp` — `frpc`) que abre una conexión de **salida**
persistente hacia un relay (`frps`) operado por cjhirashi en infraestructura propia.
Studio nunca se conecta directo al Server; le llega a través de `frps`, que reenvía al
`frpc` correspondiente.

- El Server **nunca** necesita un puerto entrante — nada que tocar en el firewall/router
  del cliente.
- Se descarta explícitamente depender de Cloudflare Tunnel para esta pieza (decisión del
  propietario): v1 es self-hosted, infraestructura propia.

### 2. Alcance mínimo expuesto — segmentación de red explícita

El backend de `hira-server` necesita alcance real a la red de campo del cliente para
cumplir su función (BACnet/Modbus/MQTT, `SRV-003/004/005`, ya `verified`) — eso **no**
es una vulneración, es el producto haciendo su trabajo. BACnet en particular necesita
broadcast UDP real (Who-Is), que un bridge de Docker normal no garantiza; en producción
exige `network_mode: host` o una red `macvlan` pegada a la VLAN del cliente. Modbus y
MQTT son TCP unicast — funcionan con un bridge normal mientras el host de Docker esté en
esa red.

**Esa necesidad es independiente del túnel y nunca debe compartir su alcance.** El
backend corre con **dos interfaces de red separadas**:

1. Una con alcance real a la LAN/VLAN del cliente (host o macvlan) — exclusiva para
   BACnet/Modbus/MQTT.
2. Una segunda, en una red Docker **interna y aislada**, compartida únicamente con
   `frpc`, que expone solo el puerto de la API (p. ej. `127.0.0.1:8000`).

`frpc` vive **exclusivamente** en la red (2) — nunca en la (1), nunca en `network_mode:
host`. Así el túnel hacia Studio solo ve el puerto de la API, sin heredar visibilidad de
la red de campo del cliente. Esta separación es una regla de despliegue explícita (no
una convención implícita): el `docker-compose.yml` de producción debe declarar ambas
redes por nombre y fijar qué contenedor va en cuál — no basta con "frpc está en el mismo
compose".

- `frpc` reenvía **exactamente un puerto** (la API). Nunca la LAN del cliente, nunca
  otros servicios.
- La config de `frpc` **no es editable por el integrador**. Se genera fija en el momento
  de aprovisionar la instalación (punto 3) — nunca es un paso manual.

### 3. Instalación personalizada emitida por Hub

El integrador no descarga un instalador genérico. Pide el Server desde Hub (donde ya
gestiona su cuenta/licencia, `CT-license`); Hub genera un **paquete de instalación
personalizado** con:

- license key ya ligada a esa activación (reutiliza `max_activations` de `CT-license`
  para que un paquete filtrado no se reuse fuera de su activación),
- token de túnel `frp` único, pre-registrado en `frps`,
- config de `frpc` ya fija (un puerto, sin campos editables).

El integrador solo descarga y ejecuta ese paquete. Integridad: servido únicamente por
HTTPS desde el dominio de Hub, con firma/checksum verificable por el instalador.

### 4. Gate de autorización por propiedad (depende de `HUB-ADR-06`)

La credencial de emparejamiento de `STU-ADR-003` deja de ser suficiente por sí sola.
Cada apertura de sesión de ingeniería (`CT-engineering-session`) valida además, contra
Hub, que la cuenta de integrador que solicita sigue en `project_linked_integrators` (o es
`owner_account_id`) del proyecto — `HUB-ADR-06`. Si fue revocada, `403` aunque la
credencial de emparejamiento siga siendo técnicamente válida.

### 5. Revocación en dos candados

Revocar una vinculación en Hub (`HUB-ADR-06`) debe propagar a la revocación del token de
túnel de ese integrador/proyecto — no basta con que el siguiente intento de apertura de
sesión falle el gate del punto 4; el acceso de red también se cierra.

## Alternativas consideradas

- **Cloudflare Tunnel.** Descartada para esta pieza por decisión explícita del
  propietario (no depender de esa infraestructura en la conectividad de clientes
  finales) — aunque el patrón es idéntico y queda como opción si se reconsidera más
  adelante.
- **Conexión entrante directa** (IP pública/port-forward/DynDNS del lado del cliente).
  Descartada: mismo criterio ya usado para descartar mTLS en `STU-ADR-003` —
  operativamente inaceptable para integradores/clientes no expertos, y expone
  justo lo que el propietario quiere evitar.
- **VPN mesh self-hosted (WireGuard/Headscale).** Descartada para v1: da alcance de red
  completo entre nodos (mayor superficie si algo se compromete) cuando hoy solo se
  necesita un único contrato HTTP. Queda como evolución posible si en el futuro se
  necesita más superficie que esa API (soporte remoto, multi-servicio).

## Consecuencias

- **Hub** gana el flujo de generación de paquete de instalación (license + token de
  túnel + config fija) y la validación de `HUB-ADR-06` en cada apertura de sesión.
- **Server**: nuevo sidecar `frpc` en su `docker compose`, en una red Docker propia y
  aislada del backend — es infraestructura de despliegue, no toca código ya `verified`
  ni ninguna spec de producto. El `docker-compose.yml` de producción debe declarar
  explícitamente la red de campo (host/macvlan, exclusiva del backend) separada de la
  red interna compartida con `frpc` — pendiente de fijar en el compose real (hoy usa el
  bridge por defecto, sin esta segmentación todavía).
- **`frps`**: nueva pieza de infraestructura propia a operar (VPS con IP pública,
  hardened: sin otros servicios, firewall, monitoreo — es ahora un punto central cuyo
  compromiso afectaría a todos los Servers conectados).
- `STU-ADR-003` se mantiene vigente para la mecánica de credencial de emparejamiento;
  este ADR añade la capa de red y el gate de propiedad por encima.
