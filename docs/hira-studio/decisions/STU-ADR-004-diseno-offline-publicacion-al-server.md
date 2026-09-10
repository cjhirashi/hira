---
título: "STU-ADR-004 — Diseño y pruebas offline con simuladores; publicación del proyecto al Server"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-09-03
resuelve: [SQ-5, SQ-6, SQ-8]
supersede_parcialmente: [SRV-ADR-020]
tags: [adr, hira-studio, hira-server, diseño, simuladores, publicación]
---

## Contexto

SQ-5 (dónde corre la ejecución de lógica/pruebas y el Agente del Integrador), SQ-6
(multi-proyecto en el modelo cloud) y SQ-8 (diseño offline sin Server) estaban abiertas.
Decisión del propietario:

> Studio es la herramienta de **diseño** de los proyectos. Los proyectos se **cargan al
> servidor del cliente**. En Studio el integrador corre pruebas **fuera de línea**; y
> Studio se **conecta a un servidor** para cargar el proyecto y correr pruebas **en
> línea**. Sin conexión, el integrador **crea controladores offline** que son
> **simuladores**; al cargar el proyecto al servidor, esos controladores se deben
> **buscar en la red** para conectarse a los dispositivos reales.

## Decisión

### Dos modos de trabajo

| Modo | Dónde | Qué puede hacer |
|---|---|---|
| **Diseño offline** | Studio (BFF + sandbox propio) | Crear el proyecto: dispositivos como **simuladores**, puntos, asociaciones, scripts de lógica y de prueba, mimics, alarmas. **Ejecutar lógica y pruebas contra los simuladores** para validar el diseño. |
| **En línea** | Studio conectado a un Server (sesión de ingeniería) | Publicar el proyecto en el Server; correr pruebas **en el Server** contra sus dispositivos; ajustar configuración en vivo. |

### Ejecución

- **Offline (Studio):** un motor de simulación + un sandbox **RestrictedPython** en el BFF
  de Studio ejecutan lógica y pruebas contra valores de puntos simulados. Es validación de
  diseño — **no** es runtime de producción: sin Celery multi-worker, sin locks entre
  usuarios, sin historización, sin alarmas operativas persistentes. Coherente con
  `E-ADR-001` ("Studio no es runtime SCADA").
- **En línea (Server):** la ejecución real de lógica continua y de pruebas ocurre siempre
  en el Server, con su Celery, sus dos capas y sus locks (`SRV-ADR-007`, `SRV-ADR-009`).
  Studio dispara "correr prueba" / "desplegar script" y el Server encola.
- **Paridad de sandbox:** el mismo contrato de la API `hira` (`read`/`write`/`subscribe`/
  `wait`) y las mismas restricciones de RestrictedPython aplican en los dos motores, para
  que un script validado offline se comporte igual en el Server. La spec de
  `spec/hira-server/modules/motor-logica-y-pruebas.md` es la fuente de ese contrato; el
  motor offline de Studio la implementa, no la redefine.

### Publicación del proyecto

- Studio serializa el proyecto de diseño a un **paquete de proyecto** (formato = `.hira`
  extendido; ver `spec/hira-server/modules/backup-y-portabilidad.md` y `VUL-SRV-015`) y lo
  **carga al Server** por un endpoint de la sesión de ingeniería.
- En el Server, cada dispositivo que en Studio era un **simulador** llega marcado como tal
  (`device_class: simulator`, ver `VUL-SRV-011`). El integrador entonces:
  1. lanza un **escaneo de red** (`SRV-ADR-012`),
  2. mapea cada simulador a un dispositivo real descubierto,
  3. reasocia sus puntos (candidato → asociación con `access_mode` / `bacnet_write_priority`,
     `SRV-ADR-019`).
  Los simuladores que no se mapean pueden quedarse como simuladores (demo) o eliminarse.
- La publicación es **incremental**: re-publicar un proyecto ya cargado hace merge por
  identidad, no duplica (misma semántica que el import de `.hira`).

### Biblioteca de proyectos y multi-proyecto (SQ-6)

- La **biblioteca de proyectos de Studio** = los borradores de diseño offline del
  integrador **+** la lista de pares `(Server emparejado, proyecto)` a los que tiene
  acceso.
- **`SRV-ADR-020` se conserva** — el multi-proyecto sigue siendo capacidad **del Server**,
  exclusiva de licencia de integrador. Cambia solo el encuadre: ya no hay una "instalación
  local del integrador con SQLite multi-proyecto"; hay (a) borradores en Studio y (b) uno
  o varios Servers reales emparejados, cada uno con uno (comercial) o varios (integrador)
  proyectos.

### Sin Server (SQ-8)

El diseño offline en Studio **es** el flujo sin Server: el integrador diseña con
simuladores y valida con el motor offline. Para arrancar rápido, puede partir de una
plantilla `.hirat` del marketplace de Hub (v0.3). No hay "Server efímero en la nube": para
correr en línea hace falta un Server real (el del cliente, o uno que el integrador instale
como banco de pruebas).

## Alternativas consideradas

- **Toda la ejecución en el Server (Studio solo proxya).** Descartada: contradice el
  requisito de correr pruebas fuera de línea.
- **Toda la ejecución en Studio (incluida la de producción).** Descartada: duplicaría el
  runtime SCADA y contradice `E-ADR-001`.

## Consecuencias

- **Studio** necesita: motor de simulación de puntos, sandbox RestrictedPython de
  diseño, serializador de paquete de proyecto, y el cliente de publicación.
- **Contrato:** `CT-engineering-session` (o un `CT-project-publish` aparte) gana una
  operación de **publicar/actualizar proyecto**. Pendiente de diseñar el endpoint —
  registrado en `.harness/contracts/`.
- **Server:** el import de proyecto por la sesión de ingeniería reutiliza la lógica de
  import de `.hira`; el flujo simulador→real ya está cubierto por `SRV-ADR-012/014/019`.
- El formato de paquete de proyecto debe quedar definido antes de la primera publicación
  (relacionado con `VUL-SRV-009` — compatibilidad de versiones — y `VUL-SRV-015` —
  esquema `.hirat`).
