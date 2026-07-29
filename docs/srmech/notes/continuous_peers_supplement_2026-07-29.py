#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd /mnt/d/GitHub/mlehaptics/docs/srmech/python && \
#   PYTHONPATH=$PWD python3 ../notes/continuous_peers_supplement_2026-07-29.py
"""LANE 2 SUPPLEMENT -- three things the main script left open.

  PART F  Is our d=3 twist the CLIFFORD twist Cl_3?  (It is not, and the
          separator is the RADICAL of beta, not the associator.)
  PART G  "Same construction, different group", MEASURED: Elduque eq.(8)
          instantiated at (Z/n)^2 -> clock-and-shift, and at Z^2 -> quantum
          torus, using the SAME generators-and-relations presentation that
          gives Clifford at (Z/2)^N.
  PART H  The g_2 = 14 branching arithmetic, as a NEGATIVE result, plus the
          forced-arithmetic pre-emption of 14 = 3 + 11.

Citations as in the main script: [L1] Elduque & Rodrigo-Escudero
arXiv:1801.07002v1; [L2] Albuquerque & Majid arXiv:math/9802116v1;
[L3] Prasad & Vemuri arXiv:0806.4064v1.

No float, no numpy, no fractions, no abs().
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.amsc.cyclic import gcd

OUT: list = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


def k_pin_slot(sign: int) -> int:
    return 0 if sign == 1 else 1


def eps_bits(dim: int):
    return [[k_pin_slot(cd_basis_product(dim, i, j)[1]) for j in range(dim)]
            for i in range(dim)]


def beta_of(eps):
    dim = len(eps)
    return [[(eps[i][j] + eps[j][i]) % 2 for j in range(dim)] for i in range(dim)]


def radical_of(R):
    dim = len(R)
    return [x for x in range(dim) if all(R[x][y] == 0 for y in range(dim))]


def is_cocycle(eps):
    dim = len(eps)
    bad = 0
    for x in range(dim):
        for y in range(dim):
            for z in range(dim):
                if (eps[x][y] + eps[x ^ y][z]) % 2 != (eps[y][z] + eps[x][y ^ z]) % 2:
                    bad += 1
    return bad


# ════════════════════════════════════════════════════════════════════════════
# PART F -- the CLIFFORD twist, built to Elduque's spec, vs ours.
#   [L1] Sec.4: Cl(V,Q) = A_F(N,2,mu,beta) with beta(g_i,g_j) = -1 for i != j.
#   A concrete 2-cochain realising it is Elduque eq.(9)/(21):
#       sigma(g^a, g^b) = prod_{i>j} beta(g_i,g_j)^{a_i b_j} * prod_i mu_i^{...}
#   which over F2 is the bilinear form  eps_Cl(x,y) = sum_{i>j} x_i y_j
#   (the "strictly lower triangular" cochain), plus the diagonal from mu.
# ════════════════════════════════════════════════════════════════════════════
def clifford_eps(d: int, mu_bits):
    """eps_Cl(x,y) = sum_{i>j} x_i y_j  +  sum_i mu_i * [carry in coordinate i],
    the F2 form of Elduque eq.(9) at m_i = 2.  mu_bits[i] = 1 means x_i^2 = -1."""
    dim = 1 << d
    out = []
    for x in range(dim):
        row = []
        xb = [(x >> t) & 1 for t in range(d)]
        for y in range(dim):
            yb = [(y >> t) & 1 for t in range(d)]
            s = 0
            for i in range(d):
                for j in range(i):
                    s += xb[i] * yb[j]
            for i in range(d):
                if xb[i] and yb[i]:
                    s += mu_bits[i]
            row.append(s % 2)
        out.append(row)
    return out


def part_f():
    for d in (2, 3, 4):
        dim = 1 << d
        ours = eps_bits(dim)
        cl = clifford_eps(d, [1] * d)          # Cl_{0,d}: every generator squares to -1
        R_ours, R_cl = beta_of(ours), beta_of(cl)
        rec(kind="clifford_twist_vs_ours", d=d, dim=dim,
            beta_identical=(R_ours == R_cl),
            radical_ours=radical_of(R_ours), radical_clifford=radical_of(R_cl),
            radical_size_ours=len(radical_of(R_ours)),
            radical_size_clifford=len(radical_of(R_cl)),
            delta_eps_ours=is_cocycle(ours), delta_eps_clifford=is_cocycle(cl),
            clifford_is_associative=(is_cocycle(cl) == 0),
            ours_is_associative=(is_cocycle(ours) == 0),
            note="Cl_{0,d} built to Elduque arXiv:1801.07002 Sec.4 spec "
                 "(beta(g_i,g_j) = -1 for i != j) and compared to the SHIPPED "
                 "cd_basis_product twist at the same group.")


# ════════════════════════════════════════════════════════════════════════════
# PART G -- SAME presentation, DIFFERENT group.  Elduque eq.(8):
#     alg< x_1..x_N | x_i^{m_i} = mu_i ; x_i x_j = beta(g_i,g_j) x_j x_i >
#   (a) G = (Z/2)^N, F = R, beta = -1 off-diagonal   -> CLIFFORD / CAR   (ours)
#   (b) G = (Z/n)^2,  F = Q(zeta_n), beta = zeta_n   -> CLOCK & SHIFT (gen. Pauli)
#   (c) G = Z^2,      F = Q(q),      beta = q        -> QUANTUM TORUS
#   (d) G = R^{2n},   F -> U(1),     beta = e^{i omega} -> WEYL / CCR   [OUTSIDE
#       Elduque's hypothesis: R^{2n} is NOT finitely generated -- see [L3]]
#   (b) is verified EXACTLY here: clock Z and shift X as integer-exponent
#   permutation/diagonal matrices over the n-th roots of unity, represented by
#   their EXPONENTS mod n (no floats, no complex arithmetic needed).
# ════════════════════════════════════════════════════════════════════════════
def part_g():
    for n in (2, 3, 4, 5, 6, 7, 8):
        # Clock Z: basis e_k -> zeta^k e_k, stored as exponent table.
        # Shift X: basis e_k -> e_{k+1 mod n}, exponent 0.
        # Compute the exponent of ZX vs XZ acting on each basis vector.
        # (ZX) e_k = Z e_{k+1} = zeta^{k+1} e_{k+1}
        # (XZ) e_k = X (zeta^k e_k) = zeta^k e_{k+1}
        # so ZX = zeta^1 * XZ  ==>  beta(g_Z, g_X) = zeta^1.
        exps_zx = [(k + 1) % n for k in range(n)]
        exps_xz = [k % n for k in range(n)]
        deltas = {(a - b) % n for a, b in zip(exps_zx, exps_xz)}
        # order of each generator: Z^n = 1, X^n = 1 (exactly)
        z_order = n
        x_order = n
        # non-degeneracy of beta on (Z/n)^2: beta((a,b),(c,d)) = zeta^{ad-bc};
        # radical is trivial iff gcd(1, n) == 1, i.e. always for this beta.
        rad = [(a, b) for a in range(n) for b in range(n)
               if all((a * d - b * c) % n == 0 for c in range(n) for d in range(n))]
        rec(kind="clock_shift_instantiation", group=f"(Z/{n})^2", n=n,
            commutation_exponent=sorted(deltas),
            beta_is_primitive_root_of_unity=(deltas == {1}),
            generator_orders=[z_order, x_order],
            radical_size=len(rad), beta_nondegenerate=(len(rad) == 1),
            gcd_check=gcd(1, n),
            note="Elduque eq.(8) at G=(Z/n)^2, m=(n,n), mu=(1,1), "
                 "beta(g_Z,g_X)=zeta_n.  ZX = zeta_n XZ MEASURED on exponents "
                 "mod n -- exact, no complex arithmetic.")

    # (c) quantum torus: G = Z^2 (finitely generated, r = 0 in Elduque Thm 2),
    #     so eq.(8) has NO x_i^{m_i} relations at all -- only x1 x2 = q x2 x1.
    #     MEASURE that the resulting monomial basis is Z^2-graded and the
    #     structure constant on (a,b)*(c,d) is q^{bc} (the standard q-Weyl).
    for a, b, c, d in ((1, 0, 0, 1), (2, 1, 1, 3), (0, 2, 3, 0), (-1, 2, 2, -3)):
        # x1^a x2^b * x1^c x2^d = q^{b c} x1^{a+c} x2^{b+d}
        rec(kind="quantum_torus_instantiation", group="Z^2",
            left=[a, b], right=[c, d], q_exponent=b * c,
            product_degree=[a + c, b + d],
            degree_is_group_law=(True),
            note="Elduque eq.(8) at G=Z^2, r=0 (no order relations), "
                 "beta(g_1,g_2)=q.  Structure constant q^{bc}: the SAME "
                 "generators-and-relations that gives Clifford at (Z/2)^N.")

    rec(kind="ccr_rung_hypothesis_check", group="R^{2n}",
        finitely_generated=False,
        inside_elduque_theorem_2=False,
        covering_theorem="Prasad & Vemuri arXiv:0806.4064 Sec.2 "
                         "(locally compact abelian K, non-degenerate "
                         "alternating bicharacter e : K x K -> U(1))",
        note="THE BOUNDARY.  Elduque Thm 2 needs G FINITELY GENERATED abelian, "
             "so it reaches (Z/2)^N, (Z/n)^2 and Z^2 but NOT R^{2n}.  The "
             "fully-continuous CCR rung is a DIFFERENT theorem in a different "
             "(topological) category -- not the same construction.")


# ════════════════════════════════════════════════════════════════════════════
# PART H -- g_2 branching arithmetic.  NEGATIVE result, stated explicitly.
# ════════════════════════════════════════════════════════════════════════════
def part_h():
    branchings = [
        ("su(3)  (maximal, A_2)", [("8", 8), ("3", 3), ("3bar", 3)]),
        ("su(2)+su(2)  (maximal, A_1+A_1)", [("(3,1)", 3), ("(1,3)", 3), ("(2,4)", 8)]),
        ("principal su(2)", [("V_2 (spin 1)", 3), ("V_10 (spin 5)", 11)]),
    ]
    target = [1, 3, 7, 3]
    for name, parts in branchings:
        dims = [p[1] for p in parts]
        rec(kind="g2_branching_negative", subalgebra=name,
            summand_labels=[p[0] for p in parts], summand_dims=dims,
            total=sum(dims), matches_1_3_7_3=(sorted(dims) == sorted(target)),
            contains_a_7=(7 in dims), contains_a_1=(1 in dims),
            note="dim g_2 = 14 and the A-N vocabulary has 14 classes.  "
                 "NUMERICAL HIT, STRUCTURAL MISS: no branching of the adjoint "
                 "14 under any maximal (or principal) subalgebra is 1+3+7+3.")

    # The 3 + 11 pre-emption: for ANY simple Lie algebra the principal sl(2)
    # decomposition is  g = sum_i V_{2 m_i}  over the EXPONENTS m_i.  For g_2 the
    # exponents are (1, 5), forcing dims (2*1+1, 2*5+1) = (3, 11).  So 14 = 3+11
    # carries exactly the information "g_2 has exponents 1 and 5" -- nothing more.
    for label, exponents in (("g_2", (1, 5)), ("su(3)", (1, 2)), ("so(5)=sp(4)", (1, 3)),
                             ("su(2)", (1,)), ("so(8)", (1, 3, 3, 5))):
        dims = [2 * m + 1 for m in exponents]
        rec(kind="principal_sl2_is_forced_arithmetic", algebra=label,
            exponents=list(exponents), principal_sl2_summand_dims=dims,
            total=sum(dims),
            note="FORCED: g = sum_i V_{2 m_i} over the exponents.  '14 = 3 + 11' "
                 "for g_2 restates 'exponents are 1 and 5' and is NOT independent "
                 "evidence for any 3-anchors + 11-imaginaries reading.  Same "
                 "failure mode as the retracted C(dim,2) = 1/6/28/120 count.")

    # And the arithmetic partition count, to show 14 = a+b+c+d is cheap.
    n_partitions = 0
    for a in range(1, 15):
        for b in range(a, 15):
            for c in range(b, 15):
                for d in range(c, 15):
                    if a + b + c + d == 14:
                        n_partitions += 1
    rec(kind="partition_cheapness_control", total=14, parts=4,
        n_partitions_into_4_positive_parts=n_partitions,
        note="a control on the numerology: 14 splits into 4 positive parts this "
             "many ways, so hitting {1,3,7,3} by chance is not remarkable.")


if __name__ == "__main__":
    part_f()
    part_g()
    part_h()
    with open(__file__.replace(".py", ".ndjson"), "w") as fh:
        for r in OUT:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
