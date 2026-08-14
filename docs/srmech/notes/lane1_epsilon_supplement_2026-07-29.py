#!/usr/bin/env python3
# RUN (WSL2, numpy-absent, from the srmech python tree):
#   cd docs/srmech/python && \n#   PYTHONPATH=$PWD python3 <this file>
"""LANE 1 SUPPLEMENT — settle the residual (c) questions exactly.

Same conventions, same SUBJECT ops (cd_basis_product / algebra_table /
gf_rref) and the same labelled oracles as lane1_epsilon.py.
"""
import itertools
import json
import sys

from srmech.amsc.cascade.cayley_dickson import cd_basis_product, algebra_table
from srmech.amsc.modular_linalg import gf_rref


def rec(**kw):
    print(json.dumps(kw, sort_keys=True))
    sys.stdout.flush()


def faces(s):
    out = [s[1:]]
    for k in range(len(s) - 1):
        out.append(s[:k] + (s[k] ^ s[k + 1],) + s[k + 2:])
    out.append(s[:-1])
    return out


def basis(d, n, normalised=False):
    lo = 1 if normalised else 0
    return list(itertools.product(range(lo, 1 << d), repeat=n))


def apply_delta(vec, d, n, normalised=False):
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


def eps_table(dim, gammas=None):
    if gammas is None:
        return [[0 if cd_basis_product(dim, i, j)[1] == 1 else 1
                 for j in range(dim)] for i in range(dim)]
    T = algebra_table(dim, gammas)
    return [[0 if T[i][j][i ^ j] == 1 else 1 for j in range(dim)]
            for i in range(dim)]


def eps_vec(tab, d, normalised=False):
    return [tab[x][y] for (x, y) in basis(d, 2, normalised)]


def _oracle_det3(x, y, z, bits=(0, 1, 2)):
    def b(v, k):
        return (v >> bits[k]) & 1
    return (b(x, 0) * (b(y, 1) * b(z, 2) + b(y, 2) * b(z, 1))
            + b(x, 1) * (b(y, 0) * b(z, 2) + b(y, 2) * b(z, 0))
            + b(x, 2) * (b(y, 0) * b(z, 1) + b(y, 1) * b(z, 0))) % 2


# ── S1. how many GAUGE ORBITS does the 8-member gamma family occupy? ──────
d = 3
tables = {}
for g in itertools.product((-1, 1), repeat=3):
    tables[g] = tuple(eps_vec(eps_table(8, list(g)), 3))


def orbit(ev):
    o = set()
    for bitsv in range(1 << 8):
        c = [(bitsv >> k) & 1 for k in range(8)]
        dc = apply_delta(c, 3, 1)
        o.add(tuple(a ^ b for a, b in zip(ev, dc)))
    return o


orbits = []
for g, ev in tables.items():
    hit = None
    for oi, (members, o) in enumerate(orbits):
        if ev in o:
            hit = oi
            break
    if hit is None:
        orbits.append(([g], orbit(ev)))
    else:
        orbits[hit][0].append(g)
rec(kind="gamma_family_orbits", d=3,
    n_gamma_tables=len(tables), n_distinct_gauge_orbits=len(orbits),
    orbit_membership=[{"gammas": [list(x) for x in m], "size": len(o)}
                      for m, o in orbits],
    note="the whole 8-member gamma family collapses to exactly this many "
         "gauge classes of 2-cochain")

# ── S2. q and R: gauge-invariant shadows of epsilon that DO separate ──────
def q_of(tab, dim):
    return [tab[x][x] for x in range(dim)]


def R_of(tab, dim):
    return [[(tab[x][y] ^ tab[y][x]) for y in range(dim)] for x in range(dim)]


base = eps_table(8)
ev0 = eps_vec(base, 3)
q0, R0 = q_of(base, 8), R_of(base, 8)
q_inv = R_inv = 0
n_c = 0
for bitsv in range(1 << 8):
    c = [(bitsv >> k) & 1 for k in range(8)]
    if c[0] != 0:
        continue                      # unitality-preserving gauge only
    n_c += 1
    dc = apply_delta(c, 3, 1)
    ev2 = [a ^ b for a, b in zip(ev0, dc)]
    t2 = [[ev2[x * 8 + y] for y in range(8)] for x in range(8)]
    if q_of(t2, 8) == q0:
        q_inv += 1
    if R_of(t2, 8) == R0:
        R_inv += 1
rec(kind="q_and_R_gauge_invariance", d=3, n_unital_gauge_1cochains=n_c,
    q_invariant_count=q_inv, q_is_gauge_invariant=(q_inv == n_c),
    R_invariant_count=R_inv, R_is_gauge_invariant=(R_inv == n_c),
    note="q(x)=eps(x,x) and R(x,y)=eps(x,y)+eps(y,x) are gauge invariants; "
         "unlike epsilon itself they are single-cochain readable")

sep = []
for g in itertools.product((-1, 1), repeat=3):
    t = eps_table(8, list(g))
    sep.append({"gammas": list(g), "q": q_of(t, 8),
                "n_q_ones": sum(q_of(t, 8)),
                "q_equals_definite_O": (q_of(t, 8) == q0),
                "R_equals_definite_O": (R_of(t, 8) == R0)})
rec(kind="q_separates_definite_from_split", d=3, rows=sep,
    q_separates=(sum(1 for s in sep if s["q_equals_definite_O"]) == 1),
    R_separates=(sum(1 for s in sep if s["R_equals_definite_O"]) == 8),
    note="q separates definite O from all 7 split forms; R does NOT (all 8 "
         "share the same commutation form) -- and phi does not either. "
         "rc404 (`#T1069`): read 'commutation bicharacter'. This row is d=3 "
         "(O), where the form is measured NOT bimultiplicative -- 168 of 512 "
         "triples fail -- so it is not a bicharacter here. The separation "
         "result this row reports is untouched.")

# ── S3. dim of the COMPLETE gauge invariant C^2 / B^2 ─────────────────────
for normalised in (False, True):
    lab = "normalised" if normalised else "unnormalised"
    rws = basis(3, 1, normalised)
    cls = basis(3, 2, normalised)
    ridx = {t: i for i, t in enumerate(rws)}
    M = [[0] * len(cls) for _ in rws]
    for cj, s in enumerate(cls):
        for f in faces(s):
            i = ridx.get(f)
            if i is not None:
                M[i][cj] ^= 1
    rk = gf_rref(M, 2)["rank"]
    rec(kind="gauge_moduli", complex=lab, d=3,
        dim_C2=len(cls), dim_B2=rk, dim_C2_mod_B2=len(cls) - rk,
        n_gauge_classes_of_2cochain=f"2^{len(cls) - rk}",
        note="the COMPLETE gauge invariant of a G-graded quasialgebra twist "
             "is the class of epsilon in C^2/B^2 -- not a cohomology class, "
             "because epsilon is not a cocycle")

# ── S4. sedenion phi: is the CUBIC part the sum of the four 3x3 minors? ───
d = 4
tab16 = eps_table(16)
ph16 = apply_delta(eps_vec(tab16, 4), 4, 2)
order4 = basis(4, 3)
minors = list(itertools.combinations(range(4), 3))
minor_sum = []
for (x, y, z) in order4:
    v = 0
    for m in minors:
        v ^= _oracle_det3(x, y, z, bits=m)
    minor_sum.append(v % 2)
agree = sum(1 for a, b in zip(ph16, minor_sum) if a == b)
rec(kind="sedenion_phi_vs_minor_sum", d=4, dim=16,
    n_triples=len(ph16), phi_support=sum(ph16),
    minor_sum_support=sum(minor_sum), agreements=agree,
    exact_match=(agree == len(ph16)),
    residual_support=sum(1 for a, b in zip(ph16, minor_sum) if a != b),
    note="phi_16 vs sum over the four 3x3 minors of (x,y,z)")

# restriction of phi_16 to the rank-3 subgroup spanned by bits 0,1,2
sub = [i for i in range(16) if i < 8]
res_agree = 0
res_total = 0
for x in sub:
    for y in sub:
        for z in sub:
            idx = order4.index((x, y, z))
            res_total += 1
            if ph16[idx] == _oracle_det3(x, y, z):
                res_agree += 1
rec(kind="sedenion_phi_restricted_to_O_subgroup", d=4,
    subgroup="<e1,e2,e4> (bits 0,1,2)", n_triples=res_total,
    agreements_with_det3=res_agree,
    restriction_equals_octonion_phi=(res_agree == res_total),
    note="the octonion cocycle is the restriction of the sedenion one")
