#!/usr/bin/env python3
"""Entry-point CI del gate de trazabilidad.

Encadena:
  1. .harness/anchors/tools/check_traceability.py   (registry + endpoints + superseded)
  2. .harness/anchors/tools/spec_checksum.py        (specs ancladas sin registrar)
  3. build_claude.py --check                        (AGENTS.md/CLAUDE.md al día)

Sale 1 si algún paso reporta errores.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = [
    [sys.executable, str(ROOT / ".harness" / "anchors" / "tools" / "check_traceability.py")],
    [sys.executable, str(ROOT / ".harness" / "anchors" / "tools" / "spec_checksum.py")],
    [sys.executable, str(ROOT / ".harness" / "claude" / "build_claude.py"), "--check"],
]


def main() -> int:
    failed = 0
    for cmd in STEPS:
        name = Path(cmd[1]).name
        print(f"\n──── {name} ────")
        rc = subprocess.run(cmd, cwd=ROOT).returncode
        if rc != 0:
            failed += 1
            print(f"[{name}] FALLÓ (rc={rc})")
    print("\n" + ("TRAZABILIDAD OK" if not failed else f"{failed} paso(s) fallaron"))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
