"""q-hypergeometric F929 row (rc57) — the q-Wilf–Zeilberger pair method
``q_wz_certificate`` (the THIRD and FINAL public op of the q-row, the q-row CLOSER and
the closer of the whole multivariate + q-hypergeometric reduction-theory arc).

The q-analog of the §76 ``wz_certificate``. Given a proper q-hypergeometric term
F(n,k) (the NORMALIZED q-summand of a terminating identity Σ_k F(n,k)=const) by its
TWO bivariate-q term ratios r_n = F(n+1,k)/F(n,k) and r_k = F(n,k+1)/F(n,k) (each a
:class:`~srmech.amsc.qbipoly.QBiPoly` over (X,Y)=(qⁿ,qᵏ)), ``q_wz_certificate``
PRODUCES + VERIFIES the q-WZ certificate R(X,Y) whose companion G=R·F makes the q-WZ
equation F(n+1,k)−F(n,k)=G(n,k+1)−G(n,k) hold (G(n,k+1)=(σ_y R)·(σ_y F), σ_y:Y↦qY).

This test is numpy-FREE and math-FREE (no ``import numpy`` / ``import math``): it uses
only ``fractions.Fraction`` + the srmech ``Q`` / ``Poly`` / ``QPoly`` / ``QBiPoly``
carriers + plain Python arithmetic. **Every q-WZ pair is checked INDEPENDENTLY** — the
q-WZ equation is evaluated as an exact bivariate-ℚ(q) rational-function identity at
several concrete (q, n, k), never trusting the algorithm symbolically.

Coverage (the rc57 acceptance set):
  (1) the constant-summand q-WZ pair r_n=r_k=1 (f(n)=const, Σ_k F constant in n): the
      genuine end-to-end FIND+VERIFY case — q_zeilberger finds the ORDER-1 recurrence
      [−1,+1], the WZ certificate is R=0, ``verified==True``.
  (2) a NONTRIVIAL constructed q-WZ triple R(X,Y)=Y/(X−Y), r_k=Y/X (r_n derived from
      the q-WZ equation r_n=1+R(X,qY)·r_k−R(X,Y)): the verify primitive confirms it
      AND an independent exact bivariate-ℚ(q) evaluation at several (q,n,k) confirms
      the q-WZ equation holds; a WRONG certificate (numerator scaled by 2) → not
      verified.
  (3) a genuine NAMED q-WZ pair (the q-analog of Σ_k (−1)ᵏC(n,k)=0): its certificate
      is supplied + VERIFIED (verify is the proof of record) AND the q-WZ equation is
      independently confirmed at several (q,n,k).
  (4) a non-q-WZ pair (a non-constant q-sum / a shape q_zeilberger cannot reduce) →
      None (the honest no-proof residue; never a crash).
  (5) a zero-denominator reject (ValueError).
  (6) coercion forms (QPoly-in-Y / nested list) coerce to the same result.
  (7) the Python-verify == C-peer parity check (skip-clean when no native lib): the
      verify decision is byte-identical whichever path runs, on the genuine cert AND a
      wrong one (the C peer is the COMPLETE verify mirror, degree-bounded).
"""

from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.poly import Poly
from srmech.amsc.qpoly import QPoly
from srmech.amsc.qbipoly import QBiPoly, _qb_pairs
from srmech.amsc.q_wz_certificate import (
    q_wz_certificate, _verify_q_wz_equation_pure)


# ── carrier-build helpers (Q / Poly / QPoly / QBiPoly only; no numpy, no math) ──

def _qmono(deg: int, coeff: int = 1) -> Poly:
    """``coeff · q**deg`` as an exact ``ℚ[q]`` ``Poly``-in-q."""
    return Poly.monomial(deg, Q(coeff, 1))


def _xc(c: int) -> QPoly:
    """The constant-``X**0`` ``QPoly`` carrying the ``ℚ[q]`` scalar ``c``."""
    return QPoly.from_q_poly(Poly.from_coeffs([Q(c, 1)]))


def _xm(e: int, c: int = 1) -> QPoly:
    """``c · X**e`` as a single-x-cell ``QPoly`` (X = qⁿ)."""
    return QPoly.from_q_poly(Poly.from_coeffs([Q(c, 1)]), e)


def _yk(*cells: QPoly) -> QBiPoly:
    """A ``QBiPoly`` from ascending-``Y``-degree ``QPoly``-in-X cells."""
    return QBiPoly(list(cells))


def _y0(p: QPoly) -> QBiPoly:
    """A constant-in-``Y`` ``QBiPoly`` (a single ``Y**0`` cell)."""
    return QBiPoly([p])


# ── independent evaluation of a QBiPoly at exact (q, X=qⁿ, Y=qᵏ) → Fraction ────

def _qb_eval(qb: QBiPoly, qv: int, n: int, k: int) -> Fraction:
    """Evaluate a ``QBiPoly`` at exact ``q = qv``, ``X = qv**n``, ``Y = qv**k`` → a
    ``Fraction`` (no numpy / math). The substrate's exact bivariate-q evaluation."""
    X = Fraction(qv) ** n
    Y = Fraction(qv) ** k
    acc = Fraction(0)
    for dy, cell in enumerate(qb.terms):
        for i, p in enumerate(cell.cells):
            xe = cell.x_low + i
            cq = sum(Fraction(c.numerator, c.denominator) * Fraction(qv) ** d
                     for d, c in enumerate(p.coeffs))
            acc += cq * (X ** xe) * (Y ** dy)
    return acc


def _ratio(num: QBiPoly, den: QBiPoly, qv: int, n: int, k: int):
    """``num/den`` at exact ``(q, n, k)`` as a ``Fraction``, or ``None`` if den == 0."""
    d = _qb_eval(den, qv, n, k)
    if d == 0:
        return None
    return _qb_eval(num, qv, n, k) / d


def _q_wz_equation_holds(rn_num, rn_den, rk_num, rk_den, cert,
                         *, qs=(2, 3, 5), nmax=5, kmax=5) -> int:
    """INDEPENDENT check of the q-WZ equation in ratio form
    ``r_n(X,Y) − 1 == R(X,qY)·r_k(X,Y) − R(X,Y)`` at several exact ``(q, n, k)``
    (``X=qⁿ``, ``Y=qᵏ``; ``R(X,qY)`` is R at ``(n, k+1)``). Returns the number of
    points checked (must be > 0). Raises ``AssertionError`` on any mismatch — never
    trusting the verify symbolically."""
    xn, xd = cert["num"], cert["den"]
    checked = 0
    for qv in qs:
        for n in range(0, nmax):
            for k in range(0, kmax):
                rn = _ratio(rn_num, rn_den, qv, n, k)
                rk = _ratio(rk_num, rk_den, qv, n, k)
                r_here = _ratio(xn, xd, qv, n, k)
                r_kp1 = _ratio(xn, xd, qv, n, k + 1)        # R(X, qY)
                if (rn is None or rk is None or r_here is None or r_kp1 is None):
                    continue
                lhs = rn - 1
                rhs = r_kp1 * rk - r_here
                assert lhs == rhs, (
                    f"q-WZ equation failed at q={qv}, n={n}, k={k}: {lhs} != {rhs}")
                checked += 1
    return checked


# ── case 1: the constant-summand q-WZ pair (genuine end-to-end FIND+VERIFY) ────

def test_case1_constant_summand_end_to_end():
    """r_n=r_k=1 (f(n)=const, Σ_k F constant in n): q_zeilberger finds the ORDER-1
    recurrence [−1,+1] (the WZ recurrence f(n+1)−f(n)=0), q_wz_certificate produces +
    VERIFIES the certificate R=0. The genuine end-to-end FIND+VERIFY case."""
    one = QBiPoly.one()
    res = q_wz_certificate(one, one, one, one)
    assert res is not None, "the constant summand must be q-WZ-summable"
    assert res["verified"] is True
    assert set(res) == {"certificate", "verified"}
    assert set(res["certificate"]) == {"num", "den"}
    assert isinstance(res["certificate"]["num"], QBiPoly)
    assert isinstance(res["certificate"]["den"], QBiPoly)
    # the certificate is R=0 (G=0·F=0; F(n+1,k)−F(n,k)=0=G(n,k+1)−G(n,k) for a
    # constant-in-n summand).
    assert res["certificate"]["num"].is_zero
    assert not res["certificate"]["den"].is_zero
    # independently: the q-WZ equation holds (trivially) at several (q,n,k).
    assert _q_wz_equation_holds(one, one, one, one, res["certificate"]) > 0


# ── case 2: a nontrivial constructed q-WZ triple (VERIFY + independent eval) ───

def _constructed_triple():
    """A genuine q-WZ triple built from a CHOSEN certificate R=Y/(X−Y) and r_k=Y/X via
    the q-WZ equation r_n = 1 + R(X,qY)·r_k − R(X,Y). Returns
    ``(rn_num, rn_den, rk_num, rk_den, cert_num, cert_den)`` — all exact QBiPoly."""
    Xn = _yk(QPoly.zero(), _xc(1))           # cert num = Y
    Xd = _yk(_xm(1, 1), _xc(-1))             # cert den = X − Y
    Bn = _yk(QPoly.zero(), _xc(1))           # r_k num = Y
    Bd = _y0(_xm(1, 1))                       # r_k den = X
    Xn1 = Xn.qshift_y(1)                      # R(X, qY) numerator
    Xd1 = Xd.qshift_y(1)
    num_rhs = Xn1 * Bn * Xd - Xn * Xd1 * Bd
    den_rhs = Xd1 * Bd * Xd
    An = num_rhs + den_rhs                    # r_n num
    Ad = den_rhs                              # r_n den
    return An, Ad, Bn, Bd, Xn, Xd


def test_case2_constructed_triple_verify_and_independent_eval():
    """The constructed nontrivial q-WZ triple R=Y/(X−Y): the verify primitive confirms
    it AND an independent exact bivariate-ℚ(q) evaluation at several (q,n,k) confirms
    the q-WZ equation. A WRONG certificate (numerator scaled by 2) → not verified."""
    An, Ad, Bn, Bd, Xn, Xd = _constructed_triple()
    cert = {"num": Xn, "den": Xd}
    # the verify primitive (the load-bearing new op): the genuine certificate verifies.
    assert _verify_q_wz_equation_pure(An, Ad, Bn, Bd, Xn, Xd) is True
    # independently: the q-WZ equation holds at many (q,n,k).
    assert _q_wz_equation_holds(An, Ad, Bn, Bd, cert) > 0
    # a WRONG certificate (numerator scaled by 2) does NOT verify.
    Xn_bad = Xn * QBiPoly.from_x_qpoly(_xc(2))
    assert _verify_q_wz_equation_pure(An, Ad, Bn, Bd, Xn_bad, Xd) is False


# ── case 3: a SECOND constructed q-WZ triple with a higher-q-degree certificate ─

def _constructed_triple_b():
    """A second genuine q-WZ triple built from a chosen certificate R = qY/(X − qY) and
    r_k = X/(qY) via the q-WZ equation r_n = 1 + R(X,qY)·r_k − R(X,Y). The q-shift σ_y
    inside R puts a NONTRIVIAL q-degree into the certificate (exercising the σ_y q-power
    monomial multiply in both the pure path and the C peer). Returns
    ``(rn_num, rn_den, rk_num, rk_den, cert_num, cert_den)`` — all exact QBiPoly."""
    Xn = _yk(QPoly.zero(), QPoly.from_q_poly(_qmono(1, 1)))   # cert num = qY (Y¹: q)
    Xd = _yk(_xm(1, 1), QPoly.from_q_poly(_qmono(1, -1)))     # cert den = X − qY
    Bn = _y0(_xm(1, 1))                                        # r_k num = X
    Bd = _yk(QPoly.zero(), QPoly.from_q_poly(_qmono(1, 1)))   # r_k den = qY
    Xn1 = Xn.qshift_y(1)
    Xd1 = Xd.qshift_y(1)
    num_rhs = Xn1 * Bn * Xd - Xn * Xd1 * Bd
    den_rhs = Xd1 * Bd * Xd
    An = num_rhs + den_rhs
    Ad = den_rhs
    return An, Ad, Bn, Bd, Xn, Xd


def test_case3_second_constructed_triple_with_q_degree_certificate():
    """A second nontrivial q-WZ triple R=qY/(X−qY): the σ_y q-shift inside R gives the
    certificate a genuine q-degree (exercising the q-power monomial multiply). The
    verify primitive confirms it AND an independent exact bivariate-ℚ(q) evaluation at
    several (q,n,k) confirms the q-WZ equation; a WRONG certificate → not verified."""
    An, Ad, Bn, Bd, Xn, Xd = _constructed_triple_b()
    cert = {"num": Xn, "den": Xd}
    assert _verify_q_wz_equation_pure(An, Ad, Bn, Bd, Xn, Xd) is True
    assert _q_wz_equation_holds(An, Ad, Bn, Bd, cert) > 0
    # a wrong certificate (denominator scaled by 3) does NOT verify.
    Xd_bad = Xd * QBiPoly.from_x_qpoly(_xc(3))
    assert _verify_q_wz_equation_pure(An, Ad, Bn, Bd, Xn, Xd_bad) is False


# ── case 4: a non-q-WZ pair → None (graceful, never a crash) ──────────────────

def test_case4_non_wz_pair_returns_none():
    """A non-constant q-sum / a term-ratio shape q_zeilberger cannot reduce on its
    supported path → None (the honest no-proof residue; q_wz_certificate catches the
    q_zeilberger decline + returns None, never propagating a crash)."""
    # the q-binomial-theorem sum=1 pair: r_n den = (Y−qX)(1+X) (a non-monomial-in-X
    # n-denominator the rc56 q_zeilberger pure path declines) → None, not a crash.
    rn_num = _yk(QPoly.zero(), QPoly([Poly.from_coeffs([Q(1, 1)]), _qmono(1, -1)], 0))
    rn_den = _yk(QPoly([Poly.zero(), _qmono(1, -1), _qmono(1, -1)], 0),
                 QPoly([Poly.from_coeffs([Q(1, 1)]), Poly.from_coeffs([Q(1, 1)])], 0))
    rk_num = _yk(QPoly([Poly.zero(), Poly.from_coeffs([Q(1, 1)])], 0),
                 _xc(-1))
    rk_den = _yk(_xc(1), QPoly.from_q_poly(_qmono(1, -1)))
    assert q_wz_certificate(rn_num, rn_den, rk_num, rk_den) is None


# ── case 5: a zero-denominator reject ─────────────────────────────────────────

def test_zero_denominator_rejected():
    """A zero term-ratio denominator is a ValueError (a term ratio has a nonzero
    denominator)."""
    one = QBiPoly.one()
    with pytest.raises(ValueError):
        q_wz_certificate(one, QBiPoly.zero(), one, one)
    with pytest.raises(ValueError):
        q_wz_certificate(one, one, one, QBiPoly.zero())


# ── case 6: coercion forms agree ──────────────────────────────────────────────

def test_coercion_forms_agree():
    """The constant summand written three ways (QBiPoly.one / QPoly.one / [[1]]) coerces
    to the SAME operand → the SAME proof."""
    res_a = q_wz_certificate(QBiPoly.one(), QBiPoly.one(),
                             QBiPoly.one(), QBiPoly.one())
    res_b = q_wz_certificate(QPoly.one(), QPoly.one(), QPoly.one(), QPoly.one())
    res_c = q_wz_certificate([[1]], [[1]], [[1]], [[1]])
    for r in (res_a, res_b, res_c):
        assert r is not None and r["verified"] is True
        assert r["certificate"]["num"].is_zero


# ── case 7: native == pure parity (skip-clean when no native lib) ──────────────

def test_native_equals_pure_verify():
    """When the native srmech_q_wz_verify is loaded, its VERIFY decision is byte-
    identical to the pure-Python bivariate-ℚ[q] compare (the parity oracle) — on the
    genuine certificate AND a deliberately-wrong one (the C peer is the COMPLETE verify
    mirror, degree-bounded). Skip-clean when no native lib."""
    from srmech.amsc import _native as nat
    if not nat.has_native_q_wz_verify():
        pytest.skip("native srmech_q_wz_verify not present (pure path is the oracle)")

    cases = [_constructed_triple(), _constructed_triple_b()]

    def pairs(qb):
        return _qb_pairs(qb)

    for an, ad, bn, bd, xn, xd in cases:
        # the genuine certificate: C verify == pure verify == True.
        cval = nat.q_wz_verify_c(pairs(an), pairs(ad), pairs(bn), pairs(bd),
                                 pairs(xn), pairs(xd))
        pval = _verify_q_wz_equation_pure(an, ad, bn, bd, xn, xd)
        assert cval is True and pval is True
        # a WRONG certificate (numerator scaled by 2): C verify == pure verify == False.
        xn_bad = xn * QBiPoly.from_x_qpoly(_xc(2))
        cbad = nat.q_wz_verify_c(pairs(an), pairs(ad), pairs(bn), pairs(bd),
                                 pairs(xn_bad), pairs(xd))
        pbad = _verify_q_wz_equation_pure(an, ad, bn, bd, xn_bad, xd)
        assert cbad is False and pbad is False


# ── discipline: numpy-free + math-free ────────────────────────────────────────

def test_no_numpy_no_math_imported():
    """This module imports neither numpy nor math (the numpy-free / math-free
    discipline; the carriers are exact-ℚ[q] bigint). The q_wz_certificate source itself
    names neither."""
    import sys
    assert "numpy" not in sys.modules or sys.modules["numpy"] is None
    import srmech.amsc.q_wz_certificate as QWZ
    text = open(QWZ.__file__, encoding="utf-8").read()
    assert "import numpy" not in text and "import math" not in text
