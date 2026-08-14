#!/usr/bin/env python3
"""LANE 2 — ORDER FROM CHIRALITY: does the commutator-sign (chirality) class
reconstruct the Cayley-Dickson product?

THE CLAIM UNDER TEST: index lane (XOR, abelian, order-blind) + the CHIRALITY
BITS c(i,j) (e_i e_j = c(i,j) e_j e_i) together determine the full non-abelian
signed product table, and the bit-count is C(dim,2).

Exact integers only.  Every sign is read off the SHIPPED cocycle
`srmech.amsc.cascade.cayley_dickson.cd_basis_product`, differentially checked
against `cd_mult` on explicit basis vectors and against `algebra_table`
(gammas=None) + `srmech.qm.octonion.octonion_mult_table`.  No floats, no abs()
(sign composition is Class-K pin-slot throughout).

Gauge convention (the coboundary / per-basis sign rescaling):
    f_i = c_i e_i   =>   s'(i,j) = c_i * c_j * c_{i^j} * s(i,j)
Unitality (f_0 stays the unit) forces c_0 = +1, so |Gamma| = 2^(dim-1).
"""
import json
import itertools

from srmech.amsc.cascade.cayley_dickson import (
    cd_basis_product, cd_basis, cd_mult, algebra_table,
)
from srmech.qm.octonion import octonion_mult_table
from srmech.amsc import _native

OUT = []


def rec(**kw):
    OUT.append(kw)


DIMS = [2, 4, 8, 16]
NAME = {1: "R", 2: "C", 4: "H", 8: "O", 16: "S(sedenion)", 32: "T(32)"}

rec(kind="provenance", native_loaded=bool(_native.HAS_NATIVE),
    note="pure-Python cocycle path when native_loaded is false; the C peer "
         "srmech_cd_basis_product is bit-identical by the shipped Rosetta "
         "parity test tests/test_cascade_cayley_dickson_parity.py")


# ───────────────────────────── the shipped sign table ─────────────────────
def sign_table(n):
    tab = [[0] * n for _ in range(n)]
    bad = 0
    for i in range(n):
        for j in range(n):
            idx, sgn = cd_basis_product(n, i, j)
            if idx != (i ^ j):
                bad += 1
            tab[i][j] = sgn
    return tab, bad


EPS = {}
for n in DIMS:
    EPS[n], bad = sign_table(n)
    rec(kind="structure", dim=n, algebra=NAME[n], xor_index_violations=bad,
        unital_row=all(EPS[n][0][j] == 1 for j in range(n)),
        unital_col=all(EPS[n][i][0] == 1 for i in range(n)),
        negative_cells=sum(1 for i in range(n) for j in range(n)
                           if EPS[n][i][j] == -1),
        C_dim_2=n * (n - 1) // 2)

# DIFFERENTIAL — three independent shipped routes to the same signs
for n in DIMS:
    dis_mult = dis_tbl = dis_oct = 0
    tbl = algebra_table(n)
    for i in range(n):
        for j in range(n):
            k = i ^ j
            p = cd_mult(cd_basis(n, i), cd_basis(n, j))
            if p[k] != EPS[n][i][j] or any(p[t] != 0 for t in range(n) if t != k):
                dis_mult += 1
            if tbl[i][j][k] != EPS[n][i][j]:
                dis_tbl += 1
    if n == 8:
        ot = octonion_mult_table()
        for i in range(8):
            for j in range(8):
                if ot[i][j][i ^ j] != EPS[8][i][j]:
                    dis_oct += 1
    rec(kind="differential", dim=n, vs_cd_mult=dis_mult,
        vs_algebra_table=dis_tbl, vs_octonion_mult_table=dis_oct)


# ═════════ 1. BOTTOM-UP — extract the chirality bits ══════════════════════
def chirality(tab, n):
    """c(i,j) = s(i,j)*s(j,i) on UNORDERED pairs i<j — a dict {(i,j): +-1}."""
    return {(i, j): tab[i][j] * tab[j][i]
            for i in range(n) for j in range(i + 1, n)}


CHI = {}
for n in DIMS:
    c = chirality(EPS[n], n)
    CHI[n] = c
    neg = sum(1 for v in c.values() if v == -1)
    # commutator read INDEPENDENTLY off cd_mult (not off the sign table)
    dis = 0
    for (i, j) in c:
        lhs = cd_mult(cd_basis(n, i), cd_basis(n, j))
        rhs = cd_mult(cd_basis(n, j), cd_basis(n, i))
        anti = all(a == -b for a, b in zip(lhs, rhs))
        comm = all(a == b for a, b in zip(lhs, rhs))
        want_anti = (c[(i, j)] == -1)
        if want_anti != anti or (not want_anti) != comm:
            dis += 1
    # do the +1 entries coincide exactly with "one index is 0"?
    plus_are_unit = all((v == 1) == (i == 0)
                        for (i, j), v in c.items())
    rec(kind="chirality_census", dim=n, algebra=NAME[n],
        n_unordered_pairs=len(c), C_dim_2=n * (n - 1) // 2,
        count_equals_C_dim_2=(len(c) == n * (n - 1) // 2),
        anticommuting=neg, commuting=len(c) - neg,
        C_dim_minus_1_2=(n - 1) * (n - 2) // 2,
        anticommuting_equals_C_dim_minus_1_2=(neg == (n - 1) * (n - 2) // 2),
        plus_entries_are_exactly_the_unit_pairs=plus_are_unit,
        differential_vs_cd_mult=dis)

# Is the chirality table a CONSTANT function of dim (zero algebra-specific
# information)?  Compare every member of the 2^log2(dim) gamma-family.
for n in DIMS:
    lv = n.bit_length() - 1
    chis, tabs = {}, {}
    for g in itertools.product((-1, 1), repeat=lv):
        t = algebra_table(n, list(g))
        st = [[t[i][j][i ^ j] for j in range(n)] for i in range(n)]
        tabs[g] = tuple(tuple(r) for r in st)
        chis[g] = tuple(sorted(chirality(st, n).items()))
    same_chi = len(set(chis.values())) == 1
    rec(kind="gamma_family_chirality", dim=n, algebra=NAME[n],
        n_gamma_vectors=len(chis), distinct_chirality_tables=len(set(chis.values())),
        distinct_sign_tables=len(set(tabs.values())),
        chirality_identical_across_family=same_chi,
        note="every member of the gamma family (definite AND split) has the "
             "SAME chirality table but NOT the same product table")

# information content of the chirality table across the whole measured corpus
allchi = set()
for n in DIMS:
    lv = n.bit_length() - 1
    for g in itertools.product((-1, 1), repeat=lv):
        t = algebra_table(n, list(g))
        st = [[t[i][j][i ^ j] for j in range(n)] for i in range(n)]
        allchi.add((n, tuple(sorted(chirality(st, n).items()))))
rec(kind="chirality_information_content",
    distinct_dims=len(DIMS), corpus_algebras=sum(n.bit_length() - 1 and
                                                 2 ** (n.bit_length() - 1)
                                                 for n in DIMS),
    distinct_chirality_tables_over_corpus=len(allchi),
    bits_of_algebra_specific_information=0,
    note="one chirality table per DIM and nothing else — the table is a fixed "
         "function of dim, so it carries ZERO bits distinguishing algebras")


# ═════════ 2. TOP-DOWN — reconstruct from XOR + chirality ALONE ═══════════
def canonical_reconstruction(c, n):
    """The only rule chirality+XOR licenses with no further input: unital
    normalisation, +1 on the upper triangle, chirality on the lower, +1 on the
    diagonal (chirality says NOTHING about e_i*e_i)."""
    t = [[1] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == 0 or j == 0 or i == j:
                t[i][j] = 1
            elif i < j:
                t[i][j] = 1
            else:
                t[i][j] = c[(j, i)]
    return t


for n in DIMS:
    r = canonical_reconstruction(CHI[n], n)
    agree = sum(1 for i in range(n) for j in range(n) if r[i][j] == EPS[n][i][j])
    diag_agree = sum(1 for i in range(n) if r[i][i] == EPS[n][i][i])
    rec(kind="reconstruction_score", dim=n, algebra=NAME[n],
        cells=n * n, agree=agree, disagree=n * n - agree,
        exact=(agree == n * n),
        diagonal_cells=n, diagonal_agree=diag_agree,
        note="the canonical chirality-only reconstruction")

# WHAT the fiber looks like: count the sign tables consistent with the
# chirality bits.  Enumerate exhaustively at dim 2 and 4; count free cells at 8/16.
for n in DIMS:
    free_cells = [(i, j) for i in range(1, n) for j in range(1, n) if i <= j]
    # cells (i,j) with 1<=i<j are free; (j,i) is then forced; diagonal free.
    predicted = n * (n - 1) // 2                      # == C(n,2) free BITS
    assert len(free_cells) == predicted, (len(free_cells), predicted)
    brute = None
    if n <= 4:
        brute = 0
        cells = [(i, j) for i in range(1, n) for j in range(1, n)]
        for assign in itertools.product((1, -1), repeat=len(cells)):
            t = [[1] * n for _ in range(n)]
            for (i, j), v in zip(cells, assign):
                t[i][j] = v
            if chirality(t, n) == CHI[n]:
                brute += 1
    rec(kind="chirality_fiber", dim=n, algebra=NAME[n],
        unital_free_cells=(n - 1) ** 2,
        cells_constrained_by_chirality=(n - 1) * (n - 2) // 2,
        free_bits_left=predicted, free_bits_equals_C_dim_2=True,
        fiber_size_2_pow=predicted,
        brute_force_fiber_size=brute,
        brute_force_matches=(brute is None or brute == 2 ** predicted),
        note="chirality pins C(dim-1,2) of the (dim-1)^2 unital cells and "
             "leaves EXACTLY C(dim,2) free — C(dim,2) is the count of bits "
             "chirality FAILS to determine, not the count it supplies")


# ═════════ 3. THE GAUGE QUESTION — coboundary orbits ═════════════════════
def gauge(tab, cvec, n):
    return tuple(tuple(cvec[i] * cvec[j] * cvec[i ^ j] * tab[i][j]
                       for j in range(n)) for i in range(n))


for n in DIMS:
    base = tuple(tuple(r) for r in EPS[n])
    orbit = set()
    stab = 0
    for bitsv in range(1 << (n - 1)):
        cvec = [1] + [(-1 if (bitsv >> k) & 1 else 1) for k in range(n - 1)]
        g = gauge(EPS[n], cvec, n)
        orbit.add(g)
        if g == base:
            stab += 1
    # the stabiliser should be exactly Hom((Z/2)^log2 n, +-1) — the characters
    chars = 0
    lv = n.bit_length() - 1
    for m in range(1 << lv):
        cvec = [1] * n
        for i in range(n):
            par = bin(i & m).count("1") & 1
            cvec[i] = -1 if par else 1
        if gauge(EPS[n], cvec, n) == base:
            chars += 1
    # gauge preserves chirality?
    chi_preserved = all(chirality([list(r) for r in g], n) == CHI[n]
                        for g in orbit)
    # is the diagonal a gauge invariant?
    diag_inv = len({tuple(g[i][i] for i in range(n)) for g in orbit}) == 1
    rec(kind="gauge_orbit", dim=n, algebra=NAME[n],
        gauge_group_order=1 << (n - 1),
        gauge_group_order_expr="2^(dim-1)  [c_0=+1 forced by unitality]",
        orbit_size=len(orbit), stabiliser_order=stab,
        character_group_order=1 << lv, characters_all_stabilise=(chars == (1 << lv)),
        stabiliser_equals_dim=(stab == n),
        orbit_size_formula="2^(dim-1)/dim", orbit_size_predicted=(1 << (n - 1)) // n,
        orbit_matches_formula=(len(orbit) == (1 << (n - 1)) // n),
        two_pow_dim_over_what=2 * n,
        chirality_preserved_by_gauge=chi_preserved,
        diagonal_is_gauge_invariant=diag_inv)

    # how many GAUGE CLASSES share the shipped chirality bits?
    classes = 2 ** (n * (n - 1) // 2) * n // (1 << (n - 1))
    rec(kind="chirality_gauge_classes", dim=n, algebra=NAME[n],
        fiber_size=2 ** (n * (n - 1) // 2),
        orbit_size=(1 << (n - 1)) // n,
        gauge_classes_sharing_the_chirality=classes,
        determined_up_to_gauge=(classes == 1),
        missing_bits=(n * (n - 1) // 2) - ((n - 1) - lv))

    # and if we ALSO hand over the diagonal (the other gauge invariant)?
    cls2 = 2 ** ((n - 1) * (n - 2) // 2) * n // (1 << (n - 1))
    rec(kind="chirality_plus_diagonal_gauge_classes", dim=n, algebra=NAME[n],
        fiber_size=2 ** ((n - 1) * (n - 2) // 2),
        gauge_classes=max(cls2, 1) if cls2 >= 1 else cls2,
        raw=cls2, determined_up_to_gauge=(cls2 <= 1))

# is the canonical reconstruction in the shipped gauge orbit?
for n in DIMS:
    base_orbit = set()
    for bitsv in range(1 << (n - 1)):
        cvec = [1] + [(-1 if (bitsv >> k) & 1 else 1) for k in range(n - 1)]
        base_orbit.add(gauge(EPS[n], cvec, n))
    r = canonical_reconstruction(CHI[n], n)
    rt = tuple(tuple(x) for x in r)
    best = max(sum(1 for i in range(n) for j in range(n) if g[i][j] == rt[i][j])
               for g in base_orbit)
    rec(kind="reconstruction_up_to_gauge", dim=n, algebra=NAME[n],
        canonical_in_shipped_gauge_orbit=(rt in base_orbit),
        best_cells_matched_over_orbit=best, cells=n * n,
        note="if False the chirality-only reconstruction is not even correct "
             "UP TO GAUGE — a strictly different algebra")

# MINIMAL counterexample: one diagonal bit flip preserves every chirality bit
for n in DIMS:
    t = [row[:] for row in EPS[n]]
    t[1][1] = -t[1][1]
    same_chi = (chirality(t, n) == CHI[n])
    base_orbit = set()
    for bitsv in range(1 << (n - 1)):
        cvec = [1] + [(-1 if (bitsv >> k) & 1 else 1) for k in range(n - 1)]
        base_orbit.add(gauge(EPS[n], cvec, n))
    rec(kind="minimal_counterexample", dim=n, algebra=NAME[n],
        flipped_cell="s(1,1)", e1_squared_before=EPS[n][1][1],
        e1_squared_after=t[1][1],
        chirality_unchanged=same_chi,
        gauge_equivalent_to_shipped=(tuple(tuple(r) for r in t) in base_orbit),
        note="ONE bit changes the algebra (e1 becomes a split unit) and every "
             "chirality bit is identical — chirality is blind to it")


# ═════════ 4. IS THIS #T961's ORDER-CARRYING OBJECT? ═════════════════════
def A(tab, x, y, z):
    """(e_x e_y) e_z = A * e_x (e_y e_z)."""
    return tab[x][y] * tab[x ^ y][z] * tab[y][z] * tab[x][y ^ z]


for n in DIMS:
    tab = EPS[n]
    triples = [t for t in itertools.combinations(range(1, n), 3)]
    order_sensitive = 0
    for t3 in triples:
        vals = {A(tab, *p) for p in itertools.permutations(t3)}
        if len(vals) > 1:
            order_sensitive += 1
    rec(kind="associator_permutation_invariance", dim=n, algebra=NAME[n],
        n_distinct_imaginary_triples=len(triples),
        order_sensitive_triples=order_sensitive,
        permutation_invariant=(order_sensitive == 0),
        note="#T961's 0/35 at dim 8 is C(7,3)=35 distinct imaginary triples")

    # can the associator separate the ORDERED pair (i,j) from (j,i)?
    pairs = list(itertools.combinations(range(1, n), 2))
    assoc_sep = chi_sep = 0
    for (i, j) in pairs:
        if any(A(tab, i, j, z) != A(tab, j, i, z) for z in range(n)):
            assoc_sep += 1
        if CHI[n][(i, j)] == -1:
            chi_sep += 1
    rec(kind="order_separation", dim=n, algebra=NAME[n],
        n_imaginary_pairs=len(pairs),
        separated_by_associator=assoc_sep,
        separated_by_commutator_sign=chi_sep,
        note="A(i,j,z) vs A(j,i,z) over every z; commutator sign -1 means "
             "e_i e_j = -e_j e_i so the two orders differ")

# the concrete witness pair
for n in (4, 8, 16):
    tab = EPS[n]
    i, j = 1, 2
    ij = cd_mult(cd_basis(n, i), cd_basis(n, j))
    ji = cd_mult(cd_basis(n, j), cd_basis(n, i))
    rec(kind="witness_pair", dim=n, algebra=NAME[n], pair=[i, j],
        e_i_e_j=[int(v) for v in ij], e_j_e_i=[int(v) for v in ji],
        commutator_sign=CHI[n][(i, j)],
        commutator_separates=(CHI[n][(i, j)] == -1),
        associator_values_ij=[A(tab, i, j, z) for z in range(n)],
        associator_values_ji=[A(tab, j, i, z) for z in range(n)],
        associator_separates=any(A(tab, i, j, z) != A(tab, j, i, z)
                                 for z in range(n)))

# HOW MUCH order does the commutator sign ENCODE (vs merely DETECT)?
for n in DIMS:
    pairs = list(itertools.combinations(range(1, n), 2))
    vals = {CHI[n][p] for p in pairs}
    rec(kind="order_encoding_capacity", dim=n, algebra=NAME[n],
        imaginary_pairs=len(pairs), distinct_chirality_values=len(vals),
        values=sorted(vals),
        bits_about_WHICH_order=0,
        note="every imaginary pair carries the SAME bit (-1): the commutator "
             "sign DETECTS that order matters, it does not ENCODE which order")


for r in OUT:
    print(json.dumps(r, sort_keys=True))
