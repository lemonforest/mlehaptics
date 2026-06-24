"""rc61 — elliptic_gosper, the FIRST engine op of the ELLIPTIC F929 reduction row.

The ELLIPTIC analog of Gosper's indefinite hypergeometric summation over the
modified-theta ``EllRatio`` carrier (Gasper–Schlosser, *Adv. Stud. Contemp. Math.*
(Kyungshang) 11, no. 1 (2005), 67–84, arXiv:math/0505215 — "using indefinite
summation"; secondary anchor Warnaar, *Constr. Approx.* 18 (2002) 479–502).

Numpy-free + math-free + abs()-free in the engine source: the certificate ``R`` is
verified to satisfy the elliptic Gosper equation ``R(qx)·r − R = 1`` exactly in ``ℚ``
(the carrier ``eval_trunc`` oracle; the theta-quotient carrier is multiplicatively
but not additively closed). The keystone cases:

  - a genuinely elliptic-summable term (the elliptic-geometric constant ratio
    ``r = z``) → a certificate ``R``, with ``R.qshift()·r − R == 1`` exact;
  - a balanced-but-not-summable theta term → honest ``None``;
  - a non-elliptic (unbalanced) term → ``None`` (out of the row).
"""

import io
import os
import re
import tokenize

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.elliptic_gosper import elliptic_gosper
from srmech.amsc.q import Q

_A, _B, _X = M.symbol("a"), M.symbol("b"), M.symbol("x")
_VALS = {"q": Q(2, 1), "p": Q(1, 9), "x": Q(2, 3), "a": Q(3, 5), "b": Q(4, 7)}


def _th(m):
    return Theta(m)


# ── KEYSTONE 1: a genuinely elliptic-summable term → a verified certificate ───
def test_elliptic_geometric_constant_ratio_is_summable():
    """The elliptic-geometric core: a CONSTANT term ratio r = z = 3/2 is
    elliptically balanced AND elliptic-Gosper-summable, with the closed-form
    certificate R = 1/(z − 1) = z_den/(z_num − z_den) = 2 (then R(qx)·r − R =
    R·(z − 1) = 1, exact at any truncation). The elliptic analogue of the ordinary
    / q-geometric Σ zⁿ closed form."""
    r = R.monomial(M.scalar(Q(3, 2)))
    assert r.is_elliptic() is True                    # in the row (balanced)
    res = elliptic_gosper(r)
    assert res is not None                            # summable → a certificate
    cert = res["certificate"]
    # the verified certificate satisfies the elliptic Gosper equation EXACTLY:
    lhs = cert.qshift() * r                            # R(qx)·r(x), in the carrier
    assert lhs.eval_trunc(_VALS, 8) - cert.eval_trunc(_VALS, 8) == Q(1, 1)
    # the certificate is the constant R = 2 (1/(3/2 − 1)):
    assert res["prefactor"]["coeff"] == (2, 1)
    assert res["prefactor"]["exps"] == {}
    assert res["num"] == [] and res["den"] == []


def test_elliptic_geometric_several_constants():
    """Several constant ratios → R = z_den/(z_num − z_den), each verified exact."""
    for zn, zd, rn, rd in [(5, 4, 4, 1), (7, 3, 3, 4), (2, 5, 5, -3)]:
        r = R.monomial(M.scalar(Q(zn, zd)))
        res = elliptic_gosper(r)
        assert res is not None
        cert = res["certificate"]
        assert cert.qshift() * r != r                 # nontrivial
        lhs = cert.qshift() * r
        assert lhs.eval_trunc(_VALS, 8) - cert.eval_trunc(_VALS, 8) == Q(1, 1)
        # R = z_den / (z_num − z_den) reduced:
        from srmech.amsc.cyclic import gcd
        g = gcd(abs(rd), abs(rn)) if rn else abs(rd)
        assert res["prefactor"]["coeff"] in ((rn // g, rd // g),
                                             (-(rn // g), -(rd // g)))


def test_certificate_roundtrips_to_ellratio():
    """The returned operand dict rebuilds the SAME EllRatio (an exact re-check
    handle for the caller)."""
    r = R.monomial(M.scalar(Q(9, 5)))
    res = elliptic_gosper(r)
    assert res is not None
    cert = res["certificate"]
    rebuilt = R.monomial(
        M(Q(*res["prefactor"]["coeff"]), res["prefactor"]["exps"]))
    assert rebuilt == cert


# ── KEYSTONE 2: a non-summable elliptic term → honest None ────────────────────
def test_balanced_but_not_summable_is_none():
    """A balanced (elliptic, in-row) theta term that has NO elliptic-hypergeometric
    antidifference → honest None. θ(ax)θ(bx)/[θ(x)θ(abx)] is balanced but not
    Gosper-summable (the single-x lattice carries no theta telescoper for it)."""
    bal = R(num=(_th(_A * _X), _th(_B * _X)), den=(_th(_X), _th(_A * _B * _X)))
    assert bal.is_elliptic() is True                  # in the row
    assert elliptic_gosper(bal) is None               # but not summable


def test_constant_one_has_no_finite_certificate():
    """r = 1 is balanced but z = 1 has no finite certificate R = 1/(z − 1) → None."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(1, 1)))) is None


# ── KEYSTONE 3: a non-elliptic (unbalanced) term → None (out of the row) ──────
def test_unbalanced_term_is_out_of_row():
    """θ(ax)/θ(x) is NOT elliptically balanced (∏ args mismatch) → out of the row,
    so elliptic_gosper returns None without attempting a closed form."""
    unbal = R(num=(_th(_A * _X),), den=(_th(_X),))
    assert unbal.is_elliptic() is False               # out of the row
    assert elliptic_gosper(unbal) is None


def test_zero_ratio_is_none():
    """The zero term ratio has no nonzero elliptic-hypergeometric closed form."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(0, 1)))) is None


# ── coercion: an EllMonomial / Theta lifts to the term-ratio EllRatio ─────────
def test_coerces_ellmonomial_and_scalar():
    """A bare EllMonomial scalar (z = 5/2) lifts to the constant-ratio EllRatio and
    is certified the same as the explicit EllRatio.monomial form."""
    res_m = elliptic_gosper(M.scalar(Q(5, 2)))
    res_r = elliptic_gosper(R.monomial(M.scalar(Q(5, 2))))
    assert res_m is not None and res_r is not None
    assert res_m["prefactor"] == res_r["prefactor"]


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
