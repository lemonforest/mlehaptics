#!/usr/bin/env python3
"""#T1145 re-measurement at srmech 0.9.0rc444 — dotted step-op spellings that
do not ``resolve()`` through the introspection surface.

Issue #1653 carries "32 of 35 dotted step-op spellings do not resolve()" from
~rc435, EXPLICITLY flagged as requiring re-measurement. This script IS the
re-measurement. Run it; the numbers it prints are the numbers. Nothing here is
quoted from the issue.

WHAT IT MEASURES
----------------
1. HARVEST — walk all 21 shipped cascade-catalog TOML descriptors and collect
   every value of every step-op discriminator key (``op``, ``fold_op``,
   ``reduce_op``, ``parallel_body``, ``map_op``) at ANY depth of the parsed
   TOML tree. ``map_op`` is harvested even though ``srmech/dsl/_catalog.py``
   ``_COMPOSITE_OP_KEYS`` still omits it (#T1142) — the harvest is on the DATA,
   not on the validator's key tuple, so a descriptor that started using
   ``map_op`` would still be seen here.
2. RESOLVE — for each DISTINCT DOTTED spelling (a spelling containing "."),
   attempt:
     * ``ToolSchema.lookup(name)``     exact fully-qualified match
     * ``ToolSchema.resolve(name)``    exact, else unique dotted-suffix match
     * ``ToolSchema.resolve_all(name)``  every dotted-suffix candidate
     * ``srmech.introspect.search.search(name)``  secondary (fuzzy) surface
3. CLASSIFY each non-resolving spelling into a FIX-OWNER:
     * ``data:descriptor-overqualified`` — the bare leaf DOES resolve in the
       registry, but under a SHORTER fully-qualified path than the descriptor
       spells (descriptor inserts a submodule segment the registry flattens
       away). Fix = the descriptor string, or a resolve() that tolerates
       interior-segment skipping. NOT a registry gap.
     * ``registry:unregistered`` — the bare leaf resolves to NOTHING anywhere
       in the 663-entry tool schema. The op exists as a Python callable (or
       not) but the introspection surface has never heard of it. Fix = register.
     * ``registry:unregistered+no-callable`` — as above AND the descriptor's
       dotted path does not even import to a callable. Fix = registry AND a
       real implementation/rename.
     * ``data:ambiguous-leaf`` — the bare leaf resolves to >1 FQ name, so
       ``resolve()`` correctly refuses; the descriptor's own spelling still
       misses. Fix = descriptor must spell one of the candidates exactly.

CONFOUND GUARD
--------------
This measurement has NO C harness and NO arena — it is pure Python
introspection, so the "my harness rejected it, not the grammar" confound of the
C-parity measurements cannot arise here. The one confound that CAN arise is
harness-side import failure masquerading as an unregistered op; it is guarded by
recording, per spelling, an INDEPENDENT ``importlib`` probe of the dotted path
(``callable_import``) alongside the registry verdict. A spelling is only ever
labelled ``registry:unregistered`` when the registry genuinely has no entry for
its leaf; the callable probe is reported separately and never used to
manufacture a rejection.

Discipline: no ``abs()``, no numpy, no RNG, no ``fractions``. Counting only.

Writes ``_1653_t1145_spellings_rc444.ndjson`` next to this file.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# --- locate the worktree's srmech (never a site-packages srmech) -------------
_NOTES = Path(__file__).resolve().parent
_PY_ROOT = _NOTES.parent / "python"
sys.path.insert(0, str(_PY_ROOT))

import srmech  # noqa: E402
from srmech import _toml as srmech_toml  # noqa: E402
from srmech.dsl import _catalog as dsl_catalog  # noqa: E402
from srmech.introspect import search as srmech_search  # noqa: E402
from srmech.introspect import tool_schema as srmech_tool_schema  # noqa: E402

#: The five step-op discriminator keys. ``map_op`` is included deliberately:
#: ``srmech/dsl/_catalog.py`` ``_COMPOSITE_OP_KEYS`` omits it at rc444 (#T1142),
#: so harvesting it here measures the DATA rather than the validator's blind
#: spot.
OP_KEYS: Tuple[str, ...] = ("op", "fold_op", "reduce_op", "parallel_body", "map_op")

CATALOG_DIR = _PY_ROOT / "srmech" / "cascade" / "catalogs" / "cascade_catalog"


def _walk(node: Any, path: str, out: List[Dict[str, Any]]) -> None:
    """Collect every OP_KEYS value at any depth of a parsed TOML tree."""
    if isinstance(node, dict):
        for key, val in node.items():
            here = f"{path}.{key}" if path else key
            if key in OP_KEYS and isinstance(val, str):
                out.append({"key": key, "value": val, "toml_path": here})
            else:
                _walk(val, here, out)
    elif isinstance(node, list):
        for idx, val in enumerate(node):
            _walk(val, f"{path}[{idx}]", out)


def harvest() -> List[Dict[str, Any]]:
    """Every step-op occurrence across the 21 shipped descriptors."""
    occurrences: List[Dict[str, Any]] = []
    files = sorted(CATALOG_DIR.glob("*.toml"))
    assert files, f"no descriptors found under {CATALOG_DIR}"
    for toml_path in files:
        doc = srmech_toml.loads(toml_path.read_text(encoding="utf-8"))
        found: List[Dict[str, Any]] = []
        _walk(doc, "", found)
        for rec in found:
            rec["descriptor"] = toml_path.name
            occurrences.append(rec)
    return occurrences


def _import_probe(dotted: str) -> Dict[str, Any]:
    """Independent confound guard: does the descriptor's dotted path import?

    Tries progressively shorter module prefixes and looks up the remaining
    segments as attributes. Reported alongside — never substituted for — the
    registry verdict.
    """
    parts = dotted.split(".")
    for split in range(len(parts) - 1, 0, -1):
        mod_name = ".".join(parts[:split])
        attr_names = parts[split:]
        try:
            obj: Any = importlib.import_module(mod_name)
        except Exception:
            continue
        ok = True
        for attr in attr_names:
            if not hasattr(obj, attr):
                ok = False
                break
            obj = getattr(obj, attr)
        if ok:
            return {
                "callable_import": True,
                "callable_module": mod_name,
                "callable_is_callable": bool(callable(obj)),
            }
    return {"callable_import": False, "callable_module": None,
            "callable_is_callable": False}


def classify(spelling: str, schema: Any) -> Dict[str, Any]:
    """Resolution attempt + fix-owner classification for one spelling."""
    leaf = spelling.rsplit(".", 1)[-1]

    exact = schema.lookup(spelling)
    resolved = schema.resolve(spelling)
    all_matches = schema.resolve_all(spelling)

    leaf_resolved = schema.resolve(leaf)
    leaf_all = schema.resolve_all(leaf)

    # SECONDARY SURFACE — srmech.introspect.search.search.
    #
    # HARNESS CONFOUND, ATTRIBUTED AND CLOSED. A first pass of this script read
    # the result as ``getattr(sr, "tools") or getattr(sr, "results")`` and got
    # an empty list for EVERY spelling, which would have reported "the
    # secondary surface finds nothing" — a fabricated gap. ``SearchResult`` is
    # a TUPLE SUBCLASS of ``{"kind","name","score","why","reach"}`` dicts (it
    # carries ``count`` / ``index`` / ``witness`` as EXTRA fields, not as the
    # hit list), so the hits are obtained by ITERATING it. Corrected below; the
    # secondary surface in fact recovers most of the data-class misses.
    try:
        sr = srmech_search.search(spelling, k=5)
        search_hits = [
            h["name"] if isinstance(h, dict) else getattr(h, "name", str(h))
            for h in sr
        ]
    except Exception as exc:  # pragma: no cover - defensive only
        search_hits = [f"<search error: {type(exc).__name__}: {exc}>"]

    rec: Dict[str, Any] = {
        "spelling": spelling,
        "leaf": leaf,
        "lookup_exact": exact.name if exact is not None else None,
        "resolve": resolved.name if resolved is not None else None,
        "resolve_all": [t.name for t in all_matches],
        "resolves": resolved is not None,
        "leaf_resolve": leaf_resolved.name if leaf_resolved is not None else None,
        "leaf_resolve_all": [t.name for t in leaf_all],
        "search_top5": search_hits,
    }
    rec.update(_import_probe(spelling))

    # cross-resolver column so this NDJSON stands alone: the BUILDER resolver
    # (srmech/dsl/_catalog.py:388 lookup_cascade_op) over the same spelling.
    # The EXECUTOR resolver (srmech/cascade/compose.py:1180 _resolve_step_op)
    # needs the step's `class` letter for a BARE op, so it lives in the
    # companion probe `_1653_t1145_executor_probe_rc444.py`.
    try:
        fn = dsl_catalog.lookup_cascade_op(spelling)
        rec["builder_resolve"] = (
            f"{getattr(fn, '__module__', '?')}.{getattr(fn, '__name__', '?')}")
        rec["builder_resolves"] = True
    except Exception as exc:
        rec["builder_resolve"] = None
        rec["builder_resolves"] = False
        rec["builder_error"] = f"{type(exc).__name__}: {exc}"[:160]

    if resolved is not None:
        rec["fix_owner"] = "none"
        rec["fix_note"] = "resolves as spelled"
        return rec

    if len(leaf_all) == 1:
        registry_name = leaf_all[0].name
        rec["fix_owner"] = "data:descriptor-overqualified"
        rec["registry_name"] = registry_name
        rec["fix_note"] = (
            f"registry has {registry_name!r}; descriptor over-qualifies with "
            f"an interior segment the registry flattens away"
        )
        # exactly which interior segment(s) the registry drops
        rec["dropped_segments"] = [
            s for s in spelling.split(".") if s not in registry_name.split(".")
        ]
        rec["search_rank_of_registry_name"] = (
            search_hits.index(registry_name) + 1
            if registry_name in search_hits else 0
        )
    elif len(leaf_all) > 1:
        rec["fix_owner"] = "data:ambiguous-leaf"
        rec["registry_name"] = None
        rec["fix_note"] = (
            "bare leaf is ambiguous in the registry ("
            + ", ".join(t.name for t in leaf_all)
            + "); descriptor spelling matches none of them exactly"
        )
    else:
        rec["registry_name"] = None
        if rec["callable_import"]:
            rec["fix_owner"] = "registry:unregistered"
            rec["fix_note"] = (
                "no registry entry for the leaf anywhere; the dotted path DOES "
                "import to a real object, so this is a registration gap"
            )
        else:
            rec["fix_owner"] = "registry:unregistered+no-callable"
            rec["fix_note"] = (
                "no registry entry for the leaf AND the dotted path does not "
                "import; needs both an implementation/rename and registration"
            )
    return rec


def main() -> int:
    schema = srmech_tool_schema.get_tool_schema()
    occurrences = harvest()

    dotted = sorted({o["value"] for o in occurrences if "." in o["value"]})
    bare = sorted({o["value"] for o in occurrences if "." not in o["value"]})

    # occurrence counts per distinct spelling / per descriptor
    occ_count: Dict[str, int] = {}
    occ_descriptors: Dict[str, set] = {}
    for o in occurrences:
        occ_count[o["value"]] = occ_count.get(o["value"], 0) + 1
        occ_descriptors.setdefault(o["value"], set()).add(o["descriptor"])

    rows: List[Dict[str, Any]] = []
    for spelling in dotted:
        rec = classify(spelling, schema)
        rec["occurrences"] = occ_count[spelling]
        rec["descriptors"] = sorted(occ_descriptors[spelling])
        rec["kind"] = "dotted"
        rows.append(rec)

    # bare spellings measured too, so the denominator choice is auditable
    bare_rows: List[Dict[str, Any]] = []
    for spelling in bare:
        resolved = schema.resolve(spelling)
        all_m = schema.resolve_all(spelling)
        try:
            hits = [h["name"] for h in srmech_search.search(spelling, k=5)]
        except Exception as exc:  # pragma: no cover - defensive only
            hits = [f"<search error: {type(exc).__name__}>"]
        bare_rows.append({
            "kind": "bare",
            "spelling": spelling,
            "leaf": spelling,
            "resolve": resolved.name if resolved is not None else None,
            "resolve_all": [t.name for t in all_m],
            "resolves": resolved is not None,
            "search_top5": hits,
            "occurrences": occ_count[spelling],
            "descriptors": sorted(occ_descriptors[spelling]),
        })

    n_dotted = len(rows)
    n_dotted_fail = sum(1 for r in rows if not r["resolves"])
    n_bare = len(bare_rows)
    n_bare_fail = sum(1 for r in bare_rows if not r["resolves"])

    owners: Dict[str, int] = {}
    for r in rows:
        if not r["resolves"]:
            owners[r["fix_owner"]] = owners.get(r["fix_owner"], 0) + 1

    search_recovered = sum(
        1 for r in rows
        if not r["resolves"] and r.get("search_rank_of_registry_name", 0) == 1)

    summary = {
        "record": "summary",
        "srmech_version": srmech.__version__,
        # native_status() is the real surface; `srmech.HAS_NATIVE` does NOT
        # exist at rc444 and reading it reported has_native=False in a first
        # pass of this script. Attributed and corrected.
        "native_status": srmech.native_status(),
        "tool_schema_entries": len(schema.tools),
        "descriptors_scanned": len(sorted(CATALOG_DIR.glob("*.toml"))),
        "op_keys_harvested": list(OP_KEYS),
        "op_key_occurrences_total": len(occurrences),
        "op_key_occurrence_by_key": _by_key(occurrences),
        "distinct_spellings_total": n_dotted + n_bare,
        "distinct_dotted_spellings": n_dotted,
        "distinct_dotted_not_resolving": n_dotted_fail,
        "distinct_dotted_resolving": n_dotted - n_dotted_fail,
        "distinct_bare_spellings": n_bare,
        "distinct_bare_not_resolving": n_bare_fail,
        "dotted_occurrences_total": sum(r["occurrences"] for r in rows),
        "dotted_occurrences_not_resolving": sum(
            r["occurrences"] for r in rows if not r["resolves"]),
        "fix_owner_counts": owners,
        "builder_resolves_dotted": sum(1 for r in rows if r["builder_resolves"]),
        "builder_fails_dotted": sum(
            1 for r in rows if not r["builder_resolves"]),
        "search_recovers_registry_name_at_rank1": search_recovered,
        "issue_carried_figure": "32 of 35 dotted step-op spellings do not resolve()",
        "measured_figure": f"{n_dotted_fail} of {n_dotted}",
        "denominator_note": (
            "denominator = DISTINCT dotted spelling strings. The companion "
            "probe keys by (spelling, class-letter) and therefore reports 38, "
            "not 37: 'srmech.cascade.leaves.seq_get' appears under BOTH class "
            "'C' and class 'E' in klein4_from_one.toml / octonion_dft.toml / "
            "quaternion_dft.toml. The class letter is irrelevant to a DOTTED "
            "op (both resolvers import it), so 37 is the correct #T1145 "
            "denominator."
        ),
    }

    # ---- adjunct: can the introspection surface name the 21 DESCRIPTORS? ---
    # #T1145's framing is "the introspection surface cannot name the ops its own
    # shipped proofs use". The step-op measurement above answers that for STEPS;
    # this answers it for the descriptor NAMES themselves ([cascade].name), which
    # are the names a caller would reach for first.
    from srmech.dsl._cascade_chain import cascade_catalog_status  # noqa: E402
    status = cascade_catalog_status()
    name_rows: List[Dict[str, Any]] = []
    for op_name in sorted(status):
        hit = schema.resolve(op_name)
        name_rows.append({
            "kind": "descriptor_name",
            "spelling": op_name,
            "descriptor_kind": status[op_name],
            "resolve": hit.name if hit is not None else None,
            "resolves": hit is not None,
        })
    summary["descriptor_names_total"] = len(name_rows)
    summary["descriptor_names_not_resolving"] = [
        r["spelling"] for r in name_rows if not r["resolves"]]

    out_path = _NOTES / "_1653_t1145_spellings_rc444.ndjson"
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(summary, sort_keys=True) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
        for r in bare_rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
        for r in name_rows:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\nwrote {out_path}")
    print(f"\nMEASURED: {n_dotted_fail} of {n_dotted} distinct DOTTED spellings "
          f"do not resolve()")
    for owner, count in sorted(owners.items()):
        print(f"  {owner}: {count}")
    return 0


def _by_key(occurrences: List[Dict[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for o in occurrences:
        out[o["key"]] = out.get(o["key"], 0) + 1
    return out


if __name__ == "__main__":
    raise SystemExit(main())
