#!/usr/bin/env python3
"""gh #1653 round-2 BONUS finding — a THIRD blindness in the JPL Rule 4 / Rule 5
function scanner, of exactly the class rc441 (`#T1148`) closed two of.

FOUND WHILE measuring the map-arm prototype against the shipped ratchet. The
round-1 fold prototype's `pf_resolve_ref` did not appear in `_scan_functions`'
output. The cause generalises: `_scan_functions` (and `_function_bodies`) skip
any candidate whose definition line starts with `static const`, a heuristic
meant for `static const` DATA declarations. It also eats every FUNCTION whose
definition line begins `static const <type> *name(`.

srmech's C tree has such functions. For each one, Rule 4 (<= 60 lines) and
Rule 5 (>= 2 asserts) are VACUOUS: the gate cannot see them.

This script measures the population and — importantly — measures whether any of
them would actually VIOLATE if the gate could see them, so the finding is
reported at its true severity rather than inflated. It writes
docs/srmech/notes/_1653_jpl_scanner_blindspot_rc444.ndjson.

RELEVANCE TO gh #1653 specifically: two of the invisible functions live in
`srmech_compose_run.c`, which is the file the rcN map arm edits. A helper
written there as `static const srmech_json_value_t *cr_something(...)` — the
natural spelling for a JSON-node accessor, and exactly what the two existing
invisible ones are — would land UNCHECKED on both rules.
"""

import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parents[0] / "python" / "tests" / "test_jpl_audit.py"
SRC = HERE.parents[0] / "c" / "src"
OUT = HERE / "_1653_jpl_scanner_blindspot_rc444.ndjson"

DEF_PAT = re.compile(
    r"^[a-zA-Z_][a-zA-Z_0-9 \t\*]+[ \t\*]([a-zA-Z_][a-zA-Z_0-9]+)\s*\("
)


def load_audit():
    spec = importlib.util.spec_from_file_location("_jpl_audit_probe", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scan_relaxed(mod, path):
    """`_scan_functions` with ONLY the `static const` skip removed."""
    text = mod._mask_c_literals(path.read_text(encoding="utf-8"))
    lines = text.split("\n")
    starts = []
    for i, line in enumerate(lines):
        if line.rstrip().endswith(";"):
            continue
        m = DEF_PAT.match(line)
        if m is None:
            continue
        if line.lstrip().startswith(("typedef", "extern", "#")):
            continue
        for look in range(i, min(i + 10, len(lines))):
            if "{" in lines[look] and not lines[look].lstrip().startswith("/*"):
                starts.append((m.group(1), i))
                break
    out = []
    for name, start in starts:
        bs = start
        while bs < len(lines) and "{" not in lines[bs]:
            bs += 1
        if bs >= len(lines):
            continue
        depth = lines[bs].count("{") - lines[bs].count("}")
        asserts, end = 0, bs
        for j in range(bs + 1, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if "assert(" in lines[j]:
                asserts += 1
            if depth == 0:
                end = j
                break
        out.append((name, end - start + 1, asserts))
    return out


def main():
    mod = load_audit()
    hidden, seen_total = [], 0
    for f in sorted(SRC.glob("*.c")):
        seen = {n for n, _, _ in mod._scan_functions(f)}
        seen_total += len(seen)
        for name, lines, asserts in scan_relaxed(mod, f):
            if name not in seen:
                hidden.append({"file": f.name, "function": name,
                               "lines": lines, "asserts": asserts,
                               "would_violate_rule_4":
                                   lines > mod.RULE_4_MAX_LINES,
                               "would_violate_rule_5":
                                   asserts < mod.RULE_5_MIN_ASSERTS})
    v4 = sum(1 for h in hidden if h["would_violate_rule_4"])
    v5 = sum(1 for h in hidden if h["would_violate_rule_5"])
    summary = {
        "record": "summary",
        "functions_the_gate_sees": seen_total,
        "functions_the_gate_CANNOT_see": len(hidden),
        "cause": ("_scan_functions / _function_bodies skip any candidate whose "
                  "definition line starts with 'static const'; the heuristic "
                  "is for DATA declarations but also eats every function "
                  "returning 'static const <type> *'"),
        "would_be_rule_4_violations": v4,
        "would_be_rule_5_violations": v5,
        "library_is_sound": (v4 == 0 and v5 == 0),
        "gate_has_a_hole": len(hidden) > 0,
        "files_affected": sorted({h["file"] for h in hidden}),
        "in_srmech_compose_run_c": sorted(h["function"] for h in hidden
                                          if h["file"] ==
                                          "srmech_compose_run.c"),
        "rule_1_recursion_also_blind":
            ("_function_bodies applies the SAME skip, so an invisible function "
             "is also absent from the Rule 1 call graph — a recursion cycle "
             "THROUGH one of these 24 is undetectable"),
    }
    with OUT.open("w", encoding="utf-8") as fh:
        for h in sorted(hidden, key=lambda d: -d["lines"]):
            fh.write(json.dumps({"record": "hidden_function", **h},
                                sort_keys=True) + "\n")
        fh.write(json.dumps(summary, sort_keys=True) + "\n")

    print("=== JPL Rule 4 / Rule 5 scanner blind spot (measured) ===")
    for k, v in summary.items():
        if k == "record":
            continue
        print(f"  {k}: {v}")
    print("\n--- the invisible population, longest first ---")
    for h in sorted(hidden, key=lambda d: -d["lines"]):
        print(f"  {h['file']:24s} {h['function']:26s} "
              f"{h['lines']:3d} lines {h['asserts']:3d} asserts")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
