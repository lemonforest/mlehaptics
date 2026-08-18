#!/usr/bin/env python3
"""ADVERSARIAL independent recount of the 11 wedge chains' distinct ops (#1653).

Does NOT import the other agent's script. Loads the 11 shipped descriptors
through the SAME shipped loader the runtime uses and enumerates
[[cascade.chain.steps]].op across every chain variant, then cross-checks the
14 / 2 / 7 split claimed in _1653_wedge_optable_rc444.ndjson against nm on
the shipped archive.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

CAT = os.path.join(PY_ROOT, "srmech", "cascade", "catalogs", "cascade_catalog")
ARCHIVE = os.path.abspath(os.path.join(HERE, "..", "c", "build", "libsrmech.a"))

WEDGE = [
    "best_rational_signed", "chiral_dual", "cyclic_gcd", "cyclic_mod_add",
    "cyclic_mod_inv", "cyclic_mod_mul", "cyclic_mod_mul_wide",
    "cyclic_mod_pow", "encode_loe_content", "magnitude", "schur_complement",
]

from srmech import _toml as _dsl_toml  # noqa: E402


def load(name):
    path = os.path.join(CAT, name + ".toml")
    with open(path, "r", encoding="utf-8") as fh:
        return _dsl_toml.loads(fh.read())


def main():
    per_chain = {}
    ops = {}
    n_cases = 0
    for name in WEDGE:
        doc = load(name)
        chains = doc.get("cascade", {}).get("chain", [])
        if isinstance(chains, dict):
            chains = [chains]
        per_chain[name] = []
        for ci, ch in enumerate(chains):
            steps = ch.get("steps", [])
            if isinstance(steps, dict):
                steps = [steps]
            cases = ch.get("proof_cases", [])
            if isinstance(cases, dict):
                cases = [cases]
            n_cases += len(cases)
            for st in steps:
                op = st.get("op")
                ops.setdefault(op, set()).add(name)
                per_chain[name].append(op)
        print("  %-24s variants=%d steps=%s cases=%d"
              % (name, len(chains), len(per_chain[name]),
                 sum(len(c.get("proof_cases", [])) for c in chains)))

    print()
    print("distinct ops across the 11 wedge chains:", len(ops))
    for op in sorted(ops):
        print("   %-56s used_by=%s" % (op, ",".join(sorted(ops[op]))))
    print()
    print("total declared proof cases across the 11:", n_cases)

    # cross-check the ndjson ledger
    nd = os.path.join(HERE, "_1653_wedge_optable_rc444.ndjson")
    verdicts = {}
    if os.path.exists(nd):
        for ln in open(nd, "r", encoding="utf-8"):
            d = json.loads(ln)
            if d.get("record") == "op":
                verdicts[d["op"]] = (d.get("verdict"), d.get("symbols"),
                                     d.get("symbols_present"))
    print()
    print("ndjson op records:", len(verdicts))
    mine = set(ops)
    theirs = set(verdicts)
    print("  ops I found but ndjson lacks :", sorted(mine - theirs))
    print("  ops ndjson has but I lack    :", sorted(theirs - mine))
    tally = {}
    for op, (v, syms, present) in verdicts.items():
        tally[v] = tally.get(v, 0) + 1
    print("  verdict tally:", tally)

    # independent nm check of every named symbol
    out = subprocess.run(["nm", "-g", "--defined-only", ARCHIVE],
                         capture_output=True, text=True, check=False)
    syms = set()
    for line in out.stdout.splitlines():
        p = line.split()
        if len(p) == 3 and p[1] in ("T", "D", "B", "R"):
            syms.add(p[2])
    bad = []
    for op, (v, sl, present) in verdicts.items():
        for s in (sl or []):
            if s not in syms:
                bad.append((op, s))
    print("  named symbols MISSING from archive:", bad if bad else "none")
    return 0


if __name__ == "__main__":
    sys.exit(main())
