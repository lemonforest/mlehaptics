#!/usr/bin/env python3
"""LANE C — WHAT the C(dim,2) coboundary distance actually measures, and what
DEGREE the irreducible twist lives in.  Exact integers only; sign composition
is Class-K pin-slot (no abs()).  Subject = the SHIPPED srmech cocycle.

SOURCES (each verified by extracting the actual PDF; authors + title + ID checked):

  [1] S. B. Conlon, "Twisted group algebras and their representations",
      J. Austral. Math. Soc. 4 (1964) 152-173, doi:10.1017/S1446788700023363.
      OPEN (PDF downloads free from Cambridge Core).  p.152 defines a twisted
      group algebra as ASSOCIATIVE with (A)(B) = f_{A,B}(AB); p.153 gives the
      associativity condition f_{A,B} f_{AB,C} = f_{A,BC} f_{B,C} (= the
      2-cocycle condition) and the rebasing f~_{A,B} = (d_A d_B / d_AB) f_{A,B}
      (= EXACTLY the diagonal rescaling used below), modulo which the factor
      systems form Schur's "Multiplikator".

  [2] H. Albuquerque & S. Majid, "Quasialgebra structure of the octonions",
      arXiv:math/9802116, DAMPT/97-138.  p.2: "However, for the octonions, the
      cocycle is a COBOUNDARY and can be identified as the result of twisting
      k(G) by a 2-cochain F."  Def 2.3 / Cor 2.4 name k_F G a "COBOUNDARY
      G-graded quasialgebra".  Prop 4.4 gives f for C / H / O / 16-onion; the
      following paragraph: for C and H "F is a bicharacter and hence, in
      particular, its group coboundary phi = 1"; the octonion f "has this
      bilinear part ... plus a CUBIC term which contributes to phi".

  [3] J. Kirshtein, "Multiplication groups and inner mapping groups of
      Cayley-Dickson loops", arXiv:1207.4230 (17 Jul 2012).  Defines the
      Cayley-Dickson loop Q_n (order 2^{n+1}) as the multiplicative closure of
      the basis elements; Thm 4: Q_n/{1,-1} = (Z_2)^n; Lemma 3.3: Z(Q_n) =
      {1,-1} for n >= 2.  "the Cayley-Dickson loops are not associative after
      dimension 8."

  [4] M. K. Murray, "Bundle gerbes", arXiv:dg-ga/9407015, J. Lond. Math. Soc.
      54 (1996) 403-416 — gerbes realise THREE-DIMENSIONAL INTEGRAL cohomology
      via the Dixmier-Douady class.  Cited here only to RULE OUT the gerbe
      reading: that is H^3(M, Z) on a SPACE, and our degree-3 class is ZERO.

NOT related, despite the shared word: Penrose TWISTOR space (T = C^4, projective
PT = CP^3, a complex three-fold attached to the conformal geometry of complexified
compactified Minkowski space; Atiyah, Dunajski & Mason, arXiv:1704.07464).  It is
continuous complex/conformal geometry with no finite group and no finite-group
cohomology anywhere in it.  The coincidence is lexical only.
"""
import json
import sys
from itertools import product

from srmech.amsc.cascade.cayley_dickson import cd_basis_product

OUT = []
def rec(**kw): OUT.append(kw)

DIMS = [2, 4, 8, 16]
NAME = {2: "C", 4: "H", 8: "O", 16: "S"}

# S[x][y] = 1 iff eps(x,y) = -1   (additive GF(2) coordinates)
S = {n: [[0 if cd_basis_product(n, x, y)[1] == 1 else 1 for y in range(n)]
         for x in range(n)] for n in DIMS}

# ── 1. EXHAUSTIVE distance to the nearest coboundary ────────────────────
for n in DIMS:
    rows = S[n]
    rng = range(n)
    best, ident, n_opt = None, None, 0
    for tail in product((0, 1), repeat=n - 1):
        a = (0,) + tail
        d = 0
        for x in rng:
            ax, rx = a[x], rows[x]
            for y in rng:
                if (ax ^ a[y] ^ a[x ^ y]) != rx[y]:
                    d += 1
        if best is None or d < best:
            best, n_opt = d, 1
        elif d == best:
            n_opt += 1
        if not any(a):
            ident = d
    rec(kind="coboundary_distance", dim=n, algebra=NAME[n],
        rescalings=2 ** (n - 1), cells=n * n, min_distance=best,
        binom_dim_2=n * (n - 1) // 2, equals_binom=(best == n * (n - 1) // 2),
        identity_distance=ident, identity_is_optimal=(ident == best),
        n_optimal_rescalings=n_opt)

# ── 2. WHY C(n,2)?  the floor is a SYMMETRY count, not an H^2 norm ──────
for n in DIMS:
    neg_sq = sum(1 for x in range(n) if S[n][x][x] == 1)
    anti = sum(1 for x in range(n) for y in range(x + 1, n)
               if S[n][x][y] != S[n][y][x])
    rec(kind="floor_decomposition", dim=n, algebra=NAME[n],
        negative_squares=neg_sq, antisymmetric_unordered_pairs=anti,
        forced_floor=neg_sq + anti, binom_dim_2=n * (n - 1) // 2,
        floor_equals_binom=(neg_sq + anti == n * (n - 1) // 2),
        note="every coboundary is SYMMETRIC with an all-+1 diagonal, so each "
             "negative square costs 1 and each anticommuting unordered pair "
             "costs 1 -- (n-1) + C(n-1,2) = C(n,2) EXACTLY, for every rung")

# ── 3. degree-2: is eps a 2-cocycle, and is its class nonzero in H^2? ───
def cocycle_fails(n, T):
    return sum(1 for x in range(n) for y in range(n) for z in range(n)
               if (T[x][y] ^ T[x ^ y][z] ^ T[y][z] ^ T[x][y ^ z]) != 0)


for n in DIMS:
    cf = cocycle_fails(n, S[n])
    hit = None
    if cf == 0:
        hit = any(all((a[x] ^ a[y] ^ a[x ^ y]) == S[n][x][y]
                      for x in range(n) for y in range(n))
                  for a in ((0,) + t for t in product((0, 1), repeat=n - 1)))
    rec(kind="degree2_class", dim=n, algebra=NAME[n],
        triples=n ** 3, cocycle_failures=cf, eps_is_2_cocycle=(cf == 0),
        eps_is_a_coboundary=hit,
        class_nonzero_in_H2=(None if hit is None else not hit),
        note="nonzero [eps] in H^2(G,Z/2) <=> NON-SPLIT central extension")

# ── 4. degree-3: A = delta(eps).  a 3-cocycle?  a 3-COBOUNDARY? ─────────
def A(n, x, y, z):
    T = S[n]
    return T[x][y] ^ T[x ^ y][z] ^ T[y][z] ^ T[x][y ^ z]


for n in DIMS:
    fails = 0
    for w in range(n):
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if (A(n, x, y, z) ^ A(n, w, x ^ y, z) ^ A(n, w, x, y ^ z)
                            ^ A(n, w ^ x, y, z) ^ A(n, w, x, y)) != 0:
                        fails += 1
    nz = sum(1 for x in range(n) for y in range(n) for z in range(n)
             if A(n, x, y, z))
    rec(kind="degree3_class", dim=n, algebra=NAME[n], quadruples=n ** 4,
        cocycle_failures=fails, is_3_cocycle=(fails == 0),
        nonassociative_triples=nz, associator_nontrivial=(nz > 0),
        is_a_3_coboundary=True, class_in_H3="ZERO",
        note="A = delta(eps) BY CONSTRUCTION => delta A = 0 (3-cocycle) AND "
             "[A] = 0 in H^3(G,Z/2) (3-coboundary).  Albuquerque-Majid p.2: "
             "'for the octonions, the cocycle is a coboundary'.")

# ── 5. can ANY rescaling gauge eps back into Z^2?  (the real obstruction)
for n in (2, 4, 8):
    vals = set()
    for tail in product((0, 1), repeat=n - 1):
        a = (0,) + tail
        T = [[S[n][x][y] ^ a[x] ^ a[y] ^ a[x ^ y] for y in range(n)]
             for x in range(n)]
        vals.add(cocycle_fails(n, T))
    rec(kind="gauge_orbit_cocycle_failures", dim=n, algebra=NAME[n],
        rescalings=2 ** (n - 1), distinct_failure_counts=sorted(vals),
        any_rescaling_is_a_cocycle=(0 in vals),
        note="delta(eps . delta c) = delta eps, so the associator is CONSTANT "
             "on the whole gauge orbit -- the degree-3 obstruction is exactly "
             "what CANNOT be rescaled away")

rec(kind="provenance", srmech_version=__import__("srmech").__version__,
    python=sys.version.split()[0])

for r in OUT:
    print(json.dumps(r, sort_keys=True))
