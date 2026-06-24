"""rc62 — elliptic_zeilberger, the SECOND engine op of the ELLIPTIC F929 reduction row.

The ELLIPTIC analog of Zeilberger's creative telescoping over the modified-theta
``EllRatio`` carrier (Frenkel & Turaev, "Elliptic solutions of the Yang–Baxter equation
and modular hypergeometric functions," in *The Arnold–Gelfand Mathematical Seminars*,
eds. Arnold/Gelfand/Retakh/Smirnov, Birkhäuser Boston 1997, pp. 171–204; keystone the
terminating very-well-poised Frenkel–Turaev ₁₀E₉ sum = the elliptic Jackson ₈W₇ sum,
S.O. Warnaar, *Constr. Approx.* 18 (2002) 479–502, Cor. 2.2 / Eq. 2.11,
arXiv:math/0001006).

Numpy-free + math-free + abs()-free in the engine source. The recurrence + certificate
are PROOF objects: accepted ONLY when the creative-telescoping identity is verified
EXACTLY by the elliptic DEGREE BOUND (the carrier multiplicative collapse + exact-``ℚ``
``eval_trunc`` agreement on the theta-free residual at more than ``d`` sample points),
NEVER on a merely-converging residual (the rc61 no-hallucination standard). The keystone
cases:

  - the FT ₁₀E₉ closed-form n-recurrence (a ``k``-free-``r_n`` elliptic-geometric term):
    ``rₙ_den(x)·f(n+1) − rₙ_num(x)·f(n) = 0`` (certificate ``G ≡ 0``) → verified EXACTLY
    (residual ≡ 0, degree ``d = 0``, theta-free) at multiple exact-``ℚ`` sample points;
  - a genuine ``k``-dependent-``r_n`` creative telescoping (additive theta lattice) →
    honest ``None`` (out of the multiplicative carrier's exact reach);
  - a non-summable / degenerate input → ``None``.
"""

import io
import os
import re
import tokenize

from srmech.amsc.ellbase import EllMonomial as M, Theta, EllRatio as R
from srmech.amsc.elliptic_zeilberger import elliptic_zeilberger
from srmech.amsc.q import Q

_X, _Y = M.symbol("x"), M.symbol("y")
_A, _B, _C, _D = M.symbol("a"), M.symbol("b"), M.symbol("c"), M.symbol("d")

# the degree-bound exact-ℚ sample points (a theta-free residual evaluates exactly here).
_VALS = ({"q": Q(2, 1), "p": Q(1, 9), "x": Q(2, 3), "y": Q(3, 5), "a": Q(3, 5),
          "b": Q(4, 7), "c": Q(5, 8), "d": Q(2, 9)},
         {"q": Q(3, 1), "p": Q(1, 16), "x": Q(3, 4), "y": Q(4, 9), "a": Q(2, 5),
          "b": Q(5, 7), "c": Q(3, 8), "d": Q(4, 9)})

_NEG1 = R.monomial(M.scalar(Q(-1, 1)))


def _th(m):
    return Theta(m)


def _verify_order1(rn, res):
    """The EXACT degree-bound check of the returned order-1 recurrence: with the
    certificate ``G ≡ 0`` the identity divides (by ``F``) to ``a_0 + a_1·r_n = 0``, i.e.
    ``a_1·r_n == −a_0`` as carrier objects (exact multiplicative theta collapse) AND the
    exact-``ℚ`` evals of the two sides AGREE at every sample (degree ``d = 0``,
    theta-free residual — exact, not converging). State: d = 0 surviving theta factors,
    checked at len(_VALS) > d distinct exact-ℚ points."""
    a0, a1 = res["coeffs"][0], res["coeffs"][1]
    lhs = a1 * rn                       # a_1·r_n
    rhs = a0 * _NEG1                     # −a_0
    assert lhs == rhs                   # exact carrier identity (the residual is ≡ 0)
    for vals in _VALS:                  # degree-bound: agree at > d = 0 points, EXACT
        assert lhs.eval_trunc(vals, 12) - rhs.eval_trunc(vals, 12) == Q(0, 1)
    assert res["certificate"].is_zero   # G ≡ 0 for the k-free order-1 case


# ── KEYSTONE 1: the FT ₁₀E₉ closed-form n-recurrence (k-free r_n) ─────────────
def test_ft_10e9_closed_form_n_recurrence_is_certifiable():
    """The Frenkel–Turaev ₁₀E₉ sum's closed form is a ratio of theta-Pochhammers in
    ``n``; that closed form satisfies the EXACT order-1 elliptic recurrence
    ``θ(d·x)·f(n+1) − θ(c·x)·f(n) = 0`` where ``r_n = θ(c·x)/θ(d·x)`` (k-free). The
    op finds it and the recurrence VERIFIES EXACTLY by the degree bound (residual ≡ 0,
    d = 0, checked at > 0 distinct exact-ℚ points)."""
    rn = R(num=(_th(_C * _X),), den=(_th(_D * _X),))         # r_n = θ(c x)/θ(d x), k-free
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))              # r_k elliptic in (x,y)
    res = elliptic_zeilberger(rn, rk)
    assert res is not None
    assert res["order"] == 1
    _verify_order1(rn, res)


def test_scalar_k_free_elliptic_geometric_order1():
    """The simplest k-free elliptic-geometric term: r_n = z = 2/3 (a pure scalar in n,
    independent of k). f(n) = zⁿ·C satisfies a_0 = −z, a_1 = 1, certificate G ≡ 0 —
    verified EXACTLY (the native C scope + the parity oracle)."""
    rn = R.monomial(M.scalar(Q(2, 3)))
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    res = elliptic_zeilberger(rn, rk)
    assert res is not None and res["order"] == 1
    assert res["coeffs"][0].prefactor.coeff == Q(-2, 3)     # a_0 = −z = −2/3
    assert res["coeffs"][1].is_unit                          # a_1 = 1
    _verify_order1(rn, res)


def test_scalar_several_constants_exact():
    """Several scalar k-free r_n = z → a_0 = −z, a_1 = 1, each verified EXACTLY."""
    for zn, zd in [(5, 4), (7, 3), (2, 5), (9, 7)]:
        rn = R.monomial(M.scalar(Q(zn, zd)))
        rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
        res = elliptic_zeilberger(rn, rk)
        assert res is not None and res["order"] == 1
        assert res["coeffs"][0].prefactor.coeff == Q(-zn, zd)
        _verify_order1(rn, res)


def test_theta_quotient_k_free_r_n_order1():
    """A theta-quotient k-free r_n = θ(c x)·θ(a x)/[θ(d x)·θ(b x)] (still k-free) → the
    exact order-1 recurrence a_1 = rₙ_den, a_0 = −rₙ_num, verified EXACTLY (the pure
    path; the native C peer declines a theta-bearing r_n)."""
    rn = R(num=(_th(_C * _X), _th(_A * _X)), den=(_th(_D * _X), _th(_B * _X)))
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    res = elliptic_zeilberger(rn, rk)
    assert res is not None and res["order"] == 1
    _verify_order1(rn, res)


def test_constant_r_n_one_is_wz_recurrence():
    """r_n ≡ 1 (f constant in n) → the WZ recurrence f(n+1) − f(n) = 0 (a_0 = −1,
    a_1 = +1), certificate G ≡ 0, verified EXACTLY."""
    rn = R.one()
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    res = elliptic_zeilberger(rn, rk)
    assert res is not None and res["order"] == 1
    assert res["coeffs"][0].prefactor.coeff == Q(-1, 1)
    assert res["coeffs"][1].is_unit
    _verify_order1(rn, res)


# ── KEYSTONE 2: the genuine k-dependent creative telescoping → honest None ────
def test_k_dependent_r_n_is_honest_none():
    """A genuine k-dependent r_n = θ(c·x·y)/θ(d·x) (the certificate G would be a
    nontrivial theta-quotient; the residual carries surviving theta factors needing the
    ADDITIVE theta addition formula) lies OUTSIDE the multiplicative EllRatio carrier's
    exact reach → honest None, never a numerically-witnessed recurrence (the rc61
    no-hallucination standard; the same boundary elliptic_gosper hits)."""
    rn = R(num=(_th(_C * _X * _Y),), den=(_th(_D * _X),))
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    assert elliptic_zeilberger(rn, rk) is None


def test_zero_k_ratio_is_none():
    """A zero k-term-ratio (F(n,k+1) ≡ 0) is not a proper summand → None."""
    rn = R.monomial(M.scalar(Q(2, 3)))
    assert elliptic_zeilberger(rn, R.monomial(M.scalar(Q(0, 1)))) is None


def test_max_order_zero_declines():
    """max_order = 0 admits no order-1 recurrence → None (the order-1 k-free case needs
    max_order ≥ 1)."""
    rn = R.monomial(M.scalar(Q(2, 3)))
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    assert elliptic_zeilberger(rn, rk, max_order=0) is None


# ── a perturbed (wrong) recurrence would NOT verify (the exactness guard) ──────
def test_wrong_recurrence_fails_exact_verify():
    """Sanity on the exact verifier: a WRONG a_0 (θ(a x) instead of −θ(c x)) does NOT
    satisfy a_1·r_n == −a_0 — so the engine would reject it (it only emits the verified
    one). Confirms the verifier is exact, not a numerical convergence acceptance."""
    rn = R(num=(_th(_C * _X),), den=(_th(_D * _X),))
    a1 = R(num=(_th(_D * _X),))                              # the correct a_1 = rₙ_den
    wrong_a0 = R(M.scalar(Q(-1, 1)), num=(_th(_A * _X),))    # WRONG: −θ(a x), not −θ(c x)
    assert (a1 * rn) != (wrong_a0 * _NEG1)                   # exact carrier inequality


# ── coercion: an EllMonomial / Theta lifts to the term-ratio EllRatio ─────────
def test_coerces_ellmonomial_scalar():
    """A bare EllMonomial scalar (z = 5/2) lifts to the scalar k-free term-ratio and is
    certified the same as the explicit EllRatio.monomial form."""
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    res_m = elliptic_zeilberger(M.scalar(Q(5, 2)), rk)
    res_r = elliptic_zeilberger(R.monomial(M.scalar(Q(5, 2))), rk)
    assert res_m is not None and res_r is not None
    assert res_m["coeffs"][0].prefactor == res_r["coeffs"][0].prefactor


def test_coeff_operands_rebuild_to_ratio():
    """The returned coeff_operands rebuild the SAME EllRatio coefficients (an exact
    re-check handle for the caller)."""
    rn = R.monomial(M.scalar(Q(9, 5)))
    rk = R(num=(_th(_A * _Y),), den=(_th(_Y),))
    res = elliptic_zeilberger(rn, rk)
    assert res is not None
    op = res["coeff_operands"][0]
    rebuilt = R.monomial(M(Q(*op["prefactor"]["coeff"]), op["prefactor"]["exps"]))
    assert rebuilt == res["coeffs"][0]


# ── discipline: no numpy / no math / no abs() in the engine source ────────────
def test_elliptic_zeilberger_source_is_numpy_math_abs_free():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "srmech", "amsc", "elliptic_zeilberger.py")
    with tokenize.open(src) as fh:
        text = fh.read()
    assert "import numpy" not in text
    assert "import math" not in text
    assert re.search(r"abs\([^)]", text) is None          # no bare abs() CALL


# ── the ToolEntry is registered + invocable ───────────────────────────────────
def test_tool_entry_registered():
    from srmech.amsc import tool_schema
    names = {t.name for t in tool_schema.get_tool_schema().tools}
    assert "srmech.amsc.elliptic_zeilberger.elliptic_zeilberger" in names
