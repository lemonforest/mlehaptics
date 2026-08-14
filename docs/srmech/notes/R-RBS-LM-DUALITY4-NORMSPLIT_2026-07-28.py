"""LANE 4 / M6 -- does the CONSERVED norm preserve the 1+n split?

The conserved-norm rescue reads our carrier as "ONE conserved scalar over n
phases".  That is two claims glued together:
   (i)  N(x) = Re(x.x-bar) is conserved (multiplicative), and
   (ii) the carrier splits 1 (real) + n (imaginary).
This measures whether the SAME transformations do both.

  M6a  Left-multiplication by a UNIT (N(u)=1) conserves N -- but does it fix
       the real direction (i.e. preserve the 1+n split)?
  M6b  A concrete sedenion witness that N is NOT multiplicative at dim 16,
       so "conserved on the definite ladder" is false above O.
  M6c  Is N even SENSITIVE to the split?  Compare N on a pure-real and a
       pure-imaginary element of equal coordinate size.

No numpy, no stdlib fractions, no abs().
"""
import json, random
from srmech.amsc.q import Q
from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, cd_mult, cd_norm_sq, cd_conjugate)

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw))


def unit_like(dim, i, j):
    """(e_i + e_j)/1 -- N = 2; used as a NON-real norm-preserving generator
    after we work with the ratio, so exactness is kept in Q."""
    return tuple(Q(1) if k in (i, j) else Q(0) for k in range(dim))


def main():
    # ---- M6a: does a norm-conserving left-multiplication fix the real line?
    for dim in (2, 4, 8):
        moved_real, kept_norm, trials = 0, 0, 0
        e0 = tuple(Q(1) if k == 0 else Q(0) for k in range(dim))
        for i in range(1, dim):
            for j in range(i + 1, dim + 1):
                if j >= dim:
                    continue
                u = unit_like(dim, i, j)          # N(u) = 2, a scaled unit
                nu = cd_norm_sq(u)
                trials += 1
                # norm behaviour: N(u . e0) == N(u) * N(e0)
                ue0 = cd_mult(u, e0)
                if cd_norm_sq(ue0) == nu * cd_norm_sq(e0):
                    kept_norm += 1
                # split behaviour: is the image still on the real line?
                if any(c != Q(0) for c in ue0[1:]):
                    moved_real += 1
        rec(kind="M6a_unit_action", dim=dim, trials=trials,
            norm_preserved=kept_norm, real_line_MOVED=moved_real,
            note="norm conserved by every one; the 1+n split destroyed by every one")

    # ---- M6b: sedenion witness that N is not multiplicative ---------------
    random.seed(7)
    dim = 16
    witness = None
    for _ in range(400):
        x = tuple(Q(random.randint(-3, 3)) for _ in range(dim))
        y = tuple(Q(random.randint(-3, 3)) for _ in range(dim))
        lhs = cd_norm_sq(cd_mult(x, y))
        rhs = cd_norm_sq(x) * cd_norm_sq(y)
        if lhs != rhs:
            witness = (x, y, lhs, rhs)
            break
    if witness:
        x, y, lhs, rhs = witness
        rec(kind="M6b_sedenion_norm_not_multiplicative", dim=16,
            x=[str(c) for c in x], y=[str(c) for c in y],
            N_xy=str(lhs), N_x_times_N_y=str(rhs), equal=(lhs == rhs))
    else:
        rec(kind="M6b_sedenion_norm_not_multiplicative", found=False)

    # also confirm it DOES hold at dim 8 with the same generator
    ok8 = 0
    for _ in range(400):
        x = tuple(Q(random.randint(-3, 3)) for _ in range(8))
        y = tuple(Q(random.randint(-3, 3)) for _ in range(8))
        if cd_norm_sq(cd_mult(x, y)) == cd_norm_sq(x) * cd_norm_sq(y):
            ok8 += 1
    rec(kind="M6b_control_dim8", trials=400, multiplicative=ok8)

    # ---- M6c: is N sensitive to the 1+n split at all? --------------------
    for dim in (2, 4, 8, 16):
        e0 = tuple(Q(1) if k == 0 else Q(0) for k in range(dim))
        e1 = tuple(Q(1) if k == 1 else Q(0) for k in range(dim))
        rec(kind="M6c_norm_blind_to_split", dim=dim,
            N_real_unit=str(cd_norm_sq(e0)), N_imag_unit=str(cd_norm_sq(e1)),
            norm_distinguishes_them=(cd_norm_sq(e0) != cd_norm_sq(e1)),
            trace_real=str(cd_mult(e0, e0)[0]),
            trace_imag=str(cd_mult(e1, e1)[0]),
            trace_distinguishes_them=(cd_mult(e0, e0)[0] != cd_mult(e1, e1)[0]))

    with open("lane4_norm_vs_split.ndjson", "w", encoding="utf-8") as fh:
        for r in OUT:
            fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
