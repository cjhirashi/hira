---
título: "STU-ADR-001 — Studio cloud multi-tenant: SPA + BFF con BD, arquitectura directa"
componente: hira-studio
tipo: ADR
status: accepted
fecha_creación: 2026-09-03
resuelve: [SQ-3, SQ-4]
tags: [adr, hira-studio, arquitectura, hosting]
---

## Contexto

`E-ADR-001` define Hira Studio como producto cloud. `spec/hira-studio/OPEN-QUESTIONS.md`
dejaba abiertos el modelo de hosting/tenancy (SQ-3) y si Studio necesita backend propio
con estado (SQ-4).

## Decisión

**Instancia multi-tenant única, hospedada junto a Hira Hub** (VPS de cjhirashi),
con aislamiento **lógico** por `integrator_id`. Self-host y despliegue por integrador no
son parte de v1.

Studio se compone de:

- **SPA** (React + TypeScript, MD3 + Cyan — mismo sistema de diseño que Server/Hub).
- **BFF** (FastAPI) con **base de datos propia (PostgreSQL) + Redis**. Arquitectura
  **directa**, sin puertos/adaptadores — mismo criterio que `HUB-ADR-05` (un único
  deployment target).

El BFF persiste, siempre segregado por `integrator_id`:

| Dato | Para qué |
|---|---|
| Cuenta de integrador + licencia enlazada | Identidad y acceso (`STU-ADR-002`) |
| Registro de Servers emparejados + credenciales de emparejamiento (cifradas) | Conexión a Servers (`STU-ADR-003`) |
| Proyectos de diseño (borradores): dispositivos-simulador, puntos, scripts, mimics, alarmas | Diseño y pruebas offline (`STU-ADR-004`) |
| Preferencias de usuario, historial de sesiones de ingeniería | UX y auditoría |
| Caché del catálogo de bloques SVG / plantillas `.hirat` de Hub | Rendimiento (v0.3) |

El BFF además **media**: proxya `CT-engineering-session` hacia los Servers y
`CT-license` / `CT-crash-report` hacia Hub.

## Alternativas consideradas

- **BFF sin estado (solo proxy).** Descartada: hay estado real que persistir (borradores,
  emparejamientos, preferencias) — sin BD no hay diseño offline.
- **Namespace / instancia por integrador.** Descartada para v1: multiplica el coste
  operativo de un proyecto bootstrapped sin necesidad real (los datos sensibles de campo
  viven en los Servers, no en Studio).
- **Hosting separado de Hub.** Aplazada: si la carga o el ciclo de release de Studio lo
  piden, se mueve; hoy compartir footprint con Hub es lo más barato de operar.

## Consecuencias

- `hira-studio/` tiene `backend/` (FastAPI, estructura directa), `frontend/` (SPA),
  `docs/openapi.yaml` (contrato interno), `nginx/`.
- El cifrado de credenciales de emparejamiento usa una clave de entorno
  (`STUDIO_PAIRING_ENCRYPTION_KEY`), análoga a `AI_ENCRYPTION_KEY` de Server.
- Todo acceso a datos en el BFF filtra por `integrator_id` del token de sesión — es la
  frontera de aislamiento; se verifica en pruebas (`AC-STU-*`).
- Studio comparte VPS con Hub pero **no** comparte base de datos ni proceso.
