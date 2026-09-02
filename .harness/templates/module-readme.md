---
module: <nombre-corto>
component: <hira-server | hira-hub | hira-studio>
anchors: [<IDs de ADR/REQ/AC/VUL que este módulo realiza>]
spec: .harness/spec/<comp>/<ruta al doc de spec del módulo>
---

# Módulo `<nombre>`

## Propósito

Qué hace esta carpeta en 2-3 líneas.

## Archivos

- `archivo.py` — una línea de descripción.

## Cómo funciona

Flujo de uso: quién llama a qué y qué devuelve.

## Dependencias

Qué otros módulos importa y por qué. (En `hira-server`: recordar que `services/` solo
importa de `core/ports/`, nunca de `adapters/`.)

## Anclas

| Ancla | Qué cubre en este módulo |
|---|---|
| `<ID>` | … |
