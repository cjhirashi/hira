#!/usr/bin/env python3
"""Ensambla AGENTS.md y CLAUDE.md desde los overlays de .harness/claude/.

Uso:  python .harness/claude/build_claude.py [--check]

  (sin args)  regenera:
      hira-server/AGENTS.md, hira-server/CLAUDE.md (= ecosystem.md + hira-server.md)
      hira-hub/AGENTS.md,    hira-hub/CLAUDE.md    (= ecosystem.md + hira-hub.md)
      hira-studio/AGENTS.md, hira-studio/CLAUDE.md (= ecosystem.md + hira-studio.md)
  --check     no escribe; sale 1 si algún archivo generado está desactualizado
              (para usar en CI).

CLAUDE.md y AGENTS.md de cada producto llevan el MISMO contenido. Son artefactos
generados: no editarlos a mano — editar los overlays en .harness/claude/ y volver a
correr este script.

La raíz (AGENTS.md, CLAUDE.md) NO se genera desde aquí (nota de migración 2026-09-04
en el CLAUDE.md raíz): sigue el stub manual del esquema simplificado (Constitución
Art. 12, un canon por hecho), no el overlay ecosystem.md.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / ".harness" / "claude"

BANNER = (
    "<!-- GENERADO por .harness/claude/build_claude.py — NO EDITAR A MANO.\n"
    "     Editar los overlays en .harness/claude/ y volver a ejecutar el script. -->\n\n"
)

# destino_dir : [overlays a concatenar, en orden]
TARGETS = {
    "hira-server":  ["ecosystem.md", "hira-server.md"],
    "hira-hub":     ["ecosystem.md", "hira-hub.md"],
    "hira-studio":  ["ecosystem.md", "hira-studio.md"],
}


def strip_source_comment(text: str) -> str:
    lines = text.splitlines()
    out = []
    for ln in lines:
        if ln.strip().startswith("<!--") and "FUENTE" in ln.upper():
            continue
        out.append(ln)
    return "\n".join(out).lstrip("\n")


def render(overlays: list[str]) -> str:
    parts = [BANNER.rstrip("\n")]
    for name in overlays:
        parts.append(strip_source_comment((SRC / name).read_text(encoding="utf-8")).rstrip())
    return "\n\n".join(parts) + "\n"


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    for dest, overlays in TARGETS.items():
        if any(not (SRC / o).exists() for o in overlays):
            continue
        content = render(overlays)
        dest_dir = ROOT / dest
        if not dest_dir.is_dir():
            # app todavía no existe (F0): saltar en silencio
            continue
        for fname in ("AGENTS.md", "CLAUDE.md"):
            path = dest_dir / fname
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current == content:
                continue
            if check:
                stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(content, encoding="utf-8")
                print(f"escrito {path.relative_to(ROOT)}")
    if check and stale:
        print("DESACTUALIZADOS: " + ", ".join(stale))
        return 1
    if check:
        print("AGENTS.md / CLAUDE.md al día")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
