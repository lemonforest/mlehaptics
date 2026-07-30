"""rc7 Rosetta-completeness audit — enumerate the live Python public-op surface.

Walks srmech's public modules, collects public callables (functions defined in
the srmech package, excluding private _names, re-exported stdlib, classes, and
the pure bignum-reference oracle tier). Emits one NDJSON row per op so the
audit's denominator is mechanical, not hand-listed.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import json
import pkgutil
import sys
from pathlib import Path

# rc361 (`#T1034`) — the walk roots are SINGLE-SOURCED in
# python/tests/rosetta_roots.py. This file used to carry a fourth hardcoded copy
# under a comment asking the next author to keep it "IDENTICAL to the three
# test-side walk sites"; all four were measured identical before the collapse.
# ADR-0010 moves ~73 modules between namespaces, and this walk is the ledger's
# DENOMINATOR — a root missing here makes moved ops invisible, which surfaces as
# "the ledger has stale rows" (the symptom of a deletion) rather than as a move.
#
# WHY BY PATH AND NOT BY IMPORT: this script lives outside the package AND
# outside tests/, so `tests/` is not on sys.path and `import rosetta_roots`
# cannot resolve. Loading the canonical module by file location is the one import
# path that works from here. It is safe precisely because rosetta_roots.py
# imports nothing itself — there is no dependency to resolve out of context. This
# is a genuine single source, NOT a justified-second-copy-plus-equality-gate.
_CANONICAL_ROOTS = (
    Path(__file__).resolve().parents[1] / "python" / "tests" / "rosetta_roots.py")
if not _CANONICAL_ROOTS.is_file():
    raise SystemExit(
        f"cannot find the canonical Rosetta walk roots at {_CANONICAL_ROOTS}.\n"
        "This script deliberately keeps NO local copy of the root tuple — a "
        "fallback copy is what rc361 removed. If the file moved, repoint this "
        "path; do not re-inline the list.")
_spec = importlib.util.spec_from_file_location(
    "_srmech_rosetta_roots", _CANONICAL_ROOTS)
_roots_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_roots_mod)

#: A list rather than the canonical tuple only because this script's own history
#: spelled it that way; the VALUE is the canonical one.
ROOTS = list(_roots_mod.ROSETTA_ROOTS)


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
        # .adapters = the net/file-IO collector surface (requests + optional
        # netCDF4/rasterio) — the documented IO-exclusion, see ROSETTA_LEDGER.md.
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
