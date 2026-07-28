#!/usr/bin/env python3
"""LANE D supplement — why the cubical degree-3 reading is trivial, where the
associator actually lives, and the gauge layer.  Exact integers only."""
import json
import sys
from itertools import product

from srmech.amsc.cascade.cayley_dickson import cd_basis_product

OUT = []


def rec(**kw):
    OUT.append(kw)


DIMS = [2, 4, 8, 16, 32]
NAME = {1: "R", 2: "C", 4: "H", 8: "O", 16: "S(sedenion)", 32: "T(32)"}
EPS = {}
for n in DIMS:
    EPS[n] = [[cd_basis_product(n, x, y)[1] for y in range(n)] for x in range(n)]


def A(n, x, y, z):
    e = EPS[n]
    return e[x][y] * e[x ^ y][z] * e[y][z] * e[x][y ^ z]


def bits(n):
    return n.bit_length() - 1


# ── 1. RIGHT vs LEFT vs ADJOINT connection: is any plaquette base-dependent? ─
def W_right(n, v, g, h):
    e = EPS[n]
    return e[v][g] * e[v ^ g][h] * e[v ^ h][g] * e[v][h]


def W_left(n, v, g, h):
    e = EPS[n]
    return e[g][v] * e[h][v ^ g] * e[g][v ^ h] * e[h][v]


for n in DIMS:
    d = bits(n)
    gens = [1 << i for i in range(d)]
    res = {}
    for label, gset in (("generators", gens), ("all_nonzero", list(range(1, n)))):
        for cname, Wf in (("right", W_right), ("left", W_left)):
            varying = pairs = 0
            for g in gset:
                for h in gset:
                    if g == h:
                        continue
                    pairs += 1
                    vals = {Wf(n, v, g, h) for v in range(n)}
                    if len(vals) > 1:
                        varying += 1
            res[f"{label}_{cname}_basepoint_varying"] = varying
            res[f"{label}_{cname}_pairs"] = pairs
    rec(kind="plaquette_basepoint_dependence", dim=n, algebra=NAME[n], **res)

# ── 2. When the generalised plaquette DOES vary, is the variation the ────────
#      alternativity defect A(v,g,h)*A(v,h,g)?
for n in DIMS:
    ok = tot = 0
    for v in range(n):
        for g in range(1, n):
            for h in range(1, n):
                if g == h:
                    continue
                beta = EPS[n][g][h] * EPS[n][h][g]
                pred = A(n, v, g, h) * A(n, v, h, g) * beta
                tot += 1
                if W_right(n, v, g, h) == pred:
                    ok += 1
    rec(kind="plaquette_equals_assoc_pair_times_commutator", dim=n,
        algebra=NAME[n], agreements=ok, cases=tot, exact=(ok == tot))

# ── 3. The associator needs a DIAGONAL step: eps(x, y XOR z).  Count how ────
#      many nonassociative generator-triples have y XOR z a hypercube edge.
for n in DIMS:
    d = bits(n)
    gens = [1 << i for i in range(d)]
    diag = 0
    for g, h, k in product(gens, repeat=3):
        if len({g, h, k}) != 3:
            continue
        if A(n, g, h, k) == -1:
            # y XOR z = h^k is never a generator when h != k
            if (h ^ k) in gens:
                diag += 1
    rec(kind="associator_needs_diagonal", dim=n, algebra=NAME[n],
        nonassoc_generator_triples_whose_second_leg_is_an_edge=diag,
        note="h XOR k is a 2-bit weight => never a hypercube edge")

# ── 4. The SIMPLEX reading: delta-eps as the alternating product over the ────
#      four 2-faces of the tetrahedron (0, x, x+y, x+y+z) in the bar complex.
for n in DIMS:
    ok = tot = 0
    for x in range(n):
        for y in range(n):
            for z in range(n):
                e = EPS[n]
                # the four 2-simplices of the bar complex
                f0 = e[y][z]            # d0: drop x
                f1 = e[x][y ^ z]        # d1: merge y,z
                f2 = e[x ^ y][z]        # d2: merge x,y
                f3 = e[x][y]            # d3: drop z
                tot += 1
                if f0 * f1 * f2 * f3 == A(n, x, y, z):
                    ok += 1
    rec(kind="tetrahedron_face_product_is_associator", dim=n, algebra=NAME[n],
        agreements=ok, cases=tot, exact=(ok == tot))

# ── 5. GAUGE: regauge e_x -> s(x) e_x.  What survives? ──────────────────────
#      eps'(x,y) = s(x)s(y)/s(x^y) * eps(x,y)  (s(0)=+1)
import random
random.seed(20260728)
for n in DIMS:
    trials = 64
    edge_changed = q_changed = beta_changed = assoc_changed = plaq_changed = 0
    d = bits(n)
    gens = [1 << i for i in range(d)]
    for _ in range(trials):
        s = [1] + [random.choice((1, -1)) for _ in range(n - 1)]
        e2 = [[s[x] * s[y] * s[x ^ y] * EPS[n][x][y] for y in range(n)]
              for x in range(n)]

        def A2(x, y, z):
            return e2[x][y] * e2[x ^ y][z] * e2[y][z] * e2[x][y ^ z]

        if any(e2[v][g] != EPS[n][v][g] for v in range(n) for g in gens):
            edge_changed += 1
        if any(e2[x][x] != EPS[n][x][x] for x in range(n)):
            q_changed += 1
        if any(e2[x][y] * e2[y][x] != EPS[n][x][y] * EPS[n][y][x]
               for x in range(n) for y in range(n)):
            beta_changed += 1
        if any(A2(x, y, z) != A(n, x, y, z)
               for x in range(n) for y in range(n) for z in range(n)):
            assoc_changed += 1
        chg = False
        for g in gens:
            for h in gens:
                if g == h:
                    continue
                for v in range(n):
                    w2 = e2[v][g] * e2[v ^ g][h] * e2[v ^ h][g] * e2[v][h]
                    if w2 != W_right(n, v, g, h):
                        chg = True
        if chg:
            plaq_changed += 1
    rec(kind="gauge_invariance", dim=n, algebra=NAME[n], regaugings=trials,
        edge_weight_changed=edge_changed, square_q_changed=q_changed,
        commutator_beta_changed=beta_changed,
        plaquette_changed=plaq_changed, associator_changed=assoc_changed)

# ── 6. ALGEBRAIC NORMAL FORM of eps over F2 — is "degree" literal? ──────────
#      (hand-rolled Reed-Muller/Moebius transform; NO srmech surface exists.)
for n in DIMS:
    d = bits(n)
    nv = 2 * d
    f = [0] * (1 << nv)
    for x in range(n):
        for y in range(n):
            f[x | (y << d)] = 0 if EPS[n][x][y] == 1 else 1
    a = f[:]
    for i in range(nv):
        step = 1 << i
        for j in range(1 << nv):
            if j & step:
                a[j] ^= a[j ^ step]
    terms = [m for m in range(1 << nv) if a[m]]
    degs = [bin(m).count("1") for m in terms]
    rec(kind="anf_of_eps", dim=n, algebra=NAME[n], n_variables=nv,
        n_monomials=len(terms), max_degree=(max(degs) if degs else 0),
        degree_histogram={str(k): degs.count(k) for k in sorted(set(degs))})

for r in OUT:
    print(json.dumps(r, sort_keys=True))
