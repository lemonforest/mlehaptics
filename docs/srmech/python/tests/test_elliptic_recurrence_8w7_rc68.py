"""elliptic_recurrence_8w7 — the ELLIPTIC Σ-row ORDER-1 RECURRENCE op for the
Frenkel–Turaev ₈ω₇ summation, a STRUCTURAL (beat-decomposition) finder that builds the
order-1 recurrence coefficient ``ρ(n)`` from the elementary symmetric functions of the
free parameters (NOT a coefficient nullspace solve — provably dead for the elliptic case).

The recurrence is ``f(n+1) = ρ(n)·f(n)`` for the ₈ω₇ DEFINITE sum (Warnaar,
*Constr. Approx.* 18 (2002) 479–502, arXiv:math/0001006, **Corollary 2.2**: the closed
product form ``(aq, aq/bc, aq/bd, aq/cd; q,p)_n / (aq/b, aq/c, aq/d, aq/bcd; q,p)_n``).
The op RECOGNIZES the canonical ₈ω₇ term-ratio (the very-well-poised core
``θ(aq²x²)θ(ax)/[θ(ax²)θ(qx)]`` over five Pochhammer pairs with the balancing
``bcde = a²q^{n+1}``), DECOMPOSES it into ``a`` + the three free params ``[b, c, d]``, and
CONSTRUCTS ``ρ`` (4 num + 4 den thetas in ``y = qⁿ``).

Tests:
  (a) the op reproduces ``ρ(n)`` on the canonical ₈ω₇ — the constructed ``ρ`` equals the
      actual ₈ω₇ sum's ``f(n+1)/f(n)`` to ``< 1e-9`` for ``n = 1, 2, 3`` (the closed
      product form the INDEPENDENT oracle, evaluated by the carrier's truncated theta);
  (b) ``None`` on a non-₈ω₇ ratio (unbalanced, or balanced-but-wrong-shape);
  (c) Python==C byte-exact parity on the ``ρ`` EllRatio output (drive BOTH paths, compare
      element-for-element — do NOT trust the C; the rc67 hardening lesson). Skipped when
      the native peer is absent (pure-Python is then the complete alternative).
"""

import os
import re
import tokenize

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.q import Q
from srmech.amsc.thetasum import _Y
from srmech.amsc import elliptic_recurrence as er
from srmech.amsc.elliptic_recurrence import elliptic_recurrence_8w7

# An independent verification point (DIFFERENT from the op's internal gate sample) so the
# test is not merely re-running the op's own gate.
_PARAMS = {"q": Q(2, 1), "p": Q(1, 19), "a": Q(4, 7),
           "b": Q(3, 8), "c": Q(5, 9), "d": Q(7, 12)}
# |p| = 1/19 → the truncated-theta tail ~|p|^depth ≈ 10^-30 at depth 24 (ample under 1e-9).
_TRUNC = 24


def _make_8w7():
    """The canonical Frenkel–Turaev ₈ω₇ term-ratio ``t(n+1)/t(n)`` (``x = qⁿ``,
    ``y = qⁿ``) with the balancing ``bcde = a²q^{n+1}`` (Warnaar Cor 2.2)."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM); y = M.symbol(_Y)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    e = (a * a * q * y) * (b * c * d).inv()              # bcde = a²q^{n+1}, y = qⁿ
    poch = [b, c, d, e, y.inv()]                         # 5 Pochhammer params incl q^-n
    num = [Theta(a * q * q * xk * xk), Theta(a * xk)]
    den = [Theta(a * xk * xk), Theta(q * xk)]
    for u in poch:
        num.append(Theta(u * xk)); den.append(Theta(a * q * xk * u.inv()))
    return R(q, num=num, den=den)


def _poch_value(u_mono, n):
    """The theta-Pochhammer ``(u; q, p)_n`` at the test point (the independent oracle)."""
    acc = Q(1, 1)
    for j in range(n):
        acc = acc * Theta(u_mono * M.symbol(_Q_SYM, j)).eval_trunc(_PARAMS, _TRUNC)
    return acc


def _f_sum(n):
    """The ₈ω₇ DEFINITE sum ``f(n)`` via Warnaar Cor 2.2's closed product form — the
    INDEPENDENT oracle (NOT the constructed ρ)."""
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    q = M.symbol(_Q_SYM)
    aq = a * q
    num_u = [aq, aq * (b * c).inv(), aq * (b * d).inv(), aq * (c * d).inv()]
    den_u = [aq * b.inv(), aq * c.inv(), aq * d.inv(), aq * (b * c * d).inv()]
    acc = Q(1, 1)
    for u in num_u:
        acc = acc * _poch_value(u, n)
    for u in den_u:
        acc = acc / _poch_value(u, n)
    return acc


def _close(lhs: Q, rhs: Q) -> bool:
    """``|lhs − rhs| < 1e-9`` in EXACT ℚ (the Class-K sign branch, not ALU abs())."""
    diff = lhs - rhs
    mag = diff if diff.numerator >= 0 else (Q(0, 1) - diff)
    return mag.numerator * 1_000_000_000 < mag.denominator


# ── (a) the op reproduces ρ(n) on the canonical ₈ω₇ ─────────────────────────────────
def test_canonical_8w7_returns_order_1():
    """The canonical ₈ω₇ is in class: the op returns an order-1 recurrence with a 4-num /
    4-den balanced ρ and coeffs ``[-ρ, 1]`` (``f(n+1) = ρ(n)·f(n)``)."""
    rk = _make_8w7()
    assert rk.is_elliptic() is True                      # in the row (very-well-poised)
    res = elliptic_recurrence_8w7(rk)
    assert res is not None
    assert res["order"] == 1
    rho = res["rho"]
    assert len(rho.num) == 4 and len(rho.den) == 4
    assert rho.is_elliptic() is True                     # ρ is balanced on the y-axis
    # coeffs = [-ρ, 1].
    assert res["coeffs"][1].is_unit                      # a1 == 1
    neg_rho = R.monomial(M.scalar(Q(-1, 1))) * rho
    assert res["coeffs"][0] == neg_rho                   # a0 == -ρ


def test_rho_reproduces_f_ratio_independent_point():
    """ρ(n) equals the actual ₈ω₇ sum's f(n+1)/f(n) to < 1e-9 for n = 1, 2, 3 at an
    INDEPENDENT sample point (the closed product form the oracle; the op's gate uses a
    different sample, so this is a genuine re-verification, not the op re-running itself)."""
    rk = _make_8w7()
    res = elliptic_recurrence_8w7(rk)
    assert res is not None
    rho = res["rho"]
    for n in (1, 2, 3):
        vals = dict(_PARAMS)
        vals[_Y] = _PARAMS["q"] ** n
        lhs = rho.eval_trunc(vals, _TRUNC)
        f_n = _f_sum(n)
        assert f_n != Q(0, 1)
        rhs = _f_sum(n + 1) / f_n
        assert _close(lhs, rhs), f"n={n}: rho={float(lhs)} f(n+1)/f(n)={float(rhs)}"


def test_rho_roundtrips_to_ellratio():
    """The returned operand dict rebuilds the SAME ρ EllRatio (an exact re-check handle)."""
    rk = _make_8w7()
    res = elliptic_recurrence_8w7(rk)
    assert res is not None
    rho = res["rho"]
    pref = M(Q(*res["prefactor"]["coeff"]), res["prefactor"]["exps"])
    num = tuple(Theta(M(Q(1, 1), exps)) for exps in res["num"])
    den = tuple(Theta(M(Q(1, 1), exps)) for exps in res["den"])
    rebuilt = R(pref, num=num, den=den)
    assert rebuilt == rho


# ── (b) None on a non-₈ω₇ ratio ─────────────────────────────────────────────────────
def test_unbalanced_term_is_none():
    """θ(ax)/θ(x) is NOT very-well-poised / balanced → out of the row → None (no
    decomposition attempted)."""
    unbal = R(num=(Theta(M.symbol("a") * M.symbol(_X)),), den=(Theta(M.symbol(_X)),))
    assert unbal.is_elliptic() is False
    assert elliptic_recurrence_8w7(unbal) is None


def test_balanced_but_not_8w7_is_none():
    """A balanced (elliptic, in-row) theta ratio that is NOT a ₈ω₇ (no very-well-poised
    quadratic core, not three free params) → honest None."""
    a = M.symbol("a"); b = M.symbol("b"); x = M.symbol(_X)
    wrong = R(num=[Theta(a * x), Theta(a * x.inv())],
              den=[Theta(b * x), Theta(b * x.inv())])
    assert wrong.is_elliptic() is True                   # in the row
    assert elliptic_recurrence_8w7(wrong) is None        # but not a ₈ω₇


def test_zero_ratio_is_none():
    """The zero term ratio has no ₈ω₇ recurrence."""
    assert elliptic_recurrence_8w7(R.monomial(M.scalar(Q(0, 1)))) is None


# ── (c) Python==C byte-exact parity on the ρ EllRatio output ─────────────────────────
def _has_native():
    from srmech.amsc import _native
    return _native.has_native_elliptic_recurrence_8w7()


@pytest.mark.skipif(not _has_native(),
                    reason="native srmech_elliptic_recurrence_8w7 not loaded "
                           "(pure-Python is the complete alternative)")
def test_python_equals_c_byte_exact():
    """Drive BOTH the C and pure-Python paths on the canonical ₈ω₇ and compare the ρ
    EllRatio element-for-element (do NOT trust the C — the rc67 hardening lesson)."""
    from srmech.amsc import _native
    rk = _make_8w7()
    form = er._ratio_to_form(rk)
    c_got = _native.elliptic_recurrence_8w7_c(form)
    assert c_got is not None
    c_has, c_rho_form = c_got
    assert c_has is True                                 # C recognizes the ₈ω₇
    c_rho = er._form_to_ratio(c_rho_form)
    pure = er._elliptic_recurrence_8w7_pure(rk)
    assert pure is not None
    py_rho = pure["rho"]
    # element-for-element (the carrier compare): prefactor + every theta arg.
    assert py_rho.prefactor.coeff == c_rho.prefactor.coeff
    assert py_rho.prefactor.exps == c_rho.prefactor.exps
    assert len(py_rho.num) == len(c_rho.num)
    assert len(py_rho.den) == len(c_rho.den)
    for pa, ca in zip(py_rho.num, c_rho.num):
        assert pa == ca
    for pa, ca in zip(py_rho.den, c_rho.den):
        assert pa == ca
    # the strongest check: the canonical EllRatio compare.
    assert py_rho == c_rho


@pytest.mark.skipif(not _has_native(),
                    reason="native srmech_elliptic_recurrence_8w7 not loaded")
def test_public_op_c_dispatched_equals_pure():
    """The public op (C-dispatched when native) returns the SAME gate-verified ρ as the
    pure path — the dispatch trusts the C only after the byte-for-byte rebuild + gate."""
    rk = _make_8w7()
    res = elliptic_recurrence_8w7(rk)
    pure = er._elliptic_recurrence_8w7_pure(rk)
    assert res is not None and pure is not None
    assert res["rho"] == pure["rho"]


# ── discipline: no numpy / no math / no abs() in the op source ───────────────────────
def test_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_recurrence.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL


# ── the ToolEntry is registered + invocable ─────────────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7" in names
