---
título: Modelo de negocio — Ecosistema Hira
componente: ecosystem
tipo: Especificación
status: activo
última_actualización: 2026-09-02
deriva_de: ["spec/hira-server/context.md"]
---

## Tres ejes de ingreso

| Eje | Producto | Naturaleza del ingreso |
|---|---|---|
| 1 | Licencia de integrador | Cuota anual simbólica (~$99–$199/año). Objetivo: **retener integradores**, no generar ingreso. |
| 2 | Licencia comercial (por instalación de Server) | Ingreso principal por proyecto. Tiers: Starter $399 · Professional $999 · Enterprise $2,499 · módulo IA opcional $199/instalación. |
| 3 | Marketplace de plantillas `.hirat` (v0.3, en Hub) | Comisión por transacción + plantillas premium de cjhirashi. Genera **efectos de red**. |

## El flywheel

```
Licencia de integrador barata
    → más integradores adoptan
    → se vuelven expertos en Hira
    → venden licencias comerciales en cada proyecto
    → más instalaciones activas
    → ingresos escalables sin fuerza de ventas propia
```

Referencia de mercado: Inductive Automation (Ignition) usó exactamente este modelo —
integradores certificados como canal principal, software de ingeniería accesible, runtime
de producción como ingreso central.

## Licenciamiento por puntos en línea (`SRV-ADR-018`)

El límite de licencia se mide en **puntos en línea simultáneos**, no en puntos creados ni
en controladores:

- **Licencia de integrador:** escaneo e integración sin restricción; puntos que puede
  *diseñar/crear* sin límite; puntos *en línea (activos) simultáneos* limitados a un tope
  de demo. Multi-proyecto (`SRV-ADR-020`).
- **Licencia comercial:** tope de puntos en línea según el tier contratado
  (`license.max_points`). Un solo proyecto por servidor.
- Cuando Studio se conecta a un Server remoto, rige la licencia **del Server**, no la del
  integrador.

Esto impide que una instalación local del integrador sustituya a una comercial sin contar
controladores. `VUL-SRV-014` quedó resuelto por rediseño con este ADR.

> **Pendiente por `E-ADR-001`:** con Studio como producto cloud, el modelo comercial de
> Studio (suscripción aparte vs incluido con la licencia de integrador) está en
> `spec/hira-studio/OPEN-QUESTIONS.md` (SQ-7).

## Segmentos

| Segmento | Descripción |
|---|---|
| Integradores de SmartBuildings / HVAC / IoT | Mercado objetivo principal. |
| Fabricantes de controladores | Socios comerciales: tienda oficial en el marketplace, Hira como SCADA recomendado junto a su hardware, mapas de puntos BACnet/Modbus nativos en plantillas. Traen su red completa de clientes e integradores. |
| Cliente final | Propietario del edificio; aprueba la compra junto al integrador. |

## Viabilidad (orden de magnitud)

- Costo de infraestructura por instalación: **$0** (on-premise del cliente).
- Break-even estimado: ~10 licencias Professional = $9,990.
- Potencial con 10 integradores activos: ~50 instalaciones/año × $999 promedio ≈ $49,950/año.

El ingreso escala con el número de **integradores activos** y los proyectos que cada uno
cierra, no con clientes directos.
