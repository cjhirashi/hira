#!/usr/bin/env bash
# Todos los gates del harness. Correr antes de cerrar cualquier tarea y en CI.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"
fail=0

run() { echo; echo "════════ $1 ════════"; shift; "$@" || fail=1; }

run "openapi_lint"        "$PY" .harness/ci/openapi_lint.py
run "contract_gate"       "$PY" .harness/ci/contract_gate.py
run "traceability_gate"   "$PY" .harness/ci/traceability_gate.py

echo
if [ "$fail" -eq 0 ]; then
  echo "✅  run_all: todos los gates en verde"
else
  echo "❌  run_all: hay gates en rojo"
fi
exit "$fail"
