#!/usr/bin/env python3
"""#T1145 fix PROTOTYPE + safety measurement (standalone; edits nothing shipped).

The measurement (``_1653_t1145_spellings_rc444.py``) says 35 of 37 distinct
dotted step-op spellings fail ``ToolSchema.resolve()`` at rc444, and splits them
32 DATA / 3 REGISTRY. This script prototypes the ONE candidate rule that would
close the 32, and MEASURES whether it is safe to ship — i.e. whether it
introduces any ambiguity or regresses any name that resolves today.

CANDIDATE RULE — "segment-subsequence resolve"
----------------------------------------------
``ToolSchema.resolve`` at rc444 accepts an exact fully-qualified name or a
UNIQUE dotted SUFFIX (``srmech/introspect/tool_schema.py resolve_all``:
``t.name == name or t.name.endswith("." + name)``). A descriptor spelling like
``srmech.cascade.leaves.seq_get`` is neither: it is LONGER than the registry
name ``srmech.cascade.seq_get``, because the descriptor addresses the real
Python module path while the registry namespace is FLAT under ``srmech.cascade``.

Rule: after exact and suffix both miss, accept a registry name whose dotted
segments are an ordered SUBSEQUENCE of the query's dotted segments, with the
LEAF (last segment) required to match exactly, and only when EXACTLY ONE
registry entry qualifies. Everything else is unchanged, so the rule is purely
additive — it can only turn a ``None`` into a hit, never change an existing hit.

Three safety properties are measured, not asserted:
  S1 NO REGRESSION — for all 663 registry names and all 48 harvested
     descriptor spellings, every name that resolves today resolves to the SAME
     entry under the new rule.
  S2 NO AMBIGUITY on the target set — each of the 32 data-class spellings
     yields exactly one qualifying entry, and it is the expected flat name.
  S3 NO FALSE POSITIVES — the 3 registry-class spellings (genuinely
     unregistered) still resolve to NOTHING. A rule that "fixed" those would be
     inventing a match and would hide the real registration gap.

Also reported: an ALTERNATIVE fix (rewrite the 32 descriptor strings to the flat
registry spelling) with the exact per-file edit counts, and the cross-check that
the C tool registry (``c/src/srmech_tool_registry.c``) spells the same 32 names
FLAT — so either fix keeps C/Python parity and neither requires a C change.

Discipline: no ``abs()``, no numpy, no RNG, no ``fractions``. Set logic and
counting only. Nothing here is imported by shipped code.

Writes ``_1653_t1145_fix_prototype_rc444.ndjson`` next to this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_NOTES = Path(__file__).resolve().parent
_PY_ROOT = _NOTES.parent / "python"
_C_ROOT = _NOTES.parent / "c"
sys.path.insert(0, str(_PY_ROOT))

import srmech  # noqa: E402
from srmech.introspect import tool_schema as srmech_tool_schema  # noqa: E402


def is_segment_subsequence(registry_name: str, query: str) -> bool:
    """True when ``registry_name``'s segments are an ordered subsequence of
    ``query``'s segments AND the leaves match exactly.

    ``srmech.cascade.seq_get`` vs ``srmech.cascade.leaves.seq_get`` -> True
    ``srmech.cascade.seq_len`` vs ``srmech.cascade.leaves.seq_get`` -> False
    ``srmech.math.cyclic.mod_add`` vs ``srmech.cascade.leaves.mod_add`` -> False
        (``cyclic`` is not present in the query, so not a subsequence)
    """
    rparts = registry_name.split(".")
    qparts = query.split(".")
    if not rparts or not qparts:
        return False
    if rparts[-1] != qparts[-1]:
        return False
    if len(rparts) > len(qparts):
        return False
    qi = 0
    for seg in rparts:
        while qi < len(qparts) and qparts[qi] != seg:
            qi += 1
        if qi == len(qparts):
            return False
        qi += 1
    return True


def resolve_v2(schema: Any, name: str) -> Tuple[Optional[str], str, List[str]]:
    """The PROTOTYPE resolver. Returns (name_or_None, tier, candidates).

    Tier is ``exact`` / ``suffix`` / ``subsequence`` / ``ambiguous`` / ``miss``
    so the caller can prove the new tier never displaces an old one.
    """
    exact = schema.lookup(name)
    if exact is not None:
        return exact.name, "exact", [exact.name]

    suffix_matches = [t.name for t in schema.resolve_all(name)]
    if len(suffix_matches) == 1:
        return suffix_matches[0], "suffix", suffix_matches
    if len(suffix_matches) > 1:
        return None, "ambiguous", suffix_matches

    subseq = [t.name for t in schema.tools
              if is_segment_subsequence(t.name, name)]
    if len(subseq) == 1:
        return subseq[0], "subsequence", subseq
    if len(subseq) > 1:
        return None, "ambiguous", subseq
    return None, "miss", []


def load_measured() -> List[Dict[str, Any]]:
    """The rows from the primary measurement — never re-derived here."""
    path = _NOTES / "_1653_t1145_spellings_rc444.ndjson"
    assert path.exists(), (
        f"run _1653_t1145_spellings_rc444.py first; missing {path}")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert rows and rows[0].get("record") == "summary", "unexpected NDJSON shape"
    return rows


def main() -> int:
    schema = srmech_tool_schema.get_tool_schema()
    rows = load_measured()
    summary_in = rows[0]
    spellings = [r for r in rows[1:]]

    registry_names = [t.name for t in schema.tools]

    # ---- S1 NO REGRESSION -------------------------------------------------
    regressions: List[Dict[str, Any]] = []
    probes = registry_names + [r["spelling"] for r in spellings]
    for probe in probes:
        old = schema.resolve(probe)
        old_name = old.name if old is not None else None
        new_name, tier, _cands = resolve_v2(schema, probe)
        if old_name is not None and new_name != old_name:
            regressions.append({"probe": probe, "old": old_name,
                                "new": new_name, "tier": tier})

    # ---- S2 / S3 on the target sets --------------------------------------
    per_spelling: List[Dict[str, Any]] = []
    fixed_data = 0
    still_missing_registry = 0
    unexpected_fix = 0
    for r in spellings:
        spelling = r["spelling"]
        owner = r.get("fix_owner", "n/a")
        new_name, tier, cands = resolve_v2(schema, spelling)
        expect = r.get("registry_name")
        row = {
            "record": "prototype",
            "spelling": spelling,
            "kind": r.get("kind"),
            "fix_owner": owner,
            "old_resolve": r.get("resolve"),
            "new_resolve": new_name,
            "new_tier": tier,
            "new_candidates": cands,
            "expected_registry_name": expect,
            "occurrences": r.get("occurrences"),
            "descriptors": r.get("descriptors"),
        }
        if owner == "data:descriptor-overqualified":
            row["S2_ok"] = (new_name == expect and tier == "subsequence")
            if row["S2_ok"]:
                fixed_data += 1
        elif owner.startswith("registry:"):
            row["S3_ok"] = new_name is None
            if row["S3_ok"]:
                still_missing_registry += 1
            else:
                unexpected_fix += 1
        per_spelling.append(row)

    # ---- ALTERNATIVE FIX: rewrite the descriptor strings -----------------
    edits: Dict[str, int] = {}
    for r in spellings:
        if r.get("fix_owner") == "data:descriptor-overqualified":
            for desc in r.get("descriptors", []):
                edits[desc] = edits.get(desc, 0) + 0
    # count OCCURRENCES per descriptor, not distinct spellings
    catalog_dir = _PY_ROOT / "srmech" / "cascade" / "catalogs" / "cascade_catalog"
    for r in spellings:
        if r.get("fix_owner") != "data:descriptor-overqualified":
            continue
        needle = f'"{r["spelling"]}"'
        for desc in r.get("descriptors", []):
            text = (catalog_dir / desc).read_text(encoding="utf-8")
            edits[desc] = edits.get(desc, 0) + text.count(needle)

    # ---- C-parity cross-check -------------------------------------------
    c_registry = _C_ROOT / "src" / "srmech_tool_registry.c"
    c_text = c_registry.read_text(encoding="utf-8", errors="replace")
    c_flat_present = 0
    c_flat_absent: List[str] = []
    for r in spellings:
        if r.get("fix_owner") != "data:descriptor-overqualified":
            continue
        flat = r["registry_name"]
        if f'"{flat}"' in c_text:
            c_flat_present += 1
        else:
            c_flat_absent.append(flat)
    # A dotted spelling that ALREADY resolves is, by construction, a real
    # registry name and SHOULD be in the C registry — counting it as evidence
    # of a needed C change was a logic bug in a first pass of this script
    # (it flagged srmech.math.hdc.bind / .permute, the two spellings that
    # resolve today). Only a NON-resolving dotted spelling appearing as a
    # registered C name would mean the two registries disagree.
    c_dotted_present: List[str] = []
    for r in spellings:
        if r.get("kind") != "dotted" or r.get("resolves"):
            continue
        if f'"{r["spelling"]}"' in c_text:
            c_dotted_present.append(r["spelling"])

    out_summary = {
        "record": "summary",
        "srmech_version": srmech.__version__,
        "native_status": srmech.native_status(),
        "measured_input": summary_in.get("measured_figure"),
        "registry_names_probed": len(registry_names),
        "spellings_probed": len(spellings),
        "S1_regressions": len(regressions),
        "S1_verdict": "PASS" if not regressions else "FAIL",
        "S2_data_class_total": summary_in["fix_owner_counts"].get(
            "data:descriptor-overqualified", 0),
        "S2_data_class_fixed_uniquely": fixed_data,
        "S2_verdict": (
            "PASS" if fixed_data == summary_in["fix_owner_counts"].get(
                "data:descriptor-overqualified", 0) else "FAIL"),
        "S3_registry_class_total": sum(
            v for k, v in summary_in["fix_owner_counts"].items()
            if k.startswith("registry:")),
        "S3_still_correctly_unresolved": still_missing_registry,
        "S3_falsely_fixed": unexpected_fix,
        "S3_verdict": "PASS" if unexpected_fix == 0 else "FAIL",
        "alt_fix_descriptor_edits": dict(sorted(edits.items())),
        "alt_fix_edit_total": sum(edits.values()),
        "alt_fix_files_touched": len([k for k, v in edits.items() if v]),
        "c_parity_flat_names_present_in_c_registry": c_flat_present,
        "c_parity_flat_names_absent_from_c_registry": c_flat_absent,
        "c_parity_dotted_descriptor_spellings_present_in_c_registry":
            c_dotted_present,
        "c_change_required": bool(c_flat_absent) or bool(c_dotted_present),
    }

    out = _NOTES / "_1653_t1145_fix_prototype_rc444.ndjson"
    with out.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(out_summary, sort_keys=True, default=str) + "\n")
        for row in per_spelling:
            fh.write(json.dumps(row, sort_keys=True, default=str) + "\n")
        for reg in regressions:
            reg2 = dict(reg)
            reg2["record"] = "regression"
            fh.write(json.dumps(reg2, sort_keys=True, default=str) + "\n")

    print(json.dumps(out_summary, indent=2, sort_keys=True, default=str))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
