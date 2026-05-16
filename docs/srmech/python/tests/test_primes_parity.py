"""Parity tests for Class J — prime-factorisation / period.

Reference values + Python-equivalence on random uint64 inputs + native
↔ fallback parity sweep.
"""

from __future__ import annotations

import random

import pytest

from srmech.amsc import _native, primes


# ---------------------------------------------------------------------
# is_prime
# ---------------------------------------------------------------------

@pytest.mark.parametrize("n, expected", [
    (0, False),
    (1, False),
    (2, True),
    (3, True),
    (4, False),
    (5, True),
    (6, False),
    (7, True),
    (8, False),
    (9, False),
    (10, False),
    (11, True),
    (12, False),
    (13, True),
    (97, True),
    (100, False),
    (101, True),
    (1000003, True),       # known prime
    (1000004, False),
    (982451653, True),     # known large 32-bit prime
])
def test_is_prime_reference_values(n, expected):
    assert primes.is_prime(n) == expected


def test_is_prime_sweep_low_range():
    # Cross-check against stdlib trial-division reference (no sympy dep).
    def _ref_is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n < 4:
            return True
        if n % 2 == 0:
            return False
        d = 3
        while d * d <= n:
            if n % d == 0:
                return False
            d += 2
        return True
    for n in range(2, 1000):
        assert primes.is_prime(n) == _ref_is_prime(n), f"mismatch at n={n}"


# ---------------------------------------------------------------------
# factor
# ---------------------------------------------------------------------

@pytest.mark.parametrize("n, expected", [
    (1, []),
    (0, []),
    (2, [(2, 1)]),
    (3, [(3, 1)]),
    (4, [(2, 2)]),
    (6, [(2, 1), (3, 1)]),
    (8, [(2, 3)]),
    (12, [(2, 2), (3, 1)]),
    (60, [(2, 2), (3, 1), (5, 1)]),
    (100, [(2, 2), (5, 2)]),
    (97, [(97, 1)]),
    (1024, [(2, 10)]),
    (12345, [(3, 1), (5, 1), (823, 1)]),
])
def test_factor_reference_values(n, expected):
    assert primes.factor(n) == expected


def test_factor_round_trip():
    rng = random.Random(20260515)
    for _ in range(50):
        n = rng.randrange(2, 10**9)
        result = primes.factor(n)
        product = 1
        for p, e in result:
            product *= p ** e
        assert product == n, f"factor({n}) = {result} did not multiply back"


def test_factor_primes_sorted_ascending():
    rng = random.Random(20260516)
    for _ in range(20):
        n = rng.randrange(2, 10**8)
        result = primes.factor(n)
        if len(result) > 1:
            ps = [p for p, _ in result]
            assert ps == sorted(ps), f"factor({n}) primes not sorted: {ps}"


# ---------------------------------------------------------------------
# cyclic_period
# ---------------------------------------------------------------------

@pytest.mark.parametrize("a, n, expected", [
    (1, 7, 1),
    (2, 7, 3),     # 2^3 = 8 ≡ 1 mod 7
    (3, 7, 6),     # 3 generates (Z/7Z)*
    (2, 5, 4),     # 2^4 = 16 ≡ 1 mod 5
    (4, 5, 2),     # 4^2 = 16 ≡ 1 mod 5
    (3, 11, 5),    # 3^5 = 243 = 22*11 + 1
])
def test_cyclic_period_reference_values(a, n, expected):
    assert primes.cyclic_period(a, n) == expected


def test_cyclic_period_matches_brute_force():
    rng = random.Random(20260517)
    for _ in range(30):
        n = rng.randrange(3, 1000)
        a = rng.randrange(1, n)
        if primes.factor.__defaults__:  # smoke
            pass
        # Skip if gcd != 1
        from math import gcd
        if gcd(a, n) != 1:
            continue
        period = primes.cyclic_period(a, n)
        # Verify a^period ≡ 1 (mod n)
        assert pow(a, period, n) == 1
        # Verify no smaller k works
        for k in range(1, period):
            assert pow(a, k, n) != 1, (
                f"cyclic_period({a}, {n}) = {period} but a^{k} ≡ 1"
            )


def test_cyclic_period_non_invertible_raises():
    # gcd(6, 9) = 3 != 1; no order exists
    with pytest.raises(ValueError):
        primes.cyclic_period(6, 9)


def test_cyclic_period_n_lt_2_raises():
    with pytest.raises(ValueError):
        primes.cyclic_period(2, 1)


# ---------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------

def test_negative_rejected():
    with pytest.raises(ValueError):
        primes.is_prime(-3)
    with pytest.raises(ValueError):
        primes.factor(-12)


def test_non_int_rejected():
    with pytest.raises(TypeError):
        primes.is_prime(7.5)
    with pytest.raises(TypeError):
        primes.cyclic_period("2", 7)


# ---------------------------------------------------------------------
# C ↔ Python parity (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_matches_fallback():
    rng = random.Random(20260518)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(50):
            n = rng.randrange(2, 10**9)
            _native.HAS_NATIVE = True
            native_prime = primes.is_prime(n)
            native_factor = primes.factor(n)
            _native.HAS_NATIVE = False
            assert primes.is_prime(n) == native_prime
            assert primes.factor(n) == native_factor
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_cyclic_period_matches_fallback():
    from math import gcd
    rng = random.Random(20260519)
    saved = _native.HAS_NATIVE
    try:
        successful = 0
        attempts = 0
        while successful < 30 and attempts < 300:
            attempts += 1
            n = rng.randrange(3, 1000)
            a = rng.randrange(1, n)
            if gcd(a, n) != 1:
                continue
            _native.HAS_NATIVE = True
            native_period = primes.cyclic_period(a, n)
            _native.HAS_NATIVE = False
            fallback_period = primes.cyclic_period(a, n)
            assert native_period == fallback_period
            successful += 1
        assert successful == 30
    finally:
        _native.HAS_NATIVE = saved
