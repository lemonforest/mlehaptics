#!/usr/bin/env python3
"""LANE 3 — NAME THE SHAPE: quotient-addressing vs dimension-addressing.

Settles, by MEASUREMENT on the shipped srmech surface, five things:

  A  QUOTIENT   the presentation R[(Z/2)^d] = R[x_1..x_d]/(x_i^2 - 1), and that
                the shipped index lane of ``cd_basis_product`` IS the monomial
                product of that quotient (subset-XOR).  NEGATIVE CONTROL: the
                *cyclic* quotient R[x]/(x^n - 1) is a different algebra and the
                same probe SEPARATES them.
  B  COST       what each presentation actually costs, so "2^d vs d" stops
                being a slogan: dense structure tensor vs a d-step recursion.
  C  LITERATURE Albuquerque & Majid (arXiv:math/9802116) Prop. 4.4 gives an
                EXPLICIT F = (-1)^f for C / H / O.  Built here and checked
                against the shipped ``cd_basis_product``, resolving a subscript
                the PDF text layer loses.  Also checks their Cor. 4.3 doubling
                recursion for f.
  D  POLYTOPE   which polytope, in which space, on each side.  Label space ->
                the d-cube Q_d in R^d.  Scalar space -> the cross-polytope
                beta_n in R^n, n = 2^d.  Duality tested, not assumed.
  E  CONTROL    the gamma-family (split twists) share the index lane exactly
                and differ in the sign lane — so the cube probe reads the index
                lane and only the index lane, and the cocycle probe reads the
                sign lane.  That is the "does the instrument distinguish" gate.

Exact integers / exact Q only.  No numpy, no float, no stdlib ``fractions``,
and no ``abs()`` — every sign is a Class-K pin-slot read, re-applied Class-C.

Run from ``docs/srmech/python``::

    python3 ../notes/lane3_quotient_vs_dimension_addressing_2026-07-29.py
    python3 ../notes/lane3_quotient_vs_dimension_addressing_2026-07-29.py --ndjson
"""
from __future__ import annotations

import json
import sys
from itertools import product as iproduct
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PY = _HERE.parent / "python"
if str(_PY) not in sys.path:
    sys.path.insert(0, str(_PY))

import srmech                                                     # noqa: E402
from srmech.amsc.q import Q                                       # noqa: E402
from srmech.amsc.cascade.cayley_dickson import (                  # noqa: E402
    cd_basis_product, cd_basis, cd_mult, cd_norm_sq, algebra_table,
    CD_MAX_DIM, ALGEBRA_TABLE_MAX_DIM,
)

OUT = []


def rec(**kw):
    OUT.append(kw)


# ── Class-K / Class-C sign discipline ────────────────────────────────

def k_pin(v):
    """Class-K pin-slot: the ORIENTATION of an exact value, in {-1, 0, +1}.

    Never ``abs()``; this is the sign-flip read itself, and :func:`c_magnitude`
    is the Class-C re-application that recovers the unsigned part from it.
    """
    if v == 0:
        return 0
    return -1 if v < 0 else 1


def c_magnitude(v):
    """Class-C: re-apply the pin so the orientation is +1.  ``|v|`` without
    ``abs()`` — the composition K then C, which is the cascade shape claimed."""
    return v * k_pin(v) if k_pin(v) != 0 else v


# ────────────────────────────────────────────────────────────────────
# A — THE QUOTIENT PRESENTATION
# ────────────────────────────────────────────────────────────────────

def subset_xor_oracle(d, S, T):
    """LABELLED ORACLE (hand-rolled, not a shipped op).

    The monomial product of R[x_1..x_d]/(x_i^2 - 1): a monomial is a SUBSET
    S of {1..d} written as a d-bit mask; x^S * x^T = x^(S xor T) because every
    variable that appears in both squares to 1.  Returns the mask.
    """
    return S ^ T


def cyclic_oracle(n, i, j):
    """NEGATIVE-CONTROL ORACLE: the *other* quotient of a polynomial ring with
    the same dimension, R[x]/(x^n - 1) = R[Z/n].  Product index is (i+j) mod n,
    NOT xor.  If a probe cannot tell this from subset-XOR it is measuring
    nothing."""
    return (i + j) % n


def section_A():
    rec(kind="env", srmech_version=srmech.__version__,
        subject_ops=["cd_basis_product", "algebra_table", "cd_basis",
                     "cd_mult", "cd_norm_sq"])

    for d in range(0, 9):                      # dim 1 .. 256 = CD_MAX_DIM
        dim = 1 << d
        xor_mismatch = 0
        cyc_mismatch = 0
        for i in range(dim):
            for j in range(dim):
                idx, _sign = cd_basis_product(dim, i, j)   # SHIPPED subject
                if idx != subset_xor_oracle(d, i, j):
                    xor_mismatch += 1
                if idx != cyclic_oracle(dim, i, j):
                    cyc_mismatch += 1
        rec(kind="A1_quotient_index_lane", d=d, dim=dim,
            pairs=dim * dim,
            mismatch_vs_subset_xor_quotient=xor_mismatch,
            mismatch_vs_cyclic_quotient=cyc_mismatch,
            probe_separates=(xor_mismatch == 0 and (cyc_mismatch > 0 or d <= 1)),
            note="R[(Z/2)^d] = R[x_1..x_d]/(x_i^2-1); monomial basis = subsets; "
                 "product = XOR of masks. Cyclic control = R[x]/(x^dim - 1).")


# ────────────────────────────────────────────────────────────────────
# B — WHAT EACH PRESENTATION COSTS
# ────────────────────────────────────────────────────────────────────

def section_B():
    for d in range(0, 9):
        dim = 1 << d
        # DIMENSION-ADDRESSED cost: the dense rank-3 structure tensor.
        table_built = False
        tensor_cells = dim ** 3
        tensor_nonzero = None
        if dim <= ALGEBRA_TABLE_MAX_DIM:
            t = algebra_table(dim)                            # SHIPPED subject
            tensor_nonzero = sum(1 for i in range(dim) for j in range(dim)
                                 for k in range(dim) if t[i][j][k] != 0)
            table_built = True
        # QUOTIENT-ADDRESSED cost: the recursion depth of cd_basis_product is
        # exactly log2(dim) = d doubling steps (one per GENERATOR), and it
        # holds O(d) bits of state.  MEASURED as: it answers at dims where the
        # tensor cannot be materialised at all.
        answered = cd_basis_product(dim, dim - 1, dim - 1)     # SHIPPED subject
        rec(kind="B1_cost", d=d, dim=dim,
            generators=d,
            dimension_addressed_tensor_cells=tensor_cells,
            dimension_addressed_tensor_nonzero=tensor_nonzero,
            dimension_addressed_materialisable=table_built,
            quotient_addressed_recursion_steps=d,
            quotient_addressed_answers=list(answered),
            cochain_table_signs=dim * dim,
            note="tensor cells = dim^3 = 2^(3d); nonzero = dim^2 = 2^(2d); "
                 "recursion steps = d. The cochain as a TABLE is still 2^(2d) "
                 "signs — what is linear in d is the GENERATOR count and the "
                 "recursion, not a generic cochain's own storage.")


# ────────────────────────────────────────────────────────────────────
# C — ALBUQUERQUE & MAJID Prop. 4.4, verified against the shipped op
# ────────────────────────────────────────────────────────────────────
#
# AM define (Cor. 2.4) k_F G = kG with product  x ._F y = (x+y) F(x,y),
# and (Prop. 4.4) for G = (Z/2)^n, F = (-1)^f with
#   (i)   C : n=1, f(x,y) = x1 y1
#   (ii)  H : n=2, f(x,y) = x1y1 + (x1+x2) y2
#   (iii) O : n=3, f(x,y) = sum_{i<=j} xi yj + y1x2x3 + x1y2x3 + <CUBIC-3>
# The PDF text layer renders <CUBIC-3> as "x2x2y3", which is not a well-formed
# peer of the other two cubic terms.  We do not guess: we build every candidate
# and MEASURE which one reproduces the shipped algebra.

def am_f_C(x, y):
    return (x[0] * y[0]) % 2


def am_f_H(x, y):
    return (x[0] * y[0] + (x[0] + x[1]) * y[1]) % 2


def am_bilinear(x, y, n):
    """The bilinear part sum_{i<=j} x_i y_j common to the whole 2^n-onion family
    (AM p.19: the upper-triangular-with-unit-diagonal form)."""
    return sum(x[i] * y[j] for i in range(n) for j in range(i, n)) % 2


AM_O_CUBIC_CANDIDATES = {
    # the reading that makes the three cubic terms peers (one y, two x's)
    "y1x2x3 + x1y2x3 + x1x2y3":
        lambda x, y: (y[0] * x[1] * x[2] + x[0] * y[1] * x[2]
                      + x[0] * x[1] * y[2]) % 2,
    # the literal text-layer reading, kept as a falsifiable candidate
    "y1x2x3 + x1y2x3 + x2x2y3":
        lambda x, y: (y[0] * x[1] * x[2] + x[0] * y[1] * x[2]
                      + x[1] * x[1] * y[2]) % 2,
    "y1x2x3 + x1y2x3 + x2x3y3":
        lambda x, y: (y[0] * x[1] * x[2] + x[0] * y[1] * x[2]
                      + x[1] * x[2] * y[2]) % 2,
    # bilinear part alone (control: must FAIL, O is not associative)
    "no cubic term (CONTROL)":
        lambda x, y: 0,
}


def bits(n, v):
    return tuple((v >> k) & 1 for k in range(n))


def am_sign_table(n, f):
    """F(x,y) = (-1)^f(x,y) as a dim x dim sign table, dim = 2^n."""
    dim = 1 << n
    return [[1 if f(bits(n, i), bits(n, j)) == 0 else -1
             for j in range(dim)] for i in range(dim)]


def shipped_sign_table(dim):
    """The sign lane of the SHIPPED cd_basis_product."""
    return [[cd_basis_product(dim, i, j)[1] for j in range(dim)]
            for i in range(dim)]


def diagonal_rescalings(dim):
    """Every 1-cochain lam: G -> {+-1} with lam(e) = 1 (2^(dim-1) of them).

    This is EXACTLY Conlon (1964) eq. (1): a change of basis sigma'(A) =
    d_A sigma(A) modifies the factor system by the principal factor system
    f'(A,B) = d_A d_B d_(AB)^-1 f(A,B).  Searching over it is searching the
    coboundary orbit."""
    for m in range(1 << (dim - 1)):
        lam = [1] + [1 if ((m >> k) & 1) == 0 else -1 for k in range(dim - 1)]
        yield lam


def coboundary_equivalent(dim, A, B):
    """Is sign table A equal to B after some diagonal rescaling (Conlon eq.1)?

    Returns (bool, hamming_min).  Hamming distance counted as an INTEGER over
    the dim^2 cells; sign comparison is a Class-K pin read, never abs()."""
    best = dim * dim + 1
    hit = None
    for lam in diagonal_rescalings(dim):
        dist = 0
        for i in range(dim):
            for j in range(dim):
                twisted = A[i][j] * lam[i] * lam[j] * lam[i ^ j]
                if twisted != B[i][j]:
                    dist += 1
        if dist < best:
            best, hit = dist, list(lam)
        if best == 0:
            break
    return best == 0, best, hit


def section_C():
    # (i) and (ii) — direct
    for name, n, f in (("C  (AM 4.4 i)", 1, am_f_C),
                       ("H  (AM 4.4 ii)", 2, am_f_H)):
        dim = 1 << n
        A = am_sign_table(n, f)
        B = shipped_sign_table(dim)
        exact = (A == B)
        eq, dist, lam = coboundary_equivalent(dim, A, B)
        rec(kind="C1_am_prop44", algebra=name, n=n, dim=dim,
            equals_shipped_exactly=exact,
            equals_shipped_up_to_diagonal_rescaling=eq,
            min_hamming_over_rescalings=dist, witness_rescaling=lam)

    # (iii) — resolve the lost subscript by measurement
    n, dim = 3, 8
    B = shipped_sign_table(dim)
    for label, cubic in AM_O_CUBIC_CANDIDATES.items():
        def f(x, y, _c=cubic):
            return (am_bilinear(x, y, 3) + _c(x, y)) % 2
        A = am_sign_table(n, f)
        exact = (A == B)
        eq, dist, lam = coboundary_equivalent(dim, A, B)
        # is the candidate algebra even non-associative?  count triples where
        # phi = dF differs from 1.
        bad = 0
        for a in range(dim):
            for b in range(dim):
                for c in range(dim):
                    lhs = A[a][b] * A[a ^ b][c]
                    rhs = A[b][c] * A[a][b ^ c]
                    if lhs != rhs:
                        bad += 1
        rec(kind="C2_am_octonion_cubic_candidate", candidate=label, dim=dim,
            equals_shipped_exactly=exact,
            equals_shipped_up_to_diagonal_rescaling=eq,
            min_hamming_over_rescalings=dist, witness_rescaling=lam,
            phi_nontrivial_triples=bad, triples=dim ** 3)

    # AM Cor. 4.3 — the doubling recursion on f itself.
    #   ftilde((x,x_{n+1}),(y,y_{n+1})) =
    #       f(x,y)(1-x_{n+1}) + f(y,x)x_{n+1} + y_{n+1} f(x,x) + x_{n+1}y_{n+1}
    def am_double(n, f):
        def ft(X, Y):
            x, xn = X[:n], X[n]
            y, yn = Y[:n], Y[n]
            return (f(x, y) * (1 - xn) + f(y, x) * xn
                    + yn * f(x, x) + xn * yn) % 2
        return ft

    f = lambda x, y: 0                              # n = 0: R, f is empty
    for n in range(0, 6):
        dim = 1 << n
        A = am_sign_table(n, f) if n > 0 else [[1]]
        B = shipped_sign_table(dim)
        eq, dist, lam = coboundary_equivalent(dim, A, B) if dim <= 32 \
            else (None, None, None)
        rec(kind="C3_am_cor43_recursion", n=n, dim=dim,
            equals_shipped_exactly=(A == B),
            equals_shipped_up_to_diagonal_rescaling=eq,
            min_hamming_over_rescalings=dist,
            note="AM Cor. 4.3 doubling of f, iterated from f = 0 on the "
                 "trivial group; compared against shipped cd_basis_product.")
        f = am_double(n, f)


# ────────────────────────────────────────────────────────────────────
# D — THE POLYTOPES.  Two spaces.  Do not conflate them.
# ────────────────────────────────────────────────────────────────────

def section_D():
    # D1 — LABEL SPACE.  G = (Z/2)^d, Cayley graph on the d standard
    # generators.  Claim: that graph IS the hypercube graph Q_d, whose
    # geometric realisation is the d-cube in R^d.
    for d in range(1, 8):
        dim = 1 << d
        gens = [1 << k for k in range(d)]
        edges = set()
        for g in range(dim):
            for s in gens:
                # the shipped op supplies the product index; the generator
                # e_(2^k) sends label g -> g xor 2^k
                idx, _sgn = cd_basis_product(dim, g, s)        # SHIPPED
                edges.add(frozenset((g, idx)))
        deg_ok = all(sum(1 for e in edges if v in e) == d for v in range(dim))
        # every edge must join labels at Hamming distance exactly 1
        ham1 = all(bin(a ^ b).count("1") == 1 for e in edges for a, b in [tuple(e)])
        # bipartite by parity of popcount
        bip = all(bin(a).count("1") % 2 != bin(b).count("1") % 2
                  for e in edges for a, b in [tuple(e)])
        rec(kind="D1_label_space_hypercube", d=d, ambient_dimension_R=d,
            vertices=dim, edges=len(edges),
            expected_edges=d * (1 << (d - 1)),
            all_degrees_equal_d=deg_ok,
            every_edge_hamming_one=ham1, bipartite=bip,
            polytope="hypercube Q_d (2^d vertices, 2d facets) in R^d",
            is_hypercube_graph=(deg_ok and ham1 and bip
                                and len(edges) == d * (1 << (d - 1))))

    # D2 — NEGATIVE CONTROL for D1: the SAME construction on the cyclic group
    # Z/2^d with d generators is not Q_d.
    for d in range(2, 6):
        dim = 1 << d
        gens = [1 << k for k in range(d)]
        edges = set()
        for g in range(dim):
            for s in gens:
                edges.add(frozenset((g, cyclic_oracle(dim, g, s))))
        ham1 = all(bin(a ^ b).count("1") == 1 for e in edges for a, b in [tuple(e)])
        rec(kind="D2_label_space_control_cyclic", d=d, vertices=dim,
            edges=len(edges), expected_hypercube_edges=d * (1 << (d - 1)),
            every_edge_hamming_one=ham1,
            is_hypercube_graph=(ham1 and len(edges) == d * (1 << (d - 1))))

    # D3 — SCALAR SPACE.  The +-unit basis of a dim-n CD algebra as POINTS of
    # R^n.  Claim: they are the 2n vertices of the cross-polytope beta_n.
    # Certificate: all norm 1 (shipped cd_norm_sq), pairwise inner products in
    # {0, +-1}, so the point set is exactly {+-e_i} = vertices of the unit
    # l1-ball in R^n, which IS beta_n by definition.
    for d in range(0, 6):
        dim = 1 << d
        pts = []
        for i in range(dim):
            e = cd_basis(dim, i)                               # SHIPPED
            pts.append(e)
            pts.append(tuple(Q(0) - v for v in e))
        norms = set()
        for p in pts:
            norms.add(cd_norm_sq(p).as_pair())                 # SHIPPED
        ip = set()
        for a in range(len(pts)):
            for b in range(len(pts)):
                s = Q(0)
                for k in range(dim):
                    s = s + pts[a][k] * pts[b][k]
                ip.add(s.as_pair())
        rec(kind="D3_scalar_space_cross_polytope", d=d,
            algebra_dim=dim, ambient_dimension_R=dim,
            signed_unit_points=len(pts),
            distinct_norms=sorted(norms),
            distinct_pairwise_inner_products=sorted(ip),
            polytope=("cross-polytope beta_%d (2*%d = %d vertices, 2^%d = %d "
                      "facets) in R^%d" % (dim, dim, 2 * dim, dim,
                                           1 << dim, dim)),
            cross_polytope_vertices=2 * dim,
            cross_polytope_facets=1 << dim,
            is_16_cell=(dim == 4),
            note="beta_4 IS the 16-cell. It is the signed-unit set of H "
                 "(dim 4) in R^4 — NOT a grading shadow, and not general.")

    # D4 — DUALITY, tested rather than assumed.
    # Q_m and beta_m are dual ONLY when they live in the same R^m.
    #   label side:  Q_d           in R^d          (2^d verts, 2d facets)
    #   scalar side: beta_(2^d)    in R^(2^d)      (2^(d+1) verts, 2^(2^d) facets)
    # so a duality would need d == 2^d.
    for d in range(0, 6):
        dim = 1 << d
        rec(kind="D4_duality_test", d=d,
            label_polytope="Q_%d in R^%d" % (d, d),
            label_vertices=dim, label_facets=2 * d,
            scalar_polytope="beta_%d in R^%d" % (dim, dim),
            scalar_vertices=2 * dim, scalar_facets=1 << dim,
            same_ambient_space=(d == dim),
            dual_pair=(d == dim),
            unit_label_cube="Q_%d in R^%d" % (d + 1, d + 1),
            unit_label_cube_vertices=1 << (d + 1),
            unit_label_cube_matches_scalar_vertex_count=True,
            unit_label_cube_is_dual_to_scalar_polytope=((d + 1) == dim),
            note="Q_m is dual to beta_m. Our two polytopes are Q_d in R^d and "
                 "beta_(2^d) in R^(2^d): never the same space for d>=1. The "
                 "rc354 unit-label cube Q_(d+1) has the SAME VERTEX COUNT as "
                 "beta_(2^d) (both 2^(d+1)) but is only its dual when "
                 "d+1 == 2^d, i.e. d = 1 (C) alone.")


# ────────────────────────────────────────────────────────────────────
# E — DOES THE INSTRUMENT DISTINGUISH?
# ────────────────────────────────────────────────────────────────────
#
# The gamma-family (algebra_table with per-doubling gammas) changes the SIGN
# lane and leaves the INDEX lane alone.  If the cube probe is really reading
# the index lane it must return the SAME cube for every gamma; if the cocycle
# probe is really reading the sign lane it must SEPARATE them.

def section_E():
    for d in (1, 2, 3):
        dim = 1 << d
        base = None
        sign_sets = set()
        index_sets = set()
        for gam in iproduct((-1, 1), repeat=d):
            t = algebra_table(dim, gammas=gam)                 # SHIPPED
            idx = []
            sgn = []
            for i in range(dim):
                for j in range(dim):
                    row = t[i][j]
                    nz = [k for k in range(dim) if row[k] != 0]
                    assert len(nz) == 1, (gam, i, j, row)
                    idx.append(nz[0])
                    sgn.append(row[nz[0]])
            index_sets.add(tuple(idx))
            sign_sets.add(tuple(sgn))
        rec(kind="E1_gamma_control", d=d, dim=dim,
            gamma_variants=1 << d,
            distinct_index_lanes=len(index_sets),
            distinct_sign_lanes=len(sign_sets),
            cube_probe_is_gamma_blind=(len(index_sets) == 1),
            cocycle_probe_separates_gammas=(len(sign_sets) > 1),
            note="index lane identical across every gamma (so the cube is a "
                 "statement about the QUOTIENT, not the twist); sign lane "
                 "differs (so the cocycle probe is reading the twist).")


def main() -> int:
    section_A()
    section_B()
    section_C()
    section_D()
    section_E()
    if "--ndjson" in sys.argv:
        for r in OUT:
            print(json.dumps(r, sort_keys=True))
        return 0
    for r in OUT:
        print(json.dumps(r, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
