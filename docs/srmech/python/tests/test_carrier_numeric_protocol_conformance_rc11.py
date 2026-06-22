"""0.9.0rc11 — the scalar carriers honour the ``numbers`` ABCs they advertise.

The rc10 native-CI failure (``Fraction(Q)`` raised on the 3.10–3.13 matrix while
the local 3.14 dev box masked it — `[[feedback_fraction_of_q_carrier_needs_as_integer_ratio_route_pre_314]]`)
was a *conformance* gap: ``Q`` carried ``as_integer_ratio`` but was not a
registered :class:`numbers.Rational`, so the stdlib numeric protocols that depend
on the ABC membership (``Fraction(q)``, ``int(q)``, ``round(q)``, ``//``/``%``,
the ``real``/``imag``/``conjugate`` accessors) errored. This ratchet pins the
fix at the protocol level so the class of bug cannot recur silently:

  * ``Q`` IS a :class:`numbers.Rational` (hence Real / Complex / Number, NOT
    Integral) and matches :class:`fractions.Fraction` — the stdlib EXACT-rational
    oracle (not numpy/libm) — operation-for-operation across a grid;
  * ``Complex128`` IS a :class:`numbers.Complex` (hence Number, NOT Real) with a
    working power and an ``abs`` that lands on a :class:`numbers.Real` (a ``Q``).

It runs on EVERY CI Python (3.10–3.13 native cells + the pure-wheel cell), which
is the only place the cross-version gap surfaces — the local 3.14 dev box is too
new to fail. Numpy-free by construction (the oracle is stdlib ``fractions``);
asserted numpy-absent so it PASSES, not skips, on the numpy-absent matrix.
"""

import importlib.util
import math
import numbers
from fractions import Fraction

import pytest

from srmech.amsc.q import Q
from srmech.amsc.complex128 import Complex128


# A grid of reduced + unreduced (num, den), spanning signs / zero / integers.
_GRID = [(7, 2), (-7, 2), (5, 2), (1, 2), (-1, 2), (0, 1), (8, 4), (-9, 4),
         (100, 7), (-100, 7), (1, 3), (123, 1), (-123, 1), (2, 1)]
_DIVISORS = [(1, 1), (3, 2), (-2, 3), (5, 4)]


def test_Q_is_a_registered_numbers_rational():
    q = Q(3, 4)
    assert isinstance(q, numbers.Rational)
    assert isinstance(q, numbers.Real)
    assert isinstance(q, numbers.Complex)
    assert isinstance(q, numbers.Number)
    # A non-integer rational is NOT an Integral; an integer-valued one isn't either
    # (it is a Rational that happens to be integral) — same as Fraction.
    assert not isinstance(q, numbers.Integral)
    assert not isinstance(Q(8, 4), numbers.Integral)


@pytest.mark.parametrize("n,d", _GRID)
def test_Q_matches_fraction_oracle(n, d):
    """Every numbers.Real conversion / rounding op equals the Fraction oracle."""
    q = Q(n, d)
    f = Fraction(n, d)
    assert Fraction(q) == f                         # the rc10 gap, now structural
    assert int(q) == int(f)
    assert math.trunc(q) == math.trunc(f)
    assert math.floor(q) == math.floor(f)
    assert math.ceil(q) == math.ceil(f)
    assert round(q) == round(f)                     # ties-to-even
    assert complex(q) == complex(f)
    # numbers.Complex accessors for a real value
    assert q.real == q and q.imag == 0 and q.conjugate() == q
    for ndigits in (0, 1, 2, 3, -1, -2):
        rq = round(q, ndigits)
        assert isinstance(rq, Q)
        assert Fraction(rq.numerator, rq.denominator) == round(f, ndigits)


@pytest.mark.parametrize("n,d", _GRID)
@pytest.mark.parametrize("dn,dd", _DIVISORS)
def test_Q_floordiv_mod_divmod_match_fraction(n, d, dn, dd):
    q, o = Q(n, d), Q(dn, dd)
    f, fo = Fraction(n, d), Fraction(dn, dd)
    assert (q // o) == (f // fo)                     # int quotient
    rem = q % o
    assert isinstance(rem, Q)
    assert Fraction(rem.numerator, rem.denominator) == (f % fo)
    quo, r2 = divmod(q, o)
    fquo, fr2 = divmod(f, fo)
    assert quo == fquo
    assert Fraction(r2.numerator, r2.denominator) == fr2


def test_Q_power_exact_for_integer_float_boundary_otherwise():
    """Integer (incl. integer-valued ``Q``) exponent → exact ``Q``; a genuinely
    non-integer exponent → the float boundary, Fraction-consistent."""
    assert Q(3, 4) ** 2 == Q(9, 16)
    assert Q(3, 4) ** Q(2, 1) == Q(9, 16)
    assert Q(2, 1) ** -2 == Q(1, 4)
    assert 2 ** Q(3, 1) == Q(8, 1)                   # __rpow__ integer-self exact
    assert abs((Q(3, 4) ** 0.5) - 0.75 ** 0.5) < 1e-12
    assert abs((2 ** Q(1, 2)) - 2 ** 0.5) < 1e-12    # __rpow__ non-integer → float


def test_Q_round_half_to_even_explicitly():
    """Banker's rounding on the exact rational halves, matching Python/Fraction."""
    assert round(Q(7, 2)) == 4      # 3.5 → 4 (even)
    assert round(Q(5, 2)) == 2      # 2.5 → 2 (even)
    assert round(Q(1, 2)) == 0      # 0.5 → 0 (even)
    assert round(Q(-7, 2)) == -4    # -3.5 → -4 (even)
    assert round(Q(-5, 2)) == -2    # -2.5 → -2 (even)


def test_Complex128_is_a_registered_numbers_complex():
    c = Complex128(0.75, -0.5)
    assert isinstance(c, numbers.Complex)
    assert isinstance(c, numbers.Number)
    assert not isinstance(c, numbers.Real)          # genuinely complex
    # the full Complex surface is honoured (not just isinstance)
    assert complex(c) == 0.75 - 0.5j
    assert c.real == 0.75 and c.imag == -0.5
    assert complex(c.conjugate()) == 0.75 + 0.5j
    assert complex(c ** 2) == complex(c) ** 2
    assert isinstance(abs(c), numbers.Real)         # |z| is a Real (a Q)
