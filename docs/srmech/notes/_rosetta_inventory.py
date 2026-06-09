"""rc7 Rosetta-completeness audit — enumerate the live Python public-op surface.

Walks srmech's public modules, collects public callables (functions defined in
the srmech package, excluding private _names, re-exported stdlib, classes, and
the pure bignum-reference oracle tier). Emits one NDJSON row per op so the
audit's denominator is mechanical, not hand-listed.
"""
from __future__ import annotations

import importlib
import inspect
import json
import pkgutil
import sys

# The public submodule roots to walk. The DSL/bus/mcp/agent/profile surfaces are
# wrapper/IO layers, not compute kernels — enumerated separately if needed.
ROOTS = [
    "srmech.amsc",
    "srmech.qm",
    "srmech.signal_processing",
]


def _iter_submodules(root_name):
    root = importlib.import_module(root_name)
    yield root
    if not hasattr(root, "__path__"):
        return
    for info in pkgutil.walk_packages(root.__path__, root_name + "."):
        name = info.name
        # skip private + research/test/_native internals
        tail = name.rsplit(".", 1)[-1]
        if tail.startswith("_") and tail != "__init__":
            continue
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield importlib.import_module(name)
        except Exception as e:  # noqa: BLE001
            print(f"# SKIP import {name}: {type(e).__name__}: {e}", file=sys.stderr)


def main():
    seen = set()
    rows = []
    for root_name in ROOTS:
        try:
            importlib.import_module(root_name)
        except Exception as e:  # noqa: BLE001
            print(f"# SKIP root {root_name}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for mod in _iter_submodules(root_name):
            modname = mod.__name__
            # Prefer __all__ when present (the curated public surface); else
            # fall back to public top-level names defined in this module.
            names = getattr(mod, "__all__", None)
            if names is None:
                names = [n for n in dir(mod) if not n.startswith("_")]
            for n in names:
                obj = getattr(mod, n, None)
                if not callable(obj):
                    continue
                if inspect.isclass(obj):
                    continue  # classes audited separately
                # only functions actually DEFINED in the srmech package
                # (skip numpy/stdlib re-exports leaking through dir())
                objmod = getattr(obj, "__module__", "") or ""
                if not objmod.startswith("srmech"):
                    continue
                # canonical id = defining module + qualname (dedup re-exports)
                qual = getattr(obj, "__qualname__", n)
                key = f"{objmod}.{qual}"
                if key in seen:
                    continue
                seen.add(key)
                try:
                    sig = str(inspect.signature(obj))
                except (ValueError, TypeError):
                    sig = "(?)"
                rows.append({
                    "exposed_as": f"{modname}.{n}",
                    "defined_at": key,
                    "module": objmod,
                    "name": n,
                    "sig": sig,
                })

    rows.sort(key=lambda r: (r["module"], r["name"]))
    for r in rows:
        print(json.dumps(r))
    # summary to stderr
    bymod = {}
    for r in rows:
        bymod[r["module"]] = bymod.get(r["module"], 0) + 1
    print(f"\n# TOTAL public callables: {len(rows)}", file=sys.stderr)
    for m in sorted(bymod):
        print(f"#   {bymod[m]:3d}  {m}", file=sys.stderr)


if __name__ == "__main__":
    main()
