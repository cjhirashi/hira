#!/usr/bin/env python3
"""Checksums de las secciones de spec ancladas en el registro.

  python .harness/anchors/tools/spec_checksum.py           # verifica contra el manifiesto
  python .harness/anchors/tools/spec_checksum.py --update   # regenera el manifiesto

El manifiesto vive en .harness/anchors/spec-checksums.txt (una línea `sha256  ruta`).
Solo cubre entradas del registry con kind: spec-section. Sirve para que el gate de
trazabilidad avise cuando una spec anclada cambió sin que nadie lo registrara — no impide
el cambio, obliga a reconocerlo (`--update` + commit `[SPEC]`).
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / ".harness" / "anchors" / "registry.yaml"
MANIFEST = ROOT / ".harness" / "anchors" / "spec-checksums.txt"


def spec_paths() -> list[str]:
    if yaml is None:
        raise SystemExit("ERROR: PyYAML no instalado.")
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    out = []
    for e in data.get("entries", []) or []:
        if isinstance(e, dict) and e.get("kind") == "spec-section" and e.get("spec"):
            out.append(e["spec"])
    return sorted(set(out))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> dict[str, str]:
    result = {}
    for p in spec_paths():
        fp = ROOT / p
        result[p] = sha(fp) if fp.exists() else "MISSING"
    return result


def load_manifest() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    out = {}
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, path = line.partition("  ")
        out[path] = digest
    return out


def write_manifest(data: dict[str, str]) -> None:
    lines = ["# sha256  ruta   —  generado por spec_checksum.py --update"]
    lines += [f"{v}  {k}" for k, v in sorted(data.items())]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    current = build()
    if "--update" in sys.argv:
        write_manifest(current)
        print(f"manifiesto actualizado: {len(current)} secciones de spec")
        return 0
    saved = load_manifest()
    problems = []
    if not saved:
        problems.append("no existe .harness/anchors/spec-checksums.txt "
                        "(correr con --update una vez)")
    for path, digest in current.items():
        if digest == "MISSING":
            problems.append(f"spec anclada no existe: {path}")
        elif path not in saved:
            problems.append(f"spec anclada sin checksum en el manifiesto: {path} (--update)")
        elif saved[path] != digest:
            problems.append(f"spec cambió sin registrar: {path} "
                            f"(correr --update y commitear como [SPEC])")
    for p in problems:
        print(f"ERROR: {p}")
    print(f"\n{len(problems)} problema(s), {len(current)} sección(es) de spec.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
