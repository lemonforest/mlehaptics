#!/usr/bin/env python3
"""LANE 2 SUPPLEMENT — name the MISSING object, in bits, over GF(2).

The main lane measured that the chirality bits do NOT reconstruct the product.
This supplement decomposes the gauge-invariant content of the shipped sign table
into DEGREE strata and shows which stratum chirality covers.

Ranks are taken with the SHIPPED srmech GF(2) op ``gf_rref`` (rc350) — not a
hand-rolled elimination.
"""
import json
import itertools
import random

from srmech.amsc.cascade.cayley_dickson import cd_basis_product
from srmech.amsc.modular_linalg import gf_rref

OUT = []


def rec(**kw):
    OUT.append(kw)


DIMS = [2, 4, 8, 16]
NAME = {2: "C", 4: "H", 8: "O", 16: "S(sedenion)"}


def sign_table(n):
    return [[cd_basis_product(n, i, j)[1] for j in range(n)] for i in range(n)]


EPS = {n: sign_table(n) for n in DIMS}

# ── the coboundary map delta over GF(2) ───────────────────────────────────
# additive coordinates: s(i,j) = (-1)^S[i][j];  (delta c)(i,j) = c_i+c_j+c_{i^j}
# domain: c_1..c_{n-1}  (c_0 = 0 forced by unitality)
# codomain: the (n-1)^2 unital cells (i,j), i,j >= 1
for n in DIMS:
    cells = [(i, j) for i in range(1, n) for j in range(1, n)]
    rows = []
    for k in range(1, n):                     # basis vector c_k = 1
        row = []
        for (i, j) in cells:
            v = (1 if i == k else 0) + (1 if j == k else 0) + \
                (1 if (i ^ j) == k else 0)
            row.append(v % 2)
        rows.append(row)
    res = gf_rref(rows, 2)
    lv = n.bit_length() - 1
    total = (n - 1) ** 2
    coboundary_rank = res["rank"]
    quotient = total - coboundary_rank
    rec(kind="gf2_coboundary_rank", dim=n, algebra=NAME[n],
        total_unital_sign_bits=total,
        coboundary_rank=coboundary_rank,
        coboundary_rank_formula="(dim-1) - log2(dim)",
        coboundary_rank_predicted=(n - 1) - lv,
        matches=(coboundary_rank == (n - 1) - lv),
        gauge_invariant_bits=quotient,
        kernel_of_delta=(n - 1) - coboundary_rank,
        kernel_is_the_character_group=((n - 1) - coboundary_rank == lv),
        note="the kernel of delta is Hom((Z/2)^log2 dim, +-1) minus the unit — "
             "log2(dim) free bits, i.e. |characters| = dim")

    # DEGREE STRATA of the gauge-invariant content
    deg1 = n - 1                              # q(i) = s(i,i), i >= 1
    deg2 = (n - 1) * (n - 2) // 2             # beta(i,j) = s(i,j)s(j,i), i<j
    rec(kind="degree_strata", dim=n, algebra=NAME[n],
        gauge_invariant_bits=quotient,
        degree1_square_bits=deg1,
        degree2_chirality_bits=deg2,
        degree1_plus_degree2=deg1 + deg2,
        residual_bits=quotient - deg1 - deg2,
        chirality_share=f"{deg2}/{quotient}",
        chirality_share_pct=round(100.0 * deg2 / quotient, 1) if quotient else None,
        note="what the CHIRALITY BITS cover of the gauge-invariant content")


# ── dim 4 EXHAUSTIVE: is (q, beta, A) a complete gauge invariant? ─────────
def A_of(tab, n, x, y, z):
    return tab[x][y] * tab[x ^ y][z] * tab[y][z] * tab[x][y ^ z]


def invariants(tab, n, degrees):
    q = tuple(tab[i][i] for i in range(n))
    b = tuple(tab[i][j] * tab[j][i] for i in range(n) for j in range(i + 1, n))
    a = tuple(A_of(tab, n, x, y, z)
              for x in range(n) for y in range(n) for z in range(n))
    out = []
    if 1 in degrees:
        out.append(q)
    if 2 in degrees:
        out.append(b)
    if 3 in degrees:
        out.append(a)
    return tuple(out)


def gauge_orbit(tab, n):
    orb = set()
    for bitsv in range(1 << (n - 1)):
        c = [1] + [(-1 if (bitsv >> k) & 1 else 1) for k in range(n - 1)]
        orb.add(tuple(tuple(c[i] * c[j] * c[i ^ j] * tab[i][j]
                            for j in range(n)) for i in range(n)))
    return orb


n = 4
cells = [(i, j) for i in range(1, n) for j in range(1, n)]
tables = []
for assign in itertools.product((1, -1), repeat=len(cells)):
    t = [[1] * n for _ in range(n)]
    for (i, j), v in zip(cells, assign):
        t[i][j] = v
    tables.append(t)
seen = {}
for t in tables:
    seen.setdefault(tuple(tuple(r) for r in t), None)
orbits = []
todo = set(seen)
while todo:
    t = next(iter(todo))
    orb = gauge_orbit([list(r) for r in t], n) & todo
    orbits.append(orb)
    todo -= orb
for degrees in ((2,), (1, 2), (1, 2, 3)):
    buckets = {}
    for orb in orbits:
        rep = [list(r) for r in next(iter(orb))]
        key = invariants(rep, n, degrees)
        # invariant must be constant on the orbit
        assert all(invariants([list(r) for r in m], n, degrees) == key
                   for m in orb)
        buckets.setdefault(key, []).append(orb)
    rec(kind="dim4_invariant_completeness", dim=4, algebra="H",
        degrees=list(degrees), n_unital_tables=len(tables),
        n_gauge_classes=len(orbits),
        n_distinct_invariant_values=len(buckets),
        max_classes_sharing_one_value=max(len(v) for v in buckets.values()),
        complete=(len(buckets) == len(orbits)),
        note="degrees 1=square 2=chirality 3=associator cochain")

# ── dim 8: does the associator cochain discriminate inside the (q,beta) fiber?
n = 8
random.seed(20260728)
base = EPS[8]
base_q = tuple(base[i][i] for i in range(n))
base_b = tuple(base[i][j] * base[j][i] for i in range(n) for j in range(i + 1, n))
base_A = tuple(A_of(base, n, x, y, z)
               for x in range(n) for y in range(n) for z in range(n))
free = [(i, j) for i in range(1, n) for j in range(i + 1, n)]   # C(7,2)=21 free
N = 20000
match_A = 0
distinct_A = set()
for _ in range(N):
    t = [row[:] for row in base]
    for (i, j) in free:
        if random.getrandbits(1):
            t[i][j] = -t[i][j]
            t[j][i] = -t[j][i]      # keep beta; diagonal untouched keeps q
    assert tuple(t[i][i] for i in range(n)) == base_q
    assert tuple(t[i][j] * t[j][i]
                 for i in range(n) for j in range(i + 1, n)) == base_b
    a = tuple(A_of(t, n, x, y, z)
              for x in range(n) for y in range(n) for z in range(n))
    distinct_A.add(a)
    if a == base_A:
        match_A += 1
rec(kind="dim8_associator_discrimination", dim=8, algebra="O",
    samples=N, fiber_of_q_and_beta=2 ** 21,
    samples_matching_shipped_associator=match_A,
    distinct_associator_cochains_seen=len(distinct_A),
    note="random members of the (square, chirality) fiber — the associator "
         "cochain almost never agrees, so the residual 17 bits at dim 8 are "
         "DEGREE-3 content the chirality bits cannot reach")

for r in OUT:
    print(json.dumps(r, sort_keys=True))
