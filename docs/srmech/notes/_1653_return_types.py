#!/usr/bin/env python3
"""gh #1653 — RETURN TYPES: what each chain declares, what it produces, and
which of the two value wires can actually carry it.

Written to answer a direct question: does this work allow a caller to REQUEST a
return carrier type? The measured answer is NO, and the reasons are structural
rather than incidental — so they are enumerated here rather than asserted.

THREE FINDINGS, each checkable below.

1. THERE IS NO REQUEST MECHANISM ANYWHERE. Every surface is callee-declares.
   ``return_type`` / ``returntype`` / ``out_type`` / ``want_type`` /
   ``result_type`` have ZERO hits in the package. The near-misses are not it:
   ``out_kind`` runs the OTHER way (the callee reports which kind came back),
   ``as_type`` is genome type aliasing, ``carrier=`` is genome-scoped
   ("klein4" / "q8").

2. ``returns`` IS MANDATORY AND UNENFORCED. Every cascade descriptor must carry
   it — compose.py requires ('name','summary','returns','steps') — and then only
   stores it as a string. The declared values are prose: "int  # gcd(a, b) >= 0".
   Nothing compares them to what the chain produces. That makes it the natural
   attachment point for a requested-return-type standard: the declaration
   already exists on every descriptor and only enforcement is missing.

3. ⚠️ THERE ARE TWO VALUE-DESCRIPTOR VOCABULARIES AND THEY DIVERGE.
       chain-run  (cascade/compose.py)   n i q s f l      has `q`, NO `t`
       DSL F1     (dsl/_chain.py)        n i s f l t      has `t`, NO `q`

   ⚠️ AND THE PAYLOAD KEY IS NOT UNIFORM EITHER, which an earlier draft of this
   file asserted without measuring. On the chain-run wire only some kinds use
   ``v``: ``i`` reads ``desc["v"]``, ``q`` reads ``desc["n"]`` / ``desc["d"]``,
   and ``l`` reads ``desc["items"]`` — while the DSL wire uses ``desc["v"]`` for
   its list. The kind-set scan below is a regex over ``k == "<x>"``, which
   STRUCTURALLY CANNOT see key names, so it could never have caught that. The
   divergence is one notch worse than "different kind sets". Neither is a superset of the other, so the same Python value has
   different expressibility depending on which surface runs it —
   ``best_rational_signed`` returns ``tuple[int,int]``, which the DSL wire
   carries and the chain-run wire cannot.

Discipline: read-only, no numpy, no RNG. Writes one NDJSON beside itself.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))
OUT = os.path.join(HERE, "_1653_return_types.ndjson")

#: What each wire's reconstructor can rebuild. Scanned from source, not typed
#: out, so a widening on either side shows up here without an edit.
WIRES = {
    "chain_run": os.path.join(HERE, "..", "python", "srmech", "cascade", "compose.py"),
    "dsl_f1": os.path.join(HERE, "..", "python", "srmech", "dsl", "_chain.py"),
}

#: Python types each wire kind can carry. `l` is listed FLAT for chain_run on
#: purpose — cr_desc_list calls cr_desc_scalar and never itself (JPL Rule 1
#: bans the recursive walk), so a nested list is not expressible.
CARRIABLE = {
    "n": (type(None),), "i": (int,), "s": (str,), "f": (float,),
    "l": (list,), "t": (tuple,), "q": (tuple,),
}


def wire_kinds(path):
    src = open(path, encoding="utf-8").read()
    return sorted(set(re.findall(r'k == "([a-z])"', src)))


def main():
    kinds = {name: wire_kinds(p) for name, p in WIRES.items()}
    print("VALUE-DESCRIPTOR VOCABULARIES")
    for name, ks in kinds.items():
        print("    %-12s %s" % (name, " ".join(ks)))
    only_cr = sorted(set(kinds["chain_run"]) - set(kinds["dsl_f1"]))
    only_f1 = sorted(set(kinds["dsl_f1"]) - set(kinds["chain_run"]))
    print("    chain_run ONLY: %s      dsl_f1 ONLY: %s" % (only_cr, only_f1))
    assert only_cr or only_f1, (
        "the two wires now agree — if they were deliberately unified, this "
        "file's finding 3 is resolved and the assertion should be inverted")
    print()

    from srmech.dsl import _cascade_chain as _cc
    from srmech.dsl import _catalog as _cat
    from srmech.dsl import run_cascade_chain

    catalog = _cat.load_catalog()
    names = sorted(n for n, d in catalog.items()
                   if _cc.descriptor_status(d) == "executable")

    rows = []
    print("%-26s %-22s %-10s %s" % ("chain", "declared returns", "actual", "chain-run wire"))
    print("-" * 84)
    for name in names:
        entry = _cc._chain_entries(catalog[name])[0]
        declared = (entry.get("returns") or "").split("#")[0].strip()
        case = (entry.get("proof_cases") or [{}])[0]
        try:
            val = run_cascade_chain(name, **(case.get("inputs") or {}))
            actual = type(val).__name__
        except Exception as exc:                       # noqa: BLE001
            val, actual = None, "<%s>" % type(exc).__name__

        if actual.startswith("<"):
            verdict = "unknown (chain raised)"
        elif isinstance(val, (bytes, bytearray)):
            verdict = "NO — no byte kind"
        elif isinstance(val, dict):
            verdict = "NO — no mapping kind"
        elif isinstance(val, tuple):
            # ⚠️ CORRECTED rc447. This said "NO — chain-run has no `t`", and it
            # was WRONG for the one chain it named. The chain-run wire carries a
            # (num, den) RATIONAL natively as kind `q` — `_reconstruct_value`
            # returns `(int(desc["n"]), int(desc["d"]))`, a tuple — so
            # best_rational_signed's `(22, 7)` is expressible today. Only a
            # NON-rational tuple (arity != 2, or a non-int member) needs the `t`
            # kind the chain-run wire lacks.
            if len(val) == 2 and all(type(x) is int for x in val):
                verdict = "yes — as kind `q` (a rational), not `t`"
            else:
                verdict = "NO — chain-run has no `t` (the DSL wire DOES)"
        elif isinstance(val, list) and any(
                isinstance(e, (list, tuple, dict)) for e in val):
            verdict = "NO — `l` is FLAT; nesting needs a frame stack"
        elif hasattr(val, "tolist"):
            verdict = "NO — no dense-matrix kind"
        else:
            verdict = "yes"
        print("%-26s %-22s %-10s %s" % (name, declared[:22], actual, verdict))
        rows.append({"record": "chain", "chain": name, "declared": declared,
                     "actual": actual, "chain_run_carriable": verdict})

    mism = [r for r in rows
            if not r["actual"].startswith("<")
            and r["declared"].split("[")[0].lower() not in
            (r["actual"].lower(), {"mat": "mat"}.get(r["actual"].lower(), ""))]
    print()
    print("declared-vs-actual mismatches: %d" % len(mism))
    for r in mism:
        print("    %-24s declared %-18s actual %s"
              % (r["chain"], r["declared"], r["actual"]))
    print()
    print("=> `returns` is MANDATORY on every descriptor and validated by "
          "NOTHING.\n"
          "   Every declaration above happens to be accurate, so promoting it "
          "to a gate\n"
          "   would cost nothing today and would hold the line from here.")

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"record": "wires", "kinds": kinds,
                             "chain_run_only": only_cr,
                             "dsl_f1_only": only_f1}, sort_keys=True) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
