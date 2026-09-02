---
título: "HUB-ADR-01 — Mismo stack que Hira Server (FastAPI + PostgreSQL + Redis)"
componente: hira-hub
tipo: ADR
status: accepted
fecha_creación: 2026-07-24
origen_vault: "7.2 - Hira Hub/7.2.3 - Diseño Conceptual.md (ADR-H01)"
tags: [adr, hira-hub, stack]
---

## Contexto

Hub es un proyecto mantenido solo por cjhirashi. Reducir la cantidad de tecnologías a
mantener es crítico.

## Decisión

FastAPI + PostgreSQL + Redis. Mismo stack que Hira Server — mismo dominio, mismo
conocimiento, mismas herramientas de debug. Nginx como reverse proxy, Docker Compose,
imágenes en GHCR vía GitHub Actions.

## Alternativas consideradas

- Node.js — más popular en SaaS, pero añade un lenguaje al ecosistema.
- Django — más baterías incluidas, pero más peso del que Hub necesita.

## Consecuencias

Código reutilizable entre proyectos (p. ej. `core/logger.py`); un solo lenguaje para todo
el ecosistema; menor superficie de mantenimiento.
