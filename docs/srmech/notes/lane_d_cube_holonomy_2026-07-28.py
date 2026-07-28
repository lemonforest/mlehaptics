#!/usr/bin/env python3
"""LANE D — the 3-cube holonomy of the Cayley-Dickson sign cocycle, and the
DEGREE hypothesis (order / commutativity / associativity <-> degree 1/2/3).

Exact integers only: every quantity below is a product of +/-1 signs read off
the SHIPPED srmech cocycle `cd_basis_product`, differentially checked against
`cd_mult` on explicit basis vectors, `algebra_table` + `table_product`, and
`srmech.qm.octonion.octonion_mult_table`.  No floats anywhere.
"""
import json
import sys

from srmech.amsc.cascade.cayley_dickson import (
    cd_basis_product, cd_basis, cd_mult, algebra_table, table_product,
)
from srmech.qm.octonion import octonion_mult_table
from srmech.amsc import _native

OUT = []


def rec(**kw):
    OUT.append(kw)


DIMS = [1, 2, 4, 8, 16, 32, 64]
NAME = {1: "R", 2: "C", 4: "H", 8: "O", 16: "S(sedenion)", 32: "T(32)", 64: "P(64)"}

# ── the sign cocycle eps: e_x . e_y = eps[x][y] * e_{x XOR y} ────────────
EPS = {}
for n in DIMS:
    tab = [[0] * n for _ in range(n)]
    bad_index = 0
    for x in range(n):
        for y in range(n):
            idx, sgn = cd_basis_product(n, x, y)
            if idx != (x ^ y):
                bad_index += 1
            tab[x][y] = sgn
    EPS[n] = tab
    rec(kind="structure", dim=n, algebra=NAME[n],
        xor_index_violations=bad_index,
        normalised_left=all(tab[0][y] == 1 for y in range(n)),
        normalised_right=all(tab[x][0] == 1 for x in range(n)))

# ── DIFFERENTIAL: three independent shipped routes to the same eps ──────
for n in DIMS:
    dis_mult = dis_tbl = dis_oct = 0
    tbl = algebra_table(n)
    for x in range(n):
        for y in range(n):
            k = x ^ y
            # route 2: cd_mult on explicit basis vectors
            p = cd_mult(cd_basis(n, x), cd_basis(n, y))
            if p[k] != EPS[n][x][y] or any(p[t] != 0 for t in range(n) if t != k):
                dis_mult += 1
            # route 3: the rank-3 structure table
            if tbl[x][y][k] != EPS[n][x][y]:
                dis_tbl += 1
    if n == 8:
        ot = octonion_mult_table()
        for x in range(8):
            for y in range(8):
                if ot[x][y][x ^ y] != EPS[8][x][y]:
                    dis_oct += 1
    rec(kind="differential", dim=n,
        vs_cd_mult=dis_mult, vs_algebra_table=dis_tbl, vs_octonion_table=dis_oct)


def bits(n):
    return n.bit_length() - 1          # number of hypercube directions


# ── DEGREE 1 — q(x) = eps(x,x): the SQUARE.  Order loss (R -> C). ───────
for n in DIMS:
    q = [EPS[n][x][x] for x in range(n)]
    neg = sum(1 for v in q if v == -1)
    rec(kind="degree1_square", dim=n, algebra=NAME[n],
        n_cells=n, negative_squares=neg, positive_squares=n - neg,
        nontrivial=neg > 0,
        census=f"{n - neg}:{neg}")

# ── DEGREE 2a — beta(x,y) = eps(x,y)eps(y,x): the COMMUTATOR sign ───────
for n in DIMS:
    q = [EPS[n][x][x] for x in range(n)]
    neg = pol_ok = 0
    tot = 0
    for x in range(n):
        for y in range(n):
            b = EPS[n][x][y] * EPS[n][y][x]
            tot += 1
            if b == -1:
                neg += 1
            if b == q[x ^ y] * q[x] * q[y]:
                pol_ok += 1
    rec(kind="degree2_commutator", dim=n, algebra=NAME[n],
        pairs=tot, anticommuting=neg, nontrivial=neg > 0,
        polarisation_of_q_agreements=pol_ok, polarisation_exact=(pol_ok == tot))


# ── DEGREE 2b — the PLAQUETTE holonomy on 2-faces of the hypercube ──────
# right-transport connection U_i(v) = eps(v, 2^i); W_ij(v) = the 4-cycle
# v -> v+i -> v+i+j -> v+j -> v.
def W(n, v, i, j):
    ui, uj = 1 << i, 1 << j
    e = EPS[n]
    return e[v][ui] * e[v ^ ui][uj] * e[v ^ uj][ui] * e[v][uj]


for n in DIMS:
    d = bits(n)
    faces = nontriv = base0_eq_beta = const_in_v = 0
    pairs = [(i, j) for i in range(d) for j in range(i + 1, d)]
    for (i, j) in pairs:
        vals = [W(n, v, i, j) for v in range(n)]
        faces += n
        nontriv += sum(1 for w in vals if w == -1)
        b = EPS[n][1 << i][1 << j] * EPS[n][1 << j][1 << i]
        if vals[0] == b:
            base0_eq_beta += 1
        if len(set(vals)) == 1:
            const_in_v += 1
    rec(kind="degree2_plaquette", dim=n, algebra=NAME[n],
        n_direction_pairs=len(pairs), n_2faces=faces,
        nontrivial_2faces=nontriv, nontrivial=nontriv > 0,
        vacuous=(len(pairs) == 0),
        base0_equals_commutator=base0_eq_beta,
        plaquette_constant_over_basepoints=const_in_v)


# ── DEGREE 3a — the group-cochain coboundary = the ASSOCIATOR sign ──────
# (e_x e_y) e_z = A(x,y,z) * e_x (e_y e_z);  A = delta-eps.
def A(n, x, y, z):
    e = EPS[n]
    return e[x][y] * e[x ^ y][z] * e[y][z] * e[x][y ^ z]


for n in DIMS:
    d = bits(n)
    tot = neg = 0
    for x in range(n):
        for y in range(n):
            for z in range(n):
                tot += 1
                if A(n, x, y, z) == -1:
                    neg += 1
    # restricted to three DISTINCT bit-directions (the geometric 3-cube case)
    gen_tot = gen_neg = 0
    for i in range(d):
        for j in range(d):
            for k in range(d):
                if len({i, j, k}) == 3:
                    gen_tot += 1
                    if A(n, 1 << i, 1 << j, 1 << k) == -1:
                        gen_neg += 1
    rec(kind="degree3_associator_cochain", dim=n, algebra=NAME[n],
        triples=tot, nonassociative_triples=neg, nontrivial=neg > 0,
        generator_triples=gen_tot, nonassociative_generator_triples=gen_neg,
        generator_case_vacuous=(gen_tot == 0))

# associator differential: check A == -1 <=> (xy)z - x(yz) != 0 via cd_mult
for n in (4, 8, 16):
    dis = 0
    for x in range(n):
        for y in range(n):
            for z in range(n):
                lhs = cd_mult(cd_mult(cd_basis(n, x), cd_basis(n, y)), cd_basis(n, z))
                rhs = cd_mult(cd_basis(n, x), cd_mult(cd_basis(n, y), cd_basis(n, z)))
                zero = all(a == b for a, b in zip(lhs, rhs))
                if zero != (A(n, x, y, z) == 1):
                    dis += 1
    rec(kind="degree3_associator_differential", dim=n, disagreements_vs_cd_mult=dis)


# ── DEGREE 3b — the LATTICE 3-cube holonomy (product of the 6 faces) ────
for n in DIMS:
    d = bits(n)
    cubes = nontriv = 0
    trips = [(i, j, k) for i in range(d) for j in range(i + 1, d)
             for k in range(j + 1, d)]
    for (i, j, k) in trips:
        ui, uj, uk = 1 << i, 1 << j, 1 << k
        for v in range(n):
            B = (W(n, v, i, j) * W(n, v ^ uk, i, j)
                 * W(n, v, j, k) * W(n, v ^ ui, j, k)
                 * W(n, v, i, k) * W(n, v ^ uj, i, k))
            cubes += 1
            if B == -1:
                nontriv += 1
    rec(kind="degree3_cube_boundary", dim=n, algebra=NAME[n],
        n_direction_triples=len(trips), n_3cubes=cubes,
        nontrivial_3cubes=nontriv, nontrivial=nontriv > 0,
        vacuous=(len(trips) == 0))

# ── DEGREE 3c — the OPPOSITE-FACE difference H_ijk(v) = W_ij(v)W_ij(v+k) ─
for n in DIMS:
    d = bits(n)
    tot = neg = 0
    eq_assoc = 0
    trips = [(i, j, k) for i in range(d) for j in range(d) for k in range(d)
             if len({i, j, k}) == 3]
    for (i, j, k) in trips:
        uk = 1 << k
        for v in range(n):
            h = W(n, v, i, j) * W(n, v ^ uk, i, j)
            tot += 1
            if h == -1:
                neg += 1
            if v == 0 and h == A(n, 1 << i, 1 << j, 1 << k):
                eq_assoc += 1
    rec(kind="degree3_opposite_face", dim=n, algebra=NAME[n],
        n_oriented_triples=len(trips), n_values=tot,
        nontrivial=neg > 0, nontrivial_count=neg,
        base0_equals_generator_associator=eq_assoc,
        base0_cases=len(trips),
        vacuous=(len(trips) == 0))

# ── DOES ANY CUBICAL QUANTITY EQUAL THE ASSOCIATOR? exhaustive at dim 8 ──
for n in (8, 16):
    d = bits(n)
    trips = [(i, j, k) for i in range(d) for j in range(d) for k in range(d)
             if len({i, j, k}) == 3]
    rows = []
    for (i, j, k) in trips:
        ui, uj, uk = 1 << i, 1 << j, 1 << k
        a = A(n, ui, uj, uk)
        Bv = W(n, 0, i, j) * W(n, uk, i, j) * W(n, 0, j, k) * W(n, ui, j, k) \
            * W(n, 0, i, k) * W(n, uj, i, k)
        rows.append(dict(dirs=[i, j, k], associator=a,
                         cube_boundary=Bv,
                         opposite_face=W(n, 0, i, j) * W(n, uk, i, j)))
    rec(kind="cube_vs_associator", dim=n, algebra=NAME[n], rows=rows,
        cube_boundary_equals_associator=sum(
            1 for r in rows if r["cube_boundary"] == r["associator"]),
        opposite_face_equals_associator=sum(
            1 for r in rows if r["opposite_face"] == r["associator"]),
        n_rows=len(rows))

# ── ALTERNATIVITY / FLEXIBILITY — the O -> S rung as a SYMMETRY of A ────
for n in DIMS:
    left = right = flex = 0
    for x in range(n):
        for y in range(n):
            if A(n, x, x, y) == -1:
                left += 1
            if A(n, x, y, y) == -1:
                right += 1
            if A(n, x, y, x) == -1:
                flex += 1
    # total antisymmetry of A on distinct nonzero basis triples
    d = bits(n)
    alt_ok = alt_tot = 0
    for x in range(n):
        for y in range(n):
            for z in range(n):
                alt_tot += 1
                if A(n, x, y, z) == A(n, y, x, z) == A(n, x, z, y):
                    alt_ok += 1
    rec(kind="alternativity", dim=n, algebra=NAME[n],
        left_alternative_violations=left, right_alternative_violations=right,
        flexible_violations=flex,
        associator_alternating_agreements=alt_ok, triples=alt_tot,
        alternating=(alt_ok == alt_tot))

# ── PERIOD-4 CENSUS vs the PLAQUETTE 4-CYCLE ────────────────────────────
# order of e_i in the sign-extended CD loop (repeated multiplication).
for n in DIMS:
    orders = {}
    for i in range(n):
        cur = cd_basis(n, i)
        one = cd_basis(n, 0)
        k = 1
        while cur != one and k < 64:
            cur = cd_mult(cur, cd_basis(n, i))
            k += 1
        orders[i] = k
    hist = {}
    for k in orders.values():
        hist[k] = hist.get(k, 0) + 1
    rec(kind="period_census", dim=n, algebra=NAME[n],
        order_histogram=hist,
        ringing=sum(v for k, v in hist.items() if k == 4),
        non_ringing=sum(v for k, v in hist.items() if k == 1))

# lifted length of each closed index-walk class
for n in DIMS:
    d = bits(n)
    if d < 1:
        rec(kind="cycle_lift", dim=n, algebra=NAME[n], note="no directions")
        continue
    # class 1: the DEGENERATE 2-gon (one direction, twice)
    hol1 = EPS[n][0][1] * EPS[n][1][1] if n >= 2 else 1
    # holonomy of walk 0 -> u0 -> 0 by right-multiplying e_{u0} twice
    hol_2gon = EPS[n][0][1] * EPS[n][1][1]
    lifted_2gon = 2 if hol_2gon == 1 else 4
    if d >= 2:
        hol_square = W(n, 0, 0, 1)
        lifted_square = 4 if hol_square == 1 else 8
    else:
        hol_square = None
        lifted_square = None
    rec(kind="cycle_lift", dim=n, algebra=NAME[n],
        two_gon_index_length=2, two_gon_holonomy=hol_2gon,
        two_gon_lifted_length=lifted_2gon,
        square_index_length=(4 if d >= 2 else None),
        square_holonomy=hol_square, square_lifted_length=lifted_square)

# is the plaquette DERIVABLE from the period-4 census?  beta = polarisation q
for n in DIMS:
    d = bits(n)
    if d < 2:
        rec(kind="plaquette_from_period", dim=n, algebra=NAME[n], vacuous=True)
        continue
    q = [EPS[n][x][x] for x in range(n)]
    ok = tot = 0
    for i in range(d):
        for j in range(d):
            if i == j:
                continue
            ui, uj = 1 << i, 1 << j
            for v in range(n):
                tot += 1
                pred = q[ui ^ uj] * q[ui] * q[uj]
                if W(n, v, i, j) == pred:
                    ok += 1
    rec(kind="plaquette_from_period", dim=n, algebra=NAME[n],
        agreements=ok, cases=tot, exact=(ok == tot))

rec(kind="provenance", srmech_version=__import__("srmech").__version__,
    has_native=_native.HAS_NATIVE,
    lib=str(getattr(_native, "LIB_PATH", getattr(_native, "_LIB_PATH", "n/a"))),
    python=sys.version.split()[0])

for r in OUT:
    print(json.dumps(r, sort_keys=True))
