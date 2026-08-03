"""rc386 (`#T1062`) provenance — cd_three_form, the exact-ℚ G₂ associative
3-form φ(x, y, z) = Re(x̄·(y·z)), the SCALAR twin of the vector associator.

φ is the regrouping-INVARIANT real shadow both (x̄·y)·z and x̄·(y·z) share
(because Re(associator) ≡ 0); associator is the pure-IMAGINARY defect that
regrouping DOES move. Together they split the octonion triple product into its
scalar (this op) and vector (associator) halves. On Im 𝕆 = ℝ⁷ φ is the
Harvey–Lawson associative calibration 3-form, ±1 on the 7 Fano planes; its
stabiliser is exactly G₂ = Der(𝕆).

This script reproduces, THROUGH the shipped rc386 op ``cd_three_form``:

  M1  the Fano census — 7 of the 35 unordered imaginary basis triples carry
      ±1: {123,145,246,257,347}=+1, {167,356}=−1; the other 28 are 0.
  M2  the co-equal dual-construction CONSISTENCY oracle — cd_three_form equals
      the shipped FLOAT peer ``srmech.math.hdc.g2_three_form`` bit-for-bit on
      all 35 unordered and 343 ordered imaginary basis triples.
  M3  G₂-invariance — every ``g2_subalgebra`` derivation D annihilates φ:
      φ(Dx,y,z) + φ(x,Dy,z) + φ(x,y,Dz) = 0 on all 14×35 = 490 (D, triple)
      identities; 56 of them are NON-TRIVIAL (at least one substitution term
      ≠ 0), so the cancellation is a measurement, not a vacuous 0 = 0.
  M4  the associator / φ Re/Im split THROUGH cd_three_form — on the 343 ordered
      imaginary triples Re(associator) ≡ 0 (φ lives entirely in the scalar the
      associator cannot see), while cd_three_form reads that scalar; on generic
      octonions cd_three_form is the single regrouping-invariant value both
      bracketings share.
  M5  full antisymmetry — φ is alternating: any transposition flips its sign,
      and a repeated argument annihilates it.

Everything is exact ℚ, reproduced through shipped ops. There is no ``abs()``
anywhere: a magnitude is only ever a Class-N Euclidean SQUARED norm (sum of
squares, inherently non-negative — ``cd_norm_sq`` / ⟨v,v⟩) and a sign is only
ever a Class-K pin (direct equality against a negation, or a product-of-signs
test), never ``abs``.

Run from ``docs/srmech/python`` with::

    PYTHONUTF8=1 PYTHONPATH="$(pwd)" python ../notes/cd_three_form_rc386.py \
        > ../notes/cd_three_form_rc386.ndjson

Emits one JSON record per line to stdout; the caller redirects to the ``.ndjson``.
"""
from __future__ import annotations

import json
from fractions import Fraction as Fr
from itertools import combinations, permutations, product

# --- shipped exact-ℚ Cayley–Dickson surface (the op under test + its kin) ------
from srmech.cascade.cayley_dickson import (
    cd_three_form,   # the rc386 op under test
    cd_mult,
    cd_conjugate,
    cd_norm_sq,
    cd_basis,
    associator,
)
# --- shipped FLOAT peers (the consistency-oracle side of the dual) -------------
from srmech.math.hdc import g2_three_form, cross7
# --- shipped gauge surface: g₂ = Der(𝕆) --------------------------------------
from srmech.physics.qm.so8 import g2_subalgebra

REC = []


def rec(**kw):
    REC.append(kw)


def E(i):
    return cd_basis(8, i)


def re(x):
    """Re(·) — the e₀ scalar component."""
    return x[0]


IMAG = list(range(1, 8))  # e₁ … e₇ span Im 𝕆 = ℝ⁷
FANO_EXPECT = {
    (1, 2, 3): 1, (1, 4, 5): 1, (2, 4, 6): 1, (2, 5, 7): 1, (3, 4, 7): 1,
    (1, 6, 7): -1, (3, 5, 6): -1,
}


# ======================================================================
# M1 — the Fano census of cd_three_form over the 35 unordered imaginary triples.
# ======================================================================
census = {}
for i, j, k in combinations(IMAG, 3):
    v = cd_three_form(E(i), E(j), E(k))
    if v != 0:
        census[(i, j, k)] = int(v)
rec(m="M1", kind="fano_census", nonzero=len(census),
    total=len(list(combinations(IMAG, 3))),
    plus=sorted(str(t) for t, s in census.items() if s == 1),
    minus=sorted(str(t) for t, s in census.items() if s == -1),
    matches_expected=(census == FANO_EXPECT),
    pass_=(census == FANO_EXPECT and len(census) == 7),
    note="cd_three_form is ±1 on exactly the 7 Fano associative 3-planes "
         "({123,145,246,257,347}=+1, {167,356}=−1) and 0 on the other 28 of 35")


# ======================================================================
# M2 — the CONSISTENCY oracle: exact-ℚ cd_three_form == float g2_three_form,
# 35/35 unordered AND 343/343 ordered (co-equal dual construction — the two
# realizations MUST agree; the disagreement, were there any, would be the find).
# ======================================================================
u_ok = u_t = 0
for i, j, k in combinations(IMAG, 3):
    u_t += 1
    q = cd_three_form(E(i), E(j), E(k))
    f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                      [float(x) for x in E(k)])
    if float(q) == float(f):
        u_ok += 1
o_ok = o_t = 0
for i, j, k in product(IMAG, repeat=3):
    o_t += 1
    q = cd_three_form(E(i), E(j), E(k))
    f = g2_three_form([float(x) for x in E(i)], [float(x) for x in E(j)],
                      [float(x) for x in E(k)])
    if float(q) == float(f):
        o_ok += 1
rec(m="M2", kind="oracle_cd_three_form_vs_g2_three_form",
    unordered_match=u_ok, unordered_total=u_t,
    ordered_match=o_ok, ordered_total=o_t,
    pass_=(u_ok == u_t == 35 and o_ok == o_t == 343),
    note="exact-ℚ cd_three_form == shipped FLOAT g2_three_form 35/35 unordered "
         "and 343/343 ordered — the co-equal dual-construction consistency oracle")

# M2b — φ(a,b,c) = ⟨a, cross7(b,c)⟩ (the calibration identity: the scalar reads
# the 7-D cross product), on the 343 ordered.
c_ok = c_t = 0
for i, j, k in product(IMAG, repeat=3):
    c_t += 1
    q = cd_three_form(E(i), E(j), E(k))
    a = [float(v) for v in E(i)]
    bc = cross7([float(v) for v in E(j)], [float(v) for v in E(k)])
    dot = sum(a[m] * bc[m] for m in range(8))
    if float(q) == float(dot):
        c_ok += 1
rec(m="M2b", kind="phi_equals_a_dot_cross7", match=c_ok, total=c_t,
    pass_=(c_ok == c_t == 343),
    note="φ(a,b,c) = ⟨a, cross7(b,c)⟩ on 343/343 — φ calibrates the 7-D cross "
         "product (Harvey–Lawson)")


# ======================================================================
# M3 — G₂-invariance: every g2_subalgebra derivation annihilates φ. The 14
# derivations have exact-integer entries, so the identity stays exact ℚ.
# ======================================================================
G = g2_subalgebra()
# assert exact-integer entries (Class-N rational anchor; NO float leaks into φ)
integer_entries = all(
    float(D[r][c]) == int(round(float(D[r][c])))
    for D in G for r in range(8) for c in range(8))


def Dact(D, e):
    """D·e, exact ℚ (D has integer entries)."""
    out = []
    for r in range(8):
        s = Fr(0)
        for c in range(8):
            s += Fr(int(round(float(D[r][c])))) * e[c]
        out.append(s)  # exact Fr
    return tuple(out)


inv_ok = inv_tot = 0
inv_nontrivial_ok = inv_nontrivial = 0
for D in G:
    for i, j, k in combinations(IMAG, 3):
        x, y, z = E(i), E(j), E(k)
        t1 = cd_three_form(Dact(D, x), y, z)
        t2 = cd_three_form(x, Dact(D, y), z)
        t3 = cd_three_form(x, y, Dact(D, z))
        s = t1 + t2 + t3
        inv_tot += 1
        if s == 0:
            inv_ok += 1
        if not (t1 == 0 and t2 == 0 and t3 == 0):
            inv_nontrivial += 1
            if s == 0:
                inv_nontrivial_ok += 1
rec(m="M3", kind="g2_invariance", derivations=len(G),
    integer_entries=integer_entries,
    identities_hold=inv_ok, identities_total=inv_tot,
    nontrivial_hold=inv_nontrivial_ok, nontrivial_total=inv_nontrivial,
    pass_=(inv_ok == inv_tot == 490 and integer_entries
           and inv_nontrivial_ok == inv_nontrivial),
    note="every g2_subalgebra derivation D annihilates φ: "
         "φ(Dx,y,z)+φ(x,Dy,z)+φ(x,y,Dz)=0 on all 14×35=490 (D,triple); 56 are "
         "NON-TRIVIAL (individual terms not all 0), so stab(φ)=G₂=Der(𝕆) is a "
         "MEASUREMENT, not a vacuous 0=0. (The task brief's '84/84' target did "
         "not reproduce; the honest census is 490/490 total, 56 non-trivial.)")


# ======================================================================
# M4 — the associator / φ Re/Im split, side by side, THROUGH cd_three_form.
# ======================================================================
re_assoc_zero = 0
assoc_tot = 0
for i, j, k in product(IMAG, repeat=3):
    A = associator(E(i), E(j), E(k))
    assoc_tot += 1
    if A[0] == 0:                        # Re(associator) — Class-K sign pin at 0
        re_assoc_zero += 1
rec(m="M4a", kind="re_associator_zero", re_zero=re_assoc_zero, total=assoc_tot,
    pass_=(re_assoc_zero == assoc_tot == 343),
    note="Re(associator)≡0 on 343/343 — the associativity defect is pure "
         "IMAGINARY, so the SCALAR φ cd_three_form reads is the part it misses")

# M4b — on generic octonions the regrouping-invariant scalar both bracketings
# share IS cd_three_form: Re(x̄·((x·y)·z direction)) — test Re((x̄·y)·z) ==
# Re(x̄·(y·z)) == cd_three_form(x,y,z), and the associator (Im defect) ≠ 0 there.

def lcg(seed, n):
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % (2 ** 31)
        out.append((x % 15) - 7)
    return out


vals = lcg(20260803, 8 * 3 * 200)
octs = []
idx = 0
while len(octs) < 60:
    v = [Fr(x) for x in vals[idx:idx + 8]]
    idx += 8
    if any(v[m] != 0 for m in range(4)) and any(v[m] != 0 for m in range(4, 8)):
        octs.append(tuple(v))
TRIPLES = [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]

split_ok = 0
defect_nonzero = 0
for a, b, c in TRIPLES:
    cb = cd_conjugate(a)
    left = re(cd_mult(cd_mult(cb, b), c))    # Re((x̄·y)·z)
    right = re(cd_mult(cb, cd_mult(b, c)))   # Re(x̄·(y·z))
    phi_op = cd_three_form(a, b, c)
    if left == right == phi_op:
        split_ok += 1
    A = associator(a, b, c)                  # the Im defect the scalar misses
    if any(v != 0 for v in A):
        defect_nonzero += 1
rec(m="M4b", kind="regroup_invariant_scalar_generic", total=len(TRIPLES),
    scalar_agrees=split_ok, associator_nonzero=defect_nonzero,
    pass_=(split_ok == len(TRIPLES)),
    note="Re((x̄·y)·z)==Re(x̄·(y·z))==cd_three_form on every generic octonion "
         "triple (the regrouping-safe scalar) while the associator (Im defect) "
         "is nonzero — the scalar/vector split of the triple product")


# ======================================================================
# M5 — full antisymmetry: φ is alternating (any transposition flips the sign;
# a repeated argument annihilates it). Class-K sign pin, no abs().
# ======================================================================
anti_ok = anti_tot = 0
for i, j, k in combinations(IMAG, 3):
    base = cd_three_form(E(i), E(j), E(k))
    for p in permutations((i, j, k)):
        sign = _perm_sign = 1
        # parity of the permutation relative to (i,j,k)
        seq = list(p)
        ref = [i, j, k]
        # count inversions to (i,j,k) ordering
        parity = 0
        arr = [ref.index(x) for x in seq]
        for a1 in range(len(arr)):
            for b1 in range(a1 + 1, len(arr)):
                if arr[a1] > arr[b1]:
                    parity += 1
        sign = -1 if parity % 2 else 1
        val = cd_three_form(E(p[0]), E(p[1]), E(p[2]))
        anti_tot += 1
        if val == sign * base:
            anti_ok += 1
repeat_zero = 0
repeat_tot = 0
for i, j in combinations(IMAG, 2):
    for trip in [(i, i, j), (i, j, i), (j, i, i), (i, j, j), (j, i, j), (j, j, i)]:
        repeat_tot += 1
        if cd_three_form(E(trip[0]), E(trip[1]), E(trip[2])) == 0:
            repeat_zero += 1
rec(m="M5", kind="antisymmetry", perm_ok=anti_ok, perm_total=anti_tot,
    repeated_zero=repeat_zero, repeated_total=repeat_tot,
    pass_=(anti_ok == anti_tot and repeat_zero == repeat_tot),
    note="φ is fully antisymmetric — every transposition flips the sign "
         "(Class-K pin, no abs()) and a repeated argument annihilates it")


# ======================================================================
# M6 — no-abs cascade honesty: a norm is only ever a Class-N SQUARED norm, and
# the norm cannot see the regrouping (composition algebra ‖xy‖²=‖x‖²‖y‖²).
# ======================================================================
norm_eq = 0
for a, b, c in TRIPLES:
    L = cd_mult(cd_mult(a, b), c)
    R = cd_mult(a, cd_mult(b, c))
    if cd_norm_sq(L) == cd_norm_sq(R):   # Class-N Euclidean squared norm; no abs()
        norm_eq += 1
rec(m="M6", kind="norm_regroup_invariant", total=len(TRIPLES), norm_equal=norm_eq,
    norm_op="cd_norm_sq (Class-N sum of squares, non-negative by construction)",
    pass_=(norm_eq == len(TRIPLES)),
    note="N((ab)c)==N(a(bc)) via cd_norm_sq — the OTHER regrouping-invariant "
         "scalar (the norm) beside φ; both read with no abs(), Class-N squared norm")


for r in REC:
    print(json.dumps(r, default=str))
