"""srmech 0.9.0rc39 — the §76 telescope polynomial-algebra foundation (Layer A):
the deferred ``srmech_poly_gcd`` C peer + the exact ``Poly.resultant`` /
``Poly.dispersion`` carrier methods. Numpy-free, math-free.

Covers:
  - gcd-C: ``poly_gcd_c`` byte/value-parity with ``Poly.gcd`` on the rc38 bignum
    keystone AND at the higher-degree rational regime that the rc38 naive per-op
    envelope OVERFLOWED on (zero overflow, Python == C exactly under native);
  - resultant: the known identities ``Res(x²−1, x−2) = 3``, ``Res(x−a, x−b) =
    a−b``, ``Res(p, c) = c^deg p``, and ``Res(p, p) = 0`` (shared factor),
    cross-checked against the product-of-differences definition;
  - dispersion: the standard Gosper–Petkovšek convention
    ``{h ≥ 0 : deg gcd(p(k), q(k + h)) ≥ 1}`` on ``(k, k) → [0]``,
    ``(x(x+5), x) → [0, 5]``, and a no-overlap pair ``→ []``.

Python == C parity (gcd) is asserted byte/value-exact when the native
``srmech_poly_gcd`` peer is present, skipped cleanly otherwise (the pure-Python
Euclid driver is the complete, ceiling-free alternative + the oracle).

CONVENTION NOTE (load-bearing): ``dispersion`` shifts the SECOND argument by
``+h`` — the standard Petkovšek/PWZ ``A=B`` convention, the one Gosper's GP
normal form consumes. Under it, ``dispersion(x, x+3)`` is ``[]`` (the root of
``x`` is ``0``, the root of ``(x+3)(k+h)`` is ``−3−h``, which is ``0`` only at
``h = −3 < 0``); the spec's ``[3]`` for that pair corresponds to the OPPOSITE
shift direction and is recovered by swapping the arguments
(``(x+3).dispersion(x) == [3]``). The opposite direction would break
``(x(x+5), x) → [0, 5]``, so the conventions are mutually exclusive; this module
ships + tests the standard one.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q


def _P(*cs):
    return Poly.from_coeffs([c if isinstance(c, tuple) else c for c in cs])


def _fracs(poly):
    return [Fraction(c.numerator, c.denominator) for c in poly.coeffs]


# ── gcd: pure-path correctness (the carrier still routes the same Euclid) ──────
def test_gcd_known_and_monic():
    # gcd(x^2 - 1, x - 1) = x - 1 (monic)
    g = _P(-1, 0, 1).gcd(_P(-1, 1))
    assert g.coeffs == (Q(-1), Q(1))
    # coprime → monic constant 1
    assert _P(0, 1).gcd(_P(3, 1)).coeffs == (Q(1),)
    # gcd(p, 0) = monic(p)
    assert _P(4, 0, 2).gcd(Poly.zero()).coeffs == (Q(2), Q(0), Q(1))
    assert Poly.zero().gcd(Poly.zero()).is_zero


# ── the higher-degree rational regime (the rc38 OVERFLOW case) ────────────────
def _shared_cubic():
    # x^3 - (1/3) x^2 - 2x + 2/3  →  [2/3, -2, -1/3, 1]
    return Poly.from_coeffs([Q(2, 3), Q(-2), Q(-1, 3), Q(1)])


def _overflow_regime_pair():
    shared = _shared_cubic()
    a = shared * Poly.from_coeffs([Q(1, 2), Q(1)])     # shared * (x + 1/2)
    b = shared * Poly.from_coeffs([Q(-1), Q(2)])       # shared * (2x - 1)
    return a, b, shared


def test_gcd_higher_degree_rational_monic_shared():
    a, b, shared = _overflow_regime_pair()
    g = a.gcd(b)
    assert g == shared                                 # monic shared cubic, exact
    assert a.divmod(g)[1].is_zero and b.divmod(g)[1].is_zero
    assert g.leading == Q(1)


# ── KEYSTONE: bignum gcd parity vs the Fraction oracle (pure path) ─────────────
def _f_trim(cs):
    cs = list(cs)
    while cs and cs[-1] == 0:
        cs.pop()
    return cs


def _f_divmod(a, b):
    a, b = _f_trim(a), _f_trim(b)
    rem = list(a)
    while _f_trim(rem) and len(_f_trim(rem)) - 1 >= len(b) - 1:
        rem = _f_trim(rem)
        rdeg = len(rem) - 1
        sh = rdeg - (len(b) - 1)
        f = rem[rdeg] / b[-1]
        for j in range(len(b)):
            rem[sh + j] -= f * b[j]
        rem = _f_trim(rem)
    return _f_trim(rem)


def _f_gcd(a, b):
    a, b = _f_trim(a), _f_trim(b)
    while b:
        a, b = b, _f_divmod(a, b)
    a = _f_trim(a)
    if not a:
        return []
    inv = Fraction(1) / a[-1]
    return [c * inv for c in a]


def test_bignum_gcd_matches_fraction_oracle():
    shared = Poly.from_coeffs([Q(-(10 ** 50), 3 ** 33), Q(1)])  # x - 10^50/3^33
    a = shared * Poly.from_coeffs([Q(7 ** 40, 13), Q(2)])
    b = shared * Poly.from_coeffs([Q(-(5 ** 44), 17), Q(3)])
    g = a.gcd(b)
    assert a.divmod(g)[1].is_zero and b.divmod(g)[1].is_zero
    assert g.leading == Q(1)
    assert _fracs(g) == _f_gcd(_fracs(a), _fracs(b))


# ── Python == C gcd parity (native present only) ──────────────────────────────
def _native_poly():
    try:
        from srmech.amsc import _native
    except ImportError:
        return None
    if not getattr(_native, "has_native_poly_gcd", lambda: False)():
        return None
    return _native


def test_python_equals_c_gcd_keystone():
    nat = _native_poly()
    if nat is None:
        pytest.skip("native srmech_poly_gcd absent — pure Euclid is the complete alternative")
    # 1) the bignum keystone (41+ digit coefficients)
    shared = Poly.from_coeffs([Q(-(10 ** 50), 3 ** 33), Q(1)])
    a = shared * Poly.from_coeffs([Q(7 ** 40, 13), Q(2)])
    b = shared * Poly.from_coeffs([Q(-(5 ** 44), 17), Q(3)])
    cg = nat.poly_gcd_c([(c.numerator, c.denominator) for c in a.coeffs],
                        [(c.numerator, c.denominator) for c in b.coeffs])
    pg = a.gcd(b)
    assert tuple(cg) == tuple((c.numerator, c.denominator) for c in pg.coeffs)
    # 2) the higher-degree rational regime (the rc38 OVERFLOW case) — zero overflow
    a2, b2, _ = _overflow_regime_pair()
    cg2 = nat.poly_gcd_c([(c.numerator, c.denominator) for c in a2.coeffs],
                         [(c.numerator, c.denominator) for c in b2.coeffs])
    pg2 = a2.gcd(b2)
    assert tuple(cg2) == tuple((c.numerator, c.denominator) for c in pg2.coeffs)
    # 3) coprime + gcd(p, 0) edge cases through C
    assert tuple(nat.poly_gcd_c([(0, 1), (1, 1)], [(3, 1), (1, 1)])) == ((1, 1),)
    assert tuple(nat.poly_gcd_c([(4, 1), (0, 1), (2, 1)], [])) == ((2, 1), (0, 1), (1, 1))


def test_python_equals_c_gcd_random_chain():
    nat = _native_poly()
    if nat is None:
        pytest.skip("native srmech_poly_gcd absent")
    import random
    random.seed(2026)
    for _ in range(40):
        dg = random.randint(1, 3)
        sh = [Q(random.randint(-6, 6), random.choice([1, 2, 3])) for _ in range(dg)]
        sh.append(Q(1))
        shared = Poly.from_coeffs(sh)
        fa = [Q(random.randint(-6, 6), random.choice([1, 2, 3]))
              for _ in range(random.randint(1, 2))] + [Q(1)]
        fb = [Q(random.randint(-6, 6), random.choice([1, 2, 3]))
              for _ in range(random.randint(1, 2))] + [Q(1)]
        a = shared * Poly.from_coeffs(fa)
        b = shared * Poly.from_coeffs(fb)
        cg = nat.poly_gcd_c([(c.numerator, c.denominator) for c in a.coeffs],
                            [(c.numerator, c.denominator) for c in b.coeffs])
        pg = a.gcd(b)
        assert tuple(cg) == tuple((c.numerator, c.denominator) for c in pg.coeffs)


# ── resultant: the known identities ───────────────────────────────────────────
def test_resultant_known_values():
    # Res(x^2 - 1, x - 2) = 3 (= product-of-differences ∏ q(roots of p))
    assert _P(-1, 0, 1).resultant(_P(-2, 1)) == Q(3)
    # Res(x - a, x - b) = a - b
    assert _P(-3, 1).resultant(_P(-7, 1)) == Q(-4)     # a-b = 3 - 7
    assert _P(-5, 1).resultant(_P(-2, 1)) == Q(3)      # a-b = 5 - 2
    # Res(p, c) = c^deg p for a constant c
    assert _P(1, 0, 1).resultant(_P(5)) == Q(25)       # 5^2
    assert _P(0, 0, 0, 1).resultant(_P(2)) == Q(8)     # 2^3
    # shared factor ⇒ resultant 0
    assert _P(-2, 0, 1).resultant(_P(-2, 0, 1)) == Q(0)
    assert _P(-1, 0, 1).resultant(_P(-1, 1)) == Q(0)   # (x^2-1) and (x-1) share (x-1)


def test_resultant_product_of_differences_crosscheck():
    # Res(p, q) = lc(p)^deg q · ∏_{r: p(r)=0} q(r). p = (x-2)(x-3) = x^2 -5x +6.
    p = _P(6, -5, 1)
    q = _P(-7, 1)                                       # x - 7
    # roots of p are 2, 3 → q(2)·q(3) = (-5)(-4) = 20 ; lc(p)=1, deg q=1
    assert p.resultant(q) == Q(20)


def test_resultant_exact_rational():
    # exact-ℚ coefficients stay exact through the PRS
    p = Poly.from_coeffs([Q(1, 2), Q(0), Q(1)])        # x^2 + 1/2
    q = Poly.from_coeffs([Q(-1, 3), Q(1)])             # x - 1/3
    # roots of q: 1/3 ; Res = lc(p)^1 · ... use product def: lc(q)^deg p · ∏ p(roots q)
    # Res(p,q) = (-1)^(2·1) lc(q)^2 p(1/3) = 1·1·((1/9)+(1/2)) = 11/18
    assert p.resultant(q) == Q(11, 18)


# ── dispersion: the standard Gosper convention ────────────────────────────────
def test_dispersion_known_values():
    x = _P(0, 1)
    assert x.dispersion(x) == [0]                       # gcd(k, k) at h=0
    assert (x * _P(5, 1)).dispersion(x) == [0, 5]       # x(x+5) vs x
    assert _P(1, 0, 1).dispersion(x) == []              # x^2+1 vs x: no overlap
    # standard convention: dispersion(x, x+3) is [] (root mismatch is at h=-3<0)
    assert x.dispersion(_P(3, 1)) == []
    # the spec's [3] is the OPPOSITE shift direction — recovered by swapping args
    assert _P(3, 1).dispersion(x) == [3]


def test_dispersion_larger_overlap():
    x = _P(0, 1)
    # p = x(x+2)(x+7), q = x : roots of p are 0,-2,-7 ; q(k+h)=k+h root -h
    # overlap when -h ∈ {0,-2,-7} → h ∈ {0,2,7}
    p = x * _P(2, 1) * _P(7, 1)
    assert p.dispersion(x) == [0, 2, 7]


def test_dispersion_rational_roots_excluded():
    # p has a NON-integer root spread vs q → only integer shifts count
    x = _P(0, 1)
    # p = (x)(x + 3) , q = (x + 1)  : q(k+h) root = -(1+h); p roots 0,-3
    #   -(1+h)=0 → h=-1 (excluded) ; -(1+h)=-3 → h=2 (kept)
    p = x * _P(3, 1)
    assert p.dispersion(_P(1, 1)) == [2]
