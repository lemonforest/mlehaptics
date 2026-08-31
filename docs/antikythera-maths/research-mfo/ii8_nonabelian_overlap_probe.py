"""Generating code for the section II.8 selection-rule measurement (2026-08-31).

Provenance for the figures now asserted at
``docs/antikythera-maths/mfo_spectral_research_notebook.md:297``:
exact-Fraction Gaunt census of SO(3) modes on S^2, all triples L <= 5 with
m1+m2+m3 = 0, n = 1256.

    CG-forbidden  => overlap zero   HOLDS 158/158 (zero violations)
    CG-ALLOWED    => overlap zero   564 triples vanish anyway
                                    (554 parity-odd + 10 accidental)

So the containment direction is exact and the identity direction is FALSE: the
geometry enforces a strictly finer filter than Clebsch-Gordan. That is the whole
basis for replacing "which ARE the selection rules" with a containment claim.

Committed under [[feedback_computational_provenance_discipline]] -- a load-bearing
numerical result must ship its generating code.

--- KNOWN GAP, stated rather than hidden -------------------------------------
This probe is stdlib ``fractions`` end to end and does NOT route through srmech
ops. That is a real departure from the tooling floor recorded at
section XIII.1 (:7135) and from
[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]] -- and
it is slightly ironic, because the marker this same pass added at :7174 tells
future readers that MFO re-runs belong on srmech ops. It is committed AS IS for
provenance (the numbers must be reproducible now, not later); re-expressing it on
srmech carriers is owed and is tracked separately. Do not cite this file as an
example of the tooling floor being met.
"""

r"""MFO §II.8 non-Abelian selection-rule probe — the committed generating code.

Claim under execution (mfo_spectral_research_notebook.md:297):
  "For non-Abelian groups (SU(2), SU(3)) the argument generalizes: modes on the
   internal manifold form irreducible representations, and overlap integrals
   enforce Clebsch-Gordan decomposition rules — which ARE the selection rules."

Smallest non-Abelian instance: SO(3)/SU(2) acting on S^2; modes = spherical
harmonics Y_lm; the three-mode junction coupling is the Gaunt-type overlap
  I = \iint Y_{l1 m1} Y_{l2 m2} Y_{l3 m3} dA.
Azimuthal factor gives exactly zero unless m1+m2+m3 = 0 (analytic, exact).
For m1+m2+m3 = 0 the polar integral is a POLYNOMIAL with rational
coefficients (|m1|+|m2|+|m3| is even, so (1-x^2)^{sum|m|/2} is polynomial),
integrated exactly over [-1,1] with Fractions. No floats anywhere; sqrt
normalisation constants are strictly positive so they cannot change the
zero/nonzero pattern and are omitted.

CG predicate (representation theory only): triangle |l1-l2| <= l3 <= l1+l2
and m1+m2+m3 = 0. Parity (l1+l2+l3 even) is NOT part of CG — it is geometry.

Measured questions:
  A. Does every CG-FORBIDDEN triple have exactly-zero overlap?  (the
     'forbidden => zero' direction — the load-bearing selection-rule half)
  B. Within CG-allowed triples, which are nonzero?  (does the manifold add
     selection beyond CG — parity zeros, accidental zeros?)
r"""
from fractions import Fraction
import json, sys

L_MAX = 5

def poly_mul(a, b):
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        if ai:
            for j, bj in enumerate(b):
                if bj:
                    out[i + j] += ai * bj
    return out

def poly_diff(a):
    return [a[i] * i for i in range(1, len(a))] or [Fraction(0)]

def legendre(l):
    # Rodrigues: P_l = 1/(2^l l!) d^l/dx^l (x^2-1)^l, exact Fractions
    p = [Fraction(1)]
    base = [Fraction(-1), Fraction(0), Fraction(1)]  # x^2 - 1
    for _ in range(l):
        p = poly_mul(p, base)
    for _ in range(l):
        p = poly_diff(p)
    import math
    c = Fraction(1, 2**l * math.factorial(l))
    return [c * x for x in p]

def assoc_legendre_polypart(l, m):
    # For m >= 0: P_l^m(x) = (1-x^2)^{m/2} * d^m/dx^m P_l(x).
    # Return the polynomial part d^m/dx^m P_l (the (1-x^2)^{m/2} factor is
    # reassembled across the triple product, where the total power is integer).
    q = legendre(l)
    for _ in range(m):
        q = poly_diff(q)
    return q

def integrate_m1_1(p):
    # exact \int_{-1}^{1} x^n dx = 2/(n+1) for even n, 0 odd
    s = Fraction(0)
    for n, c in enumerate(p):
        if c and n % 2 == 0:
            s += c * Fraction(2, n + 1)
    return s

def overlap_is_zero(l1, m1, l2, m2, l3, m3):
    # requires m1+m2+m3 == 0 (else exactly zero by the azimuthal integral)
    am1, am2, am3 = abs(m1), abs(m2), abs(m3)
    if any(a > l for a, l in ((am1, l1), (am2, l2), (am3, l3))):
        return True  # mode does not exist
    tot_m = am1 + am2 + am3          # even when m1+m2+m3 == 0
    q = poly_mul(poly_mul(assoc_legendre_polypart(l1, am1),
                          assoc_legendre_polypart(l2, am2)),
                 assoc_legendre_polypart(l3, am3))
    w = [Fraction(1)]
    base = [Fraction(1), Fraction(0), Fraction(-1)]  # 1 - x^2
    for _ in range(tot_m // 2):
        w = poly_mul(w, base)
    return integrate_m1_1(poly_mul(q, w)) == 0

def triangle_ok(l1, l2, l3):
    return abs(l1 - l2) <= l3 <= l1 + l2

tally = {
    "forbidden_triangle_zero": 0, "forbidden_triangle_NONZERO": [],
    "allowed_parity_even_nonzero": 0, "allowed_parity_even_ZERO": [],
    "allowed_parity_odd_zero": 0, "allowed_parity_odd_NONZERO": [],
}
n_checked = 0
for l1 in range(L_MAX + 1):
    for l2 in range(l1, L_MAX + 1):
        for l3 in range(l2, L_MAX + 1):        # l1<=l2<=l3 wlog (integrand symmetric)
            for m1 in range(-l1, l1 + 1):
                for m2 in range(-l2, l2 + 1):
                    m3 = -(m1 + m2)
                    if abs(m3) > l3:
                        continue
                    n_checked += 1
                    z = overlap_is_zero(l1, m1, l2, m2, l3, m3)
                    key = (l1, m1, l2, m2, l3, m3)
                    if not triangle_ok(l1, l2, l3):
                        if z: tally["forbidden_triangle_zero"] += 1
                        else: tally["forbidden_triangle_NONZERO"].append(key)
                    elif (l1 + l2 + l3) % 2 == 0:
                        if z: tally["allowed_parity_even_ZERO"].append(key)
                        else: tally["allowed_parity_even_nonzero"] += 1
                    else:
                        if z: tally["allowed_parity_odd_zero"] += 1
                        else: tally["allowed_parity_odd_NONZERO"].append(key)

print(json.dumps({
    "L_MAX": L_MAX, "n_triples_checked": n_checked,
    "forbidden_triangle_zero": tally["forbidden_triangle_zero"],
    "forbidden_triangle_NONZERO_count": len(tally["forbidden_triangle_NONZERO"]),
    "allowed_parity_even_nonzero": tally["allowed_parity_even_nonzero"],
    "allowed_parity_even_ZERO_count": len(tally["allowed_parity_even_ZERO"]),
    "allowed_parity_even_ZERO_examples": tally["allowed_parity_even_ZERO"][:12],
    "allowed_parity_odd_zero": tally["allowed_parity_odd_zero"],
    "allowed_parity_odd_NONZERO_count": len(tally["allowed_parity_odd_NONZERO"]),
}))
