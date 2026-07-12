"""elliptic_wz_certificate — the ELLIPTIC Σ-row IDENTITY-PROOF op for the Frenkel–Turaev
₈ω₇ SUMMATION: proves ``Σ_{k=0}^n F(n,k) = cf(n)`` EXACTLY (the connection-coefficient
INDUCTION — base case + the ``ThetaSum.is_zero`` inductive step, NOT a 1e-9 numerical
gate) and returns the closed form ``cf(n)``.

This is the CAPSTONE rung of the elliptic Σ-row after :func:`elliptic_gosper` (indefinite,
rc65), :func:`elliptic_recurrence_8w7` (the order-1 finder, rc68) and
:func:`elliptic_zeilberger` (the recurrence + EXACT certificate, rc90). Where
``elliptic_zeilberger`` proves the RECURRENCE ``f(n+1) = ρ(n)·f(n)``, this op proves the
full SUMMATION IDENTITY — the elliptic analogue of :func:`wz_certificate` — and its DISTINCT
output is the **closed form** ``cf(n) = (aq, aq/bc, aq/bd, aq/cd; q,p)_n /
(aq/b, aq/c, aq/d, aq/bcd; q,p)_n`` (Warnaar Cor 2.2 / Rosengren Thm 2.3.1).

Tests:
  (a) the canonical ₈ω₇ → ``verified True``, ``certificate.method ==
      'connection_coefficient_induction'``, ``certificate.exact True``, and the closed form
      has the 4 numerator + 4 denominator Pochhammer bases EXACTLY {aq, aq/bc, aq/bd, aq/cd}
      / {aq/b, aq/c, aq/d, aq/bcd};
  (b) the EXACT inductive-step certificate ``_connection_split_certificate(a,b,c).is_zero
      is True`` (the SAME exact gate elliptic_zeilberger uses; no 1e-9);
  (c) ``None`` on a non-₈ω₇ ratio (unbalanced, balanced-but-wrong-shape, zero);
  (d) Python==C parity when the native peer is present (the C verdict equals the op's; the
      certificate re-decides ≡ 0 in exact ℚ either way). Skipped when native is absent.
"""

import os
import re
import tokenize

import pytest

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.q import Q
from srmech.amsc.thetasum import ThetaSum, _Y
from srmech.amsc import elliptic_recurrence as er
from srmech.amsc.elliptic_zeilberger import _connection_split_certificate
from srmech.amsc.elliptic_wz_certificate import elliptic_wz_certificate


def _make_8w7():
    """The canonical Frenkel–Turaev ₈ω₇ term-ratio ``t(n+1)/t(n)`` (``x = qⁿ``,
    ``y = qⁿ``) with the balancing ``bcde = a²q^{n+1}`` (Warnaar Cor 2.2). The three FREE
    params are ``b, c, d``; ``e`` and ``q^{-n}`` carry ``y`` (dropped by the decompose)."""
    xk = M.symbol(_X); q = M.symbol(_Q_SYM); y = M.symbol(_Y)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    e = (a * a * q * y) * (b * c * d).inv()              # bcde = a²q^{n+1}, y = qⁿ
    poch = [b, c, d, e, y.inv()]                         # 5 Pochhammer params incl q^-n
    num = [Theta(a * q * q * xk * xk), Theta(a * xk)]
    den = [Theta(a * xk * xk), Theta(q * xk)]
    for u in poch:
        num.append(Theta(u * xk)); den.append(Theta(a * q * xk * u.inv()))
    return R(q, num=num, den=den)


def _exps_set(dicts):
    """A list of exps-dicts -> a set of frozensets of the NONZERO (sym, exp) items (so the
    comparison is order-independent over the 4 bases AND robust to any stored-zero exps)."""
    return {frozenset((s, e) for s, e in d.items() if e != 0) for d in dicts}


def _expected_endpoints():
    """The expected ₈ω₇ closed-form Pochhammer bases as exps-sets: numerator
    {aq, aq/bc, aq/bd, aq/cd}, denominator {aq/b, aq/c, aq/d, aq/bcd} (Warnaar Cor 2.2)."""
    q = M.symbol(_Q_SYM)
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c"); d = M.symbol("d")
    aq = a * q
    num = [aq, aq * (b * c).inv(), aq * (b * d).inv(), aq * (c * d).inv()]
    den = [aq * b.inv(), aq * c.inv(), aq * d.inv(), aq * (b * c * d).inv()]
    return _exps_set([dict(m.exps) for m in num]), _exps_set([dict(m.exps) for m in den])


# ── (a) the canonical ₈ω₇ → verified summation identity + the closed form ────────────
def test_canonical_8w7_verified_identity():
    """The canonical ₈ω₇ is in class: the op proves the summation identity (``verified
    True``) with the EXACT connection-coefficient-INDUCTION certificate (no 1e-9 gate)."""
    rk = _make_8w7()
    assert rk.is_elliptic() is True                      # in the row (very-well-poised)
    res = elliptic_wz_certificate(rk)
    assert res is not None
    assert res["verified"] is True
    cert = res["certificate"]
    assert cert["method"] == "connection_coefficient_induction"
    assert cert["exact"] is True
    assert "sum_{k=0}^n F(n,k)" in res["identity"]


def test_closed_form_endpoints_are_the_ft_product():
    """The closed form has the 4 numerator + 4 denominator Pochhammer bases EXACTLY
    {aq, aq/bc, aq/bd, aq/cd} / {aq/b, aq/c, aq/d, aq/bcd} (Warnaar Cor 2.2 / Rosengren
    Thm 2.3.1) — order-independent over the three free params b, c, d."""
    rk = _make_8w7()
    res = elliptic_wz_certificate(rk)
    assert res is not None
    cf = res["closed_form"]
    assert len(cf["num"]) == 4 and len(cf["den"]) == 4
    exp_num, exp_den = _expected_endpoints()
    assert _exps_set(cf["num"]) == exp_num
    assert _exps_set(cf["den"]) == exp_den
    # the first numerator base is always aq = a·q (the leading endpoint).
    aq = M.symbol("a") * M.symbol(_Q_SYM)
    aq_set = frozenset((s, e) for s, e in dict(aq.exps).items() if e != 0)
    assert aq_set in _exps_set(cf["num"])


# ── (b) the EXACT inductive-step certificate is_zero (shared with elliptic_zeilberger) ─
def test_inductive_step_certificate_is_zero():
    """The inductive step IS the cleared connection-coefficient split certificate, decided
    EXACTLY ≡ 0 in the additive ThetaSum carrier (the same exact gate, no 1e-9)."""
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c")
    cert = _connection_split_certificate(a, b, c)
    assert isinstance(cert, ThetaSum)
    assert cert.is_zero is True
    # a perturbed split (drop the term-3 weight → wrong identity) does NOT vanish — so the
    # inductive step is a genuine verification, not trivially always-True.
    N = M.symbol("N"); K = M.symbol("K"); x = M.symbol(_X)
    aN = a * N; bK = b * K; cNK = c * N * K.inv()

    def pm(mid, half):
        return [Theta(mid * half), Theta(mid * half.inv())]

    bad = ThetaSum(terms=(
        (Q(1, 1), M.one(), pm(bK, cNK) + pm(aN, x)),
        (Q(-1, 1), M.one(), pm(aN, cNK) + pm(bK, x)),
        (Q(1, 1), M.one(), pm(aN, bK) + pm(cNK, x)),     # weight dropped → not an identity
    ))
    assert bad.is_zero is False


# ── (c) None on a non-₈ω₇ ratio ─────────────────────────────────────────────────────
def test_unbalanced_term_is_none():
    """θ(ax)/θ(x) is NOT very-well-poised / balanced → out of the row → None."""
    unbal = R(num=(Theta(M.symbol("a") * M.symbol(_X)),), den=(Theta(M.symbol(_X)),))
    assert unbal.is_elliptic() is False
    assert elliptic_wz_certificate(unbal) is None


def test_balanced_but_not_8w7_is_none():
    """A balanced (in-row) theta ratio that is NOT a ₈ω₇ (no VWP quadratic core, not three
    free params) → honest None."""
    a = M.symbol("a"); b = M.symbol("b"); x = M.symbol(_X)
    wrong = R(num=[Theta(a * x), Theta(a * x.inv())],
              den=[Theta(b * x), Theta(b * x.inv())])
    assert wrong.is_elliptic() is True                   # in the row
    assert elliptic_wz_certificate(wrong) is None        # but not a ₈ω₇


def test_zero_ratio_is_none():
    """The zero term ratio has no ₈ω₇ summation identity."""
    assert elliptic_wz_certificate(R.monomial(M.scalar(Q(0, 1)))) is None


# ── (d) Python==C parity (the certificate decision) ─────────────────────────────────
def _has_native():
    from srmech.amsc import _native
    return _native.has_native_elliptic_wz_certificate()


@pytest.mark.skipif(not _has_native(),
                    reason="native srmech_elliptic_wz_certificate not loaded "
                           "(pure-Python is the complete alternative)")
def test_python_equals_c_verdict():
    """Drive the C peer on the canonical ₈ω₇ and a non-₈ω₇; the native verdict must match
    the op (the C recognizes + decides the certificate ≡ 0; the op re-decides cert.is_zero
    in exact ℚ before returning)."""
    from srmech.amsc import _native
    rk = _make_8w7()
    got = _native.elliptic_wz_certificate_c(er._ratio_to_form(rk))
    assert got is not None
    c_has, _payload = got
    assert c_has is True                                 # C recognizes + certifies the ₈ω₇
    # the op (C-dispatched when native) still returns the verified closed form.
    res = elliptic_wz_certificate(rk)
    assert res is not None and res["verified"] is True
    # a non-₈ω₇ → C declines (has False).
    bad = R(M.one(), num=(Theta(M.symbol("a") * M.symbol(_X)),),
            den=(Theta(M.symbol(_Q_SYM) * M.symbol(_X)),))
    bad_got = _native.elliptic_wz_certificate_c(er._ratio_to_form(bad))
    assert bad_got is not None
    assert bad_got[0] is False


# ── discipline: no numpy / no math / no abs() in the op source ───────────────────────
def test_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_wz_certificate.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL


# ── the ToolEntry is registered ─────────────────────────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate" in names
