# 📋 PLAN DE IMPLEMENTACIÓN — Hira (actualizado 2026-10-09)

**Ubicación:** Raíz del proyecto · **Responsable:** Cursor + Agentes Base · **Estado:** Activo (en curso)

---

## 🎯 Propósito de Este Plan

**Este es el documento maestro de continuación.** Cuando Cursor abra este proyecto, DEBE:
1. Leer este archivo (estás aquí)
2. Ejecutar: `bash .harness/gate/check.sh`
3. Leer: `.harness/memory/state.md` (correcciones de Carlos)
4. Seleccionar feature de la matriz de abajo
5. Continuar la fase correspondiente con el agente base indicado

> Este archivo es un **índice de estado**, no la fuente de verdad. Si contradice
> a `.harness/specs/<feature>/{spec,plan,tasks}.md` o a `.harness/memory/state.md`,
> ganan esos (Constitución Art. 12 — un canon por hecho).

---

## 📊 MATRIZ DE FEATURES — Prioridad y Estado

```
HITO ACTUAL (2026-10-09)
├── ✅ SRV-001 (Walking Skeleton)           [VERIFIED] Ancla: b4248e7
├── ✅ SRV-002 (Auth + RBAC)                [VERIFIED]
├── ✅ SRV-003 (BACnet Adapter)             [VERIFIED]
├── ✅ SRV-004 (Modbus Adapter)             [VERIFIED]
├── ✅ SRV-005 (MQTT Scanning)              [VERIFIED] Ancla: d93243a
├── ✅ HUB-001 (Walking Skeleton)           [VERIFIED] Ancla: 4d18044
│
├── 🚀 [EN CURSO] SRV-006 (Simuladores)     [Fase 4 — Implement]
│                                           Gate 1 y Gate 2 aprobados (Carlos, 2026-09-14)
│                                           T-001..T-014 commiteadas (db292d7)
│                                           T-015..T-028 en ejecución
│
├── ⏸ SRV-007 (Asociación de Puntos)       [Bloqueado: espera SRV-006 verified]
├── ⏸ HUB-H1 (Gestión Licencias)           [Backlog futuro]
└── ⏸ STU-001 (Walking Skeleton Studio)    [Backlog futuro]
```

---

## 🚀 FEATURE P0 (AHORA): SRV-006 · Simuladores de Dispositivos

### 📌 Estado Actual
- **Fase 1 (Specify):** approved — `spec.md` (Carlos, 2026-09-14)
- **Fase 2 (Plan):** approved — `plan.md` (Carlos, 2026-09-14). Las decisiones de
  diseño ya están cerradas en `plan.md §1` (Registro de decisiones); no hay
  decisiones pendientes.
- **Fase 3 (Tasks):** `tasks.md` con 28 tareas (T-001..T-028)
- **Fase 4 (Implement):** en curso
- **Archivos:**
  - `.harness/specs/SRV-006-simuladores/spec.md`
  - `.harness/specs/SRV-006-simuladores/plan.md` (arquitectura: `plan.md §2`)
  - `.harness/specs/SRV-006-simuladores/tasks.md` (progreso real tarea a tarea)

### Batches de Fase 4
| Batch | Tareas | Contenido | Infra requerida |
|---|---|---|---|
| 0 | T-001..T-014 | Núcleo, registro en memoria, puertos, servicio | — |
| 1 | T-015..T-017 | Contrato `openapi.yaml`, router, schemas, placeholders en `factory.py` | — |
| 2 | T-018..T-019 | `get_device_by_address` + fix de `is_simulator` en `upsert_device` (RF-008) | Postgres |
| 3 | T-020..T-025 | Adaptadores reales BACnet / Modbus / MQTT | Mosquitto |
| 4 | T-026 | e2e del sistema | compose completo |
| 5 | T-027..T-028 | Documentación y READMEs | — |

Cada batch: tests en verde → `revisor` → commit Conventional + `(RF-NNN)`.

### Cierre
- `bash .harness/gate/check.sh` en verde (unit) + `pytest -m integration` en verde.
- `spec.md`: `estado: implemented` + `anchor_commit` fijado.
- Session-End en `.harness/memory/history.md`, "Próximo paso" en `state.md`.
- **Gate 4 (`verified`): solo Carlos.**

---

## 🛡️ REGLAS INNEGOCIABLES

```
1. SIEMPRE: bash .harness/gate/check.sh (antes de cualquier trabajo)
2. SIEMPRE: Leer .harness/memory/state.md (correcciones de Carlos)
3. NO SALTES FASES — Gate 1 y Gate 2 son humanos; Gate 4 (verified) también
4. NO RECREES features previas — reutiliza modelos, adaptadores y tests de SRV-003/004/005
5. COMMITS: Conventional Commits + (RF-NNN)
6. NO MARQUES VERIFIED — solo Carlos firma Gate 4
7. BLOCKERS: no improvises; reporta qué, dónde y por qué, y espera decisión
```

---

## 🔗 REFERENCIAS RÁPIDAS

- **Método SDD:** `.harness/method.md` (§0–2; §3 para las fases)
- **Estado actual:** `.harness/memory/state.md`
- **Feature activa:** `.harness/specs/SRV-006-simuladores/`
- **Principios y arquitectura:** `.harness/constitution.md`
- **Roadmap del producto:** `docs/planning/ROADMAP.md`

---

**Documento maestro de continuación** · Creado 2026-10-09 por AIRA · Corregido
2026-10-09 al estado real de `tasks.md` · Próxima revisión: cuando SRV-006 esté verified
