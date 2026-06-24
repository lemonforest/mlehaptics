"""q-hypergeometric F929 row (rc55) — q-Gosper indefinite summation ``q_gosper``.

The FIRST public op of the q-hypergeometric F929 reduction row (the q-analog of the
§76 ``gosper``). Given a q-hypergeometric term by its term ratio ``t(k+1)/t(k) =
r(x) = num(x)/den(x)`` (``x = qᵏ``, two Laurent-in-x exact-ℚ[q] ``QPoly``), it
returns the rational certificate ``R(x)`` with q-antidifference ``T(k) = R(qᵏ)·t(k)``
(so ``Σ t(k)`` telescopes), or ``None`` when no q-hypergeometric closed form exists.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it
uses only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``QPoly`` carriers
+ plain Python arithmetic. **Every certificate is cross-checked TWO ways** — the
exact q-antidifference identity ``Δ_q(R·t) = T(k+1) − T(k) = t(k)`` at integer ``k``
for several numeric ``q``, AND a CONCRETE SUMMATION ``Σ t == T(top) − T(bottom)``
(never trusting the algorithm symbolically).

Coverage (the rc55 acceptance set):
  (1) t(k)=qᵏ          ratio r=q       -> R = 1/(q−1)        (q-geometric)
  (2) t(k)=2ᵏ          ratio r=2       -> R = 1               (numeric geometric)
  (3) t(k)=q^(2k)      ratio r=q²      -> R = 1/(q²−1)
  (4) t(k) for T=q^(2k)−q^k (a GP-nontrivial constructed antidifference)
  (5) the q-partial-theta t(k)=q^(k(k−1)/2) (ratio r=x) -> None  (NEGATIVE test)
  (6) the q-harmonic-like (x−1)/(qx−1) -> None  (the load-bearing NEGATIVE test)
  plus coercion forms, a zero-denominator reject, and a Python-op == C-peer parity
  check (skip-clean when no native lib).
"""

from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.qpoly import QPoly
from srmech.amsc.q_gosper import q_gosper


# ── helpers (Fraction + Q only; no numpy, no math) ────────────────────────────

def _R_at(cert, qv: int, xv) -> Fraction:
    """The certificate rational ``R(x) = num(x)/den(x)`` evaluated at exact
    ``(q, x)`` → a ``Fraction``."""
    num = cert["num"].eval(Q(qv, 1), Q(xv, 1))
    den = cert["den"].eval(Q(qv, 1), Q(xv, 1))
    return (Fraction(num.numerator, num.denominator)
            / Fraction(den.numerator, den.denominator))


def _assert_q_antidifference(cert, tfn, *, qs=(2, 3, 5), kmax=7):
    """Assert the q-antidifference identity ``Δ_q(R·t) = T(k+1) − T(k) = t(k)``
    EXACTLY at integer ``k`` for several numeric ``q`` (T(k) = R(qᵏ)·t(k))."""
    for qv in qs:
        def big_t(k):
            return _R_at(cert, qv, qv ** k) * tfn(qv, k)
        for k in range(0, kmax):
            assert big_t(k + 1) - big_t(k) == tfn(qv, k), (
                f"Δ_q(R·t) ≠ t at q={qv}, k={k}")


# ── the acceptance cases ──────────────────────────────────────────────────────

def test_case1_q_geometric_sum_q_to_the_k():
    """t(k)=qᵏ, ratio r=q (a constant in x). Certificate R=1/(q−1); assert
    Δ_q(R·t)=t AND Σ_{k=0}^{n−1} qᵏ == T(n) − T(0) == (qⁿ−1)/(q−1)."""
    cert = q_gosper(QPoly.from_dict({(0, 1): Q(1, 1)}), QPoly.one())   # num=q, den=1
    assert cert is not None, "Σ qᵏ must have a q-hypergeometric antidifference"
    assert set(cert) == {"num", "den"}
    assert isinstance(cert["num"], QPoly) and isinstance(cert["den"], QPoly)

    def t(qv, k):
        return Fraction(qv) ** k

    _assert_q_antidifference(cert, t)
    for qv in (2, 3, 5):
        def big_t(k):
            return _R_at(cert, qv, qv ** k) * t(qv, k)
        for n in range(1, 8):
            s = sum((t(qv, k) for k in range(n)), Fraction(0))
            assert s == big_t(n) - big_t(0), f"telescope failed q={qv} n={n}"
            assert s == Fraction(qv ** n - 1, qv - 1), f"closed form q={qv} n={n}"


def test_case2_numeric_geometric_two_to_the_k():
    """t(k)=2ᵏ, ratio r=2 (a numeric constant; q-independent). R=1 (a constant);
    assert Σ_{k=0}^{n−1} 2ᵏ == 2ⁿ − 1 == T(n) − T(0)."""
    cert = q_gosper(QPoly.from_dict({(0, 0): Q(2, 1)}), QPoly.one())   # num=2, den=1
    assert cert is not None

    def t(qv, k):
        return Fraction(2) ** k

    _assert_q_antidifference(cert, t)
    for qv in (2, 3, 5):
        def big_t(k):
            return _R_at(cert, qv, qv ** k) * t(qv, k)
        for n in range(1, 8):
            s = sum((t(qv, k) for k in range(n)), Fraction(0))
            assert s == big_t(n) - big_t(0)
            assert s == Fraction(2 ** n - 1)


def test_case3_q_geometric_q_squared():
    """t(k)=q^(2k), ratio r=q². R=1/(q²−1); assert Δ_q(R·t)=t and the concrete
    Σ_{k=0}^{n−1} q^(2k) == (q^(2n)−1)/(q²−1)."""
    cert = q_gosper(QPoly.from_dict({(0, 2): Q(1, 1)}), QPoly.one())   # num=q², den=1
    assert cert is not None

    def t(qv, k):
        return Fraction(qv) ** (2 * k)

    _assert_q_antidifference(cert, t)
    for qv in (2, 3, 5):
        def big_t(k):
            return _R_at(cert, qv, qv ** k) * t(qv, k)
        for n in range(1, 7):
            s = sum((t(qv, k) for k in range(n)), Fraction(0))
            assert s == big_t(n) - big_t(0)
            assert s == Fraction(qv ** (2 * n) - 1, qv * qv - 1)


def test_case4_gp_nontrivial_constructed_antidifference():
    """A GP-NONTRIVIAL summable term: T(k)=q^(2k)−q^k (= x²−x, x=qᵏ), so
    t(k)=T(k+1)−T(k)=(q²−1)q^(2k)−(q−1)qᵏ. Its term ratio r(x)=t(k+1)/t(k) carries a
    real q-Gosper–Petkovšek peel (num/den both x-degree 1). Assert the certificate
    reproduces T via Δ_q(R·t)=t AND Σ t == T(n) − T(0)."""
    # r(x) = q·((q²−1)q·x − (q−1)) / ((q²−1)x − (q−1)). Built monomial-by-monomial:
    #   num: x⁰: −q(q−1) = q − q² ; x¹: (q²−1)q² = q⁴ − q²
    #   den: x⁰: −(q−1) = 1 − q   ; x¹: (q²−1)   = q² − 1
    num = QPoly.from_dict({(0, 1): Q(1, 1), (0, 2): Q(-1, 1),
                           (1, 2): Q(-1, 1), (1, 4): Q(1, 1)})
    den = QPoly.from_dict({(0, 0): Q(1, 1), (0, 1): Q(-1, 1),
                           (1, 0): Q(-1, 1), (1, 2): Q(1, 1)})
    cert = q_gosper(num, den)
    assert cert is not None, "the constructed q-hypergeometric term must be summable"

    def t(qv, k):
        x = qv ** k
        return Fraction((qv * qv - 1) * x * x - (qv - 1) * x)

    _assert_q_antidifference(cert, t)
    for qv in (2, 3, 5):
        def big_t(k):
            return _R_at(cert, qv, qv ** k) * t(qv, k)
        for n in range(1, 7):
            s = sum((t(qv, k) for k in range(n)), Fraction(0))
            assert s == big_t(n) - big_t(0), f"telescope failed q={qv} n={n}"
        # the antidifference IS T(k)=q^(2k)−q^k at every k where t(k)≠0
        for k in range(1, 6):
            x = qv ** k
            assert big_t(k) == Fraction(x * x - x), f"antidiff ≠ T at q={qv} k={k}"


def test_case5_q_partial_theta_has_no_closed_form():
    """t(k)=q^(k(k−1)/2), ratio r=x (= qᵏ, growing) — a q-PARTIAL THETA. It has NO
    q-hypergeometric closed form (the q-analog of the Gaussian Σ over a quadratic
    exponent) → None (a NEGATIVE test)."""
    cert = q_gosper(QPoly.from_dict({(1, 0): Q(1, 1)}), QPoly.one())   # num=x, den=1
    assert cert is None


def test_case6_q_harmonic_like_has_no_closed_form():
    """t(k)=1/(qᵏ−1), ratio r=(x−1)/(qx−1). No q-hypergeometric closed form → None
    (the load-bearing NEGATIVE test, the q-analog of the harmonic non-summability)."""
    num = QPoly.from_dict({(0, 0): Q(-1, 1), (1, 0): Q(1, 1)})         # x − 1
    den = QPoly.from_dict({(0, 0): Q(-1, 1), (1, 1): Q(1, 1)})         # q·x − 1
    cert = q_gosper(num, den)
    assert cert is None


def test_certificate_is_one_over_q_minus_one():
    """The Σ qᵏ certificate reduces to the canonical R = −1/(1−q) (= 1/(q−1)): the
    sign is pinned so the LOWEST-degree nonzero ``den`` coefficient is positive (the
    Class-K sign pin), so num is the constant −1 and den is the x⁰ cell 1 − q. This
    pins the canonical (integer-cleared, sign-normalized) form the native + pure
    paths share, and R(qᵏ)·qᵏ = qᵏ/(qᵏ−... ) telescopes (verified in case 1)."""
    cert = q_gosper(QPoly.from_dict({(0, 1): Q(1, 1)}), QPoly.one())
    assert cert is not None
    # R(x) = −1/(1−q) = 1/(q−1): num is the constant −1, den is the x⁰ cell 1 − q.
    assert cert["num"].x_low == 0 and len(cert["num"].cells) == 1
    assert cert["num"].cells[0].coeffs == (Q(-1, 1),)
    assert cert["den"].x_low == 0 and len(cert["den"].cells) == 1
    assert cert["den"].cells[0].coeffs == (Q(1, 1), Q(-1, 1))         # 1 − q
    # and as a rational it IS 1/(q−1): R(q⁰=1) at q=3 is 1/(3−1) = 1/2.
    assert _R_at(cert, 3, 1) == Fraction(1, 2)


def test_coercion_forms_accepted():
    """The term-ratio operands accept a ``Poly``-in-q and the nested-list ℚ[q] form,
    not just ``QPoly`` handles — value-identical to the explicit QPoly."""
    from srmech.amsc.poly import Poly
    # r=2: a Poly-in-q [2] (a constant) as numerator, [1] as denominator.
    a = q_gosper(Poly.from_coeffs([2]), Poly.from_coeffs([1]))
    b = q_gosper(QPoly.from_dict({(0, 0): Q(2, 1)}), QPoly.one())
    assert a is not None and b is not None
    assert a["num"].cells == b["num"].cells
    assert a["den"].cells == b["den"].cells
    # the nested-list form [[2]] (an x⁰ cell carrying the constant 2) is value-equal.
    c = q_gosper([[2]], [[1]])
    assert c is not None
    assert c["num"].cells == b["num"].cells and c["den"].cells == b["den"].cells


def test_zero_denominator_rejected():
    """A zero-polynomial denominator (an invalid term ratio) raises ValueError."""
    with pytest.raises(ValueError):
        q_gosper(QPoly.one(), QPoly.zero())


def test_native_matches_pure_when_present():
    """When the native srmech_q_gosper is loaded, its certificate is byte-identical
    to the pure-Python body (the parity oracle) on the constant-ratio (native-scope)
    cases. Skip-clean when no native lib."""
    from srmech.amsc import _native as nat
    from srmech.amsc.q_gosper import _q_gosper_pure, _coerce_qpoly
    if not nat.has_native_q_gosper():
        pytest.skip("native srmech_q_gosper not present in this environment")

    cases = [
        QPoly.from_dict({(0, 1): Q(1, 1)}),       # r = q        (Σ qᵏ)
        QPoly.from_dict({(0, 0): Q(2, 1)}),       # r = 2        (Σ 2ᵏ)
        QPoly.from_dict({(0, 2): Q(1, 1)}),       # r = q²       (Σ q^(2k))
        QPoly.from_dict({(0, 1): Q(5, 1)}),       # r = 5q       (Σ (5q)ᵏ)
        QPoly.from_dict({(0, 0): Q(3, 2)}),       # r = 3/2      (Σ (3/2)ᵏ)
    ]
    one = QPoly.one()

    def repr_cert(c):
        if c is None:
            return None
        return (tuple(tuple((v.numerator, v.denominator) for v in cell.coeffs)
                      for cell in c["num"].cells), c["num"].x_low,
                tuple(tuple((v.numerator, v.denominator) for v in cell.coeffs)
                      for cell in c["den"].cells), c["den"].x_low)

    for num in cases:
        native = q_gosper(num, one)                                   # native path
        pure = _q_gosper_pure(_coerce_qpoly(num), _coerce_qpoly(one))
        assert repr_cert(native) == repr_cert(pure), (
            f"native/pure mismatch for ratio {num!r}")
