#!/usr/bin/env python3
"""Gate de contratos: cada app que implementa/consume un contrato de .harness/contracts/
debe mantener su docs/openapi.yaml coherente con él.

En F0 (sin apps) solo valida que los contratos parsean y que sus anclas están en el
registro. Cuando las apps existan, además:

  - App SERVIDORA de un contrato (Hub para CT-license/CT-crash-report/CT-updates; Server
    para CT-engineering-session): cada path+método del contrato debe existir en el
    openapi.yaml de la app, con los mismos códigos de respuesta.
  - App CLIENTE: se registra en .harness/contracts/CONSUMERS.yaml (qué app consume qué
    contrato) — informativo; el chequeo fuerte es del lado servidor.

El mapa contrato→servidor está abajo (SERVERS).
"""
from __future__ import annotations
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    raise SystemExit("ERROR: PyYAML no instalado.")

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / ".harness" / "contracts"
REGISTRY = ROOT / ".harness" / "anchors" / "registry.yaml"

# contrato -> (app servidora, prefijo con el que la app monta esos paths)
SERVERS = {
    "license.openapi.yaml": ("hira-hub", ""),
    "crash-report.openapi.yaml": ("hira-hub", ""),
    "updates.openapi.yaml": ("hira-hub", ""),
    "engineering-session.openapi.yaml": ("hira-server", ""),
    "marketplace.openapi.yaml": ("hira-hub", ""),  # placeholder
}
PLACEHOLDER = {"marketplace.openapi.yaml"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def registry_contract_ids() -> set[str]:
    data = load(REGISTRY)
    return {e["id"] for e in data.get("entries", []) or []
            if isinstance(e, dict) and e.get("kind") == "contract"}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    contract_files = sorted(CONTRACTS.glob("*.openapi.yaml"))
    if not contract_files:
        errors.append("no hay contratos en .harness/contracts/")
    reg_ids = registry_contract_ids()

    for cf in contract_files:
        try:
            doc = load(cf)
        except yaml.YAMLError as exc:
            errors.append(f"{cf.name}: no parsea: {exc}")
            continue
        title = (doc.get("info") or {}).get("title", "")
        # el título de nuestros contratos empieza por "CT-..."
        ct_id = title.split(" ", 1)[0].split("—")[0].strip() or cf.stem
        if ct_id.startswith("CT-") and ct_id not in reg_ids:
            warnings.append(f"{cf.name}: ancla {ct_id} no está en registry.yaml")

        if cf.name in PLACEHOLDER:
            continue

        app, prefix = SERVERS.get(cf.name, (None, ""))
        if not app:
            warnings.append(f"{cf.name}: sin app servidora asignada en contract_gate.py")
            continue
        app_spec = ROOT / app / "docs" / "openapi.yaml"
        if not app_spec.exists():
            # app todavía no implementada: informativo
            warnings.append(f"{cf.name}: {app}/docs/openapi.yaml aún no existe "
                            f"(se validará cuando {app} se implemente)")
            continue
        try:
            impl = load(app_spec)
        except yaml.YAMLError as exc:
            errors.append(f"{app}/docs/openapi.yaml: no parsea: {exc}")
            continue
        want = doc.get("paths") or {}
        got = impl.get("paths") or {}
        for p, item in want.items():
            gp = got.get(prefix + p) or got.get(p)
            if gp is None:
                errors.append(f"{cf.name}: {app} no implementa el path '{p}'")
                continue
            for method, op in item.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                if method not in gp:
                    errors.append(f"{cf.name}: {app} no implementa {method.upper()} {p}")
                    continue
                want_codes = set((op.get("responses") or {}).keys())
                got_codes = set((gp[method].get("responses") or {}).keys())
                missing = want_codes - got_codes
                if missing:
                    errors.append(f"{cf.name}: {app} {method.upper()} {p} — faltan "
                                  f"respuestas {sorted(missing)}")

    for w in warnings:
        print(f"aviso: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"\n{len(errors)} error(es), {len(warnings)} aviso(s), "
          f"{len(contract_files)} contrato(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
