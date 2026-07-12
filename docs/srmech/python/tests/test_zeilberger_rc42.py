"""§76 (F929) — Zeilberger's creative telescoping ``zeilberger.zeilberger``.

The SECOND public op of the §76 "telescope" Σ-row closed-form prover. Given a
proper hypergeometric term ``F(n,k)`` by its TWO term ratios ``r_n = F(n+1,k)/
F(n,k)`` and ``r_k = F(n,k+1)/F(n,k)`` (each a bivariate exact-``ℚ[n,k]``
``BiPoly``), it returns the minimal-order linear recurrence with polynomial
coefficients ``Σ_j a_j(n) f(n+j) = 0`` satisfied by the definite sum
``f(n) = Σ_k F(n,k)``, plus the rational certificate.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``BiPoly``
carriers + plain Python arithmetic. **Every recurrence is cross-checked by DIRECT
SUMMATION** — the actual term values are summed to get ``f(n) = Σ_k F(n,k)`` and
the returned recurrence ``Σ_j a_j(n) f(n+j)`` is asserted to be exactly ``0`` at
several integer ``n`` (never trusting the algorithm symbolically).

Coverage (the rc42 acceptance set):
  (1) F(n,k)=C(n,k)    -> f(n)=2^n,      order 1: f(n+1) − 2 f(n) = 0
  (2) F(n,k)=C(n,k)^2  -> f(n)=C(2n,n),  order 1: (n+1) f(n+1) − (4n+2) f(n) = 0
  (3) F(n,k)=C(n,k)·2^k -> f(n)=3^n,     order 1: f(n+1) − 3 f(n) = 0
  (4) negative/edge: a term with no recurrence ≤ max_order returns None
  plus the WZ-certificate telescoping identity and a Python-op == C-peer parity.
"""

from fractions import Fraction

import pytest

from srmech.amsc.poly import Poly
from srmech.amsc.q import Q
from srmech.amsc.zeilberger import BiPoly, zeilberger


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


def _recurrence_holds(res, f, nmax: int) -> bool:
    """Assert ``Σ_{j=0}^{L} a_j(n)·f(n+j) == 0`` for ``n = 0..nmax-1`` EXACTLY,
    with ``f`` the concrete term sum and ``a_j`` the returned recurrence coeffs."""
    order, coeffs = res["order"], res["coeffs"]
    for n in range(nmax):
        s = Fraction(0)
        for j in range(order + 1):
            cj = coeffs[j].eval(Q(n, 1))
            s += Fraction(cj.numerator, cj.denominator) * Fraction(f(n + j))
        if s != 0:
            return False
    return True


# ── the four ratios for the canonical proper terms ───────────────────────────

def _ratios_binomial():
    """F(n,k)=C(n,k): r_n=(n+1)/(n+1−k), r_k=(n−k)/(k+1)."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])                      # n+1
    rn_den = BiPoly([Poly.from_coeffs([1, 1]), Poly.from_coeffs([-1])])  # (n+1) − k
    rk_num = BiPoly([Poly.from_coeffs([0, 1]), Poly.from_coeffs([-1])])  # n − k
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])      # k + 1
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_squared():
    """F(n,k)=C(n,k)^2: r_n=((n+1)/(n+1−k))^2, r_k=((n−k)/(k+1))^2."""
    rn_num = BiPoly([Poly.from_coeffs([1, 2, 1])])                   # (n+1)^2
    rn_den = BiPoly([Poly.from_coeffs([1, 2, 1]),                    # (n+1−k)^2
                     Poly.from_coeffs([-2, -2]), Poly.from_coeffs([1])])
    rk_num = BiPoly([Poly.from_coeffs([0, 0, 1]),                    # (n−k)^2
                     Poly.from_coeffs([0, -2]), Poly.from_coeffs([1])])
    rk_den = BiPoly([Poly.from_coeffs([1]),                          # (k+1)^2
                     Poly.from_coeffs([2]), Poly.from_coeffs([1])])
    return rn_num, rn_den, rk_num, rk_den


def _ratios_binomial_two_k():
    """F(n,k)=C(n,k)·2^k: r_n=(n+1)/(n+1−k), r_k=2(n−k)/(k+1)."""
    rn_num = BiPoly([Poly.from_coeffs([1, 1])])
    rn_den = BiPoly([Poly.from_coeffs([1, 1]), Poly.from_coeffs([-1])])
    rk_num = BiPoly([Poly.from_coeffs([0, 2]), Poly.from_coeffs([-2])])  # 2(n − k)
    rk_den = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])
    return rn_num, rn_den, rk_num, rk_den


# ── the acceptance cases (cross-checked by concrete summation) ────────────────

def test_case1_binomial_to_two_to_the_n():
    """F(n,k)=C(n,k), f(n)=Σ_k C(n,k)=2^n. Minimal recurrence order 1; assert
    Σ_j a_j(n)·f(n+j)=0 with f the actual Σ_k C(n,k) for n=0..8."""
    res = zeilberger(*_ratios_binomial(), max_order=4)
    assert res is not None
    assert res["order"] == 1

    def f(n):                                    # f(n) = Σ_k C(n,k) = 2^n
        return sum(_comb(n, k) for k in range(n + 1))

    assert _recurrence_holds(res, f, 9)
    # the order-1 recurrence is f(n+1) − 2 f(n) = 0 (coeffs proportional to [−2, 1]).
    a0, a1 = res["coeffs"]
    r = Fraction(a0.eval(Q(0, 1)).numerator, a0.eval(Q(0, 1)).denominator) / \
        Fraction(a1.eval(Q(0, 1)).numerator, a1.eval(Q(0, 1)).denominator)
    assert r == Fraction(-2), "a_0/a_1 must be −2 (f(n+1) = 2 f(n))"


def test_case2_binomial_squared_to_central_binomial():
    """F(n,k)=C(n,k)^2, f(n)=Σ_k C(n,k)^2=C(2n,n). Order 1: (n+1) f(n+1) −
    (4n+2) f(n)=0; assert with the actual Σ_k C(n,k)^2 for n=0..7."""
    res = zeilberger(*_ratios_binomial_squared(), max_order=4)
    assert res is not None
    assert res["order"] == 1

    def f(n):                                    # f(n) = Σ_k C(n,k)^2 = C(2n,n)
        return sum(_comb(n, k) ** 2 for k in range(n + 1))

    assert _recurrence_holds(res, f, 8)
    # check the coefficients ARE (up to an overall scale) (n+1) and −(4n+2):
    a0, a1 = res["coeffs"]
    for n in range(0, 6):
        c0 = a0.eval(Q(n, 1))
        c1 = a1.eval(Q(n, 1))
        # (n+1)/(4n+2) == −c1/c0  ⇔  c0·(n+1) + c1·... ; check the ratio invariant
        lhs = Fraction(c1.numerator, c1.denominator) * Fraction(4 * n + 2)
        rhs = -Fraction(c0.numerator, c0.denominator) * Fraction(n + 1)
        assert lhs == rhs, f"C(2n,n) recurrence ratio failed at n={n}"


def test_case3_binomial_times_two_to_the_k():
    """F(n,k)=C(n,k)·2^k, f(n)=Σ_k C(n,k) 2^k=(1+2)^n=3^n. Order 1: f(n+1)−3 f(n)=0."""
    res = zeilberger(*_ratios_binomial_two_k(), max_order=4)
    assert res is not None
    assert res["order"] == 1

    def f(n):
        return sum(_comb(n, k) * 2 ** k for k in range(n + 1))

    assert _recurrence_holds(res, f, 9)
    a0, a1 = res["coeffs"]
    r = Fraction(a0.eval(Q(0, 1)).numerator, a0.eval(Q(0, 1)).denominator) / \
        Fraction(a1.eval(Q(0, 1)).numerator, a1.eval(Q(0, 1)).denominator)
    assert r == Fraction(-3), "f(n+1) = 3 f(n) for (1+2)^n"


def test_case4_no_recurrence_within_max_order_returns_none():
    """A term whose minimal recurrence exceeds ``max_order`` returns None cleanly.
    C(n,k) needs order 1, so ``max_order=0`` must return None (the negative/edge)."""
    res = zeilberger(*_ratios_binomial(), max_order=0)
    assert res is None


def test_certificate_telescoping_identity():
    """The returned certificate ``R(n,k)=x/D_P`` satisfies the Gosper telescoping
    relation ``Σ_j a_j(n) F(n+j,k) = G(n,k+1) − G(n,k)`` with ``G=R·F`` — the WZ
    proof certificate. Verified numerically at interior (n,k) where D_P ≠ 0."""
    rn_num, rn_den, rk_num, rk_den = _ratios_binomial()
    res = zeilberger(rn_num, rn_den, rk_num, rk_den, max_order=4)
    assert res is not None
    order, coeffs, cert = res["order"], res["coeffs"], res["certificate"]

    def bi_eval(b: BiPoly, nv, kv):
        s = Fraction(0)
        for dk, kp in enumerate(b.terms):
            c = kp.eval(Q(nv, 1))
            s += Fraction(c.numerator, c.denominator) * Fraction(kv) ** dk
        return s

    def dp(nv, kv):                              # D_P = Π_{i<order} rn_den(n+i,k)
        p = Fraction(1)
        for i in range(order):
            p *= bi_eval(rn_den, nv + i, kv)
        return p

    def fv(nv, kv):
        return Fraction(_comb(nv, kv)) if 0 <= kv <= nv else Fraction(0)

    def rv(nv, kv):
        return bi_eval(cert, nv, kv) / dp(nv, kv)

    checked = 0
    for n in range(2, 7):
        for k in range(0, n):                    # interior: D_P ≠ 0
            if dp(n, k) == 0 or dp(n, k + 1) == 0:
                continue
            lhs = sum(
                Fraction(coeffs[j].eval(Q(n, 1)).numerator,
                         coeffs[j].eval(Q(n, 1)).denominator) * fv(n + j, k)
                for j in range(order + 1))
            rhs = rv(n, k + 1) * fv(n, k + 1) - rv(n, k) * fv(n, k)
            assert lhs == rhs, f"certificate telescoping failed at n={n}, k={k}"
            checked += 1
    assert checked > 0


def test_poly_and_coefficient_list_operands_accepted():
    """A term-ratio operand accepts a plain ``Poly`` (read as a polynomial in k —
    each k-coeff a constant-in-n) and the explicit BiPoly form, coerced consistently.
    A bare ``Poly`` ``1 + k`` and the BiPoly built from its constant-in-n k-coeffs
    are the SAME object; the n-polynomial form ``1 + n`` is a DIFFERENT (k-constant)
    BiPoly — coercion keeps the two regimes distinct."""
    as_k_poly = BiPoly.coerce(Poly.from_coeffs([1, 1]))        # 1 + k  (k-degree 1)
    explicit_k = BiPoly([Poly.from_coeffs([1]), Poly.from_coeffs([1])])  # 1 + k
    assert as_k_poly == explicit_k
    # the n-polynomial regime (constant in k) is distinct:
    as_n_poly = BiPoly.from_n_poly(Poly.from_coeffs([1, 1]))   # 1 + n  (k-degree 0)
    assert as_n_poly != as_k_poly
    assert as_n_poly.k_degree == 0


def test_zero_denominator_rejected():
    """A zero r_n / r_k denominator (an invalid term ratio) raises ValueError."""
    with pytest.raises(ValueError):
        zeilberger(BiPoly([Poly.from_coeffs([1])]), BiPoly.zero(),
                   BiPoly([Poly.from_coeffs([1])]), BiPoly([Poly.from_coeffs([1])]))


def test_native_matches_pure_when_present():
    """When the native srmech_zeilberger is loaded, its recurrence is identical to
    the pure-Python body (the parity oracle). Skip-clean when no native lib."""
    from srmech.amsc import _native as nat
    from srmech.amsc.zeilberger import _zeilberger_pure
    if not nat.has_native_zeilberger():
        pytest.skip("native srmech_zeilberger not present in this environment")

    cases = [_ratios_binomial(), _ratios_binomial_squared(), _ratios_binomial_two_k()]

    def repr_res(r):
        if r is None:
            return None
        return (r["order"],
                tuple(tuple((v.numerator, v.denominator) for v in c.coeffs)
                      for c in r["coeffs"]))

    for ratios in cases:
        native = zeilberger(*ratios, max_order=4)        # native path
        pure = _zeilberger_pure(*(BiPoly.coerce(x) for x in ratios), 4)
        assert repr_res(native) == repr_res(pure), (
            "native/pure mismatch for a term ratio")
