# Checks de proyecto — ecosistema Hira  (lo ejecuta gate/check.sh)
# Puede usar ok / warn / err. NO hace exit (lo hace check.sh según el conteo).

# --- Constitución versionada por front-matter (fecha, no semver aquí) ---
if grep -qE '^fecha:[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}' "$H/constitution.md"; then
  ok "constitution.md tiene fecha de última enmienda"
else
  warn "constitution.md sin 'fecha:' en el front-matter"
fi

# --- Aviso: gates de contrato/anclaje retirados, pendientes de reintroducir ---
# Se retiraron contract_gate.py / openapi_lint.py / traceability_gate.py / anchors/
# (ADR-001, Constitución Art. 12) por no haber código/contratos reales que verificar
# todavía. Conservados sin editar en docs/legacy/{ci-scripts,anchors-system}/.
# Cuando exista código real en hira-server/hira-studio/hira-hub:
#   1) declarar los servicios en gate/services.txt (<ruta>:<python|node|mcp>)
#   2) si se reactivan los linters de contrato, apuntarlos a docs/contracts/*.openapi.yaml
#      y añadir aquí las llamadas correspondientes (no antes — evitar un gate de fachada).
skip "gates de contrato/anclaje legacy — retirados hasta que haya código real que verificar (ver docs/legacy/)"
