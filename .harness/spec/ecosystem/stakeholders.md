---
origen_vault: "7.1 - Hira Server/7.1.1 - Contexto/7.1.1.2 - Stakeholders.md"
título: Stakeholders — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Contexto
fecha_creación: 2026-07-23
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, contexto, stakeholders]
---

## Contexto

Hira es un **producto comercial** con dos capas de stakeholders: los del **producto** (quiénes lo adquieren y distribuyen) y los **roles dentro de cada instalación** (quiénes lo usan día a día).

Cada nivel del producto opera con **equipos**, no individuos. cjhirashi crece con un equipo de desarrollo y ventas; el integrador puede tener múltiples integradores en su empresa; el cliente tiene múltiples usuarios con distintas responsabilidades.

Los roles de instalación son **completamente configurables** por el superusuario — no existen roles fijos en el sistema. Cada proyecto define sus propios roles con permisos granulares por módulo y área, adaptados a sus necesidades específicas (HVAC, iluminación, energía, detección de incendios, IoT, etc.).

---

## Stakeholders del Producto

| Nivel | Quiénes son | Función | Objetivos/KPIs | Impacto si falla | Necesidades | Poder de decisión |
|---|---|---|---|---|---|---|
| **cjhirashi + equipo** | Desarrolladores, equipo de ventas y soporte | Desarrollan, mantienen y comercializan Hira | Producto estable, licencias vendidas, roadmap cumplido, soporte activo | Total — es el origen del sistema | Control del código, roadmap, licencias, canales de distribución | Máximo |
| **Empresa integradora + sus integradores** | Empresa que compra la licencia e instala Hira en proyectos; sus técnicos ejecutan las integraciones | Adquieren licencias, configuran y entregan Hira a clientes finales | Tiempo de integración corto, proyectos entregados a tiempo, clientes satisfechos | Pierde proyectos, entrega con retrasos, reputación afectada | Panel de configuración claro, documentación técnica, soporte técnico ágil, posibilidad de multi-proyecto con licencia de integrador | Alto — decide si adopta Hira o un competidor |
| **Cliente final + sus usuarios** | Propietario o administrador del edificio/instalación y el equipo que opera el sistema | Utilizan Hira para operar y monitorear su instalación | Sistema funcionando 24/7, visibilidad completa, ROI claro | Operación degradada, pérdida de control del edificio, pérdida económica | Estabilidad, interfaz clara, alertas a tiempo, reportes ejecutivos | Medio — aprueba la compra junto al integrador |

---

## Roles dentro de cada Instalación (RBAC Dinámico)

Los roles **no son fijos en el sistema** — el superusuario de cada instalación los define y configura según las necesidades del proyecto. El sistema provee un motor de **RBAC dinámico** donde cada rol tiene permisos granulares sobre:

- **Módulos accesibles**: Dashboard, Alarmas, Históricos, Análisis, Reportes, Motor de Lógica, Configuración
- **Áreas del sistema**: HVAC, Iluminación, Energía, Detección de Incendios, IoT, etc. (según lo que esté integrado)
- **Tipo de acceso por área**: Solo lectura / Lectura + escritura / Control total
- **Acceso al asistente IA**: habilitado o deshabilitado por rol

### Alcance por tipo de usuario

- **Usuarios de operación** (Operador, Visor y roles configurables de instalación) son **por proyecto** — un usuario de operación pertenece a un proyecto y solo ve ese proyecto
- **Usuarios integrador** son **globales al Server/Studio** — el mismo usuario integrador accede a todos los proyectos que aloja esa instancia (relevante en licencia de integrador, multi-proyecto)

### Roles de referencia (ejemplos — no son fijos)

| Rol ejemplo | Descripción | Permisos típicos |
|---|---|---|
| **Superusuario** | Configura y administra toda la instalación | Acceso total a todos los módulos y áreas |
| **Operador general** | Monitorea y opera todos los sistemas | Lectura + escritura en áreas asignadas, alarmas, IA |
| **Operador de área** | Opera solo un sistema específico (ej: HVAC) | Lectura + escritura solo en su área |
| **Técnico** | Diagnóstico, históricos y reportes | Lectura, históricos, análisis, exportación |
| **Supervisor** | Visibilidad ejecutiva sin operación | Solo lectura en dashboards y reportes |
| **Auditor energético** | Análisis de consumo y reportes | Acceso solo al módulo de energía e históricos |

Cada instalación puede definir tantos roles como necesite, con el nombre y los permisos que el proyecto requiera.

> Nota: el MVP (v0.1) implementa 3 roles fijos (Admin/Operador/Visor) como paso intermedio — el RBAC dinámico completo llega en v0.2.

---

## Protocolo de Comunicación

### Crítico — Sistema no funciona (instalación caída, datos perdidos, seguridad comprometida)
- Canal: contacto directo cjhirashi → integrador responsable
- Tiempo de respuesta objetivo: < 4 horas
- Acción: hotfix con prioridad máxima, comunicación continua hasta resolución

### Alto — Funcionalidad degradada (módulo caído, alarmas no llegando, históricos con gaps)
- Canal: sistema de soporte (ticket) + comunicación directa si el integrador lo escala
- Tiempo de respuesta objetivo: < 24 horas
- Acción: diagnóstico remoto, parche si aplica

### Medio — Mejora o comportamiento inesperado no crítico
- Canal: ticket de soporte estándar
- Tiempo de respuesta objetivo: próximo ciclo de actualización
- Acción: evaluación, registro en backlog si procede

---

## Protocolo de Resolución de Conflictos

Tensión más probable: **integrador quiere feature específico de su proyecto** vs **roadmap general del producto**.

Árbol de decisión:
1. ¿El feature beneficia a múltiples instalaciones? → Entra al roadmap con prioridad según impacto
2. ¿Es específico de un proyecto? → El integrador puede implementarlo vía script Python en el Motor de Lógica o solicitarlo como desarrollo a medida (cotización separada)
3. ¿Implica cambio arquitectural? → cjhirashi evalúa impacto antes de comprometerse

---

## Protocolo de Integración Tardía

Si se descubre un stakeholder nuevo en fases posteriores (ej: un rol de auditoría, un sistema externo que debe consumir datos de Hira):
1. Documentar quién es, qué necesita y en qué fase se descubrió
2. Evaluar si afecta decisiones de arquitectura ya tomadas (ADRs en `.harness/adr/hira-server/`)
3. Si hay impacto en diseño: abrir revisión de arquitectura o diseño UI antes de implementar
4. Registrar en Bitácora de Cambios

---

## Gate de Salida

- [x] Todos los stakeholders identificados y documentados
- [x] Función completa de cada stakeholder clara
- [x] Impacto definido explícitamente
- [x] Protocolos validados
- [ ] Revisado y aprobado por Charlie
