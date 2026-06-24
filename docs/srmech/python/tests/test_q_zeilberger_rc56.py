"""q-hypergeometric F929 row (rc56) — q-Zeilberger creative telescoping
``q_zeilberger``.

The SECOND public op of the q-hypergeometric F929 reduction row (the q-analog of the
§76 ``zeilberger``). Given a proper q-hypergeometric term F(n,k) by its two
bivariate-q term ratios ``r_n = F(n+1,k)/F(n,k)`` and ``r_k = F(n,k+1)/F(n,k)`` (each
a :class:`~srmech.amsc.qbipoly.QBiPoly` over ``(X, Y) = (qⁿ, qᵏ)``), it returns the
minimal-order linear q-recurrence ``Σ_j a_j(qⁿ)·f(n+j) = 0`` for ``f(n) = Σ_k
F(n,k)`` (each ``a_j`` an exact :class:`~srmech.amsc.qpoly.QPoly` in ``X = qⁿ``) plus
the q-Gosper certificate, or ``None`` when no recurrence of order ≤ max_order exists.

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it uses
only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``QPoly`` / ``QBiPoly``
carriers + plain Python arithmetic. **Every recurrence is INDEPENDENTLY verified** —
an exact numeric q-summation of the closed form at several integer ``q`` confirms the
found recurrence ANNIHILATES the sum, and the certificate's q-WZ relation
``Σ_j a_j(X) F(n+j,k) = Δ_q(R·F)`` is checked as an exact bivariate-q identity (never
trusting the algorithm symbolically).

Coverage (the rc56 acceptance set):
  (1) the q-binomial-theorem sum f(n)=Σ_k [n,k]_q q^{C(k,2)} = ∏_{i<n}(1+qⁱ)
      -> ORDER-1 recurrence (1+qⁿ)f(n) − f(n+1) = 0; assert it annihilates the
      closed form at several q AND the certificate q-WZ relation holds (the genuine
      k-summation case, decided on the pure path).
  (2) the k-FREE q-GEOMETRIC term r_n=X (=qⁿ), r_k=1: f(n)=q^{C(n,2)} -> ORDER-1
      recurrence qⁿ f(n) − f(n+1) = 0 (the canonical NATIVE-completed case).
  (3) a constant term r_n=r_k=1: f(n)=const -> ORDER-1 f(n+1)−f(n)=0.
  (4) max_order too low -> None (the honest no-recurrence-yet residue).
  (5) a zero-denominator reject (ValueError).
  (6) coercion forms (QPoly-in-Y / nested list) coerce to the same result.
  (7) the Python-op == C-peer parity check on the native case (skip-clean when no
      native lib): the recurrence is byte-identical whichever path runs.
"""

from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.poly import Poly
from srmech.amsc.qpoly import QPoly
from srmech.amsc.qbipoly import QBiPoly
from srmech.amsc.q_zeilberger import q_zeilberger


# ── carrier-build helpers (Q / Poly / QPoly / QBiPoly only; no numpy, no math) ──

def _qmono(deg: int, coeff: int = 1) -> Poly:
    """``coeff · q**deg`` as an exact ``ℚ[q]`` ``Poly``-in-q."""
    return Poly.monomial(deg, Q(coeff, 1))


def _x_pow(e: int, coeff_q: Poly = None) -> QPoly:
    """``coeff_q(q) · X**e`` as a single-x-cell ``QPoly`` (X = qⁿ)."""
    return QPoly.from_q_poly(coeff_q if coeff_q is not None else Poly.one(), e)


def _a_eval(coeff_qpoly: QPoly, qv: int, n: int) -> Fraction:
    """Evaluate a recurrence coefficient ``a_j(X)`` (a ``QPoly`` in ``X = qⁿ``) at
    exact ``q = qv`` and ``X = qv**n`` → a ``Fraction`` (no numpy / math)."""
    X = Fraction(qv) ** n
    acc = Fraction(0)
    for i, cell in enumerate(coeff_qpoly.cells):
        e = coeff_qpoly.x_low + i
        cq = sum(Fraction(c.numerator, c.denominator) * Fraction(qv) ** d
                 for d, c in enumerate(cell.coeffs))
        acc += cq * (X ** e)
    return acc


def _annihilates(res, fclosed, *, qs=(2, 3, 5), nmax=6) -> bool:
    """True iff ``Σ_j a_j(qⁿ)·fclosed(q, n+j) == 0`` for every integer ``n`` and
    several numeric ``q`` (the INDEPENDENT recurrence check)."""
    coeffs = res["coeffs"]
    for qv in qs:
        for n in range(0, nmax):
            s = sum(_a_eval(coeffs[j], qv, n) * fclosed(qv, n + j)
                    for j in range(len(coeffs)))
            if s != 0:
                return False
    return True


# ── the q-binomial Gaussian carriers (the genuine k-summation case) ───────────

def _q_binomial_theorem_ratios():
    """The two bivariate-q term ratios of F(n,k) = [n,k]_q · q^{C(k,2)} (the
    q-binomial-theorem term, z=1), over (X, Y) = (qⁿ, qᵏ):
      r_k = F(n,k+1)/F(n,k) = (X − Y) / (qY − 1)
      r_n = F(n+1,k)/F(n,k) = (qX − 1)·Y / (qX − Y)
    each a QBiPoly. f(n) = Σ_k F(n,k) = ∏_{i<n}(1 + qⁱ)."""
    # r_k num = X − Y  (Y⁰ cell = X, Y¹ cell = −1)
    rk_num = QBiPoly([_x_pow(1), QPoly.from_q_poly(Poly.from_coeffs([Q(-1, 1)]))])
    # r_k den = qY − 1  (Y⁰ cell = −1, Y¹ cell = q)
    rk_den = QBiPoly([QPoly.from_q_poly(Poly.from_coeffs([Q(-1, 1)])),
                      QPoly.from_q_poly(_qmono(1))])
    # r_n num = (qX − 1)·Y  (Y¹ cell = qX − 1: X⁰ cell = −1, X¹ cell = q)
    qX_1 = QPoly([Poly.from_coeffs([Q(-1, 1)]), _qmono(1)], x_low=0)
    rn_num = QBiPoly([QPoly.zero(), qX_1])
    # r_n den = qX − Y  (Y⁰ cell = qX, Y¹ cell = −1)
    rn_den = QBiPoly([QPoly([Poly.zero(), _qmono(1)], x_low=0),
                      QPoly.from_q_poly(Poly.from_coeffs([Q(-1, 1)]))])
    return rn_num, rn_den, rk_num, rk_den


def _f_qbinomial(qv: int, n: int) -> Fraction:
    """The closed form f(n) = ∏_{i=0}^{n−1}(1 + qⁱ)."""
    p = Fraction(1)
    for i in range(n):
        p *= (1 + Fraction(qv) ** i)
    return p


# ── the acceptance cases ──────────────────────────────────────────────────────

def test_case1_q_binomial_theorem_sum_order1_recurrence():
    """f(n)=Σ_k [n,k]_q q^{C(k,2)} = ∏_{i<n}(1+qⁱ): the genuine k-summation case.
    q-Zeilberger finds the ORDER-1 recurrence (1+qⁿ)f(n) − f(n+1) = 0; assert it
    ANNIHILATES the closed form at q ∈ {2,3,5}."""
    rn_num, rn_den, rk_num, rk_den = _q_binomial_theorem_ratios()
    res = q_zeilberger(rn_num, rn_den, rk_num, rk_den, max_order=3)
    assert res is not None, "Σ_k [n,k]_q q^{C(k,2)} must have a q-recurrence"
    assert res["order"] == 1
    assert set(res) == {"order", "coeffs", "certificate"}
    assert all(isinstance(c, QPoly) for c in res["coeffs"])
    assert isinstance(res["certificate"], QBiPoly)
    assert _annihilates(res, _f_qbinomial), (
        "the found recurrence must annihilate ∏_{i<n}(1+qⁱ)")
    # the recurrence is a_0 = 1 + X (= 1 + qⁿ), a_1 = −1 (up to an overall sign).
    a0, a1 = res["coeffs"]
    # a_0(X) at X=1 is 1 + 1 = 2 (or −2); a_1 is the constant ∓1 → a_0/a_1 = ∓(1+X).
    r0 = _a_eval(a0, 2, 0)        # a_0 at q=2, n=0 → 1 + q⁰ = 2 (times overall sign)
    r1 = _a_eval(a1, 2, 0)        # a_1 constant
    assert r1 != 0 and r0 / r1 == Fraction(-2), "a_0/a_1 must be −(1+qⁿ) at n=0"


def test_case1_certificate_q_wz_relation_holds():
    """The returned certificate x(X,Y) satisfies the q-WZ relation
    ``Σ_j a_j(X) F(n+j,k) = Δ_q(R·F)`` exactly (the cleared bivariate-q identity is
    zero) — the relation the rc57 q-WZ proof op verifies."""
    from srmech.amsc.q_zeilberger import (
        _qb_to_xy, _rho, _xy_mul, _xy_exact_div, _xy_qshift_y, _xy_add)
    from srmech.amsc.q_gosper import _Cq

    rn_num, rn_den, rk_num, rk_den = _q_binomial_theorem_ratios()
    res = q_zeilberger(rn_num, rn_den, rk_num, rk_den, max_order=3)
    order = res["order"]
    rnx, rnd, rkx, rkd = (_qb_to_xy(rn_num), _qb_to_xy(rn_den),
                          _qb_to_xy(rk_num), _qb_to_xy(rk_den))
    rhos = [_rho(rnx, rnd, j) for j in range(order + 1)]
    den_p = {(0, 0): _Cq.one()}
    for _, dj in rhos:
        den_p = _xy_mul(den_p, dj)
    rho_common = [_xy_mul(nj, _xy_exact_div(den_p, dj)) for nj, dj in rhos]

    def _cell_xy(qp, yd):
        out = {}
        for i, cell in enumerate(qp.cells):
            if not cell.is_zero:
                out[(qp.x_low + i, yd)] = _Cq.from_poly(cell)
        return out

    n_p = {}
    for j, c in enumerate(res["coeffs"]):
        n_p = _xy_add(n_p, _xy_mul(_cell_xy(c, 0), rho_common[j]))
    xx = {}
    for yd, cell in enumerate(res["certificate"].terms):
        for key, val in _cell_xy(cell, yd).items():
            xx[key] = val
    dp_qy = _xy_qshift_y(den_p, 1)
    lhs = _xy_mul(n_p, _xy_mul(rkd, dp_qy))
    xp = _xy_mul(_xy_qshift_y(xx, 1), _xy_mul(rkx, den_p))
    xm = _xy_mul(xx, _xy_mul(rkd, dp_qy))
    diff = _xy_add(lhs, _xy_add(xp, xm, sub=True), sub=True)
    nonzero = [1 for v in diff.values() if not v.is_zero]
    assert not nonzero, (
        "the certificate q-WZ relation Σ_j a_j F(n+j,k) = Δ_q(R·F) must hold exactly")


def test_case2_k_free_q_geometric_native_case():
    """The canonical NATIVE-completed case: r_n = X (= qⁿ), r_k = 1. f(n) = q^{C(n,2)}
    satisfies the ORDER-1 recurrence qⁿ f(n) − f(n+1) = 0."""
    rn = QBiPoly.from_x_qpoly(_x_pow(1))             # X
    one = QBiPoly.one()
    res = q_zeilberger(rn, one, one, one, max_order=2)
    assert res is not None and res["order"] == 1

    def f_geom(qv, n):
        # q^{C(n,2)} = q^{n(n-1)/2}
        return Fraction(qv) ** (n * (n - 1) // 2)

    assert _annihilates(res, f_geom), "must annihilate q^{C(n,2)}"


def test_case3_constant_term_order1():
    """A constant term r_n = r_k = 1: f(n) = const · (#k terms). For a single-k term
    f(n+1) − f(n) = 0 (order-1)."""
    one = QBiPoly.one()
    res = q_zeilberger(one, one, one, one, max_order=2)
    assert res is not None and res["order"] == 1

    def f_const(qv, n):
        return Fraction(1)

    assert _annihilates(res, f_const), "f(n)=const must be annihilated"


def test_case4_max_order_too_low_is_none():
    """max_order=0 on an order-1 term → None (the honest no-recurrence-yet residue —
    the order-0 ansatz cannot annihilate a genuinely order-1 sum)."""
    rn_num, rn_den, rk_num, rk_den = _q_binomial_theorem_ratios()
    assert q_zeilberger(rn_num, rn_den, rk_num, rk_den, max_order=0) is None


def test_zero_denominator_rejected():
    """A zero term-ratio denominator is a ValueError (a term ratio has a nonzero
    denominator)."""
    one = QBiPoly.one()
    with pytest.raises(ValueError):
        q_zeilberger(one, QBiPoly.zero(), one, one)
    with pytest.raises(ValueError):
        q_zeilberger(one, one, one, QBiPoly.zero())


def test_coercion_forms_agree():
    """A bare QPoly (read as a polynomial in Y) and the nested-list form coerce to
    the SAME QBiPoly operand → the SAME recurrence."""
    # r_n = X, r_k = 1, written three ways for r_k (QBiPoly.one / QPoly.one / [[1]]).
    rn = QBiPoly.from_x_qpoly(_x_pow(1))
    res_a = q_zeilberger(rn, QBiPoly.one(), QBiPoly.one(), QBiPoly.one(), max_order=2)
    res_b = q_zeilberger(rn, QBiPoly.one(), QPoly.one(), QPoly.one(), max_order=2)
    res_c = q_zeilberger(rn, QBiPoly.one(), [[1]], [[1]], max_order=2)

    def key(r):
        return (r["order"], tuple(
            (c.x_low, tuple(tuple((q.numerator, q.denominator) for q in cell.coeffs)
                            for cell in c.cells)) for c in r["coeffs"]))

    assert key(res_a) == key(res_b) == key(res_c)


def test_native_equals_pure_byte_identical():
    """The native C peer (the canonical k-free q-geometric case) is byte-identical to
    the pure-Python path. Skips cleanly when no native lib is present."""
    from srmech.amsc import _native
    if not _native.has_native_q_zeilberger():
        pytest.skip("no native srmech_q_zeilberger (pure-Python path is the oracle)")
    import srmech.amsc.q_zeilberger as QZ

    rn = QBiPoly.from_x_qpoly(_x_pow(1))             # X
    one = QBiPoly.one()
    res_native = q_zeilberger(rn, one, one, one, max_order=2)

    saved = QZ._native
    QZ._native = lambda: None                        # force the pure path
    try:
        res_pure = q_zeilberger(rn, one, one, one, max_order=2)
    finally:
        QZ._native = saved

    def key(r):
        return (r["order"], tuple(
            (c.x_low, tuple(tuple((q.numerator, q.denominator) for q in cell.coeffs)
                            for cell in c.cells)) for c in r["coeffs"]))

    assert key(res_native) == key(res_pure), (
        "native and pure q-Zeilberger recurrences must be byte-identical")


def test_no_numpy_no_math_imported():
    """This module imports neither numpy nor math (the numpy-free / math-free
    discipline; the carriers are exact-ℚ[q] bigint)."""
    import sys
    assert "numpy" not in sys.modules or sys.modules["numpy"] is None
    # `math` may be imported transitively by pytest internals, but never by srmech
    # source — assert the q_zeilberger module itself names neither.
    import srmech.amsc.q_zeilberger as QZ
    import srmech.amsc.qbipoly as QB
    src = QZ.__file__
    text = open(src, encoding="utf-8").read()
    assert "import numpy" not in text and "import math" not in text
    text2 = open(QB.__file__, encoding="utf-8").read()
    assert "import numpy" not in text2 and "import math" not in text2
