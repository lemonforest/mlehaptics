#!/usr/bin/env python3
"""#T1145 companion probe — which resolver actually resolves these spellings.

The #T1145 headline ("N of M dotted step-op spellings do not resolve()") is a
statement about ONE resolver: ``srmech.introspect.tool_schema.ToolSchema.
resolve``. srmech at rc444 has THREE independent op-name resolvers, and this
script measures all three over the SAME harvested spelling set, so the shipping
session can attribute the gap to a specific resolver rather than to "the
introspection surface" in the abstract.

The three resolvers (source lines verified at rc444):

  R1 EXECUTOR — ``srmech/cascade/compose.py:1180 _resolve_step_op``
     dotted  -> ``importlib.import_module(mod) + getattr(mod, attr)``
     bare    -> letter->module registry keyed by the step's ``class`` letter
                (``compose.py:128 "A": "srmech.amsc.format"`` etc.)
     This is the resolver that RUNS the 18 shipped chains.

  R2 BUILDER — ``srmech/dsl/_catalog.py:388 lookup_cascade_op``
     dotted  -> same rpartition + import + callable guard
     bare    -> the 21-name cascade catalog ONLY (no class letter available)

  R3 INTROSPECTION — ``srmech/introspect/tool_schema.py ToolSchema.resolve``
     exact fully-qualified ``ToolEntry.name`` match, else a UNIQUE dotted-SUFFIX
     match over the 663 hand-registered entries. No import, no class letter.

CONFOUND GUARD (explicit)
-------------------------
The R1 probe additionally RUNS every executable chain with its own declared
``proof_cases`` inputs. A chain that raises during INPUT BINDING or arithmetic
is NOT counted as an op-resolution failure — resolution in ``compose.py``
happens up front in ``resolve_chain`` / ``_resolve_steps`` ("activation-time
failure, never mid-run"), so an op-resolution failure surfaces as
``ChainSpecError`` and is recorded distinctly from every other exception type.
Chains are also run with NO inputs to separate "build+resolve succeeded" from
"ran to a value". A chain whose resolution cannot be attributed is labelled
UNATTRIBUTED and reported as such rather than folded into a gap number.

Discipline: no ``abs()``, no numpy, no RNG, no ``fractions``. Counting only.

Writes ``_1653_t1145_executor_probe_rc444.ndjson`` next to this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_NOTES = Path(__file__).resolve().parent
_PY_ROOT = _NOTES.parent / "python"
sys.path.insert(0, str(_PY_ROOT))

import srmech  # noqa: E402
from srmech import _toml as srmech_toml  # noqa: E402
from srmech.cascade import compose as _compose  # noqa: E402
from srmech.dsl import _catalog as dsl_catalog  # noqa: E402
from srmech.dsl._cascade_chain import (  # noqa: E402
    cascade_catalog_status,
    cascade_chain_specs,
    run_cascade_chain,
)
from srmech.introspect import tool_schema as srmech_tool_schema  # noqa: E402

OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body", "map_op")
CATALOG_DIR = _PY_ROOT / "srmech" / "cascade" / "catalogs" / "cascade_catalog"

#: HARNESS CONFOUND, ATTRIBUTED AND CLOSED. A first pass of this probe ran 93
#: of 98 proof cases; all 5 misses were ``kuramoto_step`` variant ``general``
#: with ``KeyError: 'path element .pin_anchor not found'`` /
#: ``.adjacency not found``. That is NOT an op-resolution failure and NOT a
#: descriptor defect: those chain inputs are OPTIONAL and TOML cannot spell
#: ``None``, so the per-variant defaults live in the harness. Value verbatim
#: from the SHIPPED test's own glue,
#: ``tests/test_cascade_catalog_executable_rc420.py:253 CASE_DEFAULTS`` —
#: copied here, never imported, so this probe stays standalone and touches no
#: shipped file. With it applied the probe runs 98 of 98.
CASE_DEFAULTS: Dict[Tuple[str, str], Dict[str, Any]] = {
    ("kuramoto_step", "general"): {
        "adjacency": None, "alpha": 0.0,
        "pin_anchor": None, "pin_strength": 1.0,
    },
}


def _walk(node: Any, out: List[Tuple[str, str, str]], class_id: str) -> None:
    """Collect (key, value, class_letter) for every step-op occurrence."""
    if isinstance(node, dict):
        here_class = node.get("class", class_id)
        if not isinstance(here_class, str):
            here_class = class_id
        for key, val in node.items():
            if key in OP_KEYS and isinstance(val, str):
                letter = node.get("fold_class") if key == "fold_op" else None
                if not isinstance(letter, str):
                    letter = here_class
                out.append((key, val, letter))
            else:
                _walk(val, out, here_class)
    elif isinstance(node, list):
        for val in node:
            _walk(val, out, class_id)


def harvest() -> List[Dict[str, Any]]:
    occurrences: List[Dict[str, Any]] = []
    for toml_path in sorted(CATALOG_DIR.glob("*.toml")):
        doc = srmech_toml.loads(toml_path.read_text(encoding="utf-8"))
        found: List[Tuple[str, str, str]] = []
        _walk(doc, found, "")
        for key, val, letter in found:
            occurrences.append({
                "descriptor": toml_path.name,
                "key": key,
                "value": val,
                "class_letter": letter,
            })
    assert occurrences, "harvest found no step ops"
    return occurrences


def probe_r1(spelling: str, class_letter: str) -> Dict[str, Any]:
    """EXECUTOR resolver: compose._resolve_step_op."""
    reg = dict(_compose._CLASS_MODULE_REGISTRY) if hasattr(
        _compose, "_CLASS_MODULE_REGISTRY") else None
    if reg is None:
        # discover the registry object by name-agnostic scan (rc444 names it
        # inline in compose.py); fall back to the documented letter map.
        reg = {}
        for attr in dir(_compose):
            obj = getattr(_compose, attr)
            if isinstance(obj, dict) and obj.get("A") == "srmech.amsc.format":
                reg = dict(obj)
                break
    try:
        fn = _compose._resolve_step_op("probe", 0, class_letter, spelling, reg)
        return {"r1_executor": True, "r1_target":
                f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__name__', '?')}",
                "r1_error": None}
    except Exception as exc:
        return {"r1_executor": False, "r1_target": None,
                "r1_error": f"{type(exc).__name__}: {exc}"[:200]}


def probe_r2(spelling: str) -> Dict[str, Any]:
    """BUILDER resolver: dsl._catalog.lookup_cascade_op."""
    try:
        fn = dsl_catalog.lookup_cascade_op(spelling)
        return {"r2_builder": True, "r2_target":
                f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__name__', '?')}",
                "r2_error": None}
    except Exception as exc:
        return {"r2_builder": False, "r2_target": None,
                "r2_error": f"{type(exc).__name__}: {exc}"[:200]}


def probe_r3(spelling: str, schema: Any) -> Dict[str, Any]:
    """INTROSPECTION resolver: ToolSchema.resolve."""
    hit = schema.resolve(spelling)
    return {"r3_introspect": hit is not None,
            "r3_target": hit.name if hit is not None else None}


def run_all_chains() -> List[Dict[str, Any]]:
    """Attributed run of every declared chain variant with its proof cases."""
    rows: List[Dict[str, Any]] = []
    status = cascade_catalog_status()
    for name in sorted(status):
        if status[name] != "executable":
            rows.append({"record": "chain_run", "chain": name,
                         "kind": status[name], "resolved": None,
                         "note": "leaf descriptor — no [[cascade.chain]]"})
            continue
        try:
            specs = cascade_chain_specs(name)
        except Exception as exc:
            rows.append({"record": "chain_run", "chain": name,
                         "kind": "executable", "resolved": False,
                         "attribution": "UNATTRIBUTED",
                         "error": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        for variant, spec, entry in specs:
            # (a) RESOLUTION ONLY — activation-time, no inputs bound.
            resolve_ok = True
            resolve_err = None
            try:
                _compose.resolve_chain(spec)
            except Exception as exc:
                resolve_ok = type(exc).__name__ != "ChainSpecError"
                resolve_err = f"{type(exc).__name__}: {exc}"[:200]
                if not resolve_ok:
                    resolve_err = "OP-RESOLUTION FAILURE: " + resolve_err
            # (b) FULL RUN with the descriptor's own proof-case inputs.
            cases = entry.get("proof_cases", []) if isinstance(entry, dict) else []
            ran = 0
            run_errs: List[str] = []
            for case in cases:
                inputs = case.get("inputs", {}) if isinstance(case, dict) else {}
                merged = dict(CASE_DEFAULTS.get((name, variant), {}))
                merged.update(inputs)
                try:
                    run_cascade_chain(name, merged,
                                      variant=variant if len(specs) > 1 else None)
                    ran += 1
                except Exception as exc:
                    run_errs.append(f"{type(exc).__name__}: {exc}"[:160])
            rows.append({
                "record": "chain_run",
                "chain": name,
                "variant": variant,
                "kind": "executable",
                "resolved": resolve_ok,
                "resolve_error": resolve_err,
                "proof_cases": len(cases),
                "proof_cases_ran": ran,
                "run_errors": run_errs[:3],
                "attribution": ("op-resolution OK" if resolve_ok
                                else "OP-RESOLUTION FAILURE"),
            })
    return rows


def main() -> int:
    schema = srmech_tool_schema.get_tool_schema()
    occ = harvest()

    # distinct (spelling, class_letter) so bare ops get their real letter
    seen: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for o in occ:
        key = (o["value"], o["class_letter"])
        rec = seen.setdefault(key, {
            "record": "spelling",
            "spelling": o["value"],
            "class_letter": o["class_letter"],
            "dotted": "." in o["value"],
            "occurrences": 0,
            "descriptors": set(),
            "keys": set(),
        })
        rec["occurrences"] += 1
        rec["descriptors"].add(o["descriptor"])
        rec["keys"].add(o["key"])

    rows: List[Dict[str, Any]] = []
    for (spelling, letter), rec in sorted(seen.items()):
        rec["descriptors"] = sorted(rec["descriptors"])
        rec["keys"] = sorted(rec["keys"])
        rec.update(probe_r1(spelling, letter))
        rec.update(probe_r2(spelling))
        rec.update(probe_r3(spelling, schema))
        rows.append(rec)

    chain_rows = run_all_chains()

    def _count(pred) -> int:
        return sum(1 for r in rows if pred(r))

    dotted = [r for r in rows if r["dotted"]]
    bare = [r for r in rows if not r["dotted"]]

    summary = {
        "record": "summary",
        "srmech_version": srmech.__version__,
        "native_status": srmech.native_status(),
        "tool_schema_entries": len(schema.tools),
        "distinct_spelling_rows": len(rows),
        "distinct_dotted": len(dotted),
        "distinct_bare": len(bare),
        "R1_executor_resolves": _count(lambda r: r["r1_executor"]),
        "R1_executor_fails": _count(lambda r: not r["r1_executor"]),
        "R2_builder_resolves": _count(lambda r: r["r2_builder"]),
        "R2_builder_fails": _count(lambda r: not r["r2_builder"]),
        "R3_introspect_resolves": _count(lambda r: r["r3_introspect"]),
        "R3_introspect_fails": _count(lambda r: not r["r3_introspect"]),
        "R1_dotted_resolves": sum(1 for r in dotted if r["r1_executor"]),
        "R2_dotted_resolves": sum(1 for r in dotted if r["r2_builder"]),
        "R3_dotted_resolves": sum(1 for r in dotted if r["r3_introspect"]),
        "R1_bare_resolves": sum(1 for r in bare if r["r1_executor"]),
        "R2_bare_resolves": sum(1 for r in bare if r["r2_builder"]),
        "R3_bare_resolves": sum(1 for r in bare if r["r3_introspect"]),
        "chain_variants_probed": sum(
            1 for c in chain_rows if c.get("kind") == "executable"),
        "chain_variants_op_resolution_ok": sum(
            1 for c in chain_rows if c.get("resolved") is True),
        "chain_variants_op_resolution_failed": sum(
            1 for c in chain_rows if c.get("resolved") is False),
        "proof_cases_total": sum(
            c.get("proof_cases", 0) or 0 for c in chain_rows),
        "proof_cases_ran": sum(
            c.get("proof_cases_ran", 0) or 0 for c in chain_rows),
    }

    out = _NOTES / "_1653_t1145_executor_probe_rc444.ndjson"
    with out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, sort_keys=True, default=str) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
        for c in chain_rows:
            fh.write(json.dumps(c, sort_keys=True, default=str) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
