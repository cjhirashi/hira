---
título: Código previo de Hira Server (archivado)
tipo: Puntero
status: referencia
---

# Legacy — implementación previa de Hira Server

La implementación previa de Hira Server (~24 sprints; repo original
`github.com/cjhirashi/hira-server`) **no se continúa**. Bajo el harness SDD-Anchored,
Hira Server se reimplementa desde cero siguiendo `.harness/spec/hira-server/`.

El snapshot completo de ese código está en la rama git **`legacy/hira-server-snapshot`**
(un único commit `chore(legacy): snapshot de la implementación previa de Hira Server`
sobre el commit inicial del repo). Incluye su `DEVIATIONS.md` original.

```bash
git log --oneline legacy/hira-server-snapshot
git show legacy/hira-server-snapshot:hira-server/backend/main.py
git checkout legacy/hira-server-snapshot -- hira-server   # extraer si hace falta consultar
```

Contexto de por qué se descartó y qué lecciones/deudas siguen vigentes:
`.harness/coordination/sprint-history.md` (deudas `DA-003` / `DA-004` → anclas
`REQ-SRV-candidatos` / `REQ-SRV-licencia-online` en el registro).
