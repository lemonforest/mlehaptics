"""0.9.0rc22 — the exact ℚ(α) number-field carrier ``Qalg`` (rotation-last rc-C).

``Qalg`` generalises ``Qi`` from the ONE field ℚ[x]/(x²+1) (Gaussian rationals)
to ℚ[x]/(m(x)) for any monic irreducible ``m``. This ratchet proves:

1. **Qi ≡ Qalg over x²+1 (the headline).** For several Gaussian rationals,
   ``+``/``−``/``×``/``inverse``/``/``/``**`` over ``Qalg(m=(1,0,1), …)`` give
   coords that match the corresponding ``Qi``'s ``(re, im)`` EXACTLY; and
   ``Qalg(...).to_complex()`` with ``root=1j`` equals ``complex(Qi(...))``.
2. **Field axioms** on the cubic ``m = x³−2`` (α = ∛2): associativity +
   distributivity of ``+``/``×``; ``β·β.inverse() == one``; ``α**3 == 2``.
3. **Real quadratic** ``m = x²−2`` (α = √2, ``root=2**0.5``): ``α.to_float()`` ≈
   1.4142…, ``(α*α).to_float()`` ≈ 2.0, and ``(1+α)`` evaluates correctly.
4. **The generator satisfies its own m** (``Σ m[i]·αⁱ`` reduces to 0).
5. Inverting 0 raises ``ZeroDivisionError``; mismatched-``m`` raises
   ``ValueError``; determinism (same ops twice → identical coords).

The whole module is numpy-free (it runs on the numpy-ABSENT matrix).
"""

from __future__ import annotations

import importlib.util
from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.qalg import Qalg
from srmech.amsc.qi import Qi


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this Qalg carrier ratchet must run on the numpy-ABSENT matrix")


# ── m = x²+1 (the ℂ rung) ───────────────────────────────────────────────────
_M_I = (1, 0, 1)                                   # x²+1, low→high, monic

# (re_num, re_den, im_num, im_den) over signs / zero / integers / fractions.
_GRID = [(3, 4, 1, 2), (-3, 4, 1, 2), (3, 4, -1, 2), (-3, 4, -1, 2),
         (1, 1, 0, 1), (5, 2, 7, 3), (-100, 7, 9, 4), (2, 1, -3, 1)]
_OTHER = (1, 3, -2, 5)


def _qi(t):
    return Qi(Q(t[0], t[1]), Q(t[2], t[3]))


def _qalg_i(t, root=None):
    """The ``Qalg`` over x²+1 whose coords are the (re, im) of ``Qi(t)``."""
    return Qalg(_M_I, (Q(t[0], t[1]), Q(t[2], t[3])), root=root)


def _coords_eq_qi(z_alg: Qalg, z_qi: Qi) -> bool:
    """``Qalg`` coords == ``Qi``'s (re, im), exactly."""
    return (z_alg.coords[0] == z_qi.real and z_alg.coords[1] == z_qi.imag)


# ── 1. Qi ≡ Qalg over x²+1 — the headline equivalence ───────────────────────
@pytest.mark.parametrize("t", _GRID)
def test_qalg_add_sub_match_qi(t):
    za, oa = _qalg_i(t), _qalg_i(_OTHER)
    zq, oq = _qi(t), _qi(_OTHER)
    assert _coords_eq_qi(za + oa, zq + oq)
    assert _coords_eq_qi(za - oa, zq - oq)
    assert _coords_eq_qi(-za, -zq)


@pytest.mark.parametrize("t", _GRID)
def test_qalg_mul_matches_qi(t):
    """The core: convolve-then-reduce-mod-(x²+1) IS the Gaussian product
    ``(ac−bd)+(ad+bc)i``."""
    za, oa = _qalg_i(t), _qalg_i(_OTHER)
    zq, oq = _qi(t), _qi(_OTHER)
    assert _coords_eq_qi(za * oa, zq * oq)


@pytest.mark.parametrize("t", _GRID)
def test_qalg_inverse_and_div_match_qi(t):
    if t == (1, 1, 0, 1):
        # 1 is fine; skip nothing — but ensure we never invert exact 0 here.
        pass
    za, oa = _qalg_i(t), _qalg_i(_OTHER)
    zq, oq = _qi(t), _qi(_OTHER)
    # inverse of the non-zero `other`
    assert _coords_eq_qi(oa.inverse(), Qi(Q(1, 1)) / oq)
    # division
    assert _coords_eq_qi(za / oa, zq / oq)


@pytest.mark.parametrize("t", _GRID)
@pytest.mark.parametrize("k", [0, 1, 2, 3, -1, -2])
def test_qalg_pow_matches_qi(t, k):
    if k < 0 and t == (1, 1, 0, 1):
        zq = _qi(t)
    za, zq = _qalg_i(t), _qi(t)
    if k < 0 and not bool(za):
        with pytest.raises(ZeroDivisionError):
            za ** k
        return
    assert _coords_eq_qi(za ** k, zq ** k)


@pytest.mark.parametrize("t", _GRID)
def test_qalg_to_complex_at_root_1j_equals_complex_qi(t):
    """The terminal projection: Horner-eval at ``root=1j`` == ``complex(Qi)``."""
    za = _qalg_i(t, root=1j)
    zq = _qi(t)
    assert za.to_complex() == complex(zq)


# ── 2. field axioms on the cubic x³−2 (α = ∛2) ──────────────────────────────
_M_CBRT2 = (-2, 0, 0, 1)                            # x³−2, monic, low→high


def _qalg_c(c0, c1, c2):
    return Qalg(_M_CBRT2, (Q(*c0), Q(*c1), Q(*c2)))


_ELEMS = [
    _qalg_c((1, 2), (3, 1), (-1, 5)),
    _qalg_c((2, 3), (-7, 4), (5, 2)),
    _qalg_c((-3, 1), (1, 6), (4, 1)),
]


def test_cubic_addition_is_associative():
    a, b, c = _ELEMS
    assert (a + b) + c == a + (b + c)


def test_cubic_multiplication_is_associative():
    a, b, c = _ELEMS
    assert (a * b) * c == a * (b * c)


def test_cubic_distributivity():
    a, b, c = _ELEMS
    assert a * (b + c) == a * b + a * c


def test_cubic_inverse_round_trip():
    for beta in _ELEMS:
        one = beta.one()
        assert beta * beta.inverse() == one
        assert beta.inverse() * beta == one


def test_cubic_alpha_cubed_is_two():
    """α³ = 2 in ℚ(∛2) — the defining relation of x³−2."""
    alpha = Qalg.alpha(_M_CBRT2)
    assert alpha ** 3 == Qalg.rational(2, _M_CBRT2)


# ── 3. real quadratic x²−2 (α = √2, root = 2**0.5) ──────────────────────────
_M_SQRT2 = (-2, 0, 1)                               # x²−2, monic


def test_real_quadratic_alpha_is_sqrt2():
    alpha = Qalg.alpha(_M_SQRT2, root=2 ** 0.5)
    assert alpha.to_float() == pytest.approx(1.4142135623730951)


def test_real_quadratic_alpha_squared_is_two():
    alpha = Qalg.alpha(_M_SQRT2, root=2 ** 0.5)
    # exact: α² reduces to 2 (coords (2, 0)); the float projection is 2.0
    assert (alpha * alpha) == Qalg.rational(2, _M_SQRT2, root=2 ** 0.5)
    assert (alpha * alpha).to_float() == pytest.approx(2.0)


def test_real_quadratic_one_plus_alpha_evaluates():
    alpha = Qalg.alpha(_M_SQRT2, root=2 ** 0.5)
    elem = Qalg.rational(1, _M_SQRT2, root=2 ** 0.5) + alpha
    assert elem.to_float() == pytest.approx(1.0 + 1.4142135623730951)


def test_to_float_rejects_complex_root():
    z = Qalg.alpha(_M_I, root=1j)                    # x²+1 has a non-real root
    with pytest.raises(ValueError):
        z.to_float()


# ── 4. the generator satisfies its own minimal polynomial ───────────────────
@pytest.mark.parametrize("m", [_M_I, _M_SQRT2, _M_CBRT2, (-2, -1, 1)])
def test_generator_satisfies_m(m):
    """Building ``Σ m[i]·αⁱ`` in the field reduces to the field zero (the monic
    relation αⁿ = −Σ m[i]·αⁱ is exactly m(α) = 0)."""
    alpha = Qalg.alpha(m)
    acc = Qalg.rational(0, m)
    power = alpha.one()                              # α⁰
    for coeff in m:                                  # low→high, incl. leading 1
        acc = acc + power * coeff
        power = power * alpha
    assert not bool(acc)
    assert acc == Qalg.rational(0, m)


# ── 5. edge cases + determinism ─────────────────────────────────────────────
def test_inverting_zero_raises():
    zero = Qalg.rational(0, _M_CBRT2)
    with pytest.raises(ZeroDivisionError):
        zero.inverse()
    with pytest.raises(ZeroDivisionError):
        Qalg.alpha(_M_CBRT2) / zero


def test_mismatched_field_raises():
    a = Qalg.alpha(_M_SQRT2)
    b = Qalg.alpha(_M_CBRT2)
    with pytest.raises(ValueError):
        a + b
    with pytest.raises(ValueError):
        a * b
    with pytest.raises(ValueError):
        a - b


def test_determinism():
    a, b = _ELEMS[0], _ELEMS[1]
    r1 = ((a * b) + a.inverse()) ** 3
    r2 = ((a * b) + a.inverse()) ** 3
    assert r1.coords == r2.coords
    assert r1 == r2


def test_scalar_multiply_and_fraction_coords():
    alpha = Qalg.alpha(_M_SQRT2)
    assert (alpha * 3).coords == (Q(0, 1), Q(3, 1))
    assert (3 * alpha).coords == (Q(0, 1), Q(3, 1))
    assert (alpha * Fraction(1, 2)).coords == (Q(0, 1), Q(1, 2))
    # construct directly from a Fraction coord
    z = Qalg(_M_SQRT2, (Fraction(1, 3), 2))
    assert z.coords == (Q(1, 3), Q(2, 1))


def test_qi_equiv_full_chain_to_complex():
    """A compound exact chain over x²+1 matches the same chain in Qi, including
    the single terminal projection at root=1j."""
    t, o = (5, 2, 7, 3), _OTHER
    za, oa = _qalg_i(t, root=1j), _qalg_i(o, root=1j)
    zq, oq = _qi(t), _qi(o)
    res_alg = (za * oa - za) / (oa + Qalg.rational(1, _M_I, root=1j))
    res_qi = (zq * oq - zq) / (oq + Qi(Q(1, 1)))
    assert res_alg.coords[0] == res_qi.real
    assert res_alg.coords[1] == res_qi.imag
    assert res_alg.to_complex() == complex(res_qi)
