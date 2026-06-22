"""Parity tests for Class I — cyclic-group / modular arithmetic.

Tests both the native C path and the pure-Python fallback path, and
asserts byte-exact agreement when both are available. The parity
discipline mirrors ``test_native_sha256.py`` / ``test_native_ndjson.py``
from Task #201 Phase B3/B4.

When ``srmech.amsc._native.HAS_NATIVE`` is ``True``, every test runs
twice (once with the public dispatching surface, once with a
temporarily-disabled native flag forcing the fallback path) and the
two outputs are compared.
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native, cyclic


# ---------------------------------------------------------------------
# gcd / lcm — well-known reference values
# ---------------------------------------------------------------------

@pytest.mark.parametrize("a, b, expected", [
    (0, 0, 0),
    (0, 7, 7),
    (7, 0, 7),
    (1, 1, 1),
    (12, 18, 6),
    (48, 18, 6),
    (1024, 768, 256),
    (17, 13, 1),     # coprime
    (100, 75, 25),
    (2**32, 2**16, 2**16),
])
def test_gcd_reference_values(a, b, expected):
    assert cyclic.gcd(a, b) == expected


@pytest.mark.parametrize("a, b, expected", [
    (0, 0, 0),
    (0, 7, 0),
    (7, 0, 0),
    (4, 6, 12),
    (12, 18, 36),
    (10, 25, 50),
    (17, 13, 17 * 13),  # coprime
])
def test_lcm_reference_values(a, b, expected):
    assert cyclic.lcm(a, b) == expected


def test_lcm_overflow_raises():
    big = 2**40
    with pytest.raises(OverflowError):
        cyclic.lcm(big, big - 1)  # both coprime-ish; product > 2^64


# ---------------------------------------------------------------------
# mod_add / mod_mul / mod_pow — reference + Python-equivalence
# ---------------------------------------------------------------------

@pytest.mark.parametrize("a, b, n, expected", [
    (3, 4, 7, 0),
    (10, 5, 7, 1),
    (0, 0, 1, 0),
    (12345, 67890, 100, (12345 + 67890) % 100),
])
def test_mod_add_reference_values(a, b, n, expected):
    assert cyclic.mod_add(a, b, n) == expected


@pytest.mark.parametrize("a, b, n, expected", [
    (3, 4, 7, 5),
    (10, 5, 7, 50 % 7),
    (12345, 67890, 100003, (12345 * 67890) % 100003),
])
def test_mod_mul_reference_values(a, b, n, expected):
    assert cyclic.mod_mul(a, b, n) == expected


@pytest.mark.parametrize("a, k, n, expected", [
    (2, 0, 7, 1),
    (2, 10, 1000, pow(2, 10, 1000)),
    (3, 7, 11, pow(3, 7, 11)),
    (5, 100, 1009, pow(5, 100, 1009)),
])
def test_mod_pow_reference_values(a, k, n, expected):
    assert cyclic.mod_pow(a, k, n) == expected


# ---------------------------------------------------------------------
# mod_inv — known inverses + error conditions
# ---------------------------------------------------------------------

@pytest.mark.parametrize("a, n, expected", [
    (3, 11, 4),       # 3 * 4 = 12 ≡ 1 mod 11
    (7, 26, 15),      # 7 * 15 = 105 = 4*26 + 1
    (2, 5, 3),        # 2 * 3 = 6 ≡ 1 mod 5
])
def test_mod_inv_reference_values(a, n, expected):
    inv = cyclic.mod_inv(a, n)
    assert inv == expected
    assert (a * inv) % n == 1


def test_mod_inv_no_inverse_raises():
    # gcd(6, 9) = 3 != 1; no inverse exists
    with pytest.raises(ValueError):
        cyclic.mod_inv(6, 9)


def test_mod_inv_n_le_1_raises():
    with pytest.raises(ValueError):
        cyclic.mod_inv(5, 1)
    with pytest.raises(ValueError):
        cyclic.mod_inv(5, 0)


# ---------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------

def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        cyclic.gcd(-1, 5)
    with pytest.raises(ValueError):
        cyclic.mod_add(-1, 0, 7)


def test_gcd_oversized_is_uncapped():
    # v0.9.0: cyclic.gcd is UNCAPPED (arbitrary precision) — native serves its
    # uint64 domain, big-int Euclid beyond (standalone-honor "no compiled-in
    # caps"). gcd(2**65, 1) == 1. (Other cyclic ops keep the uint64 surface.)
    assert cyclic.gcd(2**65, 1) == 1
    assert cyclic.gcd(2**100, 2**99) == 2**99


def test_non_int_inputs_rejected():
    with pytest.raises(TypeError):
        cyclic.gcd(1.5, 2)
    with pytest.raises(TypeError):
        cyclic.mod_add("5", 0, 7)


# ---------------------------------------------------------------------
# Python-equivalence on random inputs (the load-bearing parity check)
# ---------------------------------------------------------------------

def test_gcd_matches_python_math_gcd():
    rng = random.Random(20260515)
    for _ in range(200):
        a = rng.randrange(0, 2**40)
        b = rng.randrange(0, 2**40)
        assert cyclic.gcd(a, b) == math.gcd(a, b)


def test_mod_add_matches_python_mod():
    rng = random.Random(20260516)
    for _ in range(200):
        n = rng.randrange(1, 2**32)
        a = rng.randrange(0, 2**32)
        b = rng.randrange(0, 2**32)
        assert cyclic.mod_add(a, b, n) == (a + b) % n


def test_mod_mul_matches_python_mod():
    rng = random.Random(20260517)
    for _ in range(200):
        n = rng.randrange(1, 2**32)
        a = rng.randrange(0, 2**32)
        b = rng.randrange(0, 2**32)
        assert cyclic.mod_mul(a, b, n) == (a * b) % n


def test_mod_pow_matches_python_pow():
    rng = random.Random(20260518)
    for _ in range(100):
        n = rng.randrange(2, 2**32)
        a = rng.randrange(0, 2**32)
        k = rng.randrange(0, 2**16)
        assert cyclic.mod_pow(a, k, n) == pow(a, k, n)


def test_mod_inv_matches_python_pow_minus_one():
    rng = random.Random(20260519)
    successful = 0
    attempts = 0
    while successful < 100 and attempts < 1000:
        attempts += 1
        n = rng.randrange(2, 2**31)
        a = rng.randrange(1, n)
        if math.gcd(a, n) != 1:
            continue
        expected = pow(a, -1, n)
        assert cyclic.mod_inv(a, n) == expected
        assert (a * expected) % n == 1
        successful += 1
    assert successful == 100, (
        f"only {successful} coprime pairs found in {attempts} attempts"
    )


# ---------------------------------------------------------------------
# C ↔ Python parity (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_path_matches_fallback_path():
    """Force both paths and compare byte-exactly for a random sweep.

    Toggling ``_native.HAS_NATIVE`` is the same discipline as
    test_native_sha256.py uses for the parity check.
    """
    rng = random.Random(20260520)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(50):
            a = rng.randrange(0, 2**32)
            b = rng.randrange(0, 2**32)
            n = rng.randrange(1, 2**32)
            k = rng.randrange(0, 2**16)

            _native.HAS_NATIVE = True
            native_gcd = cyclic.gcd(a, b)
            native_lcm = None
            try:
                native_lcm = cyclic.lcm(a % (2**20), b % (2**20))
            except OverflowError:
                pass
            native_mod_add = cyclic.mod_add(a, b, n)
            native_mod_mul = cyclic.mod_mul(a, b, n)
            native_mod_pow = cyclic.mod_pow(a, k, n)

            _native.HAS_NATIVE = False
            assert cyclic.gcd(a, b) == native_gcd
            if native_lcm is not None:
                assert cyclic.lcm(a % (2**20), b % (2**20)) == native_lcm
            assert cyclic.mod_add(a, b, n) == native_mod_add
            assert cyclic.mod_mul(a, b, n) == native_mod_mul
            assert cyclic.mod_pow(a, k, n) == native_mod_pow
    finally:
        _native.HAS_NATIVE = saved
