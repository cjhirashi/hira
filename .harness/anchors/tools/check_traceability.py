#!/usr/bin/env python3
"""Núcleo del gate de trazabilidad. Lo invoca .harness/ci/traceability_gate.py.

Verifica sobre .harness/anchors/registry.yaml:
  1. YAML parsea, no hay `id` duplicado, campos obligatorios presentes.
  2. Toda ruta en `spec:`, `code:`, `tests:` existe en el repo.
  3. Todo ancla con status `verified` tiene >=1 entrada en `tests:`.
  4. `superseded_by` apunta a un id existente.
  5. Ningún archivo de código referenciado (`code:`) cita en su MODULE.md un ADR con
     status `superseded` (aviso, no error, si el MODULE.md no existe todavía).
  6. Endpoints declarados en routers de las apps ⊆ el openapi.yaml de esa app
     (solo si la app existe y tiene routers).

Devuelve (errores:list[str], avisos:list[str]).
"""
from __future__ import annotations
import re
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / ".harness" / "anchors" / "registry.yaml"

VALID_KIND = {"adr", "requirement", "acceptance-criterion", "vulnerability",
              "contract", "spec-section"}
VALID_STATUS = {"accepted", "superseded", "design-only", "not-started", "in-progress",
                "implemented", "verified", "open", "mitigated", "resolved",
                "accepted-risk"}
VALID_COMPONENT = {"hira-server", "hira-hub", "hira-studio", "ecosystem"}
APPS = ("hira-server", "hira-hub", "hira-studio")


def load_entries() -> list[dict]:
    if yaml is None:
        raise SystemExit("ERROR: PyYAML no está instalado (pip install pyyaml).")
    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    return data.get("entries", []) or []


def check_registry(entries: list[dict]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    ids = {e.get("id") for e in entries if isinstance(e, dict)}

    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            errors.append(f"entrada #{i} no es un mapa")
            continue
        _id = e.get("id")
        if not _id:
            errors.append(f"entrada #{i} sin `id`")
            continue
        if _id in seen:
            errors.append(f"{_id}: id duplicado")
        seen.add(_id)

        if e.get("kind") not in VALID_KIND:
            errors.append(f"{_id}: kind inválido ({e.get('kind')!r})")
        if e.get("component") not in VALID_COMPONENT:
            errors.append(f"{_id}: component inválido ({e.get('component')!r})")
        if e.get("status") not in VALID_STATUS:
            errors.append(f"{_id}: status inválido ({e.get('status')!r})")

        for field in ("spec", "code", "tests"):
            val = e.get(field)
            if val is None:
                continue
            paths = [val] if isinstance(val, str) else list(val)
            for p in paths:
                if not p:
                    continue
                target = ROOT / p
                # rutas de carpeta admitidas si terminan en '/'
                if p.endswith("/"):
                    if not target.is_dir():
                        errors.append(f"{_id}: {field} apunta a carpeta inexistente: {p}")
                elif not target.exists():
                    errors.append(f"{_id}: {field} apunta a ruta inexistente: {p}")

        if e.get("status") == "verified" and not e.get("tests"):
            errors.append(f"{_id}: status 'verified' sin `tests:`")

        sb = e.get("superseded_by")
        if sb and sb not in ids:
            errors.append(f"{_id}: superseded_by '{sb}' no existe en el registro")

    return errors, warnings


def _superseded_adrs(entries: list[dict]) -> set[str]:
    return {e["id"] for e in entries
            if isinstance(e, dict) and e.get("kind") == "adr"
            and e.get("status") == "superseded"}


def check_superseded_refs(entries: list[dict]) -> tuple[list[str], list[str]]:
    """MODULE.md que declare un ADR superseded en su frontmatter `anchors:`."""
    errors: list[str] = []
    warnings: list[str] = []
    superseded = _superseded_adrs(entries)
    if not superseded:
        return errors, warnings
    for e in entries:
        if not isinstance(e, dict):
            continue
        code = e.get("code") or []
        code = [code] if isinstance(code, str) else code
        for p in code:
            mod = ROOT / p
            mod_md = mod / "MODULE.md" if mod.is_dir() else mod.parent / "MODULE.md"
            if not mod_md.exists():
                continue
            txt = mod_md.read_text(encoding="utf-8", errors="ignore")
            m = re.search(r"anchors:\s*\[([^\]]*)\]", txt)
            if not m:
                continue
            declared = {a.strip() for a in m.group(1).split(",")}
            bad = declared & superseded
            if bad:
                errors.append(f"{mod_md.relative_to(ROOT)} cita ADR(s) superseded: {sorted(bad)}")
    return errors, warnings


_ROUTE_RE = re.compile(
    r"""@\w+\.(?:get|post|put|patch|delete)\(\s*["'`](?P<path>/[^"'`]*)["'`]""")


def check_openapi_coverage() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if yaml is None:
        return errors, warnings
    for app in APPS:
        app_dir = ROOT / app
        routers = app_dir / "backend" / "routers"
        spec = app_dir / "docs" / "openapi.yaml"
        if not routers.is_dir():
            continue
        if not spec.exists():
            errors.append(f"{app}: existe backend/routers/ pero falta docs/openapi.yaml (Contract-First)")
            continue
        try:
            doc = yaml.safe_load(spec.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{app}: docs/openapi.yaml no parsea: {exc}")
            continue
        declared = set((doc.get("paths") or {}).keys())
        for py in routers.rglob("*.py"):
            for m in _ROUTE_RE.finditer(py.read_text(encoding="utf-8", errors="ignore")):
                raw = m.group("path")
                # normaliza {param}; ignora prefijos de include_router (heurística simple)
                if raw not in declared and not any(
                    raw.split("{")[0].rstrip("/") and raw.startswith(d.split("{")[0])
                    for d in declared
                ):
                    warnings.append(
                        f"{app}: {py.relative_to(ROOT)} declara '{raw}' que no está literal "
                        f"en docs/openapi.yaml (revisar prefijo del router)")
    return errors, warnings


def run() -> tuple[list[str], list[str]]:
    entries = load_entries()
    e1, w1 = check_registry(entries)
    e2, w2 = check_superseded_refs(entries)
    e3, w3 = check_openapi_coverage()
    return e1 + e2 + e3, w1 + w2 + w3


if __name__ == "__main__":
    errs, warns = run()
    for w in warns:
        print(f"aviso: {w}")
    for x in errs:
        print(f"ERROR: {x}")
    print(f"\n{len(errs)} error(es), {len(warns)} aviso(s), {len(load_entries())} anclas.")
    raise SystemExit(1 if errs else 0)
