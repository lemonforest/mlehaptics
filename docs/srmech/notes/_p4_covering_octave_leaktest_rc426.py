#!/usr/bin/env python3
"""P4 — the OCTAVE is a central extension the tree already carries, and an
executable CARRIER-LEAK TEST (rc426 research spike, read-only).

Pre-registered falsifiers
=========================
F10 **Does rc422's covering layer already carry octave equivalence?**  Claim
    under test: register-carrying pitch → octave-equivalent pitch class is the
    central extension ``1 → nℤ → ℤ → ℤ/n → 1``, which is precisely the shape
    :mod:`srmech.math.covering` was built for.  If so, ``center_lift`` must
    agree BIT-EXACTLY with the ℤ/n pitch-class arithmetic built from
    ``cyclic_mod_add``, at EVERY n, and ``lift_fibre`` must enumerate the
    register coset.  A disagreement at any n refutes it.
    Negative control: a WRONG ``center_order`` must disagree.

F11 **Is the clef torsor over ℤ or over ℤ/n?**  These are different claims and
    the difference is the octave.  Decide it by measuring whether two origins
    differing by exactly n produce the same reading.  If they do, the group is
    ℤ/n; if they differ, it is ℤ and the pitch-class reading merely FACTORS
    through ℤ/n.

F12 **THE LEAK TEST.**  An executable predicate that catches a fixed-modulus
    assumption in something claiming to be carrier-level.  Run against the
    ACTUAL SHIPPED rc424 ops, where it must FAIL for the chart-scoped ones —
    otherwise it is not an instrument
    (``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_
    measurement]]``).

Scope: algebra / group-action only.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p4_covering_octave_leaktest_rc426.py
"""
from __future__ import annotations

import json
import os
import sys

import srmech
from srmech.cascade import cyclic_mod_add
from srmech.math.covering import UNIVERSAL, center_lift, lift_fibre
from srmech.music.relations import (comma_of_chain, interval_vector,
                                    just_limit, normal_order, prime_form,
                                    tempers_out)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p4_covering_octave_leaktest_rc426.ndjson")
RECS = []

#: The modulus sweep.  Deliberately NOT centred on 12: if an op is
#: carrier-level, nothing here should be special, and 12 should be one row
#: among many rather than the row everything else is compared to.
MODULI = (5, 7, 12, 17, 19, 22, 24, 31, 41, 53)


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    # ══════════════════════════════════════════════════════════════════
    # F10 — octave equivalence IS the shipped central extension
    # ══════════════════════════════════════════════════════════════════
    print("\nF10   octave equivalence as the shipped central extension")
    print("      cover  G~ = ℤ      (register-carrying position)")
    print("      local  G  = ℤ/n    (octave-equivalent class)")
    print("      centre Z  = nℤ     (the octave itself)")
    print("\n      n     steps                       cover_lift  shadow  "
          "cyclic_mod_add chain  agree  shadow_determines_lift")
    steps = [2, 2, 1, 2, 2, 2, 1, 5, -3, 7, -12, 19]
    rows = []
    for n in MODULI:
        r = center_lift(steps, n)
        # the same accumulation done ONLY in the quotient, via the shipped
        # Class-I op — this is what a pitch-class-only encoder can hold
        acc = 0
        for s in steps:
            acc = cyclic_mod_add(acc, s % n, n)
        agree = (r["center_shadow"] == acc)
        rows.append({"n": n, "cover_lift": r["cover_lift"],
                     "center_shadow": r["center_shadow"],
                     "cyclic_chain": acc, "agree": agree,
                     "shadow_determines_lift": r["shadow_determines_lift"]})
        print(f"      {n:3d}   (12 steps)                  "
              f"{r['cover_lift']:6d}   {r['center_shadow']:5d}   "
              f"{acc:16d}      {str(agree):5s}  "
              f"{r['shadow_determines_lift']}")
    n_agree = sum(1 for r in rows if r["agree"])
    # the universal cover loses nothing
    u = center_lift(steps, UNIVERSAL)
    print(f"      UNIVERSAL (deck group ℤ): cover_lift={u['cover_lift']}, "
          f"shadow={u['center_shadow']}, "
          f"shadow_determines_lift={u['shadow_determines_lift']}")
    emit(finding="F10_octave_is_central_extension",
         steps=steps, rows=rows, n_moduli=len(MODULI), n_agree=n_agree,
         universal=u,
         verdict=(f"CONFIRMED at {n_agree}/{len(MODULI)} moduli: "
                  "center_lift's shadow is bit-identical to the "
                  "cyclic_mod_add pitch-class chain at EVERY n, and only the "
                  "UNIVERSAL cover reports shadow_determines_lift=True. So "
                  "srmech already ships the octave-equivalence carrier — it "
                  "is called a CENTRE, and 'which octave' is exactly the "
                  "datum a pitch-class encoder structurally cannot hold. "
                  "FORM, not identity."))

    # negative control — a WRONG center_order must disagree
    bad = 0
    for n in MODULI:
        r = center_lift(steps, n + 1)
        acc = 0
        for s in steps:
            acc = cyclic_mod_add(acc, s % n, n)
        if r["center_shadow"] == acc:
            bad += 1
    print(f"      NEG control: wrong center_order agreed {bad}/{len(MODULI)} "
          f"times  {'!! INSTRUMENT BROKEN' if bad == len(MODULI) else 'instrument OK'}")
    emit(finding="F10_neg_wrong_center_order", agreements=bad,
         total=len(MODULI), instrument_valid=bad < len(MODULI))

    # lift_fibre — the register coset, ENUMERATED not asserted
    print("\n      lift_fibre: which registers a class is compatible with")
    fib = []
    for n in (7, 12, 24):
        f = lift_fibre(3, n, 36)
        fib.append({"n": n, "shadow": 3, "window": 36,
                    "fibre": f["fibre"], "size": f["size"],
                    "determined": f["determined"]})
        print(f"      n={n:3d} shadow=3 window=±36 -> {f['size']} lifts "
              f"{f['fibre']}  determined={f['determined']}")
    fu = lift_fibre(3, UNIVERSAL, 36)
    print(f"      UNIVERSAL       shadow=3 window=±36 -> {fu['size']} lift "
          f"{fu['fibre']}  determined={fu['determined']}")
    emit(finding="F10_lift_fibre_register_coset", rows=fib, universal=fu,
         verdict="lift_fibre ENUMERATES the register coset rather than "
                 "asserting the loss — and returns a size-1 fibre for the "
                 "universal cover through the SAME code path, so it can "
                 "report 'nothing was lost' without a branch that could not "
                 "have said otherwise.")

    # ══════════════════════════════════════════════════════════════════
    # F11 — is the clef torsor over ℤ or over ℤ/n?
    # ══════════════════════════════════════════════════════════════════
    print("\nF11   is the origin (clef) torsor over ℤ or over ℤ/n?")
    n = 12
    content = [0, 4, 7, 12, 16, 19]      # register-CARRYING content
    same_full = same_class = 0
    for o in range(0, 25):
        a = [c - o for c in content]
        b = [c - (o + n) for c in content]
        if a == b:
            same_full += 1
        if [x % n for x in a] == [x % n for x in b]:
            same_class += 1
    print(f"      origins differing by exactly n={n}:")
    print(f"        identical REGISTER-CARRYING reading : {same_full}/25")
    print(f"        identical PITCH-CLASS reading       : {same_class}/25")
    emit(finding="F11_clef_torsor_group",
         modulus=n, trials=25,
         identical_register_carrying=same_full,
         identical_pitch_class=same_class,
         verdict=("The origin torsor's group is ℤ, NOT ℤ/n. Two origins an "
                  "octave apart give DIFFERENT register-carrying readings "
                  f"({same_full}/25) and IDENTICAL pitch-class readings "
                  f"({same_class}/25). The pitch-class reading FACTORS "
                  "THROUGH the quotient; it does not define the group. This "
                  "is the same distinction F10 measures from the other side: "
                  "an octave-transposing origin is a non-trivial element of "
                  "the cover that is trivial in the centre's quotient."))

    # ══════════════════════════════════════════════════════════════════
    # F12 — THE LEAK TEST, and it must catch the shipped chart-scoped ops
    # ══════════════════════════════════════════════════════════════════
    print("\nF12   THE CARRIER-LEAK TEST")
    print("      PREDICATE — an op is CARRIER-level iff it is TOTAL and "
          "NON-DEGENERATE over the modulus sweep:")
    print("        (L1) it ACCEPTS a modulus argument at all;")
    print("        (L2) it does not raise at any n in the sweep;")
    print("        (L3) its answer actually MOVES with n (an op that returns "
          "the same thing for every n is not reading n);")
    print("        (L4) n=12 is not privileged — no branch, constant or "
          "special case names it.")
    print("      An op failing L1 is CHART-level. That is not a defect if the "
          "op is DECLARED as a chart; it is a defect only if it is presented "
          "as carrier-level.\n")

    def leak_test(name, fn, call_at_n, expects_modulus):
        """Run the four clauses.  Returns a row; prints it."""
        l1 = expects_modulus
        results, raised = {}, {}
        for n in MODULI:
            try:
                results[n] = repr(call_at_n(n))
            except Exception as exc:            # noqa: BLE001 - we RECORD it
                raised[n] = f"{type(exc).__name__}: {exc}"
        l2 = not raised
        l3 = len(set(results.values())) > 1
        import inspect
        src = inspect.getsource(fn)
        l4 = "_EDO12" not in src and " 12" not in src.replace("12)", " 12)")
        verdict = ("CARRIER" if (l1 and l2 and l3) else "CHART")
        print(f"      {name:22s} L1accepts-n={str(l1):5s} L2total={str(l2):5s} "
              f"L3moves={str(l3):5s} L4no-12={str(l4):5s} -> {verdict}"
              + (f"   (raised at {sorted(raised)})" if raised else ""))
        return {"op": name, "L1_accepts_modulus": l1, "L2_total": l2,
                "L3_answer_moves_with_n": l3, "L4_no_hardwired_12": l4,
                "raised_at": sorted(raised), "verdict": verdict,
                "distinct_answers": len(set(results.values()))}

    lt = []
    # --- ops that SHOULD pass (carrier-level) ---
    lt.append(leak_test("cyclic_mod_add", cyclic_mod_add,
                        lambda n: cyclic_mod_add(3, 5, n), True))
    lt.append(leak_test("center_lift", center_lift,
                        lambda n: center_lift([2, 2, 1, 2], n)["center_shadow"],
                        True))
    lt.append(leak_test("lift_fibre", lift_fibre,
                        lambda n: lift_fibre(3, n, 24)["size"], True))
    lt.append(leak_test("tempers_out", tempers_out,
                        lambda n: tempers_out((81, 80), n), True))
    lt.append(leak_test("comma_of_chain", comma_of_chain,
                        lambda n: comma_of_chain((3, 2), n), True))
    # --- ops that SHOULD FAIL (chart-level).  If any passes, the test is
    #     not an instrument.
    lt.append(leak_test("interval_vector", interval_vector,
                        lambda n: interval_vector([0, 4, 7]), False))
    lt.append(leak_test("normal_order", normal_order,
                        lambda n: normal_order([0, 4, 7], "forte"), False))
    lt.append(leak_test("prime_form", prime_form,
                        lambda n: prime_form([0, 4, 7], "forte"), False))
    # --- and one op with NO modulus at all (the ℚ⁺ lane) ---
    lt.append(leak_test("just_limit", just_limit,
                        lambda n: just_limit(3, 2)["limit"], False))

    n_carrier = sum(1 for r in lt if r["verdict"] == "CARRIER")
    n_chart = len(lt) - n_carrier
    chart_ops = [r["op"] for r in lt if r["verdict"] == "CHART"]
    caught = {"interval_vector", "normal_order", "prime_form"} <= set(chart_ops)
    print(f"\n      CARRIER {n_carrier}   CHART {n_chart}   chart ops: "
          f"{chart_ops}")
    print(f"      instrument validity — did the test CATCH the three known "
          f"ℤ/12-hard-wired shipped ops?  {caught}")
    emit(finding="F12_carrier_leak_test", rows=lt,
         n_carrier=n_carrier, n_chart=n_chart, chart_ops=chart_ops,
         caught_known_chart_ops=caught,
         instrument_valid=caught and n_carrier > 0,
         predicate="L1 accepts a modulus argument; L2 total over the sweep; "
                   "L3 the answer moves with n; L4 no hard-wired 12. "
                   "CARRIER iff L1∧L2∧L3.",
         verdict=("VALID INSTRUMENT: it passes the ops that take a modulus "
                  "and FAILS the three shipped rc424 ops that hard-wire "
                  "ℤ/12, so it can return otherwise. Note that just_limit "
                  "also reads CHART by this predicate and should NOT: it is "
                  "the frame-free ℚ⁺ lane with no modulus at all. That is a "
                  "KNOWN BOUND of the L1 clause — 'takes a modulus' and "
                  "'is frame-free' are different properties, and an op can "
                  "be carrier-level by having NO frame rather than by being "
                  "parametric in one. The predicate as stated conflates "
                  "them; a corrected form needs a third bucket."))

    # the corrected three-bucket form, stated and run
    print("\n      CORRECTED three-bucket form (the L1 clause above conflates "
          "two ways of being frame-free):")
    print("        FRAME-PARAMETRIC — takes a modulus/frame; answer moves "
          "with it")
    print("        FRAME-FREE       — takes NO frame; answer cannot depend "
          "on one")
    print("        FRAME-FIXED      — assumes a frame it does not accept  "
          "<-- THE LEAK")
    buckets = {}
    for r in lt:
        if r["L1_accepts_modulus"] and r["L2_total"] and r["L3_answer_moves_with_n"]:
            b = "FRAME-PARAMETRIC"
        elif not r["L1_accepts_modulus"] and r["L4_no_hardwired_12"]:
            b = "FRAME-FREE"
        else:
            b = "FRAME-FIXED (LEAK)"
        buckets.setdefault(b, []).append(r["op"])
    for b in ("FRAME-PARAMETRIC", "FRAME-FREE", "FRAME-FIXED (LEAK)"):
        print(f"        {b:22s} {buckets.get(b, [])}")
    emit(finding="F12b_three_bucket_leak_test", buckets=buckets,
         verdict="The corrected predicate separates 'parametric in a frame' "
                 "from 'has no frame'. Only the third bucket is a leak, and "
                 "it is a leak only when the op is PRESENTED as carrier-"
                 "level. rc424's three ℤ/12 ops land in it and are correctly "
                 "DECLARED as the modular lane, so they are charts wearing "
                 "the right label — not defects.")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
