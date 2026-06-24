"""rc61 → rc63 — elliptic_gosper, the FIRST engine op of the ELLIPTIC F929 row.

The ELLIPTIC analog of Gosper's indefinite hypergeometric summation over the
modified-theta carrier (Gasper–Schlosser, *Adv. Stud. Contemp. Math.* (Kyungshang)
11, no. 1 (2005), 67–84, arXiv:math/0505215 — "using indefinite summation"; the
Weierstrass three-term engine + degree bound cross-anchored to Rosengren
arXiv:1608.06161 §1.4 Eq. (1.12) / §1.3 Lemma 1.3.2; secondary anchor Warnaar,
*Constr. Approx.* 18 (2002) 479–502).

**rc63 — the GENUINE upgrade.** rc61 verified the elliptic Gosper equation
``R(qx)·r − R = 1`` through the multiplicative ``EllRatio.eval_trunc`` oracle,
accepting a certificate ONLY when the gap to 1 was EXACTLY 0 in exact-ℚ — which
holds only for the theta-FREE geometric core. A genuine theta telescoper's residual
only CONVERGES (it is `~4.7e-14`, never exactly 0, at finite depth), so rc61 returned
``None`` on every genuine theta telescoper. rc63 rebuilds the verifier on the rc62
``ThetaSum`` additive carrier, whose ``is_zero`` is an EXACT symbolic decision
(Weierstrass three-term reduction; NEVER a convergence threshold) — so the genuine
theta antidifference is now decidable EXACTLY. numpy-free + math-free + abs()-free.

The keystone cases:
  - the elliptic-GEOMETRIC core (constant ratio ``r = z``) → a certificate ``R``,
    end-to-end via ``elliptic_gosper`` (the rc61 keystone, kept green);
  - a GENUINE theta telescoper (a nontrivial theta-quotient ``r``) → its certificate
    ``R`` verified EXACTLY by ``ThetaSum.is_zero`` (the rc63 win — rc61's eval gap is
    nonzero on it, so rc61 returns ``None``);
  - a genuine non-summable theta term → honest ``None``;
  - a non-elliptic (unbalanced) term → ``None`` (out of the row).
"""

import os
import re
import tokenize

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.elliptic_gosper import (
    elliptic_gosper, _verifies_gosper_equation, _is_balanced, _has_zero_theta)
from srmech.amsc.q import Q

_A, _B, _X = M.symbol("a"), M.symbol("b"), M.symbol("x")
_Q = M.symbol("q")
_Xi = _X.inv()
_VALS = {"q": Q(2, 1), "p": Q(1, 9), "x": Q(2, 3), "a": Q(3, 5), "b": Q(4, 7)}
# a generic, convergent (|p| < 1) sample set for the numeric Gosper-equation cross-check.
_GVALS = {"q": Q(7, 5), "p": Q(1, 12), "x": Q(5, 7), "a": Q(2, 3), "b": Q(4, 9)}


def _th(m):
    return Theta(m)


def _pmx(al):
    """The same-α theta ±-pair θ(α·x^±) = θ(αx)·θ(α/x) as its two Theta factors."""
    return (Theta(al * _X), Theta(al * _Xi))


def _pmc(u, v):
    """The constant theta ±-pair θ(u·v^±) = θ(uv)·θ(u/v) as its two Theta factors."""
    return (Theta(u * v), Theta(u / v))


# ── the GENUINE elliptic theta telescoper (the rc63 keystone) ──────────────────
#
# Built from the Weierstrass three-term relation with c = qb (which makes
# θ(cx^±) = θ(b·(qx)^±) the q-shift of θ(bx^±) — the indefinite-summation engine):
#   R(x) = θ(bx^±)·θ(ac^±) / [ (a/c)·θ(cx^±)·θ(ba^±) ]            (c = qb)
#   r    = (R(x) + 1) / R(qx)
# R+1 = θ(ax^±)θ(bc^±)/D is a SINGLE theta product (by the three-term relation), so r
# is a single theta-quotient (a genuine theta-bearing term-ratio, NOT the geometric
# core). The elliptic Gosper equation R(qx)·r − R = 1 then holds IDENTICALLY.
def _genuine_keystone():
    c = _Q * _B
    Rc = R(prefactor=(_A.inv() * c), num=_pmx(_B) + _pmc(_A, c),
           den=_pmx(c) + _pmc(_B, _A))
    n_plus_d = R(num=_pmx(_A) + _pmc(_B, c))
    d_q = R(prefactor=(_A / c), num=_pmx(c) + _pmc(_B, _A)).qshift()
    n_q = R(num=_pmx(_B) + _pmc(_A, c)).qshift()
    d_x = R(prefactor=(_A / c), num=_pmx(c) + _pmc(_B, _A))
    r = n_plus_d * d_q * (d_x * n_q).inv()
    return r, Rc


# ── KEYSTONE 1 (rc61, kept green): the geometric core → a certificate end-to-end ─
def test_elliptic_geometric_constant_ratio_is_summable():
    """The elliptic-geometric core: a CONSTANT term ratio r = z = 3/2 is elliptically
    balanced AND elliptic-Gosper-summable, with the closed-form certificate
    R = 1/(z − 1) = 2 (then R(qx)·r − R = R·(z − 1) = 1, exact at any truncation). The
    elliptic analogue of the ordinary / q-geometric Σ zⁿ closed form — found
    end-to-end by elliptic_gosper, and certified by the rc63 ThetaSum.is_zero."""
    r = R.monomial(M.scalar(Q(3, 2)))
    assert _is_balanced(r) is True                     # in the row
    res = elliptic_gosper(r)
    assert res is not None                             # summable → a certificate
    cert = res["certificate"]
    # the verified certificate satisfies the elliptic Gosper equation EXACTLY:
    assert _verifies_gosper_equation(cert, r) is True
    lhs = cert.qshift() * r
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
        assert cert.qshift() * r != r                  # nontrivial
        lhs = cert.qshift() * r
        assert lhs.eval_trunc(_VALS, 8) - cert.eval_trunc(_VALS, 8) == Q(1, 1)
        from srmech.amsc.cyclic import gcd
        g = gcd(abs(rd), abs(rn)) if rn else abs(rd)
        assert res["prefactor"]["coeff"] in ((rn // g, rd // g),
                                             (-(rn // g), -(rd // g)))


# ── KEYSTONE 2 (the rc63 WIN): a GENUINE theta telescoper certified by ThetaSum ──
def test_genuine_theta_telescoper_is_certified_exactly_by_thetasum():
    """A GENUINE elliptic theta telescoper — a term whose r(x) is a NONTRIVIAL
    theta-quotient (NOT the geometric core) — has its Gosper certificate R verified
    EXACTLY by ThetaSum.is_zero (the rc63 capability). The pair is built from the
    Weierstrass three-term relation with c = qb; the elliptic Gosper equation
    R(qx)·r − R = 1 holds identically."""
    r, cert = _genuine_keystone()
    # the term-ratio is genuinely THETA-BEARING (not a constant / geometric core):
    assert len(r.num) + len(r.den) >= 4
    assert r.num or r.den
    # it is in the row (elliptically balanced):
    assert _is_balanced(r) is True
    # the certificate is non-degenerate (no θ(1) = 0 factor):
    assert _has_zero_theta(cert) is False
    # THE rc63 WIN: the elliptic Gosper equation is certified EXACTLY by ThetaSum.is_zero:
    assert _verifies_gosper_equation(cert, r) is True


def test_rc61_eval_oracle_could_not_certify_the_genuine_keystone():
    """The rc61 verifier accepted a certificate ONLY when the EllRatio.eval_trunc gap
    to 1 was EXACTLY 0 — which a genuine theta telescoper's residual NEVER is at finite
    depth (it only CONVERGES). So rc61 would have returned None on the rc63 keystone;
    the gap is nonzero (and shrinks with depth), exactly the no-hallucination boundary
    rc63's exact ThetaSum.is_zero crosses. (This is the rc63 win made explicit.)"""
    r, cert = _genuine_keystone()
    lhs = cert.qshift() * r
    gap12 = (lhs.eval_trunc(_GVALS, 12) - cert.eval_trunc(_GVALS, 12)) - Q(1, 1)
    gap30 = (lhs.eval_trunc(_GVALS, 30) - cert.eval_trunc(_GVALS, 30)) - Q(1, 1)
    # the rc61 oracle gap is NOT exactly 0 at finite depth → rc61 returns None:
    assert gap12 != Q(0, 1)
    assert gap30 != Q(0, 1)
    # but it CONVERGES toward 0 (the very reason the decision must be symbolic, not eval):
    assert abs(float(gap30)) < abs(float(gap12))
    # the EXACT (rc63) decision says the residual is identically zero:
    assert _verifies_gosper_equation(cert, r) is True


def test_genuine_keystone_gosper_equation_holds_numerically():
    """An independent numeric cross-check (the convergence ORACLE, NOT the decision):
    the truncated R(qx)·r − R CONVERGES to 1 at several rational sample points (|p| <
    1) as the depth grows — confirming the symbolic ThetaSum.is_zero certificate is a
    true antidifference, not a reduction artefact. (The truncated modified-theta
    products only converge; the residual is EXACTLY 1 only in the limit — which is
    precisely why the rc63 DECISION is the symbolic ThetaSum.is_zero, never this
    eval.)"""
    r, cert = _genuine_keystone()
    lhs = cert.qshift() * r
    for vals in (_GVALS,
                 {"q": Q(6, 5), "p": Q(1, 14), "x": Q(7, 9), "a": Q(3, 8), "b": Q(5, 6)},
                 {"q": Q(8, 5), "p": Q(1, 20), "x": Q(4, 7), "a": Q(5, 9), "b": Q(2, 7)}):
        gap_lo = lhs.eval_trunc(vals, 6) - cert.eval_trunc(vals, 6) - Q(1, 1)
        gap_hi = lhs.eval_trunc(vals, 14) - cert.eval_trunc(vals, 14) - Q(1, 1)
        # converges to 0 (R(qx)·r − R → 1): the deeper truncation is strictly closer.
        assert abs(float(gap_hi)) < abs(float(gap_lo))
        assert abs(float(gap_hi)) < 1e-6


# ── KEYSTONE 3: a genuine NON-summable theta term → honest None ────────────────
def test_balanced_but_not_summable_is_none():
    """A balanced (elliptic, in-row) theta term with NO elliptic-hypergeometric
    antidifference → honest None. θ(ax)θ(bx)/[θ(x)θ(abx)] is balanced but not
    Gosper-summable (no theta telescoper for it)."""
    bal = R(num=(_th(_A * _X), _th(_B * _X)), den=(_th(_X), _th(_A * _B * _X)))
    assert _is_balanced(bal) is True                   # in the row
    assert elliptic_gosper(bal) is None                # but not summable


def test_genuine_theta_geometric_term_is_not_summable():
    """A genuine theta-bearing 'theta-geometric' term ratio q²·θ(a(qx)^±)/θ(ax^±) is
    balanced (in the row) but NOT summable (the theta-Pochhammer product grows, no
    antidifference) → honest None. The rc63 exact verifier certifies no candidate."""
    r = R(prefactor=M(Q(1, 1), {"q": 2}),
          num=(Theta(_A * _Q * _X), Theta(_A / (_Q * _X))), den=_pmx(_A))
    assert _is_balanced(r) is True                     # in the row, theta-bearing
    assert (r.num or r.den)
    assert elliptic_gosper(r) is None                  # genuinely non-summable


def test_constant_one_has_no_finite_certificate():
    """r = 1 is balanced but z = 1 has no finite certificate R = 1/(z − 1) → None."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(1, 1)))) is None


# ── KEYSTONE 4: a non-elliptic (unbalanced) term → None (out of the row) ───────
def test_unbalanced_term_is_out_of_row():
    """θ(ax)/θ(x) is NOT elliptically balanced — its x↦p·x multiplier is the PARAMETER
    power a⁻¹ (not a pure q/p-power), so it is out of the row → None. The rc63
    balancing gate (_is_balanced) keeps it out exactly as the rc61 strict is_elliptic
    did (its strict is_elliptic is also False)."""
    unbal = R(num=(_th(_A * _X),), den=(_th(_X),))
    assert unbal.is_elliptic() is False                # strict (rc61) gate: out
    assert _is_balanced(unbal) is False                # balancing (rc63) gate: out
    assert elliptic_gosper(unbal) is None


def test_zero_ratio_is_none():
    """The zero term ratio has no nonzero elliptic-hypergeometric closed form."""
    assert elliptic_gosper(R.monomial(M.scalar(Q(0, 1)))) is None


# ── the balancing gate widens the strict is_elliptic without breaking it ───────
def test_balancing_gate_admits_quasi_elliptic_but_keeps_strict_cases():
    """The rc63 row gate _is_balanced is invariance under x↦p·x UP TO A CONSTANT
    q/p-power (the elliptic character). It STRICTLY widens the rc61 is_elliptic
    (multiplier-1) gate: a strict-elliptic ratio still passes, AND a genuine
    mixed-argument term-ratio (whose multiplier is a constant q-power) now passes —
    the latter is exactly the genuine theta telescoper rc61 gated out."""
    # a strictly-elliptic balanced ratio still passes the balancing gate:
    strict = R(num=(_th(_A * _X), _th(_B * _X)), den=(_th(_X), _th(_A * _B * _X)))
    assert strict.is_elliptic() is True and _is_balanced(strict) is True
    # the genuine theta keystone passes the balancing gate (it is in the row):
    r, _cert = _genuine_keystone()
    assert _is_balanced(r) is True
    # a ratio whose period-shift multiplier carries a free PARAMETER is out of the row:
    assert _is_balanced(R(num=(_th(_A * _X),), den=(_th(_X),))) is False


# ── coercion: an EllMonomial / Theta lifts to the term-ratio EllRatio ─────────
def test_coerces_ellmonomial_and_scalar():
    """A bare EllMonomial scalar (z = 5/2) lifts to the constant-ratio EllRatio and is
    certified the same as the explicit EllRatio.monomial form."""
    res_m = elliptic_gosper(M.scalar(Q(5, 2)))
    res_r = elliptic_gosper(R.monomial(M.scalar(Q(5, 2))))
    assert res_m is not None and res_r is not None
    assert res_m["prefactor"] == res_r["prefactor"]


def test_certificate_roundtrips_to_ellratio():
    """The returned operand dict rebuilds the SAME EllRatio (an exact re-check handle
    for the caller) — for the geometric-core certificate."""
    r = R.monomial(M.scalar(Q(9, 5)))
    res = elliptic_gosper(r)
    assert res is not None
    cert = res["certificate"]
    rebuilt = R.monomial(M(Q(*res["prefactor"]["coeff"]), res["prefactor"]["exps"]))
    assert rebuilt == cert


# ── degenerate certificate rejection (θ(1) = 0 guard) ─────────────────────────
def test_degenerate_theta_one_certificate_rejected():
    """A certificate carrying a θ(1; p) = 0 factor (a collapsed theta argument) is
    degenerate and rejected — the exact ThetaSum.is_zero reduction can spuriously
    'verify' such a cert symbolically, so the θ(1) guard filters it before the
    residual check."""
    degen = R(num=(_th(_A * _X),), den=(_th(M.one()),))   # carries θ(1) = 0
    assert _has_zero_theta(degen) is True
    # the verifier rejects it regardless of any symbolic reduction:
    assert _verifies_gosper_equation(degen, R.monomial(M.scalar(Q(3, 2)))) is False


# ── discipline: no numpy / no math / no abs() in the engine source ────────────
def test_elliptic_gosper_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_gosper.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None       # no bare abs() CALL


# ── the ToolEntry is registered + invocable (tools.total stays 336) ───────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_gosper.elliptic_gosper" in names


def test_tools_total_stays_336():
    """rc63 UPGRADES the existing elliptic_gosper ToolEntry in place — NOT a new
    ToolEntry, so describe()['tools']['total'] stays 336."""
    from srmech import introspect
    assert introspect.describe()["tools"]["total"] == 336
