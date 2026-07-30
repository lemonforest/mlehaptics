#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd docs/srmech/python && \n#   PYTHONPATH=$PWD python3 <this file>
"""LANE 1 PARTS B/C/D/E — place the CD sign cochain epsilon in the F2 ladder.

SUBJECTS (shipped srmech ops, the things actually measured):
  * srmech.amsc.cascade.cayley_dickson.cd_basis_product(dim, i, j) -> (index, sign)
      -- epsilon(i,j) := 0 if sign == +1 else 1, over F2.
  * srmech.amsc.cascade.cayley_dickson.algebra_table(dim, gammas)
      -- the gamma-parameterised CONTROL constructor (split algebras).
  * srmech.amsc.modular_linalg.gf_rref(rows, 2)
      -- every F2 rank / solve below.

LABELLED ORACLES (hand-rolled; srmech ships no peer -- stated as a finding):
  * _oracle_anf  : Moebius transform -> algebraic normal form of an F2 function.
  * _oracle_det3 : the 3x3 F2 determinant of (x, y, z).
  * _oracle_f2_rank_bitpacked : only as a cross-check of gf_rref.

CONVENTION: inhomogeneous bar complex, trivial action, coefficients F2 --
identical to lane1_ladder.py.  Group law on basis indices is XOR (MEASURED
below: cd_basis_product's index lane IS i^j at every pair), which is the
identification G = (Z/2)^d with d = log2(dim).

Albuquerque & Majid (arXiv:math/9802116v1, 'Quasialgebra structure of the
octonions', DAMTP/97-138) define exactly this object: their eq. (11) /
Section 3 gives phi(x,y,z) = F(x,y)F(xy,z) / (F(y,z)F(x,yz)) with
(x.y).z = x.(y.z) phi(x,y,z) -- multiplicatively the same delta.  Their
abstract paragraph (p.1) states of the octonions: 'the cocycle is a
coboundary and can be identified as the result of twisting k(G) by a
2-cochain F'.  PDF extracted locally; authors/title/arXiv id verified.

No float, no numpy, no fractions, no abs().
"""
import itertools
import json
import random
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis_product, algebra_table
from srmech.amsc.modular_linalg import gf_rref

OUT = []


def rec(**kw):
    OUT.append(kw)
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


# ── ORACLES ───────────────────────────────────────────────────────────────
def _oracle_anf(vals, m):
    """Moebius transform: vals[i] = f(i) over F2^m -> coefficient list, where
    a[mask] = 1 iff the monomial prod_{b in mask} v_b appears in f's ANF."""
    a = list(vals)
    for i in range(m):
        step = 1 << i
        for j in range(1 << m):
            if j & step:
                a[j] ^= a[j ^ step]
    return a


def _oracle_det3(x, y, z):
    """3x3 determinant over F2 of the rows x, y, z (each a 3-bit int)."""
    def b(v, k):
        return (v >> k) & 1
    return (b(x, 0) * (b(y, 1) * b(z, 2) + b(y, 2) * b(z, 1))
            + b(x, 1) * (b(y, 0) * b(z, 2) + b(y, 2) * b(z, 0))
            + b(x, 2) * (b(y, 0) * b(z, 1) + b(y, 1) * b(z, 0))) % 2


def _oracle_f2_rank_bitpacked(columns):
    piv = {}
    for c in columns:
        v = c
        while v:
            p = v.bit_length() - 1
            w = piv.get(p)
            if w is None:
                piv[p] = v
                break
            v ^= w
    return len(piv)


# ── bar complex machinery (same as lane1_ladder.py) ───────────────────────
def faces(s):
    out = [s[1:]]
    for k in range(len(s) - 1):
        out.append(s[:k] + (s[k] ^ s[k + 1],) + s[k + 2:])
    out.append(s[:-1])
    return out


def basis(d, n, normalised):
    lo = 1 if normalised else 0
    return list(itertools.product(range(lo, 1 << d), repeat=n))


def delta_matrix_rows(d, n, normalised):
    """delta_n as a DENSE row list: row t = the image of the indicator of t,
    a vector over the C^{n+1} basis.  Fed straight to the shipped gf_rref."""
    rws = basis(d, n, normalised)
    cls = basis(d, n + 1, normalised)
    ridx = {t: i for i, t in enumerate(rws)}
    M = [[0] * len(cls) for _ in rws]
    for cj, s in enumerate(cls):
        for f in faces(s):
            i = ridx.get(f)
            if i is not None:
                M[i][cj] ^= 1
    return M, rws, cls


def apply_delta(vec, d, n, normalised):
    """delta applied to a cochain given as a dict/list over the C^n basis
    order -> list over the C^{n+1} basis order."""
    rws = basis(d, n, normalised)
    ridx = {t: i for i, t in enumerate(rws)}
    out = []
    for s in basis(d, n + 1, normalised):
        v = 0
        for f in faces(s):
            i = ridx.get(f)
            if i is not None:
                v ^= vec[i]
        out.append(v)
    return out


def rank(rows):
    if not rows or not rows[0]:
        return 0
    return gf_rref(rows, 2)["rank"]


def in_rowspace(rows, target):
    """Is `target` in the F2 row space of `rows`?  Decided by the SHIPPED
    gf_rref: rank is unchanged iff yes."""
    r0 = rank(rows)
    r1 = rank(rows + [list(target)])
    return r0 == r1, r0, r1


def solve_f2(A, b):
    """One particular solution of A x = b over F2 (A: rows x unknowns), or
    None if inconsistent.  Uses the SHIPPED gf_rref on the augmented matrix;
    free variables are set to 0."""
    n_unk = len(A[0])
    aug = [row + [bv] for row, bv in zip(A, b)]
    res = gf_rref(aug, 2)
    R, piv = res["rref"], res["pivots"]
    if n_unk in piv:
        return None                       # 0 = 1 row -> inconsistent
    x = [0] * n_unk
    for ri, pc in enumerate(piv):
        x[pc] = R[ri][n_unk]
    return x


# ── PART B — build epsilon from the SHIPPED op ────────────────────────────
DIMS = {0: 1, 1: 2, 2: 4, 3: 8, 4: 16}
NAME = {0: "R", 1: "C", 2: "H", 3: "O", 4: "S (sedenion)"}


def eps_table(dim, gammas=None):
    """epsilon(i,j) in F2 from the shipped cocycle.  gammas=None is the
    definite ladder (== cd_basis_product); a gamma vector routes through the
    control constructor algebra_table."""
    if gammas is None:
        return [[0 if cd_basis_product(dim, i, j)[1] == 1 else 1
                 for j in range(dim)] for i in range(dim)]
    T = algebra_table(dim, gammas)
    return [[0 if T[i][j][i ^ j] == 1 else 1 for j in range(dim)]
            for i in range(dim)]


def eps_vec(tab, d, normalised):
    return [tab[x][y] for (x, y) in basis(d, 2, normalised)]


# index-lane check + unitality + cocycle census
for d in (0, 1, 2, 3, 4):
    dim = DIMS[d]
    xor_ok = all(cd_basis_product(dim, i, j)[0] == (i ^ j)
                 for i in range(dim) for j in range(dim))
    tab = eps_table(dim)
    unital = all(tab[0][y] == 0 and tab[x][0] == 0
                 for x in range(dim) for y in range(dim))
    ev = eps_vec(tab, d, False)
    dv = apply_delta(ev, d, 2, False)
    nz = sum(dv)
    rec(kind="epsilon_basic", d=d, dim=dim, algebra=NAME[d],
        index_lane_is_XOR=xor_ok, epsilon_is_unital_normalised=unital,
        n_triples=len(dv), delta_epsilon_nonzero=nz,
        is_2_cocycle=(nz == 0),
        note="delta epsilon == 0 is EXACTLY associativity of the sign lane")


# prior-session cross-check: min Hamming distance to a coboundary, over all
# 2^(dim-1) diagonal rescalings (the gauge orbit), on the (dim-1)^2 unital cells
for d in (1, 2, 3, 4):
    dim = DIMS[d]
    tab = eps_table(dim)
    best = None
    best_c = None
    for bits in range(1 << (dim - 1)):
        c = [0] + [(bits >> k) & 1 for k in range(dim - 1)]
        dist = 0
        for i in range(1, dim):
            for j in range(1, dim):
                if (tab[i][j] ^ c[i] ^ c[j] ^ c[i ^ j]) & 1:
                    dist += 1
        if best is None or dist < best:
            best, best_c = dist, c
    rec(kind="min_distance_to_coboundary", d=d, dim=dim, algebra=NAME[d],
        n_rescalings=1 << (dim - 1), min_hamming_distance=best,
        binom_dim_2=dim * (dim - 1) // 2,
        equals_C_dim_2=(best == dim * (dim - 1) // 2),
        optimal_rescaling_is_identity=(best_c == [0] * dim),
        note="rebuilds the prior session's number from the shipped op")


# ── cup-product cochains: the measured basis of H^n ───────────────────────
def cup2(d, a, b, normalised):
    return [((x >> a) & 1) * ((y >> b) & 1)
            for (x, y) in basis(d, 2, normalised)]


def cup3(d, a, b, c, normalised):
    return [((x >> a) & 1) * ((y >> b) & 1) * ((z >> c) & 1)
            for (x, y, z) in basis(d, 3, normalised)]


def h2_generators(d, normalised):
    return [((a, b), cup2(d, a, b, normalised))
            for a in range(d) for b in range(a, d)]


def h3_generators(d, normalised):
    return [((a, b, c), cup3(d, a, b, c, normalised))
            for a in range(d) for b in range(a, d) for c in range(b, d)]


for normalised in (False, True):
    lab = "normalised" if normalised else "unnormalised"
    for d in (1, 2, 3, 4):
        B2rows, _, _ = delta_matrix_rows(d, 1, normalised)
        B3rows, _, _ = delta_matrix_rows(d, 2, normalised)
        g2 = h2_generators(d, normalised)
        g3 = h3_generators(d, normalised)
        # every cup cochain must be a cocycle
        ok2 = all(sum(apply_delta(v, d, 2, normalised)) == 0 for _, v in g2)
        ok3 = all(sum(apply_delta(v, d, 3, normalised)) == 0 for _, v in g3)
        r2 = rank(B2rows)
        r2p = rank(B2rows + [v for _, v in g2])
        r3 = rank(B3rows)
        r3p = rank(B3rows + [v for _, v in g3])
        rec(kind="cup_basis_check", complex=lab, d=d,
            n_H2_gens=len(g2), all_H2_gens_are_cocycles=ok2,
            rank_B2=r2, rank_B2_plus_gens=r2p,
            H2_independent_mod_B=(r2p - r2 == len(g2)),
            n_H3_gens=len(g3), all_H3_gens_are_cocycles=ok3,
            rank_B3=r3, rank_B3_plus_gens=r3p,
            H3_independent_mod_B=(r3p - r3 == len(g3)),
            note="x_a cup x_b / x_a cup x_b cup x_c as explicit bar cochains")


# ── PART C (a) — WHICH class does epsilon represent at d <= 2? ────────────
def class_of_2cochain(vec, d, normalised):
    """Express a 2-COCYCLE in the measured cup basis modulo coboundaries.
    Unknowns: the cup coefficients then the C^1 gauge cochain."""
    gens = h2_generators(d, normalised)
    Brows, c1basis, _ = delta_matrix_rows(d, 1, normalised)
    m = len(gens)
    ncols = len(vec)
    A = [[0] * (m + len(Brows)) for _ in range(ncols)]
    for gi, (_, gv) in enumerate(gens):
        for r in range(ncols):
            A[r][gi] = gv[r]
    for bi, brow in enumerate(Brows):
        for r in range(ncols):
            A[r][m + bi] = brow[r]
    x = solve_f2(A, list(vec))
    if x is None:
        return None, gens
    return x[:m], gens


def class_of_3cochain(vec, d, normalised):
    gens = h3_generators(d, normalised)
    Brows, _, _ = delta_matrix_rows(d, 2, normalised)
    m = len(gens)
    ncols = len(vec)
    A = [[0] * (m + len(Brows)) for _ in range(ncols)]
    for gi, (_, gv) in enumerate(gens):
        for r in range(ncols):
            A[r][gi] = gv[r]
    for bi, brow in enumerate(Brows):
        for r in range(ncols):
            A[r][m + bi] = brow[r]
    x = solve_f2(A, list(vec))
    if x is None:
        return None, gens
    return x[:m], gens


def poly2(coeffs, gens):
    terms = []
    for c, ((a, b), _) in zip(coeffs, gens):
        if c:
            terms.append(f"x{a+1}^2" if a == b else f"x{a+1}x{b+1}")
    return " + ".join(terms) if terms else "0"


def poly3(coeffs, gens):
    terms = []
    for c, ((a, b, cc), _) in zip(coeffs, gens):
        if c:
            terms.append("".join(f"x{t+1}" for t in (a, b, cc)))
    return " + ".join(terms) if terms else "0"


for normalised in (False, True):
    lab = "normalised" if normalised else "unnormalised"
    for d in (1, 2):
        dim = DIMS[d]
        tab = eps_table(dim)
        ev = eps_vec(tab, d, normalised)
        Brows, _, _ = delta_matrix_rows(d, 1, normalised)
        is_cob, r0, r1 = in_rowspace(Brows, ev)
        coeffs, gens = class_of_2cochain(ev, d, normalised)
        rec(kind="epsilon_H2_class", complex=lab, d=d, dim=dim,
            algebra=NAME[d],
            delta_epsilon_nonzero=sum(apply_delta(ev, d, 2, normalised)),
            epsilon_is_a_coboundary=is_cob, rank_B2=r0, rank_B2_plus_eps=r1,
            class_coeffs=coeffs, class_polynomial=poly2(coeffs, gens),
            class_is_zero=(coeffs is not None and not any(coeffs)),
            quadratic_form_q=[tab[x][x] for x in range(dim)],
            note="[epsilon] in H^2(G;F2) = F2[x_1..x_d]_2")


# ── PART D (b) — THE CRUX at d = 3 (and d = 4) ────────────────────────────
for d in (3, 4):
    dim = DIMS[d]
    for normalised in (False, True):
        lab = "normalised" if normalised else "unnormalised"
        tab = eps_table(dim)
        ev = eps_vec(tab, d, normalised)
        phi = apply_delta(ev, d, 2, normalised)
        d_phi = apply_delta(phi, d, 3, normalised)
        Brows, _, _ = delta_matrix_rows(d, 2, normalised)
        is_cob, r0, r1 = in_rowspace(Brows, phi)
        coeffs, gens = class_of_3cochain(phi, d, normalised)
        # TEETH: the same instrument on genuinely nontrivial 3-cocycles
        teeth = []
        for key, gv in gens:
            ic, _, _ = in_rowspace(Brows, gv)
            teeth.append({"gen": list(key), "is_coboundary": ic})
        rec(kind="phi_crux", complex=lab, d=d, dim=dim, algebra=NAME[d],
            n_triples=len(phi), phi_support=sum(phi),
            phi_is_zero_cochain=(sum(phi) == 0),
            delta_phi_nonzero=sum(d_phi), phi_is_a_3_cocycle=(sum(d_phi) == 0),
            phi_is_a_3_coboundary=is_cob, rank_B3=r0, rank_B3_plus_phi=r1,
            phi_class_coeffs=coeffs, phi_class_polynomial=poly3(coeffs, gens),
            phi_class_is_ZERO=(coeffs is not None and not any(coeffs)),
            teeth_cup_gens_are_coboundary=teeth,
            teeth_all_cup_gens_nontrivial=all(not t["is_coboundary"]
                                              for t in teeth),
            note="the SAME rank instrument says phi is a coboundary and every "
                 "cup generator is NOT -- the probe distinguishes")


# ── PART E (c) — the DECIDABLE reformulation ──────────────────────────────
# E1. exact closed form of phi via ANF (labelled oracle), d = 3 and d = 4
def phi_full(d, tab):
    ev = eps_vec(tab, d, False)
    return apply_delta(ev, d, 2, False)


def anf_terms(vals, d):
    """vals indexed by the basis(d,3,False) order == (x,y,z) lexicographic in
    itertools.product order; re-index to the packed bit order x|y<<d|z<<2d."""
    order = basis(d, 3, False)
    packed = [0] * (1 << (3 * d))
    for v, (x, y, z) in zip(vals, order):
        packed[x | (y << d) | (z << (2 * d))] = v
    a = _oracle_anf(packed, 3 * d)
    names = []
    for k in range(3 * d):
        if k < d:
            names.append(f"x{k+1}")
        elif k < 2 * d:
            names.append(f"y{k-d+1}")
        else:
            names.append(f"z{k-2*d+1}")
    terms = []
    for mask in range(1 << (3 * d)):
        if a[mask]:
            terms.append("".join(names[k] for k in range(3 * d)
                                 if (mask >> k) & 1))
    return terms


for d in (3, 4):
    dim = DIMS[d]
    tab = eps_table(dim)
    ph = phi_full(d, tab)
    terms = anf_terms(ph, d)
    rec(kind="phi_closed_form", d=d, dim=dim, algebra=NAME[d],
        support=sum(ph), n_ANF_monomials=len(terms),
        ANF_monomials=sorted(terms),
        note="algebraic normal form of phi as an F2 polynomial in the 3d bits "
             "(labelled Moebius-transform ORACLE; srmech ships no ANF op)")

# E2. d = 3: is phi EXACTLY the 3x3 F2 determinant?
d = 3
tab = eps_table(8)
ph = phi_full(3, tab)
order = basis(3, 3, False)
det_vec = [_oracle_det3(x, y, z) for (x, y, z) in order]
agree = sum(1 for a, b in zip(ph, det_vec) if a == b)
n_indep = 0
for (x, y, z) in order:
    if _oracle_det3(x, y, z):
        n_indep += 1
rec(kind="phi_is_determinant", d=3, dim=8, algebra="O",
    n_triples=len(ph), agreements=agree, exact_match=(agree == len(ph)),
    phi_support=sum(ph), det_support=n_indep,
    order_GL_3_2=(8 - 1) * (8 - 2) * (8 - 4),
    support_equals_GL_3_2=(sum(ph) == (8 - 1) * (8 - 2) * (8 - 4)),
    note="the support of phi is exactly the set of LINEARLY INDEPENDENT "
         "triples = GL(3,2); det is GL-invariant so this is basis-free")

# E3. GAUGE INVARIANCE of phi: exhaustive over every 1-cochain
for d in (3,):
    dim = DIMS[d]
    tab = eps_table(dim)
    ev = eps_vec(tab, d, False)
    ph = apply_delta(ev, d, 2, False)
    n_c = 1 << dim
    same = 0
    distinct_eps = set()
    for bits in range(n_c):
        c = [(bits >> k) & 1 for k in range(dim)]
        dc = apply_delta(c, d, 1, False)
        ev2 = [a ^ b for a, b in zip(ev, dc)]
        distinct_eps.add(tuple(ev2))
        if apply_delta(ev2, d, 2, False) == ph:
            same += 1
    rec(kind="phi_gauge_invariance", d=d, dim=dim,
        n_gauge_1_cochains=n_c, n_with_same_phi=same,
        phi_gauge_invariant=(same == n_c),
        gauge_orbit_size=len(distinct_eps),
        note="phi is constant on the whole gauge orbit of epsilon: it is a "
             "genuine invariant of the QUASIALGEBRA, unlike epsilon itself")

# E4. NEGATIVE CONTROLS -- does the instrument return a different answer when
#     the structure it claims to measure is absent?
d = 3
n_trip = len(basis(3, 3, False))
Brows3, _, _ = delta_matrix_rows(3, 2, False)

# (i) the plain group algebra F2[(Z/2)^3]: epsilon = 0
zero_eps = [0] * len(basis(3, 2, False))
ph0 = apply_delta(zero_eps, 3, 2, False)
rec(kind="control_group_algebra", d=3, epsilon="all zero",
    phi_support=sum(ph0), phi_is_zero=(sum(ph0) == 0),
    class_is_zero=True,
    note="associative twist -> phi = 0; the instrument is not stuck on 168")

# (ii) the BICHARACTER twist (Albuquerque-Majid's 'bilinear part'):
#      f(x,y) = sum_{i<=j} x_i y_j  -- associative, phi must vanish
bic = []
for (x, y) in basis(3, 2, False):
    v = 0
    for i in range(3):
        for j in range(i, 3):
            v ^= ((x >> i) & 1) * ((y >> j) & 1)
    bic.append(v % 2)
phb = apply_delta(bic, 3, 2, False)
rec(kind="control_bicharacter", d=3,
    epsilon="f(x,y) = sum_{i<=j} x_i y_j (AM's bilinear part)",
    phi_support=sum(phb), phi_is_zero=(sum(phb) == 0),
    note="a bicharacter IS a 2-cocycle -> associative quasialgebra, phi = 0")

# (iii) every gamma-triple at dim 8 (definite O + the seven split forms)
for g in itertools.product((-1, 1), repeat=3):
    t = eps_table(8, list(g))
    ev = eps_vec(t, 3, False)
    ph_g = apply_delta(ev, 3, 2, False)
    same_as_det = (ph_g == det_vec)
    ic, _, _ = in_rowspace(Brows3, ph_g)
    orb = set()
    for bits in range(1 << 8):
        c = [(bits >> k) & 1 for k in range(8)]
        dc = apply_delta(c, 3, 1, False)
        orb.add(tuple(a ^ b for a, b in zip(ev, dc)))
    rec(kind="control_gamma_family", d=3, gammas=list(g),
        is_definite_octonion=(list(g) == [-1, -1, -1]),
        phi_support=sum(ph_g), phi_equals_det=same_as_det,
        phi_is_a_coboundary=ic, gauge_orbit_size=len(orb),
        epsilon_diag_q=[t[x][x] for x in range(8)],
        note="split algebras share the SAME phi -> phi alone does NOT "
             "separate O from split-O")

# (iv) random unital 2-cochains
random.seed(20260729)
cells = [(i, j) for i in range(1, 8) for j in range(1, 8)]
N = 20000
supports = {}
n_det = 0
n_class_zero = 0
CHECK = 200
for t in range(N):
    tb = [[0] * 8 for _ in range(8)]
    for (i, j) in cells:
        tb[i][j] = random.getrandbits(1)
    ev = eps_vec(tb, 3, False)
    p = apply_delta(ev, 3, 2, False)
    supports[sum(p)] = supports.get(sum(p), 0) + 1
    if p == det_vec:
        n_det += 1
    if t < CHECK:
        ic, _, _ = in_rowspace(Brows3, p)
        if ic:
            n_class_zero += 1
rec(kind="control_random_2cochains", d=3, n_samples=N,
    n_equal_to_det=n_det, n_support_168=supports.get(168, 0),
    support_histogram_top=sorted(supports.items(),
                                 key=lambda kv: -kv[1])[:8],
    n_checked_for_class=CHECK, n_with_zero_H3_class=n_class_zero,
    all_random_phis_have_zero_class=(n_class_zero == CHECK),
    exact_count_of_2cochains_with_phi_eq_det="2^dim(Z^2)",
    note="EVERY delta-of-a-2-cochain has zero H^3 class -- that is why the "
         "H^3 reading carries no information; the SUPPORT does")

# E5. is the gauge class of epsilon (in C^2 / B^2) the finer invariant?
d = 3
tabO = eps_table(8)
evO = eps_vec(tabO, 3, False)
orbO = set()
for bits in range(1 << 8):
    c = [(bits >> k) & 1 for k in range(8)]
    dc = apply_delta(c, 3, 1, False)
    orbO.add(tuple(a ^ b for a, b in zip(evO, dc)))
for g in itertools.product((-1, 1), repeat=3):
    t = eps_table(8, list(g))
    ev = eps_vec(t, 3, False)
    rec(kind="gauge_class_separation", d=3, gammas=list(g),
        in_same_gauge_orbit_as_definite_O=(tuple(ev) in orbO),
        orbit_size=len(orbO),
        n_negative_signs=sum(ev),
        note="epsilon mod B^2 -- the class of the PAIR (epsilon, phi) reduces "
             "to this, since phi = delta(epsilon) is determined by it")

# E6. how many unital 2-cochains have delta = det, exactly?
#     = |Z^2| in the normalised complex (measured, not asserted)
Z2rows, _, _ = delta_matrix_rows(3, 2, True)
dimC2 = len(basis(3, 2, True))
rk = rank(Z2rows)
dimZ2 = dimC2 - rk
n_solutions = 0
rec(kind="fiber_over_det", d=3,
    dim_C2_normalised=dimC2, rank_delta_2_normalised=rk,
    dim_Z2_normalised=dimZ2,
    n_unital_2cochains_with_delta_eq_phi=2 ** dimZ2,
    total_unital_2cochains=2 ** dimC2,
    note="the fiber delta^{-1}(phi) is a coset of Z^2 -- exactly 2^dim(Z^2) "
         "unital sign tables reproduce the octonion associator")
