"""Parity tests for Classes B (TLV) + G (byte search) + H (introspection).

Reference values, Python-equivalence, and native ↔ fallback parity.
"""

from __future__ import annotations

import struct

import pytest

from srmech.amsc import _native, search, tlv


# ---------------------------------------------------------------------
# Class B — tlv_pack
# ---------------------------------------------------------------------

@pytest.mark.parametrize("tag, value, expected_prefix", [
    (0, b"",     b"\x00\x00\x00\x00\x00"),
    (1, b"",     b"\x01\x00\x00\x00\x00"),
    (255, b"",   b"\xff\x00\x00\x00\x00"),
    (0x42, b"hello", b"\x42\x00\x00\x00\x05"),
])
def test_tlv_pack_reference_values(tag, value, expected_prefix):
    result = tlv.tlv_pack(tag, value)
    assert result[: tlv.TLV_PREFIX_BYTES] == expected_prefix
    assert result[tlv.TLV_PREFIX_BYTES:] == value


def test_tlv_pack_big_endian_length():
    # Length 256 should encode as 00 00 01 00 (big-endian)
    value = b"x" * 256
    result = tlv.tlv_pack(0x10, value)
    assert result[1:5] == b"\x00\x00\x01\x00"


def test_tlv_pack_total_length():
    for value_len in [0, 1, 5, 100, 1000]:
        value = b"a" * value_len
        result = tlv.tlv_pack(7, value)
        assert len(result) == tlv.TLV_PREFIX_BYTES + value_len


def test_tlv_pack_matches_struct_pack():
    # Pure-Python equivalence via struct.pack
    for tag in [0, 1, 42, 255]:
        for value in [b"", b"x", b"hello world", bytes(range(256))]:
            expected = struct.pack(">BI", tag, len(value)) + value
            assert tlv.tlv_pack(tag, value) == expected


def test_tlv_pack_invalid_tag():
    with pytest.raises(ValueError):
        tlv.tlv_pack(-1, b"")
    with pytest.raises(ValueError):
        tlv.tlv_pack(256, b"")


def test_tlv_pack_invalid_value_type():
    with pytest.raises(TypeError):
        tlv.tlv_pack(0, "not bytes")


# ---------------------------------------------------------------------
# Class G — byte_search
# ---------------------------------------------------------------------

@pytest.mark.parametrize("haystack, needle, expected", [
    (b"hello world", b"world", 6),
    (b"hello world", b"hello", 0),
    (b"hello world", b"xyz", None),
    (b"", b"x", None),
    (b"abc", b"", 0),  # empty needle matches at 0 (matches bytes.find)
    (b"abc", b"abc", 0),
    (b"abc", b"abcd", None),  # needle longer than haystack
    (b"aaa", b"a", 0),
    (b"abab", b"ab", 0),
    (b"abab", b"ba", 1),
])
def test_byte_search_reference_values(haystack, needle, expected):
    assert search.byte_search(haystack, needle) == expected


def test_byte_search_matches_bytes_find():
    import random
    rng = random.Random(20260515)
    alphabet = b"ABCD"
    for _ in range(50):
        h = bytes(rng.choices(alphabet, k=rng.randint(0, 100)))
        n = bytes(rng.choices(alphabet, k=rng.randint(0, 5)))
        expected = h.find(n)
        result = search.byte_search(h, n)
        if expected < 0:
            assert result is None, f"h={h!r} n={n!r}: expected None, got {result}"
        else:
            assert result == expected, f"h={h!r} n={n!r}: {result} != {expected}"


# ---------------------------------------------------------------------
# Class H — introspection (already in srmech.version + srmech_meta.c)
# ---------------------------------------------------------------------

def test_introspection_version_python():
    import srmech
    # Class H primitive: introspection returns a non-empty version string.
    # We assert format (non-empty) rather than a specific value so the test
    # survives version bumps without churn (the version is checked for
    # consistency between Python + C in the native-match test below).
    assert isinstance(srmech.__version__, str)
    assert len(srmech.__version__) > 0


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_introspection_version_native_matches():
    # Class H invariant: native version string must agree with Python.
    import srmech
    assert _native.NATIVE_VERSION == srmech.__version__
    # v0.5.0rc2 bumped ABI 2 → 3 (added srmech_bus_* C peer + new
    # function-pointer typedef srmech_bus_handler_callback_t).
    assert _native.NATIVE_ABI_VERSION == 3


# ---------------------------------------------------------------------
# C ↔ Python parity sweep (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_tlv_matches_fallback():
    import random
    rng = random.Random(20260516)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(50):
            tag = rng.randint(0, 255)
            value_len = rng.randint(0, 200)
            value = bytes(rng.randbytes(value_len))
            _native.HAS_NATIVE = True
            native_out = tlv.tlv_pack(tag, value)
            _native.HAS_NATIVE = False
            fallback_out = tlv.tlv_pack(tag, value)
            assert native_out == fallback_out
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_search_matches_fallback():
    import random
    rng = random.Random(20260517)
    saved = _native.HAS_NATIVE
    try:
        alphabet = b"AB"
        for _ in range(50):
            h = bytes(rng.choices(alphabet, k=rng.randint(0, 200)))
            n = bytes(rng.choices(alphabet, k=rng.randint(0, 10)))
            _native.HAS_NATIVE = True
            native_result = search.byte_search(h, n)
            _native.HAS_NATIVE = False
            fallback_result = search.byte_search(h, n)
            assert native_result == fallback_result, (
                f"h={h!r} n={n!r}: native={native_result} != "
                f"fallback={fallback_result}"
            )
    finally:
        _native.HAS_NATIVE = saved
