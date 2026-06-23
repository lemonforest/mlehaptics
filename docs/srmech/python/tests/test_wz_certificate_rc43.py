"""§76 (F929) — the Wilf–Zeilberger pair method ``wz_certificate.wz_certificate``.

The THIRD and FINAL public op of the §76 "telescope" Σ-row closed-form prover —
the Σ-row CLOSER (gosper → zeilberger → wz_certificate). Given a proper
hypergeometric term ``F(n,k)`` (the NORMALIZED summand of a terminating identity
``Σ_k F(n,k) = const``) by its TWO term ratios ``r_n = F(n+1,k)/F(n,k)`` and
``r_k = F(n,k+1)/F(n,k)`` (each a bivariate exact-``ℚ[n,k]`` ``BiPoly`` num/den
pair), ``wz_certificate`` PRODUCES + VERIFIES the WZ certificate ``R(n,k)`` whose
companion ``G = R·F`` makes the WZ equation ``F(n+1,k)−F(n,k) = G(n,k+1)−G(n,k)``
hold.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``BiPoly``
carriers + plain Python arithmetic. **Every WZ pair is checked TWO ways**:
  (a) the returned certificate satisfies the WZ equation at CONCRETE integer
      ``(n,k)`` (evaluate ``F``, ``G = R·F`` as exact ``Q``/``Fraction`` and assert
      ``F(n+1,k)−F(n,k) == G(n,k+1)−G(n,k)``);
  (b) the certified sum ``Σ_k F(n,k)`` is CONSTANT in ``n`` (the identity itself).

Coverage (the rc43 acceptance set; each ``F`` normalized so ``Σ_k F = 1``):
  (1) Σ_k C(n,k) = 2ⁿ    -> F=C(n,k)/2ⁿ;   R = −k/(2(n+1−k))  (the classic WZ cert)
  (2) Σ_k C(n,k)² = C(2n,n) -> F=C(n,k)²/C(2n,n) (the Wilf–Zeilberger 1990 pair)
  (3) Σ_k C(n,k)·2^k = 3ⁿ -> F=C(n,k)·2^k/3ⁿ  (a Chu–Vandermonde-style geometric case)
  (4) negative/edge: a non-WZ-summable term (a non-constant raw sum) returns None;
  plus a Python-op == C-peer parity check.
"""

from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.zeilberger import BiPoly
from srmech.amsc.wz_certificate import wz_certificate


# ── helpers (Fraction + Q only; no numpy, no math) ────────────────────────────

def _comb(n: int, k: int) -> int:
    """Binomial C(n,k) by exact integer arithmetic (no ``import math``)."""
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num = 1
    for i in range(k):
        num = num * (n - i) // (i + 1)
    return num


def _bi_eval(b: BiPoly, nv: int, kv: int) -> Fraction:
    """Evaluate a ``BiPoly`` at integer ``(nv, kv)`` → exact ``Fraction``."""
    s = Fraction(0)
    for dk, kp in enumerate(b.terms):
        c = kp.eval(Q(nv, 1))
        s += Fraction(c.numerator, c.denominator) * Fraction(kv) ** dk
    return s


def _wz_equation_holds(cert, F, nmax: int, kmax: int) -> int:
    """Assert the WZ equation ``F(n+1,k)−F(n,k) == G(n,k+1)−G(n,k)`` (``G=R·F``,
    ``R=Xn/Xd``) at every integer ``(n,k)`` where ``Xd ≠ 0``. Returns the number of
    points checked (must be > 0). Raises ``AssertionError`` on any mismatch."""
    xn, xd = cert["num"], cert["den"]

    def R(nv, kv):
        d = _bi_eval(xd, nv, kv)
        return None if d == 0 else _bi_eval(xn, nv, kv) / d

    def G(nv, kv):
        r = R(nv, kv)
        return None if r is None else r * F(nv, kv)

    checked = 0
    for n in range(1, nmax):
        for k in range(0, kmax):
            g0, g1 = G(n, k), G(n, k + 1)
            if g0 is None or g1 is None:
                continue
            lhs = F(n + 1, k) - F(n, k)
            rhs = g1 - g0
            assert lhs == rhs, f"WZ equation failed at n={n}, k={k}: {lhs} != {rhs}"
            checked += 1
    return checked


def _sum_is_constant(F, nmax: int, kmax: int) -> Fraction:
    """Assert ``Σ_k F(n,k)`` is the SAME constant for ``n = 1..nmax−1``; return it."""
    sums = [sum(F(n, k) for k in range(0, kmax)) for n in range(1, nmax)]
    assert all(s == sums[0] for s in sums), f"sum not constant in n: {sums}"
    return sums[0]


# ── the four ratios for the canonical NORMALIZED proper terms ─────────────────

def _ratios_binomial():
    """F(n,k)=C(n,k)/2ⁿ (Σ_k F=1): r_n=(n+1)/(2(n+1−k)), r_k=(n−k)/(k+1)."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                          # n+1
    rn_den = BiPoly([Poly.from_coeffs([2, 2]), Poly.from_coeffs([-2])])  # 2(n+1) − 2k
    rk_num = BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])  # n − k
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # k + 1
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_squared():
    """F(n,k)=C(n,k)²/C(2n,n) (Σ_k F=1; the WZ 1990 pair):
    r_n=(n+1)³/(2(2n+1)(n+1−k)²), r_k=((n−k)/(k+1))²."""
    rn_num = BiPoly([Poly.from_coeffs([1, 3, 3, 1])])                    # (n+1)³
    rn_den = BiPoly([Poly.from_coeffs([2, 8, 10, 4]),                    # 2(2n+1)(n+1−k)²
                     Poly.from_coeffs([-4, -12, -8]),
                     Poly.from_coeffs([2, 4])])
    rk_num = BiPoly([Poly.from_coeffs([0, 0, 1]),                        # (n−k)²
                     Poly.from_coeffs([0, -2]), Poly.from_coeffs([1])])
    rk_den = BiPoly([Poly.from_coeffs([1]),                             # (k+1)²
                     Poly.from_coeffs([2]), Poly.from_coeffs([1])])
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_two_k():
    """F(n,k)=C(n,k)·2^k/3ⁿ (Σ_k F=1; a Chu–Vandermonde geometric case):
    r_n=(n+1)/(3(n+1−k)), r_k=2(n−k)/(k+1)."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                          # n+1
    rn_den = BiPoly([Poly.from_coeffs([3, 3]), Poly.from_coeffs([-3])])  # 3(n+1−k)
    rk_num = BiPoly([Poly.from_coeffs([0, 2]), Poly.from_coeffs([-2])])  # 2(n−k)
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # k + 1
    return rn_num, rn_den, rk_num, rk_den


# ── the acceptance cases (verified by EVALUATION + by sum-constancy) ──────────

def test_case1_binomial_identity_sum_two_to_the_n():
    """Σ_k C(n,k) = 2ⁿ: F=C(n,k)/2ⁿ, Σ_k F=1. The certificate is the classic
    R(n,k) = −k/(2(n+1−k)); verify the WZ equation at concrete (n,k) AND the
    sum-is-1 identity."""
    res = wz_certificate(*_ratios_binomial())
    assert res is not None
    assert res["verified"] is True

    def F(n, k):                                 # normalized summand
        return Fraction(_comb(n, k), 2 ** n)

    assert _wz_equation_holds(res["certificate"], F, 7, 9) > 0
    assert _sum_is_constant(F, 7, 9) == Fraction(1)
    # the certificate IS R = −k/(2(n+1−k)): num = −k, den = 2(n+1−k).
    xn, xd = res["certificate"]["num"], res["certificate"]["den"]
    assert xn == BiPoly([Poly.zero(), Poly.from_coeffs([-1])])           # −k
    assert xd == BiPoly([Poly.from_coeffs([2, 2]), Poly.from_coeffs([-2])])  # 2(n+1−k)


def test_case2_binomial_squared_central_binomial():
    """Σ_k C(n,k)² = C(2n,n) (the Wilf–Zeilberger 1990 pair): F=C(n,k)²/C(2n,n),
    Σ_k F=1. Verify the WZ equation by evaluation AND the sum-is-1 identity."""
    res = wz_certificate(*_ratios_binomial_squared())
    assert res is not None
    assert res["verified"] is True

    def F(n, k):
        return Fraction(_comb(n, k) ** 2, _comb(2 * n, n))

    assert _wz_equation_holds(res["certificate"], F, 7, 9) > 0
    assert _sum_is_constant(F, 7, 9) == Fraction(1)


def test_case3_binomial_times_two_to_the_k():
    """Σ_k C(n,k)·2^k = 3ⁿ: F=C(n,k)·2^k/3ⁿ, Σ_k F=1 (Chu–Vandermonde geometric).
    Verify the WZ equation by evaluation AND the sum-is-1 identity."""
    res = wz_certificate(*_ratios_binomial_two_k())
    assert res is not None
    assert res["verified"] is True

    def F(n, k):
        return Fraction(_comb(n, k) * 2 ** k, 3 ** n)

    assert _wz_equation_holds(res["certificate"], F, 7, 9) > 0
    assert _sum_is_constant(F, 7, 9) == Fraction(1)


def test_case4_non_wz_summable_returns_none():
    """A term whose sum is NOT constant in n (e.g. the RAW C(n,k), Σ_k=2ⁿ — the
    un-normalized summand) is not WZ-summable: the forced f(n+1)−f(n)=0 recurrence
    does not hold, so ``wz_certificate`` returns None cleanly."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                          # n+1
    rn_den = BiPoly([Poly.from_coeffs([1, 1]), Poly.from_coeffs([-1])])  # (n+1) − k
    rk_num = BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])  # n − k
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # k + 1
    assert wz_certificate(rn_num, rn_den, rk_num, rk_den) is None


def test_zero_denominator_rejected():
    """A zero r_n / r_k denominator (an invalid term ratio) raises ValueError."""
    with pytest.raises(ValueError):
        wz_certificate(BiPoly([Poly.from_coeffs([1])]), BiPoly.zero(),
                       BiPoly([Poly.from_coeffs([1])]),
                       BiPoly([Poly.from_coeffs([1])]))


def test_poly_and_coefficient_operands_accepted():
    """A plain ``Poly`` operand is read as a polynomial in k; the explicit BiPoly
    form is the same object. (The constant-in-k binomial-style normalized term is
    the canonical case, but coercion must accept the lighter forms.)"""
    res = wz_certificate(Poly.from_coeffs([1, 1]),       # 1 + k  (r_n num, as k-poly)
                         BiPoly([Poly.from_coeffs([2, 2]), Poly.from_coeffs([-2])]),
                         BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])]),
                         BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])]))
    # 1 + k as the r_n numerator is NOT the binomial term ratio (n+1), so this is a
    # DIFFERENT term — the point is only that the Poly operand coerces + runs without
    # error (returns a dict-or-None, never a TypeError).
    assert res is None or (res["verified"] is True)


def test_native_matches_pure_when_present():
    """When the native srmech_wz_verify is loaded, its VERIFY decision is identical
    to the pure-Python bivariate-ℚ compare (the parity oracle), on the genuine
    certificate AND on a deliberately-wrong one. Skip-clean when no native lib."""
    from srmech.amsc import _native as nat
    from srmech.amsc.wz_certificate import _verify_wz_equation_pure
    if not nat.has_native_wz_verify():
        pytest.skip("native srmech_wz_verify not present in this environment")

    cases = [_ratios_binomial(), _ratios_binomial_squared(), _ratios_binomial_two_k()]

    def to_pairs(b):
        return [[(c.numerator, c.denominator) for c in kp.coeffs] for kp in b.terms]

    for rn, rd, kn, kd in cases:
        res = wz_certificate(rn, rd, kn, kd)
        assert res is not None and res["verified"] is True
        xn, xd = res["certificate"]["num"], res["certificate"]["den"]
        # the genuine certificate: C verify == pure verify == True.
        cval = nat.wz_verify_c(to_pairs(rn), to_pairs(rd), to_pairs(kn),
                               to_pairs(kd), to_pairs(xn), to_pairs(xd))
        pval = _verify_wz_equation_pure(rn, rd, kn, kd, xn, xd)
        assert cval is True and pval is True
        # a WRONG certificate (numerator scaled by 2): C verify == pure verify == False.
        wrong = xn.scale_n(Poly.from_coeffs([2]))
        cbad = nat.wz_verify_c(to_pairs(rn), to_pairs(rd), to_pairs(kn),
                               to_pairs(kd), to_pairs(wrong), to_pairs(xd))
        pbad = _verify_wz_equation_pure(rn, rd, kn, kd, wrong, xd)
        assert cbad is False and pbad is False
