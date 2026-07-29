"""LANE 1 stage 5 — the CIRCULARITY test for every survivor.

Question: modulo the gauge group (and modulo GL(d,F2)), is the ONLY thing that
differs between the definite and the split algebra of the SAME dim the DIAGONAL
eps(i,i) — i.e. the quadratic form / metric signature that DEFINES the split?

If yes, then every quantity that separates them must read the diagonal, so no
separator can be a fossil of cascade ORDER: it IS the signature.

Method (exact F2, no float, no abs()):
  D    = eps_definite XOR eps_split        (packed dim^2-bit int)
  B    = the coboundary subspace           (dim-1 generators) -- the GAUGE group
  Diag = span of the dim-1 diagonal indicators e_{(i,i)} -- the SIGNATURE
  Test "D in B" and "D in B + Diag" by GF(2) rank.

The rank is computed BOTH ways and the two are required to agree:
  * the SHIPPED srmech.amsc.modular_linalg.gf_rref over GF(2) (the subject), and
  * a packed-int echelon reduction (the LABELLED ORACLE, used for the 20160-fold
    GL sweep where re-running gf_rref on a 271 x 256 matrix each time is the only
    thing that is slow).

Also reports the zero-divisor count -- FLAGGED CIRCULAR BY DEFINITION -- via the
SHIPPED left_mult_kernel.
"""

import json
import sys

sys.path.append("../notes")
from fossil_sweep_lane1_gauge_gl_dim import (   # noqa: E402
    all_coboundaries, coboundary_gens, delta_columns, delta_of, eps_from_table,
    gl_perms, pack, relabel,
)
from srmech.amsc.cascade import (               # noqa: E402
    algebra_table, left_mult_kernel,
)
from srmech.amsc.modular_linalg import gf_rref  # noqa: E402
from srmech.amsc.q import Q                     # noqa: E402


def bits_to_rows(vecs, n):
    return [[(v >> k) & 1 for k in range(n)] for v in vecs]


def shipped_rank(vecs, n):
    """GF(2) rank via the SHIPPED gf_rref (Class-L/I)."""
    if not vecs:
        return 0
    return gf_rref(bits_to_rows(vecs, n), 2)["rank"]


def echelon(vecs):
    """LABELLED ORACLE — packed-int GF(2) echelon basis (exact, no float)."""
    ech = []
    for v in vecs:
        for e in ech:
            hi = e.bit_length() - 1
            if (v >> hi) & 1:
                v ^= e
        if v:
            ech.append(v)
            ech.sort(key=lambda z: -z.bit_length())
    return ech


def reduce_by(ech, v):
    for e in ech:
        hi = e.bit_length() - 1
        if (v >> hi) & 1:
            v ^= e
    return v


def emit(**r):
    sys.stdout.write(json.dumps(r, sort_keys=True) + "\n")
    sys.stdout.flush()


def diag_vecs(dim):
    return [1 << (i * dim + i) for i in range(1, dim)]


def offdiag_mask(dim):
    m = 0
    for i in range(dim):
        for j in range(dim):
            if i != j:
                m |= 1 << (i * dim + j)
    return m


def main():
    for dim in (4, 8, 16):
        n = dim * dim
        d = dim.bit_length() - 1
        T_def = algebra_table(dim)
        T_spl = algebra_table(dim, [-1] * (d - 1) + [1])
        E_def, E_spl = eps_from_table(T_def), eps_from_table(T_spl)
        P_def, P_spl = pack(E_def), pack(E_spl)
        D = P_def ^ P_spl
        B = coboundary_gens(dim)
        Dg = diag_vecs(dim)
        od = offdiag_mask(dim)

        # --- membership, computed by the SHIPPED gf_rref -------------------
        rB, rBD = shipped_rank(B, n), shipped_rank(B + Dg, n)
        in_B = shipped_rank(B + [D], n) == rB
        in_BD = shipped_rank(B + Dg + [D], n) == rBD
        # --- and by the packed oracle; the two MUST agree -----------------
        eB, eBD = echelon(B), echelon(B + Dg)
        assert (reduce_by(eB, D) == 0) == in_B
        assert (reduce_by(eBD, D) == 0) == in_BD
        assert len(eB) == rB and len(eBD) == rBD

        # minimal off-diagonal Hamming distance over the FULL explicit gauge
        # sweep (all 2^(dim-1) rescalings)
        best = None
        for cb in all_coboundaries(dim):
            h = bin((D ^ cb) & od).count("1")
            if best is None or h < best:
                best = h
                if best == 0:
                    break

        # over gauge x GL: how many of the |GL(d,F2)| relabellings of the
        # DEFINITE table land in (split-table + gauge + diagonal)?
        perms = gl_perms(d)
        hits_gauge = 0
        hits_gauge_diag = 0
        for perm in perms:
            Dg2 = pack(relabel(E_def, perm)) ^ P_spl
            if reduce_by(eB, Dg2) == 0:
                hits_gauge += 1
            if reduce_by(eBD, Dg2) == 0:
                hits_gauge_diag += 1

        emit(kind="circularity", dim=dim,
             raw_table_entries_differing=bin(D).count("1"),
             raw_offdiagonal_entries_differing=bin(D & od).count("1"),
             difference_is_pure_gauge=in_B,
             difference_is_gauge_plus_diagonal=in_BD,
             min_offdiag_hamming_over_gauge=best,
             gl_relabellings_definite_to_split_pure_gauge=hits_gauge,
             gl_relabellings_definite_to_split_gauge_plus_diagonal=hits_gauge_diag,
             gl_order=len(perms),
             rank_B=rB, rank_B_plus_diag=rBD, dim_C2=n)

        # delta(eps) and the commutator cochain, POINTWISE
        col = delta_columns(dim)
        dd_def = delta_of(P_def, col, dim)
        dd_spl = delta_of(P_spl, col, dim)
        b_def = pack([[E_def[i][j] ^ E_def[j][i] for j in range(dim)]
                      for i in range(dim)])
        b_spl = pack([[E_spl[i][j] ^ E_spl[j][i] for j in range(dim)]
                      for i in range(dim)])
        emit(kind="pointwise", dim=dim,
             delta_eps_identical=(dd_def == dd_spl),
             delta_eps_hamming=bin(dd_def ^ dd_spl).count("1"),
             commutator_cochain_identical=(b_def == b_spl),
             commutator_hamming=bin(b_def ^ b_spl).count("1"),
             diagonal_identical=(bin(D & ~od).count("1") == 0),
             diagonal_hamming=bin(D & ~od).count("1"))

    # ---- zero divisors: FLAGGED CIRCULAR BY DEFINITION -------------------
    for dim in (4, 8, 16):
        d = dim.bit_length() - 1
        for gam, lbl in ((None, "definite"), ([-1] * (d - 1) + [1], "split")):
            T = algebra_table(dim, gam)
            zd = 0
            probes = 0
            for i in range(dim):
                for j in range(i + 1, dim):
                    for s in (1, -1):
                        x = tuple(Q(1) if k == i else (Q(s) if k == j else Q(0))
                                  for k in range(dim))
                        probes += 1
                        if left_mult_kernel(x, table=T):
                            zd += 1
            emit(kind="zero_divisor", dim=dim, label=lbl,
                 two_term_left_zero_divisors=zd, probes=probes,
                 CIRCULAR="split-O HAS zero divisors and O does not BY "
                          "DEFINITION (Hurwitz composition); a zero-divisor "
                          "count separating them is TAUTOLOGICAL, not a fossil")


if __name__ == "__main__":
    main()
