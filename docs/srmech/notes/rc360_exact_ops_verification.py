"""rc360 — measure every shipped-prose number. Exact ints only.

Run:  python rc360_exact_ops_verification.py rc360_exact_ops_verification.ndjson

WHAT THIS COVERS THAT THE SUITE DOES NOT. `tests/test_associator_control_gf_solve_
rc360.py` re-measures dim 4 / 8 / 16 in-suite; this script is the out-of-band home
for the ONE number too slow to re-run per-suite (the dim-32 associativity census,
32768 ordered triples x two exact-Q products) and for the full per-pair /
per-twist tables the CHANGELOG quotes as ranges.

⚠️ THE DRAWN CONTROL IS GONE. An earlier revision of this script measured
`random_anticommutative_table`, whose signs were a SHA-256 draw. That op was
dropped before release: a control drawn from a structureless hash tests
GENERICITY, not structure, and a uniform +-1 draw is the abandoned alphabet --
srmech's resonant alphabet is TERNARY {-1, 0, +1} (`hdc.polar_random`), where the
0 is the rest / non-ringing value. The three controls measured below are each a
single NAMED perturbation with no draw anywhere.
"""
import itertools
import json
import sys

import srmech
from srmech.amsc import _native
from srmech.amsc.cascade import (algebra_table, associator, cd_basis,
                                 inertia_signature)

print("ARTIFACT UNDER TEST:", srmech.__file__, srmech.__version__,
      "HAS_NATIVE=%s" % _native.HAS_NATIVE, flush=True)

OUT = []


def emit(**kw):
    OUT.append(kw)
    print(json.dumps(kw), flush=True)


def flex_violations(dim, table):
    """Linearised flexible law (x,y,z)+(z,y,x)=0 over the dim**3 triples."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any((u + v) != 0 for u, v in
                      zip(associator(basis[i], basis[j], basis[k], table=table),
                          associator(basis[k], basis[j], basis[i], table=table))))


def nonassoc(dim, table):
    basis = [cd_basis(dim, i) for i in range(dim)]
    return sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
               if any(v != 0 for v in associator(basis[i], basis[j], basis[k],
                                                 table=table)))


def flip_pair(dim, i, j):
    """CONTROL 2 — negate e_i.e_j and e_j.e_i on the ladder. One NAMED bit."""
    table = [[list(row) for row in plane] for plane in algebra_table(dim)]
    lane = i ^ j
    table[i][j][lane] = -table[i][j][lane]
    table[j][i][lane] = -table[j][i][lane]
    return table


def group_ring(dim):
    """CONTROL 3 — R[Z/dim], the WRONG QUOTIENT: lane (i+j) mod dim, signs +1."""
    table = [[[0] * dim for _ in range(dim)] for _ in range(dim)]
    for i in range(dim):
        for j in range(dim):
            table[i][j][(i + j) % dim] = 1
    return table


def sig(table):
    return list(inertia_signature(table)["signature"])


# -- 1. the ladder is flexible at every rung we can reach ---------------
for dim in (2, 4, 8, 16):
    emit(claim="ladder_flexible", dim=dim,
         violations=flex_violations(dim, algebra_table(dim)), total=dim ** 3,
         signature=sig(algebra_table(dim)))

# -- 2. CONTROL 1: all eight gamma-twists at dim 8 ----------------------
# Backs the CHANGELOG claim that the gamma family has ZERO bite on the
# associativity laws (all flexible, all nonassoc 168) and full bite on the
# METRIC (signatures split 7:1, only (-1,-1,-1) = the default ladder at (1,7,0)).
tw = {}
for g in itertools.product((1, -1), repeat=3):
    key = "".join("+" if v == 1 else "-" for v in g)
    t = algebra_table(8, list(g))
    tw[key] = {"flex": flex_violations(8, t), "nonassoc": nonassoc(8, t),
               "signature": sig(t)}
emit(claim="gamma_family_dim8", n_twists=len(tw), by_twist=tw, total=8 ** 3,
     all_flexible=all(v["flex"] == 0 for v in tw.values()),
     distinct_nonassoc=sorted({v["nonassoc"] for v in tw.values()}),
     distinct_signatures=sorted({tuple(v["signature"]) for v in tw.values()}),
     definite_twists=[k for k, v in tw.items() if v["signature"] == [1, 7, 0]])

# -- 3. CONTROL 2: ONE named sign flip -- the ONLY flexibility control --
for dim, pairs in ((4, [(i, j) for i in range(1, 4) for j in range(i + 1, 4)]),
                   (8, [(i, j) for i in range(1, 8) for j in range(i + 1, 8)]),
                   (16, [(1, 2)])):
    rows = {}
    for (i, j) in pairs:
        t = flip_pair(dim, i, j)
        rows["%d,%d" % (i, j)] = {"flex": flex_violations(dim, t),
                                  "nonassoc": nonassoc(dim, t),
                                  "signature": sig(t)}
    emit(claim="named_flip_control", dim=dim, total=dim ** 3, n_pairs=len(pairs),
         by_pair=rows,
         distinct=sorted({(v["flex"], v["nonassoc"], tuple(v["signature"]))
                          for v in rows.values()}),
         all_break_flexibility=all(v["flex"] > 0 for v in rows.values()),
         signature_unchanged=all(v["signature"] == sig(algebra_table(dim))
                                 for v in rows.values()))

# -- 4. CONTROL 3: R[Z/dim], and the TAUTOLOGY it invites ---------------
for dim in (2, 4, 8, 16):
    ring, ladder = group_ring(dim), algebra_table(dim)
    basis = [cd_basis(dim, i) for i in range(dim)]
    differs = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
                  if associator(basis[i], basis[j], basis[k], table=ladder)
                  != associator(basis[i], basis[j], basis[k], table=ring))
    la_nonassoc = nonassoc(dim, ladder)
    emit(claim="wrong_quotient_control", dim=dim, total=dim ** 3,
         ring_flex=flex_violations(dim, ring), ring_nonassoc=nonassoc(dim, ring),
         ring_signature=sig(ring), ladder_signature=sig(ladder),
         # THE TAUTOLOGY, recorded as one: the ring's defect is identically 0,
         # so "differs from ladder" IS the ladder's own non-associating census.
         differs_from_ladder=differs, ladder_nonassoc=la_nonassoc,
         differs_is_forced_identity=(differs == la_nonassoc))

# -- 5. the associativity census THROUGH the op, incl. dim 32 ----------
for dim in (2, 4, 8, 16, 32):
    basis = [cd_basis(dim, i) for i in range(dim)]
    n = sum(1 for i in range(dim) for j in range(dim) for k in range(dim)
            if all(v == 0 for v in associator(basis[i], basis[j], basis[k])))
    emit(claim="associativity_census", dim=dim, associating=n, total=dim ** 3)

with open(sys.argv[1], "w", encoding="utf-8") as fh:
    for rec in OUT:
        fh.write(json.dumps(rec) + "\n")
print("WROTE", sys.argv[1])
