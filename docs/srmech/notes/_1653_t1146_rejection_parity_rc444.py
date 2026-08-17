#!/usr/bin/env python3
"""`#T1146` — REJECTION PARITY census: does C refuse what Python refuses?

Sub-item of GitHub issue #1653, pre-rcN research. srmech 0.9.0rc444, ABI 17.

WHY THIS EXISTS. #1653 frames the C parity gap as "C cannot do what Python can" -- a
MISSING CAPABILITY. The rc444 divergence probe found the opposite and more dangerous
direction: C validates REQUIRED keys and never a CLOSED KEY SET, so it silently accepts
mis-specified declarations and RETURNS A VALUE where Python raises. A capability-only fix
closes the first gap and leaves this one open, and this is the one that can hand back a
wrong answer instead of an error.

ROOT CAUSE, read from source (dsl/_chain.py:111-124 `_then_native_desc`):
    stage = {"op": op_name}
    for kk, vv in kwargs.items():
        if not _is_c_scalar(vv):   # <-- a VALUE-TYPE gate
            return None
        stage[kk] = vv             # <-- every scalar kwarg copied in, name UNCHECKED
There is no KEY-NAME gate anywhere on this path, and srmech_dsl_chain_run.c:537-565
`dsl_leaf_dispatch` has no leaf that validates its own key set. So the two projections
disagree on REJECTION while agreeing on acceptance.

WHAT THIS CENSUS ADDS over the 4 anecdotes (D1-D4): D1 probed 8 cases. This enumerates
EVERY C-backed leaf op named in srmech_dsl_chain_run.c and probes each one, so the
denominator is the surface rather than a sample. The 2x2 per cell is
(pure accepts?) x (native accepts?), and the defect cell is pure-REJECTS x native-ACCEPTS.

Discipline: no ALU-magnitude idiom, no numpy, no RNG, no stdlib fractions. Exact values.
Writes only under docs/srmech/notes/. Edits no shipped source.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python"))

import srmech
from srmech.dsl import chain
import srmech.dsl._chain as _c

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_1653_t1146_rejection_parity_rc444.ndjson")

# The C-backed leaf/body op names, harvested from the C source's own string literals.
C_BACKED = ["autocorrelation", "best_rational_signed", "chiral_flip", "cyclic_gcd",
            "magnitude", "net_chirality", "pin_slot_at_zero", "reorient", "seq_get"]

# A valid input + valid kwargs per op, so the CONTROL cell is a genuine success.
VALID = {
    "magnitude":            (-3.5, {}),
    "reorient":             (5, {"orientation": -1}),
    "pin_slot_at_zero":     (5, {}),
    "cyclic_gcd":           (12, {"b": 18}),
    "best_rational_signed": (5, {"denom": 6, "max_d": 10}),
    "net_chirality":        ([1, -1, 1], {}),
    "autocorrelation":      ([1, 2, 3], {}),
    # seq_get is NOT a catalog name in Python (that asymmetry IS divergence D3) -- so no
    # valid Python call exists and it cannot be control-paired here. Recorded, not guessed.
    "chiral_flip":          ([1, 0, 1, 0], {}),
}
# ops whose control could not be constructed -> reported as UNMEASURED, never as clean.
UNPAIRABLE = {"seq_get": "not a catalog name in Python (divergence D3) -- no valid pure call"}

# Scalar kwargs that NO op should accept. Scalar is the point: a non-scalar defers to pure.
BOGUS = ["bogus", "nonexistent_kwarg", "max_denominator", "orientation", "index"]


def run_native(op, val, kw):
    try:
        return True, chain().then(op, **kw).run(val)
    except Exception as e:
        return False, "%s: %s" % (type(e).__name__, str(e)[:90])


def run_pure(op, val, kw):
    """Force the pure runner by making the native stage-builder decline, exactly as it
    already does for a non-scalar kwarg. Restored immediately; shipped source untouched."""
    orig = _c._then_native_desc
    _c._then_native_desc = lambda *a, **k: None
    try:
        return run_native(op, val, kw)
    finally:
        _c._then_native_desc = orig


def main():
    ns = srmech.native_status()
    print("srmech %s  native=%s dispatching=%s abi=%s"
          % (srmech.__version__, ns["has_native"], ns["dispatching"], ns["abi_version"]))
    print()
    recs = []
    controls_ok = 0
    controls_total = 0
    cells = {"parity_ok_both_accept": 0, "parity_ok_both_reject": 0,
             "DEFECT_pure_rejects_native_accepts": 0, "capability_gap_pure_accepts_native_rejects": 0}
    defects = []

    print("%-22s %-22s %-11s %-11s %s" % ("op", "probe", "pure", "native", "verdict"))
    print("-" * 88)
    for op in C_BACKED:
        if op in UNPAIRABLE:
            print("%-22s %-22s %-11s %-11s %s" % (op, "UNPAIRABLE", "-", "-", UNPAIRABLE[op]))
            recs.append({"record": "unmeasured", "op": op, "reason": UNPAIRABLE[op]})
            continue
        val, good_kw = VALID[op]
        # CONTROL: the valid call must succeed on BOTH, or every verdict for this op is void.
        controls_total += 1
        p_ok, p_v = run_pure(op, val, dict(good_kw))
        n_ok, n_v = run_native(op, val, dict(good_kw))
        ctl = p_ok and n_ok and p_v == n_v
        controls_ok += bool(ctl)
        print("%-22s %-22s %-11s %-11s %s"
              % (op, "CONTROL(valid)", "ok" if p_ok else "raise",
                 "ok" if n_ok else "raise",
                 "CONTROL OK (values agree)" if ctl else "CONTROL FAILED -> op void"))
        recs.append({"record": "control", "op": op, "pure_ok": p_ok, "native_ok": n_ok,
                     "pure_value": repr(p_v), "native_value": repr(n_v), "control_ok": ctl})
        if not ctl:
            continue

        for bg in BOGUS:
            if bg in good_kw:
                continue           # not bogus for this op
            kw = dict(good_kw)
            kw[bg] = 1
            p_ok, p_v = run_pure(op, val, kw)
            n_ok, n_v = run_native(op, val, kw)
            if p_ok and n_ok:
                verdict = "parity_ok_both_accept"
            elif (not p_ok) and (not n_ok):
                verdict = "parity_ok_both_reject"
            elif (not p_ok) and n_ok:
                verdict = "DEFECT_pure_rejects_native_accepts"
                defects.append((op, bg, n_v))
            else:
                verdict = "capability_gap_pure_accepts_native_rejects"
            cells[verdict] += 1
            print("%-22s %-22s %-11s %-11s %s"
                  % (op, "+%s=1" % bg, "ok" if p_ok else "raise",
                     ("ok->%r" % (n_v,))[:11] if n_ok else "raise", verdict))
            recs.append({"record": "probe", "op": op, "bogus_kwarg": bg,
                         "pure_ok": p_ok, "pure_result": repr(p_v),
                         "native_ok": n_ok, "native_result": repr(n_v),
                         "verdict": verdict})

    print()
    print("CONTROLS: %d/%d ok  (a failed control voids that op's rows)" % (controls_ok, controls_total))
    print("CELLS:", json.dumps(cells))
    n_def = cells["DEFECT_pure_rejects_native_accepts"]
    total = sum(cells.values())
    print()
    measured = controls_ok
    print("REJECTION-PARITY DEFECT RATE: %d of %d probes" % (n_def, total))
    print("  ops AFFECTED  : %d" % len({d[0] for d in defects}))
    print("  ops MEASURED  : %d  (control passed)" % measured)
    print("  ops UNMEASURED: %d  -> %s"
          % (len(C_BACKED) - measured,
             sorted(set(C_BACKED) - {r["op"] for r in recs
                                     if r.get("record") == "control" and r.get("control_ok")})))
    print("  HONEST DENOMINATOR: %d of %d ops that could be control-paired." % (len({d[0] for d in defects}), measured))
    if defects:
        print("the defect cell -- pure RAISES, native RETURNS A VALUE:")
        for op, bg, v in defects:
            print("    chain().then(%-22s %-20s).run(...) -> %r" % ("'%s'," % op, "%s=1" % bg, v))
    # --- WHY are the parity-OK ops OK? Attribution matters: "copy that op's validator"
    # would be false advice if they reject INCIDENTALLY. Measured, not assumed.
    print()
    print("ATTRIBUTION of the parity_ok_both_reject cell -- is there a real key-set validator?")
    ok_ops = sorted({r["op"] for r in recs
                     if r.get("record") == "probe"
                     and r.get("verdict") == "parity_ok_both_reject"})
    for op in ok_ops:
        val, good_kw = VALID[op]
        kw = dict(good_kw); kw["bogus"] = 1
        n_ok, n_v = run_native(op, val, kw)
        p_ok, p_v = run_pure(op, val, kw)
        same = (str(n_v) == str(p_v))
        pyerr = "unexpected keyword argument" in str(n_v)
        print("    %-20s native=%s" % (op, str(n_v)[:74]))
        print("    %-20s identical to pure=%s ; message is a PYTHON TypeError=%s"
              % ("", same, pyerr))
        recs.append({"record": "attribution", "op": op,
                     "native_msg": str(n_v), "pure_msg": str(p_v),
                     "identical_to_pure": same,
                     "is_python_typeerror": pyerr,
                     "verdict": ("INCIDENTAL — fell back to the pure path; C validated nothing"
                                 if (same and pyerr) else "possible real C key-set check")})
    incidental = all(str(r.get("verdict","")).startswith("INCIDENTAL")
                     for r in recs if r.get("record") == "attribution")
    print()
    if incidental and ok_ops:
        print("  => ALL parity-OK ops reject INCIDENTALLY: the native stage-builder declined and")
        print("     PYTHON raised. THERE IS NO KEY-SET VALIDATOR ANYWHERE IN THE C LEAF SURFACE,")
        print("     so the rcN has NO existing in-tree pattern to copy. The 5 defective ops are")
        print("     exactly the ones that DO reach C; the clean ones are clean only because they")
        print("     do not.")
    recs.append({"record": "attribution_summary",
                 "all_parity_ok_are_incidental": bool(incidental and ok_ops),
                 "parity_ok_ops": ok_ops,
                 "implication": ("no key-set validator exists in the C leaf surface; no in-tree "
                                 "pattern for the rcN to copy")})

    recs.append({"record": "summary", "controls_ok": controls_ok,
                 "controls_total": controls_total, "cells": cells,
                 "defect_probes": n_def, "total_probes": total,
                 "ops_affected": sorted({d[0] for d in defects}),
                 "c_backed_ops": C_BACKED, "srmech": srmech.__version__,
                 "abi": ns["abi_version"]})
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("\nwrote %s (%d records)" % (OUT, len(recs)))
    return 0 if controls_ok == controls_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
