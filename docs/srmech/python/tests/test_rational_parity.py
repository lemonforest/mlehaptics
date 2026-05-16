"""Parity tests for Class N — rational-approximation (continued
fraction expansion + best convergent under denominator bound).
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native, rational


# ---------------------------------------------------------------------
# continued_fraction — reference values
# ---------------------------------------------------------------------

@pytest.mark.parametrize("p, q, expected", [
    (1, 1, [1]),                       # 1 = [1]
    (1, 2, [0, 2]),                    # 1/2 = [0; 2]
    (3, 2, [1, 2]),                    # 3/2 = [1; 2]
    (7, 3, [2, 3]),                    # 7/3 = [2; 3]
    (22, 7, [3, 7]),                   # 22/7 (canonical π approx) = [3; 7]
    (355, 113, [3, 7, 16]),            # 355/113 = [3; 7, 16]
    (5, 3, [1, 1, 2]),                 # 5/3 = [1; 1, 2]
    (13, 8, [1, 1, 1, 1, 2]),          # 13/8 (Fibonacci) = [1;1,1,1,2]
    (0, 5, [0]),                       # 0/5 = [0]
])
def test_continued_fraction_reference(p, q, expected):
    assert rational.continued_fraction(p, q) == expected


def test_continued_fraction_zero_denominator_raises():
    with pytest.raises(ValueError):
        rational.continued_fraction(1, 0)


# ---------------------------------------------------------------------
# best_rational — reference values
# ---------------------------------------------------------------------

@pytest.mark.parametrize("p, q, max_q, expected", [
    (22, 7, 7, (22, 7)),         # already fits
    (22, 7, 3, (3, 1)),          # bound forces [3] convergent
    (355, 113, 100, (22, 7)),    # bound forces 22/7 convergent
    (355, 113, 200, (355, 113)), # 113 fits, return the original
    (1, 2, 1, (0, 1)),           # no non-trivial convergent fits at q=1
    (1, 2, 2, (1, 2)),           # 1/2 fits exactly
])
def test_best_rational_reference(p, q, max_q, expected):
    assert rational.best_rational(p, q, max_q) == expected


def test_best_rational_zero_denominator_raises():
    with pytest.raises(ValueError):
        rational.best_rational(1, 0, 10)


def test_best_rational_zero_max_raises():
    with pytest.raises(ValueError):
        rational.best_rational(1, 2, 0)


# ---------------------------------------------------------------------
# Reconstruct from continued fraction (round-trip)
# ---------------------------------------------------------------------

def _from_cf(terms):
    """Reconstruct p/q from continued-fraction terms via convergent
    recurrence. Reference implementation for round-trip testing."""
    if not terms:
        return 0, 1
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    for a in terms:
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
    return h_prev, k_prev


def test_continued_fraction_round_trip():
    rng = random.Random(20260516)
    for _ in range(100):
        # Generate random reduced fraction
        a = rng.randrange(1, 10**9)
        b = rng.randrange(1, 10**9)
        g = math.gcd(a, b)
        p, q = a // g, b // g
        terms = rational.continued_fraction(p, q)
        p_back, q_back = _from_cf(terms)
        # Reduce p_back/q_back for comparison
        gb = math.gcd(p_back, q_back) if q_back > 0 else 1
        assert (p_back // gb, q_back // gb) == (p, q), (
            f"round-trip mismatch: p/q={p}/{q} terms={terms} -> "
            f"{p_back}/{q_back}"
        )


# ---------------------------------------------------------------------
# C ↔ Python parity sweep (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_continued_fraction_matches_fallback():
    rng = random.Random(20260517)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(100):
            p = rng.randrange(0, 10**9)
            q = rng.randrange(1, 10**9)
            _native.HAS_NATIVE = True
            native_result = rational.continued_fraction(p, q)
            _native.HAS_NATIVE = False
            fallback_result = rational.continued_fraction(p, q)
            assert native_result == fallback_result, (
                f"p/q={p}/{q}: native={native_result} fallback={fallback_result}"
            )
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_best_rational_matches_fallback():
    rng = random.Random(20260518)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(100):
            p = rng.randrange(0, 10**9)
            q = rng.randrange(1, 10**9)
            max_q = rng.randrange(1, 10**6)
            _native.HAS_NATIVE = True
            native_result = rational.best_rational(p, q, max_q)
            _native.HAS_NATIVE = False
            fallback_result = rational.best_rational(p, q, max_q)
            assert native_result == fallback_result
    finally:
        _native.HAS_NATIVE = saved
