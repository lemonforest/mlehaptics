"""rc20 — pi_cascade_digits two-sided Pfaff-Archimedes chiral-pair rewrite.

The rotation-last audit's rc-A: ``pi_cascade_digits`` was rewritten from the
naive linear single-bound Archimedes hexagon-doubling (one rational sqrt feeding
the next radicand at every step — the avoidable op-costly form) to the two-sided
chiral pair (harmonic-mean circumscribed bound falling to pi, geometric-mean
inscribed bound rising to pi), with pi read off as the midpoint of the bracket.

These tests pin: (1) the same canonical decimal output the old form produced,
(2) the cross-oracle equality with the exact-substrate ``pi_chudnovsky_digits``
(rc19) — the chiral-pair Archimedes value == the exact-substrate Chudnovsky
value, and (3) determinism. Numpy-free.
"""
from __future__ import annotations

from srmech.amsc.rational import pi_cascade_digits, pi_chudnovsky_digits

# Canonical pi prefix (independently verifiable; first 20 fractional digits).
_PI_PREFIX = "3.14159265358979323846"


def test_pi_cascade_digits_15() -> None:
    """15 digits == the IEEE-754 double-precision boundary expansion."""
    assert pi_cascade_digits(15) == "3.141592653589793"


def test_pi_cascade_digits_zero() -> None:
    """Zero digits -> '3.' (the integer part separator)."""
    assert pi_cascade_digits(0) == "3."


def test_pi_cascade_digits_100_prefix() -> None:
    """The 100-digit expansion starts with the canonical pi prefix."""
    result = pi_cascade_digits(100)
    assert result.startswith(_PI_PREFIX), result[:25]
    assert len(result) == 2 + 100  # "3." + 100 digits


def test_pi_cascade_digits_500_prefix() -> None:
    """The 500-digit expansion starts with the canonical pi prefix."""
    result = pi_cascade_digits(500)
    assert result.startswith(_PI_PREFIX), result[:25]
    assert len(result) == 2 + 500  # "3." + 500 digits


def test_chiral_pair_equals_chudnovsky() -> None:
    """Cross-oracle: the chiral-pair Archimedes value is byte-for-byte equal
    to the exact-substrate Chudnovsky value at every tested digit count."""
    for n in (15, 100, 500):
        assert pi_cascade_digits(n) == pi_chudnovsky_digits(n), (
            f"chiral-pair != Chudnovsky at n={n}"
        )


def test_pi_cascade_digits_deterministic() -> None:
    """Same input -> same output (no nondeterminism in the iteration)."""
    for n in (0, 15, 100, 500):
        a = pi_cascade_digits(n)
        b = pi_cascade_digits(n)
        assert a == b, f"non-deterministic at n={n}: {a[:30]!r} vs {b[:30]!r}"
