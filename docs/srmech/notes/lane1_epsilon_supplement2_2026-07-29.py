#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd docs/srmech/python && \n#   PYTHONPATH=$PWD python3 <this file>
"""LANE 1 SUPPLEMENT 2 — Aut(G) fusion, basis-freeness of phi, and the
ANF-level decomposition of the sedenion cocycle."""
import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis_product, algebra_table


def rec(**kw):
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


def faces(s):
    out = [s[1:]]
    for k in range(len(s) - 1):
        out.append(s[:k] + (s[k] ^ s[k + 1],) + s[k + 2:])
    out.append(s[:-1])
    return out


def basis(d, n):
    return list(itertools.product(range(1 << d), repeat=n))


def apply_delta(vec, d, n):
    rws = basis(d, n)
    ridx = {t: i for i, t in enumerate(rws)}
    return [
        (lambda s: sum(vec[ridx[f]] for f in faces(s)) % 2)(s)
        for s in basis(d, n + 1)
    ]


def eps_table(dim, gammas=None):
    if gammas is None:
        return [[0 if cd_basis_product(dim, i, j)[1] == 1 else 1
                 for j in range(dim)] for i in range(dim)]
    T = algebra_table(dim, gammas)
    return [[0 if T[i][j][i ^ j] == 1 else 1 for j in range(dim)]
            for i in range(dim)]


def eps_vec(tab, d):
    return [tab[x][y] for (x, y) in basis(d, 2)]


def _oracle_anf(vals, m):
    a = list(vals)
    for i in range(m):
        step = 1 << i
        for j in range(1 << m):
            if j & step:
                a[j] ^= a[j ^ step]
    return a


def _oracle_det3(x, y, z, bits=(0, 1, 2)):
    def b(v, k):
        return (v >> bits[k]) & 1
    return (b(x, 0) * (b(y, 1) * b(z, 2) + b(y, 2) * b(z, 1))
            + b(x, 1) * (b(y, 0) * b(z, 2) + b(y, 2) * b(z, 0))
            + b(x, 2) * (b(y, 0) * b(z, 1) + b(y, 1) * b(z, 0))) % 2


# ── T1. Aut(G) = GL(d,2) acting on the gamma family ──────────────────────
def automorphisms(d):
    """Every invertible d x d F2 matrix, as the induced permutation of the
    2^d group elements (columns are the images of the standard generators)."""
    out = []
    for cols in itertools.product(range(1, 1 << d), repeat=d):
        perm = [0] * (1 << d)
        for v in range(1 << d):
            w = 0
            for k in range(d):
                if (v >> k) & 1:
                    w ^= cols[k]
            perm[v] = w
        if len(set(perm)) == (1 << d):
            out.append(perm)
    return out


d = 3
AUT = automorphisms(3)
rec(kind="aut_group", d=3, order=len(AUT), expected_GL_3_2=168,
    matches=(len(AUT) == 168))


def gauge_orbit(ev):
    o = set()
    for bitsv in range(1 << 8):
        c = [(bitsv >> k) & 1 for k in range(8)]
        dc = apply_delta(c, 3, 1)
        o.add(tuple(a ^ b for a, b in zip(ev, dc)))
    return o


def full_orbit(ev):
    """gauge x Aut(G) -- the equivalence a quasialgebra ISOMORPHISM induces."""
    o = set()
    for perm in AUT:
        pulled = [0] * 64
        for i, (x, y) in enumerate(basis(3, 2)):
            pulled[i] = ev[perm[x] * 8 + perm[y]]
        o |= gauge_orbit(pulled)
    return o


tables = {g: tuple(eps_vec(eps_table(8, list(g)), 3))
          for g in itertools.product((-1, 1), repeat=3)}
classes = []
for g, ev in tables.items():
    hit = None
    for ci, (mem, o) in enumerate(classes):
        if ev in o:
            hit = ci
            break
    if hit is None:
        classes.append(([g], full_orbit(ev)))
    else:
        classes[hit][0].append(g)
rec(kind="gamma_family_full_classes", d=3, n_gamma_tables=8,
    n_classes_under_gauge_times_Aut=len(classes),
    members=[{"gammas": [list(x) for x in m], "orbit_size": len(o)}
             for m, o in classes],
    note="gauge alone gave 8 orbits; gauge x Aut(G) is the equivalence that "
         "matches ALGEBRA isomorphism (definite O vs split-O)")

# ── T2. is phi = det basis-free?  (measure over all 168 automorphisms) ────
base = eps_table(8)
ph = apply_delta(eps_vec(base, 3), 3, 2)
order3 = basis(3, 3)
oidx = {t: i for i, t in enumerate(order3)}
det_vec = [_oracle_det3(x, y, z) for (x, y, z) in order3]
n_same = 0
for perm in AUT:
    pulled = [ph[oidx[(perm[x], perm[y], perm[z])]] for (x, y, z) in order3]
    if pulled == ph:
        n_same += 1
rec(kind="phi_is_Aut_invariant", d=3, n_automorphisms=len(AUT),
    n_fixing_phi=n_same, phi_invariant_under_all_of_Aut_G=(n_same == len(AUT)),
    phi_equals_det=(ph == det_vec),
    note="det(Ax,Ay,Az) = det(A) det(x,y,z) and det A = 1 over F2, so "
         "phi = det is a BASIS-FREE statement -- measured, not assumed")

# ── T3. ANF-level decomposition of the sedenion cocycle ──────────────────
d = 4
ph16 = apply_delta(eps_vec(eps_table(16), 4), 4, 2)
order4 = basis(4, 3)
packed = [0] * (1 << 12)
for v, (x, y, z) in zip(ph16, order4):
    packed[x | (y << 4) | (z << 8)] = v
a16 = _oracle_anf(packed, 12)
minor_sum = []
for (x, y, z) in order4:
    v = 0
    for m in itertools.combinations(range(4), 3):
        v ^= _oracle_det3(x, y, z, bits=m)
    minor_sum.append(v % 2)
packed_m = [0] * (1 << 12)
for v, (x, y, z) in zip(minor_sum, order4):
    packed_m[x | (y << 4) | (z << 8)] = v
am = _oracle_anf(packed_m, 12)


def names(mask):
    out = []
    for k in range(12):
        if (mask >> k) & 1:
            out.append(("x", "y", "z")[k // 4] + str(k % 4 + 1))
    return "".join(out)


by_deg = {}
for mask in range(1 << 12):
    if a16[mask]:
        by_deg.setdefault(bin(mask).count("1"), []).append(names(mask))
cubic_phi = sorted(by_deg.get(3, []))
cubic_minor = sorted(names(m) for m in range(1 << 12)
                     if am[m] and bin(m).count("1") == 3)
rec(kind="sedenion_phi_ANF_strata", d=4, dim=16,
    total_monomials=sum(len(v) for v in by_deg.values()),
    monomials_by_degree={k: len(v) for k, v in sorted(by_deg.items())},
    cubic_part_equals_minor_sum=(cubic_phi == cubic_minor),
    n_cubic=len(cubic_phi), n_quartic=len(by_deg.get(4, [])),
    quartic_monomials=sorted(by_deg.get(4, [])),
    minor_sum_is_exactly_the_cubic_part=(cubic_phi == cubic_minor),
    full_phi_equals_minor_sum=(ph16 == minor_sum),
    note="the sedenion 3-cocycle is the sum of the four 3x3 minor "
         "determinants PLUS a 24-term quartic remainder -- the minor sum "
         "alone is NOT phi_16")
