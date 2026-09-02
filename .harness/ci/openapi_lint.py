#!/usr/bin/env python3
"""Lint estructural de todos los *.openapi.yaml (contratos + apps).

Chequeo ligero, sin dependencias externas:
  - parsea como YAML
  - tiene `openapi: 3.x`
  - tiene `info.title` e `info.version`
  - tiene `paths` no vacío
  - cada operación tiene `responses`
  - refs `#/components/...` apuntan a algo que existe en el doc

Para validación OpenAPI completa, instalar `openapi-spec-validator` y añadirlo aquí.
"""
from __future__ import annotations
import re
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit("ERROR: PyYAML no instalado.")

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIRS = [
    ROOT / ".harness" / "contracts",
    ROOT / "hira-server" / "docs",
    ROOT / "hira-hub" / "docs",
    ROOT / "hira-studio" / "docs",
]
REF_RE = re.compile(r"['\"]?\$ref['\"]?:\s*['\"]#/([^'\"]+)['\"]")


def _resolve(doc: dict, pointer: str) -> bool:
    node = doc
    for part in pointer.split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return False
    return True


def lint_file(path: Path) -> list[str]:
    errs: list[str] = []
    raw = path.read_text(encoding="utf-8")
    try:
        doc = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return [f"{path.name}: YAML inválido: {exc}"]
    if not isinstance(doc, dict):
        return [f"{path.name}: el documento raíz no es un mapa"]

    ver = str(doc.get("openapi", ""))
    if not ver.startswith("3."):
        errs.append(f"{path.name}: falta `openapi: 3.x` (encontrado {ver!r})")
    info = doc.get("info") or {}
    if not info.get("title"):
        errs.append(f"{path.name}: falta info.title")
    if not info.get("version"):
        errs.append(f"{path.name}: falta info.version")

    paths = doc.get("paths") or {}
    if not paths:
        errs.append(f"{path.name}: `paths` vacío")
    for p, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete",
                                      "head", "options", "trace"}:
                continue
            if not isinstance(op, dict) or "responses" not in op:
                errs.append(f"{path.name}: {method.upper()} {p} sin `responses`")

    for m in REF_RE.finditer(raw):
        pointer = m.group(1)
        if not _resolve(doc, pointer):
            errs.append(f"{path.name}: $ref roto: #/{pointer}")
    return errs


def main() -> int:
    files: list[Path] = []
    for d in TARGET_DIRS:
        if d.is_dir():
            files += sorted(d.glob("*.openapi.yaml")) + sorted(d.glob("openapi.yaml"))
    if not files:
        print("openapi_lint: no hay archivos OpenAPI que revisar todavía.")
        return 0
    all_errs: list[str] = []
    for f in files:
        all_errs += lint_file(f)
    for e in all_errs:
        print(f"ERROR: {e}")
    print(f"\n{len(all_errs)} error(es) en {len(files)} archivo(s) OpenAPI.")
    return 1 if all_errs else 0


if __name__ == "__main__":
    raise SystemExit(main())
