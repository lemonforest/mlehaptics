"""`#T1158` / rc449 — generating code for the "7/7 data-param residual" claim.

Per [[feedback_computational_provenance_discipline]]: the PR body states that the
IR builder stopped emitting a stage naming the op's data-carrier parameter. This
is what measured it, through the same helpers the public ``.then()`` surface uses.

Run under WSL2 (numpy-absent):
    python3 notes/_t1158_s5_residual_rc449.py
"""
from srmech.dsl._chain import _op_accepts, _then_native_desc
from srmech.dsl._catalog import lookup_cascade_op

# (op name, the op's FIRST POSITIONAL parameter = the data carrier). Resolved
# through lookup_cascade_op — the SAME resolver Chain.then() uses, so this
# measures the shipped path rather than a re-import of the same functions.
CASES = [
    ("magnitude", "x"),
    ("reorient", "value"),
    ("pin_slot_at_zero", "x"),
    ("best_rational_signed", "x"),
    ("chiral_flip", "seq"),
    ("net_chirality", "orientations"),
    ("autocorrelation", "x"),
]


def main() -> int:
    closed = 0
    print("== data-carrier param as a stage kwarg (rc448: all 7 accepted) ==")
    for name, key in CASES:
        fn = lookup_cascade_op(name)
        acc = _op_accepts(fn, key)
        ir = _then_native_desc(name, {key: 5}, fn)
        ok = (acc is False and ir is None)
        closed += ok
        print("  %-22s _op_accepts=%-5s IR=%-6s %s"
              % (name, acc, ir, "CLOSED" if ok else "OPEN"))
    print("  data-param residual closed: %d/7" % closed)

    print("\n== the control: a LEGAL kwarg must still build a stage ==")
    brs = lookup_cascade_op("best_rational_signed")
    stage = _then_native_desc("best_rational_signed", {"max_denominator": 2}, brs)
    acc = _op_accepts(brs, "max_denominator")
    print("  _op_accepts('max_denominator') =", acc)
    print("  IR stage                       =", stage)
    ctrl_ok = (acc is True and stage == {"op": "best_rational_signed",
                                         "max_denominator": 2})
    print("  control:", "OK" if ctrl_ok else "BROKEN — the check refuses "
                                            "legal keys too")
    return 0 if (closed == 7 and ctrl_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
