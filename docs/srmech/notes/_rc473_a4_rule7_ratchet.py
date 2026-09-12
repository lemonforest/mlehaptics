#!/usr/bin/env python3
"""rc473 A4 (`#T1188`) -- the Rule-7 ratchet's seeds, proven rather than quoted.

``python/tests/test_jpl_audit.py`` ships the Rule-7 gate: a roster pinned
two-way against a live scan of ``c/include/srmech.h``, strict zero on a discard
of any tagged callee, and two down-only ceilings (``c/src`` and ``c/test``,
counted separately so one cannot borrow the other's headroom).

Every number in that file's comments and in ``c/JPL_AUDIT.md``'s Rule 7 section
has to be re-derivable by a reader, which is what this script is for.  It does
NOT re-implement the predicate: it IMPORTS the shipped one from the test module
by path, so the ledger and the gate cannot drift apart.  A second
implementation that agrees is a coincidence; the same implementation is a
measurement.

What it measures, in order:

  1. **conditions** -- interpreter, platform, numpy presence, tree.
  2. **header population** -- status-returning exports and the tagged subset.
  3. **seeds** -- the ``c/src`` and ``c/test`` residuals that ARE the ceilings,
     enumerated site by site rather than summarised.
  4. **non-vacuity of strict zero** -- the SAME roster applied to a baseline
     tree (pass ``--baseline-tree``).  Without it the strict-zero clause is a
     gate nobody has watched return otherwise.  When no baseline tree is given
     the row is written with ``auto_run: false`` and the reason, BY NAME,
     rather than dropped.
  5. **predicate sensitivity** -- one clause removed at a time, so "which
     clause is load-bearing" is a reading and not an opinion.
  6. **mutation** -- three discards planted into a scratch copy of
     ``c/src/srmech_kepler.c``, including the form the predicate is KNOWN not
     to see, so the blind spot is recorded by the instrument that has it.

Run from ``docs/srmech``::

    python3 notes/_rc473_a4_rule7_ratchet.py
    python3 notes/_rc473_a4_rule7_ratchet.py --baseline-tree /path/to/tree

and the baseline tree is made with (from the repo root)::

    git archive b398b8c46 docs/srmech/c | tar -x -C /some/scratch
    ... --baseline-tree /some/scratch/docs/srmech
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import pathlib
import platform
import re
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent      # docs/srmech
GATE = ROOT / "python" / "tests" / "test_jpl_audit.py"
OUT = ROOT / "notes" / "_rc473_a4_rule7_ratchet.ndjson"


def load_gate():
    """Import the SHIPPED gate module by path -- one predicate, not two."""
    spec = importlib.util.spec_from_file_location("_rc473_a4_gate", GATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


#: The three plants.  The third is the predicate's KNOWN blind spot -- a call
#: that is the second statement on one line.  It is here so the blind spot is
#: measured by the instrument that has it, instead of being a sentence.
PLANTS = {
    "void-cast-midline-on-roster":
        "    if (e > 0.0) { (void)srmech_rational_sqrt(e, &sin_h); }",
    "bare-statement-on-roster":
        "    srmech_sin(1.0, &sin_h);",
    "second-statement-on-one-line":
        "    if (e > 0.0) { } srmech_cos(1.0, &sin_h);",
}


def scan_dir(gate, directory: pathlib.Path):
    return gate._rule7_discards(directory)


def tally(rows):
    return {
        "total": len(rows),
        "void": sum(1 for r in rows if r[2] == "void"),
        "bare": sum(1 for r in rows if r[2] == "bare"),
    }


def by_callee(rows):
    out: "dict[str, int]" = {}
    for _f, _l, _form, callee in rows:
        out[callee] = out.get(callee, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


# ----------------------------------------------------------------------
# Predicate sensitivity -- one clause at a time.  This is the ONE place a
# second implementation is unavoidable, because the shipped scan has no knobs;
# it is written to reduce to the shipped behaviour under the "as-shipped"
# variant, and the row asserts that it does.
# ----------------------------------------------------------------------
VARIANTS = {
    "as-shipped": {"cont": True, "ret": True, "els": False, "isdef": False},
    "continuation clause REMOVED": {"cont": False, "ret": True, "els": False,
                                    "isdef": False},
    "`return` NOT a continuation": {"cont": True, "ret": False, "els": False,
                                    "isdef": False},
    "trailing `else` IS a continuation": {"cont": True, "ret": True,
                                          "els": True, "isdef": False},
    "definition-head clause ADDED": {"cont": True, "ret": True, "els": False,
                                     "isdef": True},
}


def scan_variant(gate, directory: pathlib.Path, cfg):
    exports, _tagged = gate._rule7_header_population()
    rows = []
    for path in sorted(directory.glob("*.c")):
        text = gate._mask_c_literals(path.read_text(encoding="utf-8"))
        population = exports | set(gate._RULE_7_STATIC_DEF.findall(text))
        previous = ""
        for lineno, line in enumerate(text.split("\n"), 1):
            for m in gate._RULE_7_VOID_CAST.finditer(line):
                if m.group(1) in population:
                    rows.append((path.name, lineno, "void", m.group(1)))
            m = gate._RULE_7_STMT_HEAD.match(line)
            if (m is not None and m.group(1) in population
                    and m.group(1) not in gate._C_KEYWORDS_CALLLIKE):
                prev = previous.rstrip()
                cont = False
                if cfg["cont"]:
                    cont = prev.endswith(gate._RULE_7_CONTINUATION_TAIL)
                    if cfg["ret"] and gate._RULE_7_RETURN_TAIL.search(prev):
                        cont = True
                    if cfg["els"] and re.search(r"\belse$", prev):
                        cont = True
                isdef = cfg["isdef"] and bool(
                    re.match(r"^\s*(static\s+)?srmech_status_t\s", line))
                if not cont and not isdef:
                    rows.append((path.name, lineno, "bare", m.group(1)))
            if line.strip():
                previous = line
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--baseline-tree", default=None,
        help="a docs/srmech-shaped tree to cross-apply the roster to, for the "
             "strict-zero non-vacuity row (e.g. an export of the commit this "
             "branch forked from)",
    )
    args = ap.parse_args()

    gate = load_gate()
    src_dir = ROOT / "c" / "src"
    test_dir = ROOT / "c" / "test"
    rows: "list[dict]" = []

    rows.append({
        "kind": "conditions",
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "platform": platform.platform(),
        "numpy_present": importlib.util.find_spec("numpy") is not None,
        "srmech_allow_stale_native": os.environ.get(
            "SRMECH_ALLOW_STALE_NATIVE", "<unset>"),
        "tree": str(ROOT),
        "gate_module": str(GATE),
        "note": "source scan only -- this ledger reads no shared library, so "
                "no native cell is involved and none is claimed",
    })

    exports, tagged = gate._rule7_header_population()
    rows.append({
        "kind": "header_population",
        "status_returning_exports": len(exports),
        "nodiscard_tagged": len(tagged),
        "roster_matches_pin": sorted(tagged) == sorted(
            gate.RULE_7_NODISCARD_ROSTER),
        "roster": sorted(tagged),
    })

    src_rows = scan_dir(gate, src_dir)
    test_rows = scan_dir(gate, test_dir)
    rows.append({
        "kind": "seeds",
        "c_src": tally(src_rows),
        "c_test": tally(test_rows),
        "ceil_src": gate.CEIL_RULE_7_SRC,
        "ceil_test": gate.CEIL_RULE_7_TEST,
        "ceilings_equal_measurement": (
            len(src_rows) == gate.CEIL_RULE_7_SRC
            and len(test_rows) == gate.CEIL_RULE_7_TEST),
        "c_src_by_callee": by_callee(src_rows),
        "c_test_by_callee": by_callee(test_rows),
        "on_roster_src": [list(r) for r in src_rows if r[3] in tagged],
        "on_roster_test": [list(r) for r in test_rows if r[3] in tagged],
    })
    rows.append({
        "kind": "c_src_residual_sites",
        "sites": [f"c/src/{f}:{ln} ({form}) {callee}"
                  for f, ln, form, callee in src_rows],
    })

    if args.baseline_tree:
        base = pathlib.Path(args.baseline_tree)
        base_src = [r for r in scan_variant(
            gate, base / "c" / "src", VARIANTS["as-shipped"])]
        base_test = [r for r in scan_variant(
            gate, base / "c" / "test", VARIANTS["as-shipped"])]
        # NOTE: the callee population here is THIS tree's header, deliberately
        # -- the question is "what would today's roster have caught on the
        # baseline", not "what did the baseline's own header tag" (it tagged
        # nothing).
        on_src = [r for r in base_src if r[3] in tagged]
        on_test = [r for r in base_test if r[3] in tagged]
        rows.append({
            "kind": "strict_zero_non_vacuity",
            "auto_run": True,
            "baseline_tree": str(base),
            "baseline_total_src": len(base_src),
            "baseline_total_test": len(base_test),
            "on_roster_src": len(on_src),
            "on_roster_test": len(on_test),
            "on_roster_total": len(on_src) + len(on_test),
            "here_on_roster_total": len([r for r in src_rows if r[3] in tagged])
            + len([r for r in test_rows if r[3] in tagged]),
            "by_callee": by_callee(on_src + on_test),
        })
    else:
        rows.append({
            "kind": "strict_zero_non_vacuity",
            "auto_run": False,
            "reason": "no --baseline-tree given. The strict-zero clause cannot "
                      "be shown to return otherwise from this tree alone, "
                      "because on this tree it returns zero BY CONSTRUCTION "
                      "(rc473 repaired every on-roster discard). Re-run with "
                      "an export of the pre-repair commit.",
        })

    for label, cfg in VARIANTS.items():
        v_src = scan_variant(gate, src_dir, cfg)
        v_test = scan_variant(gate, test_dir, cfg)
        rows.append({
            "kind": "predicate_sensitivity",
            "variant": label,
            "c_src": len(v_src),
            "c_test": len(v_test),
            "moves_a_row_vs_shipped": (
                len(v_src) != len(src_rows) or len(v_test) != len(test_rows)),
        })

    kepler = src_dir / "srmech_kepler.c"
    original = kepler.read_text(encoding="utf-8")
    lines = original.split("\n")
    anchor = next(i for i, ln in enumerate(lines) if "double sin_h;" in ln)
    for label, stmt in PLANTS.items():
        with tempfile.TemporaryDirectory() as tmp:
            scratch = pathlib.Path(tmp) / "src"
            shutil.copytree(src_dir, scratch)
            planted = lines[:anchor + 1] + [stmt] + lines[anchor + 1:]
            (scratch / "srmech_kepler.c").write_text(
                "\n".join(planted), encoding="utf-8")
            found = scan_dir(gate, scratch)
            hit = [list(r) for r in found
                   if r[0] == "srmech_kepler.c" and r[1] == anchor + 2]
            rows.append({
                "kind": "mutation",
                "plant": label,
                "statement": stmt.strip(),
                "planted_at": f"srmech_kepler.c:{anchor + 2}",
                "found": bool(hit),
                "row": hit[0] if hit else None,
                "scan_total_src": len(found),
                "baseline_total_src": len(src_rows),
                "would_trip_strict_zero": bool(
                    hit and hit[0][3] in tagged),
                "would_trip_src_ceiling": len(found) > gate.CEIL_RULE_7_SRC,
                "expected": "NOT found -- the predicate's stated blind spot"
                if label == "second-statement-on-one-line" else "found",
            })

    assert kepler.read_text(encoding="utf-8") == original, (
        "the scratch plant leaked into the real tree")

    with OUT.open("w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    for row in rows:
        if row["kind"] in ("header_population", "seeds",
                           "strict_zero_non_vacuity", "predicate_sensitivity",
                           "mutation"):
            trimmed = {k: v for k, v in row.items()
                       if k not in ("roster", "sites", "on_roster_src",
                                    "on_roster_test", "c_test_by_callee",
                                    "c_src_by_callee", "by_callee")}
            print(json.dumps(trimmed, sort_keys=True))
    print(f"\nwrote {len(rows)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
