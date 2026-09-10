---
origen_vault: "7.1 - Hira Server/7.1.2 - Decisiones (ADRs)/7.1.2.9 - ADR-009 - Dos capas de ejecución Python con prioridad y bloqueo de puntos.md"
título: SRV-ADR-009 — Dos capas de ejecución Python con sistema de prioridad y bloqueo de puntos
proyecto: Hira Server
dominio: Productos de Software
tipo: ADR
status: activo
fecha_creación: 2026-07-23
tags: [adr, arquitectura, hira-server, motor-de-lógica, motor-de-pruebas]
---

## Contexto

El sistema necesita tanto lógica de operación continua (scripts que corren indefinidamente) como scripts de prueba funcional (ejecución única o acotada). Ambos pueden operar los mismos puntos, generando conflictos.

## Decisión

Dos capas separadas con prioridad explícita. Motor de Lógica en cola Celery `normal`; Motor de Pruebas en cola Celery `high`. Cuando una prueba inicia, registra en Redis los puntos que usará (`lock:punto_id`). Los workers de operación continua consultan ese lock antes de escribir — si el punto está bloqueado, saltan la escritura. Al terminar la prueba, los locks se liberan y la operación continua se reanuda automáticamente.

## Alternativas consideradas

Detener manualmente los scripts de operación antes de cada prueba; sistema de semáforos por dispositivo completo en lugar de por punto

## Consecuencias

Cero conflictos entre capas sin intervención manual del operador; granularidad a nivel de punto (no bloquea todo el dispositivo); la prueba tiene garantía de control exclusivo sobre los puntos que necesita
