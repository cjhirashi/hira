---
origen_vault: "7.1 - Hira Server/7.1.4 - Diseño UI-UX/7.1.4.4 - Flujos Críticos de Usuario.md"
título: Flujos Críticos de Usuario — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Diseño UI-UX
fecha_creación: 2026-07-31
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, ui, flujos-de-usuario]
---

## Flujo 1 — Reconocimiento de alarma crítica

1. Alarma crítica dispara → banner rojo en topbar + fila pulsante en Gestor de Alarmas
2. Operador hace click en la alarma
3. Drawer lateral se abre: muestra punto, valor al disparar, timestamp
4. Campo obligatorio: "Nota de reconocimiento"
5. Botón "Reconocer" → backend confirma → fila deja de parpadear, badge del topbar se reduce

---

## Flujo 2 — Escritura de valor a un punto

1. Operador hace click en valor de un punto asociado con `access_mode` de lectura y escritura (ver SRV-ADR-019)
2. Input inline aparece con valor actual pre-cargado
3. Operador ingresa nuevo valor + confirma
4. Punto pasa a color `status-writing` mientras espera confirmación
5. Backend confirma escritura (respetando prioridad BACnet si aplica) → punto vuelve a color normal con nuevo valor
6. Si escritura falla → tooltip de error + punto vuelve al valor anterior

---

## Flujo 3 — Sesión de ingeniería remota activa

1. Un integrador abre una sesión de ingeniería remota desde su instalación local hacia el Server de un cliente (ver SRV-ADR-016, CU-12) → banner azul en topbar del Server: "Sesión de ingeniería activa — [nombre del integrador]"
2. Configurador queda en modo lectura para los usuarios de operación del proyecto mientras la sesión está activa
3. El integrador realiza sus cambios (dispositivos, puntos, alarmas, scripts) — se aplican de inmediato, sin ciclo export/import
4. La sesión se cierra (manual o por inactividad, TTL/heartbeat de SRV-ADR-016) → banner desaparece, Configurador vuelve a modo normal para los usuarios de operación

---

## Flujo 4 — Conexión remota desde la instalación local del integrador

1. Desde la Biblioteca de Proyectos de su instalación local, el integrador selecciona "Conectar a servidor remoto"
2. Ingresa URL del Server del cliente + credenciales de integrador
3. El sistema valida la licencia del Server remoto (no la del integrador — ver SRV-ADR-018) y solicita el lock de sesión de ingeniería
4. Si no hay otra sesión activa: conexión establecida, la interfaz local pasa a reflejar el proyecto del Server remoto (ver Flujo 3 del lado del Server)
5. Si ya hay una sesión activa: error `409 Conflict` con el nombre de quien la tiene abierta
6. El integrador trabaja como si el proyecto fuera local; al terminar, cierra la sesión desde el mismo panel

---

## Gate de Salida

- [x] Flujos críticos documentados
- [x] Flujo de sesión de ingeniería remota alineado con SRV-ADR-016 y SRV-ADR-018
- [x] Flujo de conexión remota desde instalación local documentado (CU-12)
- [ ] Revisado y aprobado por Charlie
