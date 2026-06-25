"""elliptic_gosper — the FIRST engine op of the ELLIPTIC F929 reduction row, the
GENUINE structural finder (peel-coboundary + Weierstrass three-term key-equation
y-solve + exact ``ThetaSum.is_zero`` verifier; replaces the rc61 brute-force
enumerate-and-test + eval-based verifier).

The ELLIPTIC analog of Gosper's indefinite hypergeometric summation over the
modified-theta ``EllRatio`` carrier (Gasper–Schlosser, *Adv. Stud. Contemp. Math.*
(Kyungshang) 11, no. 1 (2005), 67–84, arXiv:math/0505215 — "using indefinite
summation"; the Weierstrass three-term key equation = Rosengren, arXiv:1608.06161,
§1.4 Eq. (1.12); secondary anchor Warnaar, *Constr. Approx.* 18 (2002) 479–502;
keystone identity = the Frenkel–Turaev ₁₀E₉ sum).

Numpy-free + math-free + abs()-free in the engine source: the certificate ``R`` is
verified to satisfy the elliptic Gosper equation ``R(qx)·r − R = 1`` EXACTLY via the
additive :attr:`~srmech.amsc.thetasum.ThetaSum.is_zero` (structural; the theta-
quotient carrier is multiplicatively but NOT additively closed, so the additive ``−``
lives in ``ThetaSum`` — never a converging-eval witness). The keystone cases:

  - the GENUINE Frenkel–Turaev keystone term ratio (a true theta-quotient, x-
    dependent) → the verified certificate ``Rc`` EXACTLY (the structural finder
    decomposes-and-computes; the cert sits in the FLIPPED chiral endianness);
  - a non-elliptic (unbalanced) term → ``None`` (out of the row);
  - the zero term ratio → ``None``.
"""

import io
import os
import re
import tokenize

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R, _X, _Q_SYM
from srmech.amsc.elliptic_gosper import elliptic_gosper
from srmech.amsc.q import Q

_A, _B = M.symbol("a"), M.symbol("b")
_x = M.symbol(_X)
_q = M.symbol(_Q_SYM)


def _th(m):
    return Theta(m)


def _th_x(alpha):
    """θ(α·x^±) = (θ(α·x), θ(α/x)) — the x-pair of a parameter α."""
    return (Theta(alpha * _x), Theta(alpha * _x.inv()))


def _th_pair(u, v):
    """θ(u·v^±) = (θ(u·v), θ(u/v)) — an x-free even theta pair."""
    return (Theta(u * v), Theta(u * v.inv()))


def _genuine_keystone():
    """Build the GENUINE Frenkel–Turaev-shaped keystone: a true x-dependent theta-
    quotient term ratio ``r`` whose known elliptic-Gosper certificate is ``Rc`` (an
    x-dependent theta-quotient, NOT the trivial geometric constant). Construction
    (c = q·b):

      Rc = R(prefactor = a⁻¹·c, num = θ(b x^±)+θ(a c^±), den = θ(c x^±)+θ(b a^±))
      r  = R(num=θ(a x^±)+θ(b c^±))
           · R(prefactor=a/c, num=θ(c x^±)+θ(b a^±)).qshift()
           · ( R(prefactor=a/c, num=θ(c x^±)+θ(b a^±))
               · R(num=θ(b x^±)+θ(a c^±)).qshift() ).inv()

    Returns ``(r, Rc)``."""
    a, b = _A, _B
    c = b * _q
    Rc = R(a.inv() * c,
           num=list(_th_x(b)) + list(_th_pair(a, c)),
           den=list(_th_x(c)) + list(_th_pair(b, a)))
    r1 = R(num=list(_th_x(a)) + list(_th_pair(b, c)))
    r2 = R(a / c, num=list(_th_x(c)) + list(_th_pair(b, a)))
    r3 = R(a / c, num=list(_th_x(c)) + list(_th_pair(b, a)))
    r4 = R(num=list(_th_x(b)) + list(_th_pair(a, c)))
    r = r1 * r2.qshift() * (r3 * r4.qshift()).inv()
    return r, Rc


# ── KEYSTONE 1: the GENUINE Frenkel–Turaev term → the verified certificate Rc ──
def test_genuine_keystone_certificate_found():
    """The genuine (x-dependent theta-quotient) Frenkel–Turaev keystone is in the
    row and elliptic-Gosper-summable: the STRUCTURAL finder returns a certificate
    (decompose-and-compute, no enumerate-and-test)."""
    r, _Rc = _genuine_keystone()
    assert r.is_zero is False
    assert r.is_elliptic() is True                    # in the row (balanced)
    res = elliptic_gosper(r)
    assert res is not None                            # summable → a certificate


def test_genuine_keystone_certificate_equals_Rc():
    """The found certificate equals the KNOWN certificate ``Rc`` EXACTLY (the cert
    sits in the flipped chiral endianness, resolved against the exact verifier)."""
    r, Rc = _genuine_keystone()
    res = elliptic_gosper(r)
    assert res is not None
    assert res["certificate"] == Rc                   # exact, not just verifying


def test_genuine_keystone_certificate_satisfies_gosper_equation():
    """The returned certificate satisfies the elliptic Gosper equation
    ``R(qx)·r − R == 1`` EXACTLY, decided structurally by ``ThetaSum.is_zero``
    (the additive carrier; never a converging eval)."""
    from srmech.amsc.thetasum import ThetaSum
    r, _Rc = _genuine_keystone()
    res = elliptic_gosper(r)
    assert res is not None
    cert = res["certificate"]
    residual = (ThetaSum.from_ellratio(cert.qshift() * r)
                - ThetaSum.from_ellratio(cert) - ThetaSum.one())
    assert residual.is_zero is True


def test_certificate_roundtrips_to_ellratio():
    """The returned operand dict rebuilds the SAME EllRatio (an exact re-check
    handle for the caller)."""
    r, Rc = _genuine_keystone()
    res = elliptic_gosper(r)
    assert res is not None
    cert = res["certificate"]
    pref = M(Q(*res["prefactor"]["coeff"]), res["prefactor"]["exps"])
    num = tuple(Theta(M(Q(1, 1), exps)) for exps in res["num"])
    den = tuple(Theta(M(Q(1, 1), exps)) for exps in res["den"])
    rebuilt = R(pref, num=num, den=den)
    assert rebuilt == cert
    assert rebuilt == Rc


# ── KEYSTONE 2: a non-elliptic (unbalanced) term → None (out of the row) ──────
def test_unbalanced_term_is_out_of_row():
    """θ(ax)/θ(x) is NOT elliptically balanced (∏ args mismatch) → out of the row,
    so elliptic_gosper returns None without attempting a closed form."""
    unbal = R(num=(_th(_A * _x),), den=(_th(_x),))
    assert unbal.is_elliptic() is False               # out of the row
    assert elliptic_gosper(unbal) is None


# ── KEYSTONE 3: the zero term ratio → None ────────────────────────────────────
def test_zero_ratio_is_none():
    """The zero term ratio has no nonzero elliptic-hypergeometric closed form."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(0, 1)))) is None
    assert elliptic_gosper(R.monomial(M(Q(0, 1)))) is None


# ── a balanced-but-not-Weierstrass theta term → honest None ───────────────────
def test_balanced_but_not_summable_is_none():
    """A balanced (elliptic, in-row) theta term that has NO elliptic-hypergeometric
    antidifference in the structurally-decidable single-Weierstrass class → honest
    None. θ(ax)θ(bx)/[θ(x)θ(abx)] is balanced but peels to no coboundary."""
    bal = R(num=(_th(_A * _x), _th(_B * _x)), den=(_th(_x), _th(_A * _B * _x)))
    assert bal.is_elliptic() is True                  # in the row
    assert elliptic_gosper(bal) is None               # but not summable


# ── the elliptic-GEOMETRIC core: a constant scalar ratio is summable ──────────
def test_geometric_constant_ratio_is_summable():
    """A CONSTANT term ratio r = z = 5/2 is the elliptic-geometric core: summable with
    the closed-form certificate R = z_den/(z_num − z_den) = 2/3 (then R(qx)·r − R =
    R·(z − 1) = 1, exact). The genuine finder is COMPLETE — it certifies BOTH the
    genuine theta keystone AND the geometric-constant core (the elliptic analogue of
    Σ zⁿ)."""
    from srmech.amsc.thetasum import ThetaSum
    r = R.monomial(M.scalar(Q(5, 2)))
    assert r.is_elliptic() is True
    res = elliptic_gosper(r)
    assert res is not None
    assert res["prefactor"]["coeff"] == (2, 3)        # R = 2/(5 − 2) = 2/3
    assert res["num"] == [] and res["den"] == []
    cert = res["certificate"]
    residual = (ThetaSum.from_ellratio(cert.qshift() * r)
                - ThetaSum.from_ellratio(cert) - ThetaSum.one())
    assert residual.is_zero is True                   # R(qx)·r − R == 1, exact


def test_geometric_constant_one_has_no_finite_certificate():
    """r = 1 is balanced but z = 1 has no finite certificate R = 1/(z − 1) → None."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(1, 1)))) is None


# ── coercion: an EllMonomial / Theta lifts to the term-ratio EllRatio ─────────
def test_coerces_ellmonomial_and_scalar():
    """A bare EllMonomial scalar (z = 5/2) lifts to the constant-ratio EllRatio and is
    certified the same as the explicit EllRatio.monomial form."""
    res_m = elliptic_gosper(M.scalar(Q(5, 2)))
    res_r = elliptic_gosper(R.monomial(M.scalar(Q(5, 2))))
    assert res_m is not None and res_r is not None
    assert res_m["prefactor"] == res_r["prefactor"]   # coerce parity


# ── discipline: no numpy / no math / no abs() in the engine source ────────────
def test_elliptic_gosper_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_gosper.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None      # no bare abs() CALL


# ── the ToolEntry is registered + invocable ───────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_gosper.elliptic_gosper" in names
