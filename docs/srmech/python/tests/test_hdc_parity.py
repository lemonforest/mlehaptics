"""Parity tests for Class M (HDC binary spatter codes).

Task #217 Phase C1 rc8. Closes the 14-class C parity roster.

Canonical SSoT per `[[feedback_science_is_ssot_not_project]]`:
- Kanerva (2009) Cognitive Computation 1, 139-159.
- Plate (1995) IEEE Trans Neural Networks 6, 623-641.
- Rachkovskij (2001) Neural Comput Appl 9, 322-345.
"""

from __future__ import annotations

import random

import pytest

from srmech.amsc import _native, hdc


def _rand_vector(n_bytes: int, rng: random.Random) -> bytes:
    return bytes(rng.randrange(256) for _ in range(n_bytes))


# ----------------------------------------------------------------------
# bind
# ----------------------------------------------------------------------


def test_bind_self_inverse():
    """bind(a, bind(a, b)) == b for any a, b."""
    rng = random.Random(0)
    for _ in range(20):
        a = _rand_vector(16, rng)
        b = _rand_vector(16, rng)
        assert hdc.bind(a, hdc.bind(a, b)) == b


def test_bind_commutative():
    """bind(a, b) == bind(b, a)."""
    rng = random.Random(1)
    for _ in range(20):
        a = _rand_vector(32, rng)
        b = _rand_vector(32, rng)
        assert hdc.bind(a, b) == hdc.bind(b, a)


def test_bind_associative():
    """bind(a, bind(b, c)) == bind(bind(a, b), c)."""
    rng = random.Random(2)
    for _ in range(20):
        a = _rand_vector(8, rng)
        b = _rand_vector(8, rng)
        c = _rand_vector(8, rng)
        assert hdc.bind(a, hdc.bind(b, c)) == hdc.bind(hdc.bind(a, b), c)


def test_bind_identity():
    """bind(a, 0) == a."""
    a = bytes([0xAA, 0x55, 0xFF, 0x00])
    zero = bytes(4)
    assert hdc.bind(a, zero) == a


def test_bind_length_mismatch():
    with pytest.raises(ValueError):
        hdc.bind(b"\x00", b"\x00\x00")


def test_bind_empty():
    with pytest.raises(ValueError):
        hdc.bind(b"", b"")


# ----------------------------------------------------------------------
# bundle
# ----------------------------------------------------------------------


def test_bundle_single_vector():
    """Bundle of a single vector returns that vector."""
    v = bytes([0xA5, 0x5A, 0xFF])
    assert hdc.bundle([v]) == v


def test_bundle_three_identical():
    """Bundle of three copies of v returns v (majority of identical bits)."""
    v = bytes([0xDE, 0xAD, 0xBE, 0xEF])
    assert hdc.bundle([v, v, v]) == v


def test_bundle_majority():
    """At each bit position, output is the majority of inputs."""
    # bit 0 of byte 0: 1, 1, 0 → majority 1
    # bit 1 of byte 0: 0, 1, 1 → majority 1
    # bit 2 of byte 0: 0, 0, 1 → majority 0
    a = bytes([0b00000001])
    b = bytes([0b00000011])
    c = bytes([0b00000110])
    # expected: bit 0 = maj(1,1,0)=1, bit 1 = maj(0,1,1)=1, bit 2 = maj(0,0,1)=0, ...
    expected = bytes([0b00000011])
    assert hdc.bundle([a, b, c]) == expected


def test_bundle_even_count_rejected():
    v = bytes(4)
    with pytest.raises(ValueError):
        hdc.bundle([v, v])


def test_bundle_empty_rejected():
    with pytest.raises(ValueError):
        hdc.bundle([])


def test_bundle_mismatched_lengths():
    with pytest.raises(ValueError):
        hdc.bundle([b"\x00\x00", b"\x00", b"\x00"])


# ----------------------------------------------------------------------
# permute
# ----------------------------------------------------------------------


def test_permute_zero_is_identity():
    a = bytes([0xAA, 0x55, 0xFF, 0x00])
    assert hdc.permute(a, 0) == a


def test_permute_preserves_popcount():
    """popcount(permute(a, k)) == popcount(a) for any k."""
    rng = random.Random(3)
    for _ in range(20):
        a = _rand_vector(16, rng)
        k = rng.randint(-256, 256)
        rotated = hdc.permute(a, k)
        pc_a = sum(bin(x).count("1") for x in a)
        pc_r = sum(bin(x).count("1") for x in rotated)
        assert pc_a == pc_r


def test_permute_inverse():
    """permute(permute(a, k), -k) == a."""
    rng = random.Random(4)
    for _ in range(20):
        a = _rand_vector(8, rng)
        k = rng.randint(-128, 128)
        round_trip = hdc.permute(hdc.permute(a, k), -k)
        assert round_trip == a


def test_permute_full_rotation_is_identity():
    """permute(a, D) == a where D = 8 * len(a)."""
    a = bytes([0xAB, 0xCD, 0xEF, 0x12])
    D = 8 * len(a)
    assert hdc.permute(a, D) == a
    assert hdc.permute(a, 2 * D) == a
    assert hdc.permute(a, -D) == a


def test_permute_single_bit_shift():
    """Shift by 1: bit 0 moves to position 1."""
    a = bytes([0b00000001, 0])
    rotated = hdc.permute(a, 1)
    assert rotated == bytes([0b00000010, 0])


def test_permute_empty():
    with pytest.raises(ValueError):
        hdc.permute(b"", 0)


# ----------------------------------------------------------------------
# similarity
# ----------------------------------------------------------------------


def test_similarity_self_is_one():
    """similarity(a, a) == 1."""
    rng = random.Random(5)
    for _ in range(10):
        a = _rand_vector(32, rng)
        assert hdc.similarity(a, a) == 1.0


def test_similarity_complement_is_minus_one():
    """similarity(a, ~a) == -1."""
    a = bytes([0xAA, 0x55, 0xFF, 0x00])
    a_not = bytes([b ^ 0xFF for b in a])
    assert hdc.similarity(a, a_not) == -1.0


def test_similarity_orthogonal_is_zero():
    """similarity for Hamming distance = D/2 is 0."""
    # 8 bytes = 64 bits; half-Hamming = 32 bit differences
    a = bytes(8)  # all zeros
    b = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0, 0, 0, 0])  # 32 set bits
    assert abs(hdc.similarity(a, b)) < 1e-12


def test_similarity_symmetric():
    rng = random.Random(6)
    for _ in range(20):
        a = _rand_vector(16, rng)
        b = _rand_vector(16, rng)
        assert hdc.similarity(a, b) == hdc.similarity(b, a)


def test_similarity_range():
    """similarity is in [-1, 1]."""
    rng = random.Random(7)
    for _ in range(50):
        a = _rand_vector(8, rng)
        b = _rand_vector(8, rng)
        s = hdc.similarity(a, b)
        assert -1.0 <= s <= 1.0


# ----------------------------------------------------------------------
# Native ↔ Python parity sweep
# ----------------------------------------------------------------------


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_bind_parity():
    rng = random.Random(8)
    for _ in range(50):
        n = rng.randint(1, 64)
        a = _rand_vector(n, rng)
        b = _rand_vector(n, rng)
        native = hdc.bind(a, b)
        py = bytes(x ^ y for x, y in zip(a, b))
        assert native == py


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_similarity_parity():
    rng = random.Random(9)
    for _ in range(50):
        n = rng.randint(1, 64)
        a = _rand_vector(n, rng)
        b = _rand_vector(n, rng)
        native = hdc.similarity(a, b)
        D = n * 8
        hamming = sum(bin(x ^ y).count("1") for x, y in zip(a, b))
        py = 1.0 - 2.0 * hamming / D
        assert abs(native - py) < 1e-14


@pytest.mark.skipif(
    not _native.HAS_NATIVE,
    reason="native lib not loaded; parity sweep skipped",
)
def test_native_python_permute_parity():
    rng = random.Random(10)
    for _ in range(50):
        n = rng.randint(1, 32)
        a = _rand_vector(n, rng)
        k = rng.randint(-128, 128)
        native = hdc.permute(a, k)
        # Pure-Python reference:
        D = n * 8
        eff = k % D
        out = bytearray(n)
        for i in range(D):
            src = (i - eff) % D
            bit_value = (a[src // 8] >> (src % 8)) & 1
            if bit_value:
                out[i // 8] |= (1 << (i % 8))
        assert native == bytes(out)
