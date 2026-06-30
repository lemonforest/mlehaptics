"""elliptic_zeilberger — the ELLIPTIC Σ-row CREATIVE-TELESCOPING op for the Frenkel–
Turaev ₈ω₇ summation: the order-1 recurrence ``f(n+1) = ρ(n)·f(n)`` PLUS an EXACT
connection-coefficient certificate that PROVES it (the ``ThetaSum.is_zero`` decision,
NOT rc68's 1e-9 numerical convergence gate).

This is the THIRD rung of the elliptic Σ-row after :func:`elliptic_gosper` (indefinite,
rc65) and :func:`elliptic_recurrence_8w7` (the order-1 finder, rc68 — whose verification
gate was numerical). Where rc68 only checked ``ρ(n)`` numerically, this op REPLACES that
gate with an EXACT proof: the cleared connection-coefficient split (Rosengren
arXiv:1608.06161 Eq. 2.12–2.14 → Eq. 1.12, the Weierstrass three-term relation) decided
``≡ 0`` in the exact additive :class:`ThetaSum` carrier.

Tests:
  (a) the canonical ₈ω₇ → ``verified True``, ``order 1``, ``certificate.exact True``, and
      the recurrence ``ρ`` equals the rc68 :func:`elliptic_recurrence_8w7` ρ (the EXACT op
      composes the SAME recognize-decompose-construct, only the GATE differs);
  (b) the EXACT certificate ``_connection_split_certificate(a,b,c).is_zero is True`` —
      built from the RAW ±-pair split (3 terms), NOT via ``ThetaSum.three_term`` — and a
      perturbed split is NOT zero (the decision is not trivially always-True);
  (c) ``None`` on a non-₈ω₇ ratio (unbalanced, or balanced-but-wrong-shape);
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
from srmech.amsc.elliptic_recurrence import elliptic_recurrence_8w7
from srmech.amsc import elliptic_zeilberger as ez
from srmech.amsc.elliptic_zeilberger import (
    elliptic_zeilberger, _connection_split_certificate,
)


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


# ── (a) the canonical ₈ω₇ → verified order-1 recurrence + the EXACT certificate ──────
def test_canonical_8w7_verified_order_1():
    """The canonical ₈ω₇ is in class: the op returns an order-1 recurrence with
    ``verified True`` and the EXACT connection-coefficient certificate (the no-1e-9 gate)."""
    rk = _make_8w7()
    assert rk.is_elliptic() is True                      # in the row (very-well-poised)
    res = elliptic_zeilberger(rk)
    assert res is not None
    assert res["order"] == 1
    assert res["verified"] is True
    cert = res["certificate"]
    assert cert["kind"] == "connection_coefficient_split"
    assert cert["exact"] is True
    rho = res["rho"]
    assert len(rho.num) == 4 and len(rho.den) == 4
    assert rho.is_elliptic() is True                     # ρ is balanced on the y-axis


def test_rho_equals_rc68_recurrence():
    """The EXACT op's ρ is byte-identical to the rc68 elliptic_recurrence_8w7 ρ (same
    recognize-decompose-construct; only the verification GATE differs — numerical→exact)."""
    rk = _make_8w7()
    res = elliptic_zeilberger(rk)
    res68 = elliptic_recurrence_8w7(rk)
    assert res is not None and res68 is not None
    assert res["rho"] == res68["rho"]
    # coeffs = [-ρ, 1] (f(n+1) = ρ(n)·f(n)).
    neg_rho = R.monomial(M.scalar(Q(-1, 1))) * res["rho"]
    assert res["coeffs"][0] == neg_rho
    assert res["coeffs"][1].is_unit


# ── (b) the EXACT certificate is_zero, built from the raw ±-pair split ───────────────
def test_connection_split_certificate_is_zero():
    """The cleared connection-coefficient split certificate decides EXACTLY ≡ 0 (the
    genuine inductive step of the Frenkel–Turaev proof; Rosengren Eq. 2.12–2.14 → 1.12)."""
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c")
    cert = _connection_split_certificate(a, b, c)
    assert isinstance(cert, ThetaSum)
    assert cert.is_zero is True


def test_certificate_built_from_raw_not_three_term():
    """The certificate is built from the RAW ±-pair split (3 weighted theta-product terms),
    NOT trivially via ThetaSum.three_term — so is_zero is a genuine verification of THIS
    instance (and a PERTURBED split is NOT zero, proving is_zero is not always-True)."""
    a = M.symbol("a"); b = M.symbol("b"); c = M.symbol("c")
    cert = _connection_split_certificate(a, b, c)
    # raw split: exactly three quasi-periodicity terms, each two ±-pairs (4 thetas).
    assert len(cert.terms) == 3
    for _pref, thetas in cert.terms:
        assert len(thetas) == 4
    # a perturbed split (drop the term-3 weight → wrong identity) does NOT vanish.
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
    assert elliptic_zeilberger(unbal) is None


def test_balanced_but_not_8w7_is_none():
    """A balanced (in-row) theta ratio that is NOT a ₈ω₇ (no VWP quadratic core, not three
    free params) → honest None."""
    a = M.symbol("a"); b = M.symbol("b"); x = M.symbol(_X)
    wrong = R(num=[Theta(a * x), Theta(a * x.inv())],
              den=[Theta(b * x), Theta(b * x.inv())])
    assert wrong.is_elliptic() is True                   # in the row
    assert elliptic_zeilberger(wrong) is None            # but not a ₈ω₇


def test_zero_ratio_is_none():
    """The zero term ratio has no ₈ω₇ recurrence."""
    assert elliptic_zeilberger(R.monomial(M.scalar(Q(0, 1)))) is None


# ── (d) Python==C parity (the certificate decision) ─────────────────────────────────
def _has_native():
    from srmech.amsc import _native
    return _native.has_native_elliptic_zeilberger()


@pytest.mark.skipif(not _has_native(),
                    reason="native srmech_elliptic_zeilberger not loaded "
                           "(pure-Python is the complete alternative)")
def test_python_equals_c_verdict():
    """Drive the C peer on the canonical ₈ω₇ and a non-₈ω₇; the native verdict must match
    the op (the C recognizes + decides the certificate ≡ 0; do NOT trust it blindly — the
    op re-decides cert.is_zero in exact ℚ before returning)."""
    from srmech.amsc import _native
    rk = _make_8w7()
    got = _native.elliptic_zeilberger_c(er._ratio_to_form(rk))
    assert got is not None
    c_has, _payload = got
    assert c_has is True                                 # C recognizes + certifies the ₈ω₇
    # the op (C-dispatched when native) still returns the verified recurrence.
    res = elliptic_zeilberger(rk)
    assert res is not None and res["verified"] is True
    # a non-₈ω₇ → C declines (has False).
    bad = R(M.one(), num=(Theta(M.symbol("a") * M.symbol(_X)),),
            den=(Theta(M.symbol(_Q_SYM) * M.symbol(_X)),))
    bad_got = _native.elliptic_zeilberger_c(er._ratio_to_form(bad))
    assert bad_got is not None
    assert bad_got[0] is False


# ── discipline: no numpy / no math / no abs() in the op source ───────────────────────
def test_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_zeilberger.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None         # no bare abs() CALL


# ── the ToolEntry is registered ─────────────────────────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_zeilberger.elliptic_zeilberger" in names
