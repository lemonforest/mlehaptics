"""0.9.0rc14 — the EXACT-complex carrier ``Qi`` honours the ``numbers.Complex``
ABC it advertises, and its sign sector IS a Klein-4 quadrant.

The carrier-conformance ratchet for ``Qi`` (the exact Gaussian-rational), the
exact peer of the rc11 ``Complex128`` float-complex ratchet. It pins, at the
protocol level, that ``Qi``:

  * IS a registered :class:`numbers.Complex` (hence Number) but NOT a
    :class:`numbers.Real`/``Rational`` (it is genuinely complex);
  * matches a stdlib **Fraction-pair** oracle — the exact Gaussian-rational
    reference (not numpy / not the lossy builtin ``complex``) — operation for
    operation across a sign/zero/integer grid for ``+`` / ``-`` / ``*`` / ``/``;
  * keeps chirality as a **Klein-4 quadrant**: ``quadrant()`` ∈ ``KLEIN4_STATES``,
    ``conjugate()`` XORs the imaginary bit, and ``from_quadrant_magnitudes``
    round-trips exactly;
  * has an ``abs`` that lands on a :class:`numbers.Real` (a ``Q``), exact when
    the squared modulus is a perfect rational square;
  * integer ``**`` is EXACT, a non-integer exponent collapses to the float
    boundary.

Numpy-free by construction (the oracle is stdlib ``fractions``); asserted
numpy-absent so it PASSES (not skips) on the numpy-absent matrix.
"""

import importlib.util
import numbers
from fractions import Fraction

import pytest

from srmech.amsc.hdc import KLEIN4_STATES
from srmech.amsc.q import Q
from srmech.amsc.qi import Qi


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this carrier-conformance ratchet must run on the numpy-ABSENT matrix")


# (re_num, re_den, im_num, im_den) over signs / zero / integers.
_GRID = [(3, 4, 1, 2), (-3, 4, 1, 2), (3, 4, -1, 2), (-3, 4, -1, 2),
         (0, 1, 1, 1), (1, 1, 0, 1), (5, 2, 7, 3), (-100, 7, 9, 4),
         (2, 1, -3, 1), (0, 1, 0, 1)]
_NONZERO = [(1, 2, 1, 3), (3, 4, -1, 2), (-2, 1, 5, 1), (1, 1, 1, 1)]


def _qi(t):
    return Qi(Q(t[0], t[1]), Q(t[2], t[3]))


def _fp(t):
    return (Fraction(t[0], t[1]), Fraction(t[2], t[3]))


def _eq(z: Qi, fp):
    return (Fraction(z.real.numerator, z.real.denominator) == fp[0]
            and Fraction(z.imag.numerator, z.imag.denominator) == fp[1])


def test_Qi_is_a_registered_numbers_complex():
    z = Qi(Q(3, 4), Q(-1, 2))
    assert isinstance(z, numbers.Complex)
    assert isinstance(z, numbers.Number)
    assert not isinstance(z, numbers.Real)          # genuinely complex
    assert not isinstance(z, numbers.Rational)


@pytest.mark.parametrize("t", _GRID)
def test_Qi_add_sub_mul_match_fraction_pair_oracle(t):
    z, fz = _qi(t), _fp(t)
    other = (1, 3, -2, 5)
    o, fo = _qi(other), _fp(other)
    assert _eq(z + o, (fz[0] + fo[0], fz[1] + fo[1]))
    assert _eq(z - o, (fz[0] - fo[0], fz[1] - fo[1]))
    # (a+bi)(c+di) = (ac-bd) + (ad+bc)i
    assert _eq(z * o, (fz[0] * fo[0] - fz[1] * fo[1],
                       fz[0] * fo[1] + fz[1] * fo[0]))


@pytest.mark.parametrize("t", _GRID)
@pytest.mark.parametrize("d", _NONZERO)
def test_Qi_division_matches_oracle_and_roundtrips(t, d):
    z, fz = _qi(t), _fp(t)
    o, fo = _qi(d), _fp(d)
    denom = fo[0] * fo[0] + fo[1] * fo[1]            # |o|^2, nonzero
    quo = ((fz[0] * fo[0] + fz[1] * fo[1]) / denom,
           (fz[1] * fo[0] - fz[0] * fo[1]) / denom)
    assert _eq(z / o, quo)
    assert (z / o) * o == z                          # exact round-trip


def test_Qi_conjugate_norm_abs():
    z = Qi(3, 4)
    assert z.conjugate() == Qi(3, -4)                # Class-K im sign-flip
    assert z.norm_sq() == 25                          # exact Q
    assert abs(z) == 5 and isinstance(abs(z), numbers.Real)   # perfect square
    # non-square modulus stays a rational boundary (Q), float matches libm
    w = Qi(1, 1)
    assert isinstance(abs(w), Q)
    assert abs(float(abs(w)) - 2 ** 0.5) < 1e-12


def test_Qi_quadrant_is_a_klein4_element():
    cases = {(3, 4): 0, (-3, 4): 1, (3, -4): 2, (-3, -4): 3,
             (0, 0): 0, (0, -5): 2, (-5, 0): 1}
    for (re, im), q in cases.items():
        z = Qi(re, im)
        assert z.quadrant() in KLEIN4_STATES and z.quadrant() == q
        # conjugation XORs the imaginary bit — but only when im ≠ 0 (conjugating
        # a real is a no-op, its im-bit is already 0, so the quadrant is fixed).
        expect = (q ^ 2) if im != 0 else q
        assert z.conjugate().quadrant() == expect
        rt = Qi.from_quadrant_magnitudes(z.quadrant(), abs(z.real), abs(z.imag))
        assert rt == z                               # quadrant ⊗ magnitude round-trip


def test_Qi_power_integer_exact_else_boundary():
    assert Qi(0, 1) ** 2 == Qi(-1, 0)                # i^2 = -1, exact
    assert Qi(1, 1) ** 4 == Qi(-4, 0)                # (1+i)^4 = -4, exact
    assert Qi(0, 1) ** Q(2, 1) == Qi(-1, 0)          # integer-valued Q exponent
    assert Qi(2, 0) ** -2 == Qi(Q(1, 4), 0)          # negative integer → reciprocal
    p = Qi(1, 1) ** 0.5                               # non-integer → float boundary
    assert isinstance(p, complex)
    assert abs(p - (1 + 1j) ** 0.5) < 1e-12


def test_Qi_real_value_interops_with_q_and_float():
    z = Qi(Q(3, 4), 0)
    assert z == 0.75 and z == Q(3, 4)
    assert complex(z) == 0.75 + 0j
    assert hash(z) == hash(Q(3, 4)) == hash(0.75)    # data-model hash invariant
