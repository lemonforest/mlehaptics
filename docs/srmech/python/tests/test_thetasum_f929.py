"""rc62 — the ThetaSum ADDITIVE theta-function carrier (the foundation under genuine
elliptic creative telescoping).

Numpy-free + math-free + abs-free: the exact ThetaSum algebra (add/sub/neg/scalar-mul/
mul/shift_x/shift_y), and the LOAD-BEARING ``is_zero`` — an EXACT Weierstrass three-term-
relation reduction (NO eval, NO convergence threshold) that decides the known
Weierstrass theta identity exactly True (and a deliberately-broken variant False), plus
the quasi-periodicity-class grouping (a 2-class sum is zero iff both classes vanish).

The two load-bearing theorems are MPM-verified from the ACTUAL source PDF (read in full,
equation numbers confirmed) — Hjalmar Rosengren, "Elliptic Hypergeometric Functions"
(arXiv:1608.06161v3, 20 Jun 2017): the Weierstrass three-term relation is §1.4 Eq.
(1.12); the degree bound is §1.3 Lemma 1.3.2 (the Fundamental Theorem of Elliptic
Functions). See the module docstring of ``srmech.amsc.thetasum`` for the verified forms.

The ``float(...)`` calls here are ONLY the test's CONVERGENCE-ORACLE cross-check
(``eval_trunc`` of a true theta identity converges to 0 as the truncation depth grows) —
they are NOT the ``is_zero`` decision path (which is exact + symbolic)."""

import os
import re
import tokenize

from srmech.amsc import ThetaSum
from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.thetasum import _VERIFY_POINTS, _VERIFY_TRUNC
from srmech.amsc.q import Q

_a, _b, _c, _d, _e = (M.symbol("a"), M.symbol("b"), M.symbol("c"),
                      M.symbol("d"), M.symbol("e"))
_x, _y = M.symbol("x"), M.symbol("y")


def _pm(u, v):
    """The plus/minus pair theta(u*v^pm) = theta(uv)*theta(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


# ── ergonomic constructors + accessors ────────────────────────────────────────
def test_zero_one_and_from_ellratio():
    assert ThetaSum.zero().is_zero is True
    assert ThetaSum.one().is_zero is False
    assert ThetaSum.one().is_unit is True
    # lift a single-term EllRatio
    r = R(num=(Theta(_a * _x),), den=(Theta(_x),))      # theta(ax)/theta(x)
    ts = ThetaSum.from_ellratio(r)
    assert len(ts.terms) == 1
    assert len(ts.den_thetas) == 1
    assert ThetaSum.from_ellratio(R.monomial(M(Q(0, 1)))).is_zero is True  # zero ratio


# ── additive + multiplicative algebra (exact) ─────────────────────────────────
def test_additive_algebra_exact():
    r = R(num=(Theta(_a * _x),), den=(Theta(_x),))
    ts = ThetaSum.from_ellratio(r)
    assert (ts - ts).is_zero is True                    # a - a = 0
    assert (ts + ts).is_zero is False                   # a + a != 0
    assert (-ts + ts).is_zero is True                   # -a + a = 0
    assert (ts.scalar_mul(2) - ts - ts).is_zero is True  # 2a - a - a = 0
    assert (ts - ThetaSum.zero() - ts).is_zero is True
    # scalar identities through __add__/__sub__ with a bare Q
    one = ThetaSum.one()
    assert ((one + Q(2, 1)) - Q(3, 1)).is_zero is True  # 1 + 2 - 3 = 0


def test_multiplicative_algebra_exact():
    r = R(num=(Theta(_a * _x),), den=(Theta(_x),))
    ts = ThetaSum.from_ellratio(r)
    assert (ts * ThetaSum.one() - ts).is_zero is True   # a * 1 == a
    assert (ts * Q(0, 1)).is_zero is True               # a * 0 == 0
    # (a + b)*1 == a + b
    r2 = R(num=(Theta(_b * _x),), den=(Theta(_x),))
    ts2 = ThetaSum.from_ellratio(r2)
    s = ts + ts2
    assert (s * ThetaSum.one() - s).is_zero is True


def test_shifts_preserve_a_known_identity():
    """The Weierstrass identity holds for ANY summation point, so shifting x->q*x (or
    y->q*y) keeps it identically zero — the shift_x / shift_y carriers are value-exact."""
    ident = ThetaSum.three_term(_a, _b, _c)
    assert ident.shift_x().is_zero is True
    assert ident.shift_y().is_zero is True
    assert ident.shift_x().shift_x().is_zero is True
    # a NON-identity ThetaSum changes under a shift (sanity: shift is not a no-op)
    r = R(num=(Theta(_a * _x),), den=(Theta(_x),))
    ts = ThetaSum.from_ellratio(r)
    assert (ts.shift_x() - ts).is_zero is False


# ── is_zero decides a KNOWN theta identity EXACTLY (the load-bearing test) ─────
def test_is_zero_decides_weierstrass_three_term_exactly():
    """The MPM-verified Weierstrass three-term relation (Rosengren Eq. 1.12) is
    identically zero -> ``is_zero`` True, decided EXACTLY by the symbolic three-term
    reduction (NO eval). A deliberately-broken variant (wrong a/c weight) -> False."""
    ident = ThetaSum.three_term(_a, _b, _c)
    assert ident.is_zero is True
    # broken: the third term's a/c weight replaced by 1
    broken = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_a, _x) + _pm(_b, _c)),
        (Q(-1, 1), M.one(), _pm(_b, _x) + _pm(_a, _c)),
        (Q(-1, 1), M.one(), _pm(_c, _x) + _pm(_b, _a)),   # weight 1, should be a/c
    ))
    assert broken.is_zero is False
    # the same identity on other parameters + on the y-variable
    assert ThetaSum.three_term(_a, _d, _e).is_zero is True
    assert ThetaSum.three_term(_a, _b, _c, x=_y).is_zero is True


def test_addition_formula_as_an_exact_rewrite():
    """``three_term`` IS the zero identity LHS - RHS, so the addition formula
    theta(ax^pm)theta(bc^pm) == theta(bx^pm)theta(ac^pm) + (a/c)theta(cx^pm)theta(ba^pm)
    holds as exact ThetaSum equality (Rosengren Eq. 1.12)."""
    lhs = ThetaSum(terms=((Q(1, 1), M.one(), _pm(_a, _x) + _pm(_b, _c)),))
    rhs = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_b, _x) + _pm(_a, _c)),
        (Q(1, 1), (_a / _c), _pm(_c, _x) + _pm(_b, _a)),
    ))
    assert lhs == rhs
    assert (lhs - rhs).is_zero is True


def test_is_zero_never_accepts_a_converging_witness():
    """A genuine theta identity is NEVER exactly 0 at any finite eval_trunc depth (it only
    CONVERGES) — so an eval-based test would be a hallucination. is_zero is exact +
    symbolic; the eval_trunc oracle here merely CONFIRMS the convergence independently."""
    ident = ThetaSum.three_term(_a, _b, _c)
    # the exact symbolic decision
    assert ident.is_zero is True
    # the convergence oracle: the truncated value shrinks toward 0 with depth, and is
    # NOT exactly 0 at finite depth (the very reason is_zero must be symbolic).
    v_lo = ident.eval_trunc(_VERIFY_POINTS[0], 6)
    v_hi = ident.eval_trunc(_VERIFY_POINTS[0], 16)
    assert v_lo != Q(0, 1) and v_hi != Q(0, 1)          # finite depth: NOT exactly 0
    assert abs(float(v_hi)) < abs(float(v_lo))          # but converging toward 0


# ── quasi-periodicity grouping (a 2-class sum is zero iff both classes vanish) ─
def test_quasiperiodicity_two_class_grouping():
    """Theta-products of different quasi-periodicity are linearly independent, so a sum
    of two identities living in different classes (x-pairs vs y-pairs) is zero iff BOTH
    vanish; breaking either class makes the whole sum nonzero."""
    idx = ThetaSum.three_term(_a, _b, _c)               # x-class identity
    idy = ThetaSum.three_term(_a, _b, _c, x=_y)         # y-class identity
    assert idx.is_zero and idy.is_zero
    assert (idx + idy).is_zero is True                  # both classes vanish
    # break the y-class only (wrong weight)
    broken_y = ThetaSum(terms=(
        (Q(1, 1), M.one(), _pm(_a, _y) + _pm(_b, _c)),
        (Q(-1, 1), M.one(), _pm(_b, _y) + _pm(_a, _c)),
        (Q(-1, 1), M.one(), _pm(_c, _y) + _pm(_b, _a)),
    ))
    assert broken_y.is_zero is False
    assert (idx + broken_y).is_zero is False            # one class nonzero -> sum nonzero


def test_is_zero_honest_on_unreducible_shape():
    """A theta-product that is NOT a clean product of plus/minus-pairs (an odd single
    theta) is outside the carrier's exact-reducible shape -> is_zero honestly returns
    False (never accepts on a converging eval)."""
    odd = ThetaSum(terms=((Q(1, 1), M.one(), (Theta(_a * _x),)),))
    assert odd.is_zero is False


# ── discipline: no numpy / no math / no abs() in the carrier source ───────────
def test_thetasum_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "thetasum.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL


# ── carrier has NO ToolEntry footprint (the running tools.total) ────────────────
def test_thetasum_is_a_carrier_no_tool_entry():
    """ThetaSum is a CARRIER (a class + private helpers), exactly like EllRatio / QMat /
    TriPoly — it adds NO ToolEntry. (The running describe()['tools']['total'] is 338 after
    carrier_spectrum's public op landed in rc69; ThetaSum itself contributes nothing.)"""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 384
