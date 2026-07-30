#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd /mnt/d/GitHub/mlehaptics/docs/srmech/python && \
#   PYTHONPATH=$PWD python3 ../notes/continuous_peers_bicharacter_bridge_2026-07-29.py
"""LANE 2 — the CONTINUOUS PEERS, named and bounded.

What is being decided, and against which literature:

  [L1] Elduque & Rodrigo-Escudero, "Clifford algebras as twisted group algebras
       and the Arf invariant", arXiv:1801.07002v1 [math.RA], 22 Jan 2018.
       Local hoodoo: docs/srmech/hoodoos/1801.07002_elduque_clifford_twisted_group_algebras.pdf
       * Theorem 2 (p.4): G a FINITELY GENERATED ABELIAN group, F a FIELD,
         beta : G x G -> F^x an ALTERNATING BICHARACTER  ==>  there EXISTS
         sigma in Z^2(G, F^x) with beta(g,h) = sigma(g,h) sigma(h,g)^{-1};
         and F^sigma G is graded-isomorphic to
             alg< x_1..x_N | x_i^{m_i} = mu_i ;  x_i x_j = beta(g_i,g_j) x_j x_i >
         =: A_F(N, m, mu, beta)   (their eq. 8).
       * Section 4 (p.5): Cl(V,Q) = A_F(N, 2, mu, beta) with mu = (Q(v_1)..Q(v_N))
         and beta(g_i,g_j) = -1 for i != j.  (their eq. 12 and the bullet list)
       * Corollary 11 (p.8): at F = R the isomorphism class of A_R(mu) is
         determined by N AND the ARF INVARIANT of mu -- NOT by beta, which is
         the same for every Cl_{p,q}(R) with p+q = N.

  [L2] Albuquerque & Majid, "Quasialgebra structure of the octonions",
       arXiv:math/9802116v1 [math.QA], 25 Feb 1998, DAMTP/97-138.
       Local hoodoo: docs/srmech/hoodoos/math9802116_albuquerque_majid_quasialgebra_octonions.pdf
       * p.1: "for the octonions, the cocycle is a coboundary and can be
         identified as the result of twisting k(G) by a 2-cochain F".
       * Example 1 of [L1] quotes AM's cochains verbatim:
             C : T = Z_2,    F(x,y)   = (-1)^{xy}
             H : T = Z_2^2,  F(x,y)   = (-1)^{x1 y1 + (x1+x2) y2}
             O : T = Z_2^3,  F(x,y)   = (-1)^{y1 x2 x3 + x1 y2 x3 + x1 x2 y3 + sum_{1<=i<=j<=3} x_i y_j}
         PART D below MEASURES our shipped cocycle against these THREE.

  [L3] Prasad & Vemuri, "Decomposition of phase space and classification of
       Heisenberg groups", arXiv:0806.4064v1 [math.GR], 25 Jun 2008.
       Sec. 2: for 1 -> U(1) -> G -> K -> 0 with K locally compact abelian, the
       commutator descends to an ALTERNATING BICHARACTER e : K x K -> U(1), and
       the data (K, e) with e NON-DEGENERATE determine G up to isomorphism of
       central extensions.  ==> the continuous peer's classification carries a
       NON-DEGENERACY hypothesis.  PART C measures whether ours has it.

SUBJECTS (shipped srmech ops -- the things actually measured):
  * cayley_dickson.cd_basis_product(dim, i, j) -> (index, sign)   [the cocycle]
  * cayley_dickson.algebra_table(dim, gammas)                     [gamma family]
  * modular_linalg.gf_rref(rows, 2)                               [every F2 rank]

LABELLED ORACLES (hand-rolled; srmech ships no peer -- each is a FINDING):
  * _oracle_bar_delta   : bar-complex coboundary over F2 (Lane 1 used the same).
  * _oracle_q_majority_class : majority class of an F2 quadratic form (the Arf
                        invariant ONLY at even d -- see its docstring).
  * _oracle_monomial_aut: enumeration of signed-permutation automorphisms.

No float, no numpy, no fractions, no abs().  Class-K sign handling only.
"""
from __future__ import annotations

import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import algebra_table, cd_basis_product
from srmech.amsc.modular_linalg import gf_rref

OUT: list = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


# ── Class K / Class C sign handling (never abs()) ────────────────────────────
def k_pin_slot(sign: int) -> int:
    """Class K pin-slot: the +1/-1 phase boundary -> the F2 bit."""
    return 0 if sign == 1 else 1


def c_reorient(bit: int) -> int:
    """Class C: re-apply orientation, F2 bit -> multiplicative sign."""
    return 1 if bit == 0 else -1


# ── ORACLES ─────────────────────────────────────────────────────────────────
def _oracle_bar_delta(n: int, order: int):
    """Rows of the F2 bar coboundary delta^n : C^n -> C^{n+1}, trivial action,
    group = (Z/2)^d with order = 2^d and group law XOR.  One row per element of
    G^{n+1}; columns indexed by G^n in lexicographic order."""
    cols = order ** n
    rows = []
    for tup in itertools.product(range(order), repeat=n + 1):
        row = [0] * cols
        # (delta f)(g_1..g_{n+1}) = f(g_2..g_{n+1})
        #   + sum_i f(.., g_i XOR g_{i+1}, ..) + f(g_1..g_n)
        def bump(idx_tuple):
            idx = 0
            for t in idx_tuple:
                idx = idx * order + t
            row[idx] ^= 1

        bump(tup[1:])
        for i in range(n):
            bump(tup[:i] + (tup[i] ^ tup[i + 1],) + tup[i + 2:])
        bump(tup[:n])
        rows.append(row)
    return rows


def _oracle_q_majority_class(q_vals, d: int) -> int:
    """The MAJORITY CLASS of the F2 quadratic form q on (Z/2)^d: 0 if q takes
    the value 0 more often than 1, else 1 (and -1 on a tie).

    ⚠ This is the Arf invariant ONLY when d is EVEN and q is non-degenerate.
    For ODD d the space is odd-dimensional, Arf is not defined by the majority
    route, and Elduque Cor.11 carries a THIRD value there.  Reported under a
    neutral name so no odd-d row reads as a verified Arf computation.  The
    load-bearing numbers in this part are n_distinct_q and beta_is_constant,
    neither of which depends on this field."""
    zeros = sum(1 for v in q_vals if v == 0)
    ones = len(q_vals) - zeros
    if zeros == ones:
        return -1
    return 0 if zeros > ones else 1


def _oracle_monomial_aut(dim: int):
    """Every map phi(e_i) = eps_i * e_{pi(i)} on the basis of the shipped CD
    algebra of dimension `dim` that is an ALGEBRA AUTOMORPHISM.  pi must fix 0
    (the unit) and eps_0 = +1.  Enumerated as: for each permutation pi of the
    imaginary indices, solve for the sign vector by propagation, then verify.
    Returns (n_automorphisms, n_permutations_that_lift, n_sign_only)."""
    n_im = dim - 1
    # multiplication as (index, sign)
    prod = [[cd_basis_product(dim, i, j) for j in range(dim)] for i in range(dim)]
    total = 0
    lifting_perms = 0
    sign_only = 0
    for perm in itertools.permutations(range(1, dim)):
        pi = [0] + list(perm)
        lifts = 0
        for mask in range(1 << n_im):
            eps = [1] + [c_reorient((mask >> t) & 1) for t in range(n_im)]
            ok = True
            for i in range(dim):
                if not ok:
                    break
                for j in range(dim):
                    k, s = prod[i][j]
                    # phi(e_i)phi(e_j) = eps_i eps_j * (e_pi(i) e_pi(j))
                    k2, s2 = prod[pi[i]][pi[j]]
                    lhs_idx, lhs_sign = k2, eps[i] * eps[j] * s2
                    # phi(e_i e_j) = s * eps_k * e_pi(k)
                    rhs_idx, rhs_sign = pi[k], s * eps[k]
                    if lhs_idx != rhs_idx or lhs_sign != rhs_sign:
                        ok = False
                        break
            if ok:
                lifts += 1
                total += 1
                if pi == list(range(dim)):
                    sign_only += 1
        if lifts:
            lifting_perms += 1
    return total, lifting_perms, sign_only


# ── shipped-op readers ──────────────────────────────────────────────────────
def eps_bits(dim: int):
    """epsilon(i,j) in F2 from the SHIPPED cocycle cd_basis_product."""
    return [[k_pin_slot(cd_basis_product(dim, i, j)[1]) for j in range(dim)]
            for i in range(dim)]


def eps_bits_from_table(dim: int, gammas):
    """Same, but through the SHIPPED gamma-parameterised algebra_table."""
    tab = algebra_table(dim, gammas)
    out = []
    for i in range(dim):
        row = []
        for j in range(dim):
            col = tab[i][j]
            idx = [k for k in range(dim) if col[k] != 0]
            assert len(idx) == 1, (i, j, col)
            row.append(k_pin_slot(col[idx[0]]))
        out.append(row)
    return out


def beta_of(eps):
    """The ALTERNATING BICHARACTER as an F2 additive form:
    R(x,y) = eps(x,y) + eps(y,x).  (Multiplicatively beta = (-1)^R.)"""
    dim = len(eps)
    return [[(eps[i][j] + eps[j][i]) % 2 for j in range(dim)] for i in range(dim)]


def q_of(eps):
    """The QUADRATIC form q(x) = eps(x,x) -- the diagonal that beta forgets."""
    return [eps[i][i] for i in range(len(eps))]


# ════════════════════════════════════════════════════════════════════════════
# PART A -- the classifying-space oracle, MEASURED, not assumed.
#   H^*(G; F2) = H^*(BG; F2) with BG = (RP^inf)^d, so dim H^n = C(n+d-1, d-1).
#   We measure H^n(G;F2) directly from the bar complex and compare.
# ════════════════════════════════════════════════════════════════════════════
def binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    num, den = 1, 1
    for t in range(k):
        num *= n - t
        den *= t + 1
    return num // den


def part_a():
    for d, nmax in ((1, 6), (2, 3), (3, 2)):
        order = 1 << d
        ranks = {}
        for n in range(0, nmax + 1):
            rows = _oracle_bar_delta(n, order)
            ranks[n] = gf_rref(rows, 2)["rank"]
        for n in range(1, nmax + 1):
            dim_Cn = order ** n
            dim_Zn = dim_Cn - ranks[n]
            dim_Bn = ranks[n - 1]
            dim_Hn = dim_Zn - dim_Bn
            pred = binom(n + d - 1, d - 1)
            rec(kind="BG_oracle_measured", d=d, n=n, dim_C=dim_Cn,
                rank_delta_n=ranks[n], dim_Z=dim_Zn, dim_B=dim_Bn,
                dim_H=dim_Hn, poincare_prediction=pred, agrees=(dim_Hn == pred),
                note="dim H^n(G;F2) vs the coefficient of t^n in 1/(1-t)^d "
                     "= dim of the degree-n part of F2[x_1..x_d] = H^n(BG;F2)")


# ════════════════════════════════════════════════════════════════════════════
# PART B -- the DIVISIBILITY GAP.  beta is NOT a complete invariant at +/-1.
# ════════════════════════════════════════════════════════════════════════════
def part_b():
    # B1: the symmetriser's kernel has dimension exactly d, at every d.
    for d in range(1, 6):
        dim = 1 << d
        # H^2(G;F2) has a basis {x_i x_j : i <= j}; the symmetriser kills
        # exactly the SQUARES x_i^2.  Measure the two dimensions.
        h2 = binom(d + 1, 2)
        alt = binom(d, 2)
        rec(kind="symmetriser_kernel", d=d, dim=dim,
            dim_H2_F2=h2, dim_alternating_bicharacters=alt,
            dim_kernel=h2 - alt, kernel_equals_d=(h2 - alt == d),
            gap_order=1 << d,
            note="ker(symmetriser) = Hom(G, F^x/(F^x)^2); at F^x = {+/-1} that "
                 "is (Z/2)^d, so 2^d twists share one bicharacter")

    # B2: MEASURE it on the shipped gamma family -- same beta, different q.
    for d in range(1, 5):
        dim = 1 << d
        betas, qs, arfs = set(), set(), set()
        rows = []
        for gam in itertools.product((-1, 1), repeat=d):
            eps = eps_bits_from_table(dim, list(gam))
            b = tuple(tuple(r) for r in beta_of(eps))
            # q as a FUNCTION on all of G, not just the basis: q(x)=eps(x,x)
            qf = tuple(q_of(eps))
            betas.add(b)
            qs.add(qf)
            arfs.add(_oracle_q_majority_class(list(qf), d))
            rows.append({"gammas": list(gam), "q": list(qf),
                         "n_q_ones": sum(qf), "q_majority_class": _oracle_q_majority_class(list(qf), d)})
        rec(kind="gamma_family_beta_vs_q", d=d, dim=dim,
            n_gamma_tables=1 << d, n_distinct_beta=len(betas),
            n_distinct_q=len(qs), beta_is_constant=(len(betas) == 1),
            q_separates_all=(len(qs) == (1 << d)),
            n_distinct_q_majority_class=len(arfs), rows=rows,
            note="Elduque Cor.11: at F=R the iso class needs N AND Arf; beta is "
                 "the SAME for every Cl_{p,q} with p+q=N.  MEASURED here on the "
                 "shipped algebra_table gamma family.")

    # B3: the gauge argument, exact.  u_g -> mu(g) u_g sends q(g) -> mu(g)^2 q(g),
    # so the diagonal is well defined ONLY modulo squares of the coefficient
    # group.  DERIVED demonstration at the smallest rung, in exact Z[i].
    #   over {+/-1} : squares = {1}       -> -1 survives  (C is not R)
    #   over R^x    : squares = R_{>0}    -> -1 survives  (Elduque Cor.11 needs Arf)
    #   over Q(i)^x : i^2 = -1            -> -1 dies
    for label, mu in (("mu=1 (identity gauge)", (1, 0)),
                      ("mu=i in Z[i]", (0, 1))):
        a, b = mu                      # mu = a + b i, exact integers
        mu_sq = (a * a - b * b, 2 * a * b)
        killed = (mu_sq[0] * -1, mu_sq[1] * -1)   # mu^2 * q with q = -1
        rec(kind="gauge_kills_diagonal_iff_square_root_exists",
            gauge=label, mu=[a, b], mu_squared=[mu_sq[0], mu_sq[1]],
            mu_squared_times_q_minus_1=[killed[0], killed[1]],
            twist_trivialised=(killed == (1, 0)),
            note="DERIVED (open premises, exact Z[i]): q(g)=eps(g,g) is well "
                 "defined only mod (F^x)^2.  A square root of -1 trivialises it; "
                 "at coefficients {+/-1} (and at R^x) none exists, so the "
                 "quadratic refinement is REAL DATA that beta does not see.")

    # B4: how many distinct 2-cochain gauge classes share one beta -- exhaustive
    # at d = 1,2,3 over the UNITAL diagonal-only family (the 2^d gamma tables
    # are one orbit representative each; Lane 1 measured orbit size 2^{d+?}).
    for d in (1, 2, 3):
        dim = 1 << d
        base = eps_bits(dim)
        b0 = beta_of(base)
        same_beta = 0
        for gam in itertools.product((-1, 1), repeat=d):
            e = eps_bits_from_table(dim, list(gam))
            if beta_of(e) == b0:
                same_beta += 1
        rec(kind="fibre_of_symmetriser_on_gamma_family", d=d, dim=dim,
            n_tables=1 << d, n_sharing_the_default_beta=same_beta,
            fibre_is_full_family=(same_beta == (1 << d)),
            note="every gamma table has the SAME commutation bicharacter")


# ════════════════════════════════════════════════════════════════════════════
# PART C -- non-degeneracy.  Prasad-Vemuri's classification needs it.
# ════════════════════════════════════════════════════════════════════════════
def part_c():
    for d in range(1, 6):
        dim = 1 << d
        eps = eps_bits(dim)
        R = beta_of(eps)
        radical = [x for x in range(dim)
                   if all(R[x][y] == 0 for y in range(dim))]
        # also: is epsilon a 2-cocycle at all (i.e. is the algebra associative)?
        bad = 0
        for x in range(dim):
            for y in range(dim):
                for z in range(dim):
                    lhs = (eps[x][y] + eps[x ^ y][z]) % 2
                    rhs = (eps[y][z] + eps[x][y ^ z]) % 2
                    if lhs != rhs:
                        bad += 1
        rec(kind="beta_nondegeneracy_and_associativity", d=d, dim=dim,
            radical=radical, radical_size=len(radical),
            beta_nondegenerate=(len(radical) == 1),
            delta_eps_nonzero=bad, is_2_cocycle=(bad == 0),
            algebra=("R", "C", "H", "O", "S", "T")[d] if d < 6 else "?",
            note="Prasad-Vemuri arXiv:0806.4064 Sec.2 classifies Heisenberg "
                 "central extensions by (K, e) with e NON-DEGENERATE.  A "
                 "nontrivial radical means that hypothesis fails.")


# ════════════════════════════════════════════════════════════════════════════
# PART D -- our shipped cocycle vs the LITERATURE cochains (AM / Elduque Ex.1)
# ════════════════════════════════════════════════════════════════════════════
def _bits(x, d):
    return [(x >> t) & 1 for t in range(d)]


def am_C(x, y):
    return (x * y) % 2


def am_H(x, y):
    x1, x2 = _bits(x, 2)
    y1, y2 = _bits(y, 2)
    return (x1 * y1 + (x1 + x2) * y2) % 2


def am_O(x, y):
    x1, x2, x3 = _bits(x, 3)
    y1, y2, y3 = _bits(y, 3)
    s = y1 * x2 * x3 + x1 * y2 * x3 + x1 * x2 * y3
    xs, ys = (x1, x2, x3), (y1, y2, y3)
    for i in range(3):
        for j in range(i, 3):
            s += xs[i] * ys[j]
    return s % 2


def part_d():
    for d, f, name in ((1, am_C, "C"), (2, am_H, "H"), (3, am_O, "O")):
        dim = 1 << d
        ours = eps_bits(dim)
        lit = [[f(i, j) for j in range(dim)] for i in range(dim)]
        exact = all(ours[i][j] == lit[i][j] for i in range(dim) for j in range(dim))
        # gauge equivalence: is ours + lit a COBOUNDARY?  delta(mu)(x,y) =
        # mu(x)+mu(y)+mu(x^y).  Solve over F2 with the shipped gf_rref.
        diff = [(ours[i][j] + lit[i][j]) % 2 for i in range(dim) for j in range(dim)]
        aug = []
        for i in range(dim):
            for j in range(dim):
                row = [0] * dim
                row[i] ^= 1
                row[j] ^= 1
                row[i ^ j] ^= 1
                row.append(diff[i * dim + j])
                aug.append(row)
        r_full = gf_rref(aug, 2)["rank"]
        r_coef = gf_rref([r[:-1] for r in aug], 2)["rank"]
        rec(kind="ours_vs_literature_cochain", algebra=name, d=d, dim=dim,
            byte_identical=exact,
            gauge_equivalent=(r_full == r_coef),
            rank_coeff=r_coef, rank_augmented=r_full,
            beta_matches=(beta_of(ours) == beta_of(lit)),
            q_ours=q_of(ours), q_literature=q_of(lit),
            note="SHIPPED cd_basis_product vs Albuquerque-Majid's published "
                 "cochain as quoted in Elduque arXiv:1801.07002 Example 1. "
                 "Gauge-equivalent == same G-graded algebra (Elduque eq.5).")


# ════════════════════════════════════════════════════════════════════════════
# PART E -- G_2 containment: the finite basis-automorphism group, MEASURED.
# ════════════════════════════════════════════════════════════════════════════
def part_e():
    for dim in (2, 4, 8):
        total, lifting, sign_only = _oracle_monomial_aut(dim)
        n_im = dim - 1
        rec(kind="monomial_automorphism_group", dim=dim,
            n_index_permutations_searched=1, order=total,
            n_permutations_that_lift=lifting,
            n_sign_only_automorphisms=sign_only,
            perms_times_signs=(lifting * (total // lifting) if lifting else 0),
            claimed_168=(total == 168), claimed_1344=(total == 1344),
            note="signed-permutation (monomial) automorphisms of the SHIPPED "
                 "cd_basis_product table.  Aut(O) = G_2 (compact real form, "
                 "dim 14) contains this finite group.")


if __name__ == "__main__":
    part_a()
    part_b()
    part_c()
    part_d()
    part_e()
    with open(__file__.replace(".py", ".ndjson"), "w") as fh:
        for r in OUT:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
