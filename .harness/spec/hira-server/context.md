---
origen_vault: "7.1 - Hira Server/7.1.1 - Contexto/7.1.1.1 - Diagnóstico.md"
título: Diagnóstico — Hira Server
proyecto: Hira Server
dominio: Productos de Software
fase: Contexto
fecha_creación: 2026-07-23
última_actualización: 2026-07-31
tipo: Documento de Proyecto
status: en-proceso
github: "https://github.com/cjhirashi/hira-server"
tags: [proyecto, productos-software, hira-server, contexto, diagnóstico]
---

## Objetivo del Sistema

Desarrollar el **Ecosistema Hira**: Hira Server/Studio (un solo producto, un solo instalador) y Hira Hub (plataforma cloud), que cubren el ciclo completo del integrador de automatización, desde el diseño hasta la operación en campo y la gestión centralizada del desarrollador.

| Producto | Quién lo usa | Dónde corre | Rol |
|---|---|---|---|
| **Hira Server/Studio** | Integrador, Cliente, Operador | PC del integrador o servidor on-premise del cliente | Un solo producto, un solo instalador. Los proyectos/sistemas **viven en Hira Server** — un Server puede contener más de un proyecto (exclusivo de licencia de integrador). **Hira Studio es la herramienta de diseño**: el integrador la usa para crear y configurar esos proyectos, ya sea trabajando directo dentro de un Server (cambios en vivo, sin exportar/importar) o conectado de forma remota a un Server desde su propia PC |
| **Hira Hub** | cjhirashi y equipo | VPS en la nube (cjhirashi.com) | Gestión de licencias, ventas, actualizaciones, bloques visuales, crash reports |

No existen dos productos ni dos instaladores distintos. Los proyectos residen en Hira Server; Hira Studio es la interfaz de diseño e ingeniería sobre esos proyectos. Hira Studio nunca opera aislado — siempre está conectado a un Server, ya sea uno local (corriendo en la misma PC del integrador, para diseño y demos sin depender del cliente) o uno remoto (la instalación real del cliente). El proyecto vive en el Server al que Studio esté conectado, nunca en Studio.

**Flujo de trabajo del ecosistema:**
1. El integrador instala Hira Server en el servidor del cliente con licencia comercial — un solo proyecto por servidor (ver SRV-ADR-020)
2. Con credenciales de integrador, diseña y configura el proyecto usando las herramientas de Studio integradas en el propio Server — dispositivos, puntos, mimics, scripts, alarmas
3. Los cambios quedan operando de inmediato — es el mismo sistema, no hay paso de exportar e importar
4. El integrador también puede abrir Hira Studio desde su propia PC (licencia de integrador, con capacidad multi-proyecto en esa instalación local) y conectarse directamente al Server del cliente para trabajar en el proyecto sin estar físicamente en el sitio
5. La exportación de un proyecto como paquete `.hira` es para moverlo a otro servidor — migración, respaldo, o llevar un proyecto diseñado en la instalación local del integrador al servidor del cliente
6. **Hira Server** valida la licencia contra **Hira Hub**
7. **Hira Hub** emite actualizaciones y nuevos bloques visuales hacia las instalaciones activas
8. Los crash reports fluyen hacia **Hira Hub** para diagnóstico

---

## Problemas que Resuelve

| # | Problema | Impacto estimado |
|---|---|---|
| 1 | Los sistemas SCADA comerciales (Ignition, Niagara, WonderWare) son costosos ($2,000–$50,000+) y con licencias restrictivas | Barreras de entrada altas para integradores medianos y proyectos pequeños |
| 2 | La adaptación a cada proyecto requiere programación o configuración técnica profunda | Tiempo de integración elevado, dependencia del desarrollador original |
| 3 | No existe una plataforma SCADA que integre nativamente IA conversacional como asistente de operación | Los operadores no tienen soporte inteligente en tiempo real |
| 4 | Los sistemas industriales (BACnet/Modbus) y los sistemas IoT/Smart Home (MQTT) viven en plataformas separadas | Fragmentación de herramientas, sin visión unificada del entorno |
| 5 | El análisis de datos de los sistemas de control requiere herramientas externas (Excel, Python, etc.) | Fricción operativa, pérdida de contexto entre el sistema y el análisis |
| 6 | Dispositivos sin lógica interna requieren un PLC externo para programar su comportamiento | Costo adicional de hardware, complejidad de integración |
| 7 | Los integradores de automatización no tienen una plataforma SCADA propia que ofrecer a sus clientes — dependen de software de terceros con licencias costosas que no controlan | El integrador no puede diferenciarse, pierde margen en cada proyecto y no construye valor propio acumulable |

---

## Stakeholders

| Actor | Rol en el ecosistema |
|---|---|
| **cjhirashi** | Desarrollador, propietario del producto y creador de contenido premium en el marketplace |
| **Integrador de sistemas** | Usa Studio para diseñar proyectos, despliega Server en instalaciones de clientes, puede publicar plantillas en el marketplace |
| **Fabricante de controladores** | Socio comercial — ofrece Hira con sus dispositivos, publica pre-ingenierías oficiales de su marca en el marketplace |
| **Operador de instalación** | Usa Hira Server para monitorear y operar el sistema día a día |
| **Visor / Supervisor** | Consulta dashboards y reportes sin operar el sistema |
| **Cliente final** | Propietario del edificio o instalación donde corre Hira Server |

> Detalle completo de roles y protocolos de comunicación → `.harness/spec/ecosystem/stakeholders.md`

---

## Variables Involucradas

### Técnicas
- Protocolos de comunicación: BACnet IP, BACnet MSTP, Modbus TCP, Modbus RTU, MQTT
- Latencia de red local y confiabilidad de conexión con dispositivos
- Capacidad de procesamiento del servidor local (CPU, RAM)
- Volumen de puntos de datos (desde 10 hasta miles de tags simultáneos)
- Disponibilidad y costo de APIs externas de IA (Claude, GPT)

### De Negocio
- **Licencia de integrador:** instala Hira Server/Studio en su propia PC. Escaneo e integración de dispositivos sin restricción. Puntos que puede **diseñar/crear**: sin límite. Puntos que puede tener **en línea (activos) simultáneamente**: limitados a un tope de demo. Soporta múltiples proyectos en la misma instancia
- **Licencia comercial (cliente):** instalación de producción en el servidor del cliente. Tope de puntos en línea según el tier contratado (Starter/Professional/Enterprise). Un solo proyecto por servidor. Cuando Studio se conecta remoto a este Server, rige la licencia del Server, no la del integrador
- **Flywheel:** licencia de integrador de bajo costo → más integradores adoptan → se vuelven expertos → venden licencias comerciales en cada proyecto → más instalaciones activas → ingresos escalables sin fuerza de ventas propia
- **Referencia de mercado:** Inductive Automation (Ignition) usó exactamente este modelo — integradores certificados como canal principal, el software de ingeniería accesible, el runtime de producción como ingreso central
- Tiers comerciales: Starter ($399), Professional ($999), Enterprise ($2,499) + módulo IA opcional ($199/instalación)
- Mercado objetivo: integradores de SmartBuildings, automatización HVAC, IoT, Smart Home
- Marca: cjhirashi (empresa) / Hira (producto)
- Competidores directos: Ignition, Niagara Framework, WonderWare/AVEVA

### De Contexto
- Entorno de despliegue: servidor local on-premise (Linux o Windows vía Docker)
- Los dispositivos BACnet/Modbus viven en la red local
- Posibilidad de configuraciones remotas vía BACnet/Modbus en algunos proyectos
- El núcleo SCADA opera 100% en la red local (BACnet, Modbus, MQTT, alarmas, históricos, lógica)
- Conectividad a internet **recomendada** para la capa de servicios: validación de licencia, actualizaciones, crash reports, IA APIs y notificaciones externas
- Operación sin internet posible con limitaciones operativas: sin actualizaciones de licencia, sin crash reports, sin notificaciones email/webhook externas, sin acceso a AI APIs externas

---

## Problem Statement

Los integradores de sistemas de automatización y SmartBuildings necesitan una plataforma de monitoreo y control unificada que sea asequible, rápida de adaptar a cada proyecto sin tocar código, y que incluya capacidades de IA para asistir a los operadores — algo que ninguna plataforma comercial actual ofrece en ese rango de precio y con esa flexibilidad.

---

## Matriz de Riesgos

| Riesgo | Categoría | Probabilidad | Impacto | Mitigación |
|---|---|---|---|---|
| Incompatibilidad con implementaciones BACnet no estándar | Técnico | Media | Alto | Pruebas con múltiples fabricantes desde etapa temprana; configuración flexible de parámetros BACnet |
| Rendimiento degradado con alto volumen de puntos (>5,000) | Técnico | Media | Alto | TimescaleDB para series de tiempo; Redis como buffer; pruebas de carga |
| Dependencia de APIs de IA externas (cortes, cambios de precio) | Técnico/Negocio | Baja | Medio | Módulo IA completamente opcional; soporte de Ollama como fallback local |
| Dificultad de uso del configurador visual para integradores no técnicos | UX | Media | Medio | UX testing temprano; documentación exhaustiva; modo formulario como alternativa |
| Piratería o uso sin licencia | Negocio | Media | Medio | License key atada al hardware del servidor; validación en backend; tope de puntos en línea por tipo de licencia (ver SRV-ADR-018) |
| Competencia de plataformas open source (Node-RED, Home Assistant) | Mercado | Alta | Medio | Diferenciación por IA nativa, gráficos animados tipo SCADA y soporte comercial |

> Registro operativo de vulnerabilidades técnicas concretas (no de negocio) → carpeta de Operación (diseño), documento de Vulnerabilidades y Seguridad

---

## Restricciones

### Económicas
- Proyecto bootstrapped por cjhirashi — sin inversión externa inicial
- El costo de APIs de IA lo asume el cliente final (no Hirashi)

### De Tiempo
- Sin deadline fijo definido — desarrollo iterativo por módulos

### Técnicas
- Despliegue exclusivamente on-premise (sin cloud)
- Compatible con Linux (Docker Engine) y Windows (Docker Desktop + WSL2)
- El módulo IA debe ser 100% opcional — el sistema opera sin él

### Regulatorias
- Licencia comercial propietaria — uso no autorizado sin licencia key válida
- No aplican regulaciones industriales específicas en la versión inicial

---

## Viabilidad Económica

| Concepto | Estimación |
|---|---|
| Costo de desarrollo | Tiempo de cjhirashi (bootstrapped) |
| Costo de infraestructura | $0 — servidor local del cliente (on-premise) |
| Licencia de integrador — precio anual | Simbólico (~$99–$199/año). Objetivo: retener integradores, no generar ingreso |
| Licencia comercial — entrada al mercado | $399 (Starter) por instalación |
| Break-even estimado | 10 licencias Professional = $9,990 |
| Potencial por instalación Enterprise | $2,499 + soporte anual |
| Potencial por integrador activo | Un integrador con 5 proyectos/año = 5 licencias comerciales/año |
| Potencial con 10 integradores activos | 50 instalaciones/año × $999 promedio = $49,950/año |

**La ecuación de crecimiento:** el ingreso no escala con el número de clientes directos sino con el número de integradores activos y los proyectos que cada uno cierra. Un integrador bien posicionado en su mercado local puede mover 3–10 instalaciones por año. El costo de adquirir ese integrador es el precio de la licencia de integrador — unas decenas de dólares. El retorno por integrador activo puede ser miles de dólares en licencias comerciales anuales.

La viabilidad es alta y el modelo es escalable sin infraestructura propia ni fuerza de ventas directa.

---

## Oportunidades de Mejora

| Oportunidad | Tipo | Esfuerzo | Beneficio |
|---|---|---|---|
| **Marketplace de plantillas de proyecto** | Feature estratégico | Alto | Muy alto — tercer eje de ingresos, efectos de red, diferenciador único en el mercado SCADA |
| Soporte de protocolos adicionales (OPC-UA, KNX) | Expansión técnica | Medio | Alto — amplía mercado |
| App móvil para monitoreo | Feature futuro | Alto | Medio — complementa la web app |
| API pública para integraciones de terceros | Feature futuro | Medio | Alto — permite extensibilidad |

### Marketplace de Plantillas — Oportunidad Estratégica

El marketplace de pre-ingenierías es el tercer eje de ingresos del ecosistema y el que genera **efectos de red**:

| Eje | Producto | Naturaleza del ingreso |
|---|---|---|
| 1 | Licencia de integrador | Cuota anual simbólica — adquisición de integradores |
| 2 | Licencia comercial | Por instalación — ingreso principal por proyecto |
| 3 | Marketplace | Comisión por transacción + plantillas oficiales cjhirashi |

**Por qué tiene efectos de red:** cada integrador que publica una plantilla atrae a otros integradores al ecosistema. Más integradores → más plantillas → más valor para todos → más integradores. Es un ciclo de crecimiento que se autoalimenta y que ninguna plataforma SCADA tradicional tiene.

**Posición de cjhirashi en el marketplace:** propietario de la plataforma (comisión por transacción) + creador de contenido premium (pre-ingenierías HVAC de referencia vendidas directamente). La experiencia en automatización HVAC se convierte en un activo comercializable independiente del software.

**Efecto en la adopción comercial:** un integrador que compra una pre-ingeniería de Fan&Coil en el marketplace tiene todo diseñado — solo necesita importarla y ajustar direcciones para desplegarla en el Server del cliente. La barrera de adopción de nuevos proyectos se reduce drásticamente, lo que acelera las ventas.

### Canal de fabricantes de controladores

Un segmento de mercado adicional de alto valor: **fabricantes de controladores como socios comerciales de Hira**.

Un fabricante interesado en Hira puede:
- Crear su propia tienda oficial en el marketplace con pre-ingenierías certificadas para sus dispositivos
- Ofrecer Hira Server como la plataforma SCADA recomendada junto con su hardware
- Integrar sus mapas de puntos BACnet/Modbus nativos en plantillas listas para usar

Para el fabricante: deja de vender solo hardware y pasa a ofrecer una solución completa (hardware + SCADA + pre-ingenierías). Diferenciador frente a su competencia.

Para Hira: cada fabricante socio trae su red completa de clientes e integradores — es un canal de distribución que multiplica el alcance sin esfuerzo comercial propio.

**Tiers del marketplace:**

| Tier | Quién | Modelo |
|---|---|---|
| Comunidad | Integradores individuales | Gratis o pago, comisión a Hub |
| Premium | Integradores especializados / cjhirashi | Pago, comisión a Hub |
| Marca oficial | Fabricantes de controladores socios | Acuerdo de partnership, tienda propia en Hub |

---

## Gate de Salida

- [x] Las 8 preguntas tienen respuestas consensuadas
- [x] Viabilidad económica clara (orden de magnitud)
- [x] Mínimo 3 riesgos identificados
- [x] Restricciones explícitas y no ambiguas
- [x] Decisión de Go / No-Go: **Go**
