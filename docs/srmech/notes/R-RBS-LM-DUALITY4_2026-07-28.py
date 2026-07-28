"""LANE 4 — does a duality counter any part of F1333?

Measures, on the SHIPPED srmech carrier (no numpy, no stdlib fractions, no abs()):

  M1  Which quadratic form carries the "1+n" census: the TRACE form q(x)=Re(x.x)
      or the NORM form N(x)=Re(x.x-bar)?  These are the amplitude-axis and
      frequency-axis candidates respectively.
  M2  Which of the two is MULTIPLICATIVE (= the conserved one)?
  M3  (b) label<->character self-duality of (Z/2)^d: transform the trace Gram by
      the Walsh/character matrix W (congruence G -> W G W^T) and re-read the
      signature through the SHIPPED inertia_signature op.
  M4  The frequency-axis census: multiplicative period of each basis direction,
      definite ladder vs split twists.
  M5  (c) base<->fiber: sizes of the two rc347 lanes (index quotient vs sign
      centre) -- can they be exchanged at all?

Class discipline: sign handling in M4 is a Class-K pin-slot read of the
structure constant (the table entry IS the +-1), never Python abs().
"""
import sys, json, random

from srmech.amsc.q import Q
from srmech.amsc.cascade.cayley_dickson import (
    algebra_table, inertia_signature, cd_mult, cd_norm_sq, cd_conjugate,
    cd_basis_product, table_product,
)
import srmech

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw))


def gram_from_table(table, form):
    """Rebuild the Gram the shipped op reads, so M3 can transform it."""
    dim = len(table)
    if form == "trace":
        return [[table[i][j][0] + table[j][i][0] for j in range(dim)]
                for i in range(dim)]
    # norm form: Re(x . x-bar); conjugation negates every i>0 slot
    def cj(j):
        return -1 if j > 0 else 1
    return [[cj(j) * table[i][j][0] + cj(i) * table[j][i][0]
             for j in range(dim)] for i in range(dim)]


def sig_of_symmetric(G):
    """Signature of the integer symmetric G, via the SHIPPED inertia op.

    inertia_signature reads gram[i][j] = t[i][j][0] + t[j][i][0]; planting
    t[i][j][0] = G[i][j] gives it 2G, and sig(2G) == sig(G).
    """
    dim = len(G)
    t = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            t[i][j][0] = G[i][j]
    r = inertia_signature(t)
    return (r["n_plus"], r["n_minus"], r["n_zero"])


def walsh(dim):
    """The (Z/2)^d character matrix: W[a][i] = (-1)^popcount(a & i)."""
    W = []
    for a in range(dim):
        row = []
        for i in range(dim):
            v = a & i
            p = 0
            while v:
                p ^= (v & 1)
                v >>= 1
            row.append(1 if p == 0 else -1)
        W.append(row)
    return W


def mat_congruence(W, G):
    dim = len(G)
    WG = [[sum(W[a][i] * G[i][j] for i in range(dim)) for j in range(dim)]
          for a in range(dim)]
    return [[sum(WG[a][j] * W[b][j] for j in range(dim)) for b in range(dim)]
            for a in range(dim)]


def basis_vec(dim, i):
    return tuple(Q(1) if k == i else Q(0) for k in range(dim))


def trace_form(x):
    """q(x) = Re(x.x) -- the 0-slot of the UNCONJUGATED square."""
    return cd_mult(x, x)[0]


def main():
    rec(kind="env", srmech_version=srmech.__version__)

    # ---- M1: which form carries 1+n ---------------------------------------
    for dim in (1, 2, 4, 8, 16):
        t = algebra_table(dim)
        rec(kind="M1_form_signature", dim=dim,
            trace=list(sig_of_symmetric(gram_from_table(t, "trace"))),
            norm=list(sig_of_symmetric(gram_from_table(t, "norm"))),
            shipped_trace=list(inertia_signature(t)["signature"])
            if "signature" in inertia_signature(t) else None)

    # ---- M2: multiplicativity ---------------------------------------------
    random.seed(20260728)
    for dim in (2, 4, 8, 16):
        n_ok, q_ok, trials = 0, 0, 200
        for _ in range(trials):
            x = tuple(Q(random.randint(-6, 6), random.randint(1, 4))
                      for _ in range(dim))
            y = tuple(Q(random.randint(-6, 6), random.randint(1, 4))
                      for _ in range(dim))
            xy = cd_mult(x, y)
            if cd_norm_sq(xy) == cd_norm_sq(x) * cd_norm_sq(y):
                n_ok += 1
            if trace_form(xy) == trace_form(x) * trace_form(y):
                q_ok += 1
        rec(kind="M2_multiplicativity", dim=dim, trials=trials,
            norm_multiplicative=n_ok, trace_multiplicative=q_ok)

    # ---- M3: (b) the (Z/2)^d label<->character self-duality ---------------
    for dim in (2, 4, 8, 16):
        t = algebra_table(dim)
        W = walsh(dim)
        for form in ("trace", "norm"):
            G = gram_from_table(t, form)
            Gp = mat_congruence(W, G)
            rec(kind="M3_walsh_congruence", dim=dim, form=form,
                label_basis=list(sig_of_symmetric(G)),
                character_basis=list(sig_of_symmetric(Gp)),
                unchanged=(sig_of_symmetric(G) == sig_of_symmetric(Gp)))

    # ---- M4: the frequency axis -- multiplicative period per direction ----
    # Class K pin-slot: the returning step is read off the structure constant.
    def period_of(dim, i, gammas):
        """Smallest k>=1 with e_i^k == +e_0, walking the basis product."""
        idx, sign = i, 1
        for k in range(1, 9):
            idx2, s2 = cd_basis_product(idx, i, dim) if gammas is None \
                else _gamma_bp(idx, i, dim, gammas)
            idx, sign = idx2, sign * s2
            if idx == 0 and sign == 1:
                return k + 1
        return None

    def _gamma_bp(a, b, dim, gammas):
        t = algebra_table(dim, gammas)
        row = t[a][b]
        for k in range(dim):
            if row[k] != 0:
                return k, row[k]
        return 0, 0

    for dim, gammas, name in ((2, None, "C"), (4, None, "H"), (8, None, "O"),
                              (16, None, "S"),
                              (2, (1,), "split-C"),
                              (4, (1, 1), "split-H"),
                              (8, (1, 1, 1), "split-O")):
        t = algebra_table(dim, gammas)
        periods = {}
        for i in range(dim):
            # e_i . e_i read straight off the table = the Class-K pin slot
            sq = t[i][i]
            k0 = next(k for k in range(dim) if sq[k] != 0)
            periods[i] = ("+1" if (k0 == 0 and sq[k0] > 0) else
                          "-1" if (k0 == 0 and sq[k0] < 0) else "other")
        n_plus = sum(1 for v in periods.values() if v == "+1")
        n_minus = sum(1 for v in periods.values() if v == "-1")
        rec(kind="M4_period_census", algebra=name, dim=dim,
            gammas=list(gammas) if gammas else None,
            squares_to_plus1=n_plus, squares_to_minus1=n_minus,
            census=f"{n_plus}+{n_minus}",
            is_one_plus_n=(n_plus == 1 and n_minus == dim - 1))

    # ---- M5: (c) lane sizes ------------------------------------------------
    for dim in (2, 4, 8, 16):
        rec(kind="M5_lane_sizes", dim=dim,
            index_lane_group_order=dim,        # (Z/2)^d quotient
            sign_lane_group_order=2,           # the {+-1} centre
            exchangeable=(dim == 2))

    with open("lane4_duality_probe.ndjson", "w", encoding="utf-8") as fh:
        for r in OUT:
            fh.write(json.dumps(r) + "\n")
    print("wrote lane4_duality_probe.ndjson", file=sys.stderr)


if __name__ == "__main__":
    main()
