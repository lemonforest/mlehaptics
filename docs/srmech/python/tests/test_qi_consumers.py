"""0.9.0rc14 — the EXACT-complex carrier ``Qi`` has live **consumer surfaces**.

A carrier nobody consumes is an orphan. This proves ``Qi`` plugs into the three
surfaces a complex value belongs in — and that exactness is preserved where the
surface is exact, and collapses cleanly where the surface is float:

  1. **The Cayley–Dickson ℂ rung.** ``Qi`` IS the dim-2 (ℂ) element of the
     Cayley–Dickson ladder, so :func:`srmech.amsc.cascade.cayley_dickson.cd_mult`
     / ``cd_add`` / ``cd_conjugate`` / ``cd_norm_sq`` consume ``[z.real, z.imag]``
     (two ``Q``) and return **bit-identical** exact rationals to ``Qi``'s own
     ``*`` / ``+`` / ``conjugate`` / ``norm_sq``. The ℂ norm is multiplicative,
     so ``N(x·y) = N(x)·N(y)`` holds through the cascade (dim ≤ 8 is a division
     algebra). This is the srmech-native exact consumer — no float anywhere.

  2. **The generic ``numbers.Complex`` protocol.** Because ``Qi`` is a registered
     ``numbers.Complex`` that actually honours the protocol, generic numeric code
     consumes it: ``sum([...])`` (starts at ``int`` 0, rides ``__radd__``),
     ``complex(z)``, ``abs(z)`` (a ``numbers.Real``), ``z ** n``, and arithmetic
     mixing ``Qi`` with ``int`` / ``Q`` / dyadic ``float`` — each stays EXACT.

  3. **The ``Complex128`` float-boundary sink.** The two framework complex
     carriers interoperate: ``Qi`` (exact) combined with ``Complex128`` (float)
     yields a ``Complex128`` — exact-meets-float → float, the same direction as
     ``Fraction(1, 2) + 0.5 → 1.0``. ``Complex128`` is the documented sink for a
     value that leaves the rationals, so it consumes any ``numbers.Complex``.

Numpy-free by construction (oracle is stdlib ``fractions``); asserted
numpy-absent so it PASSES (not skips) on the numpy-absent matrix.
"""

import importlib.util
from fractions import Fraction

import pytest

from srmech.amsc.cascade.cayley_dickson import (
    cd_add,
    cd_conjugate,
    cd_mult,
    cd_norm_sq,
)
from srmech.amsc.complex128 import Complex128
from srmech.amsc.q import Q
from srmech.amsc.qi import Qi


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this Qi consumer-surface ratchet must run on the numpy-ABSENT matrix")


# (re_num, re_den, im_num, im_den) over signs / zero / integers / reduced fractions.
_GRID = [(3, 4, 1, 2), (-3, 4, 1, 2), (3, 4, -1, 2), (-3, 4, -1, 2),
         (0, 1, 1, 1), (1, 1, 0, 1), (5, 2, 7, 3), (-100, 7, 9, 4),
         (2, 1, -3, 1), (0, 1, 0, 1)]
_OTHER = (1, 3, -2, 5)


def _qi(t):
    return Qi(Q(t[0], t[1]), Q(t[2], t[3]))


def _frac_pair(z: Qi):
    """``Qi`` → an exact ``(Fraction, Fraction)`` for oracle comparison."""
    return (Fraction(z.real.numerator, z.real.denominator),
            Fraction(z.imag.numerator, z.imag.denominator))


def _cd_pair(elem):
    """A length-2 ``cd_*`` result tuple → a ``(Fraction, Fraction)`` pair."""
    return (Fraction(elem[0]), Fraction(elem[1]))


# ──────────────────────────────────────────────────────────────────────
# 1. The Cayley–Dickson ℂ rung — the exact srmech-native consumer.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("t", _GRID)
def test_cd_mult_consumes_qi_as_the_complex_rung(t):
    """``cd_mult`` over ``[z.real, z.imag]`` == ``Qi.__mul__`` — bit-exact, the
    dim-2 Cayley–Dickson product IS complex multiplication."""
    z, o = _qi(t), _qi(_OTHER)
    cd = cd_mult([z.real, z.imag], [o.real, o.imag])
    assert _cd_pair(cd) == _frac_pair(z * o)


@pytest.mark.parametrize("t", _GRID)
def test_cd_add_and_conjugate_consume_qi(t):
    z, o = _qi(t), _qi(_OTHER)
    assert _cd_pair(cd_add([z.real, z.imag], [o.real, o.imag])) == _frac_pair(z + o)
    assert _cd_pair(cd_conjugate([z.real, z.imag])) == _frac_pair(z.conjugate())


@pytest.mark.parametrize("t", _GRID)
def test_cd_norm_sq_consumes_qi(t):
    z = _qi(t)
    n = cd_norm_sq([z.real, z.imag])
    nq = z.norm_sq()
    assert Fraction(n) == Fraction(nq.numerator, nq.denominator)


@pytest.mark.parametrize("t", _GRID)
def test_complex_norm_is_multiplicative_through_the_rung(t):
    """``N(x·y) = N(x)·N(y)`` — the ℂ norm composes (dim 2 is a division
    algebra), proven through the cascade consumer, all exact."""
    z, o = _qi(t), _qi(_OTHER)
    prod = cd_mult([z.real, z.imag], [o.real, o.imag])
    assert Fraction(cd_norm_sq(prod)) == Fraction(cd_norm_sq([z.real, z.imag])) * \
        Fraction(cd_norm_sq([o.real, o.imag]))


def test_cd_consumer_stays_exact_not_float():
    """The rung consumer never touches a float — a reduced fraction survives
    bit-exact (this is what an exact carrier buys over the ``Complex128`` path)."""
    z = Qi(Q(1, 3), Q(1, 7))
    o = Qi(Q(2, 5), Q(-1, 11))
    cd = cd_mult([z.real, z.imag], [o.real, o.imag])
    # (1/3 + i/7)(2/5 − i/11) = (2/15 + 1/77) + (2/35 − 1/33) i
    assert _cd_pair(cd) == (Fraction(2, 15) + Fraction(1, 77),
                            Fraction(2, 35) - Fraction(1, 33))
    assert all(isinstance(x, Fraction) for x in cd)


# ──────────────────────────────────────────────────────────────────────
# 2. The generic numbers.Complex protocol — generic numeric code consumes Qi.
# ──────────────────────────────────────────────────────────────────────

def test_builtin_sum_consumes_qi_exactly():
    """``sum`` starts at ``int`` 0 then rides ``Qi.__radd__`` — stays an exact
    ``Qi`` equal to the running Fraction-pair sum."""
    xs = [_qi(t) for t in _GRID]
    total = sum(xs)
    assert isinstance(total, Qi)
    re = sum((Fraction(x.real.numerator, x.real.denominator) for x in xs), Fraction(0))
    im = sum((Fraction(x.imag.numerator, x.imag.denominator) for x in xs), Fraction(0))
    assert _frac_pair(total) == (re, im)


def test_complex_and_abs_consume_qi():
    assert complex(Qi(Q(3, 2), Q(-4, 5))) == complex(1.5, -0.8)
    # 3 + 4i → exact modulus 5 (perfect rational square); abs lands on a Real Q.
    a = abs(Qi(Q(3), Q(4)))
    assert isinstance(a, Q)
    assert a == Q(5)


@pytest.mark.parametrize("t", _GRID)
def test_integer_pow_consumes_qi_exactly(t):
    z = _qi(t)
    assert z ** 3 == z * z * z
    if z:                                              # avoid 0 ** -1
        assert z ** -1 == Qi(Q(1), Q(0)) / z


def test_mixed_type_arithmetic_consumes_qi_exactly():
    """``Qi`` mixed with ``int`` / ``Q`` / dyadic ``float`` stays an exact
    ``Qi`` (dyadic floats are exact rationals; the others are exact already)."""
    z = Qi(Q(3, 2), Q(-4, 5))
    assert z + 2 == Qi(Q(7, 2), Q(-4, 5))
    assert 2 * z == Qi(Q(3), Q(-8, 5))
    assert z + Q(1, 2) == Qi(Q(2), Q(-4, 5))
    assert z - 0.5 == Qi(Q(1), Q(-4, 5))               # 0.5 is dyadic → exact
    for r in (z + 2, 2 * z, z + Q(1, 2), z - 0.5):
        assert isinstance(r, Qi)


# ──────────────────────────────────────────────────────────────────────
# 3. The Complex128 float-boundary sink — the two complex carriers meet.
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("t", _GRID)
def test_complex128_consumes_qi_at_the_float_boundary(t):
    """``Qi`` (exact) combined with ``Complex128`` (float) → ``Complex128``,
    value-equal to the builtin-complex math (exact-meets-float → float)."""
    z = _qi(t)
    c = Complex128(1.25, -0.5)
    for got, want in (
        (z + c, complex(z) + complex(c)),
        (c + z, complex(c) + complex(z)),
        (z - c, complex(z) - complex(c)),
        (z * c, complex(z) * complex(c)),
        (c * z, complex(c) * complex(z)),
    ):
        assert isinstance(got, Complex128)
        assert complex(got) == want


def test_real_valued_qi_equals_complex128_with_hash_invariant():
    """A real ``Qi`` and the ``Complex128`` it equals compare equal both ways and
    hash equal — the cross-carrier data-model invariant."""
    qr = Qi(Q(3, 2), Q(0))
    cr = Complex128(1.5, 0.0)
    assert qr == cr and cr == qr
    assert hash(qr) == hash(cr)


def test_complex128_division_consumes_qi():
    z = Qi(Q(1), Q(2))
    c = Complex128(2.0, 0.0)
    got = z / c
    assert isinstance(got, Complex128)
    assert complex(got) == complex(0.5, 1.0)
