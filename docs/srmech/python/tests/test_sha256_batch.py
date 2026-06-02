"""v0.7.0rc10 — N-way SIMD SHA-256 batch parity (F292 graft #1).

``srmech.amsc.format.sha256_batch(datas)`` returns one 64-char lowercase
hex digest per message, each byte-identical to ``sha256_bytes(d)`` /
``hashlib.sha256(d).hexdigest()``. The native peer (srmech_sha256_batch in
c/src/srmech_sha256_batch.c) dispatches at runtime to AVX2 8-way / SSE2
4-way on x86 (scalar elsewhere); whichever tier the host CPU selects, the
per-message digest is bit-exact with the single-stream path. (All three
tiers are additionally proven bit-exact locally via the
SRMECH_SHA256_FORCE_TIER hook; CI's native cells exercise the host tier.)

These tests pin parity for BOTH the native dispatch (when HAS_NATIVE +
the rc10 symbol is present) and the pure-Python hashlib fallback — the
public surface is identical either way.
"""

import hashlib

import pytest

from srmech.amsc import _native
from srmech.amsc.format import sha256_batch, sha256_bytes

# Lengths that hit every FIPS padding boundary: 0/1/2-block transitions
# (55->56 and 119->120 are where an extra padding block appears).
_LENS = [0, 1, 2, 3, 31, 32, 55, 56, 57, 63, 64, 65, 71, 72, 119, 120,
         127, 128, 129, 191, 192, 200, 256, 257, 511, 512]


def _msg(length: int, seed: int = 0) -> bytes:
    return bytes((i * 7 + length + seed) & 0xFF for i in range(length))


def test_singletons_match_hashlib():
    for L in _LENS:
        d = _msg(L)
        got = sha256_batch([d])
        assert got == [hashlib.sha256(d).hexdigest()], L


def test_matches_sha256_bytes_singleton():
    """A 1-message batch agrees with the single-stream sha256_bytes."""
    for L in (0, 1, 55, 56, 64, 200):
        d = _msg(L, seed=3)
        assert sha256_batch([d]) == [sha256_bytes(d)]


def test_mixed_length_batches():
    """Batches whose members have DIFFERENT block counts exercise the
    per-lane masking (a lane freezes once its shorter message is done)."""
    pool = [3, 7, 64, 65, 120, 200, 0, 1, 56, 63, 129, 257]
    for bs in [1, 2, 3, 4, 5, 7, 8, 9, 11, 15, 16, 17, 23, 32, 33]:
        datas = [_msg(pool[(i * 5 + bs) % len(pool)], seed=i + bs)
                 for i in range(bs)]
        got = sha256_batch(datas)
        want = [hashlib.sha256(d).hexdigest() for d in datas]
        assert got == want, bs


def test_empty_batch():
    assert sha256_batch([]) == []


def test_nist_anchors():
    anchors = {
        b"": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        b"abc": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    }
    got = sha256_batch(list(anchors.keys()))
    assert got == list(anchors.values())


def test_large_message():
    big = b"a" * 1_000_000
    assert sha256_batch([big]) == [hashlib.sha256(big).hexdigest()]


def test_coerces_bytearray_and_memoryview():
    """Non-bytes bytes-likes are accepted (coerced via bytes())."""
    d = b"\x00\x01\x02\xfe\xff" * 20
    got = sha256_batch([bytearray(d), memoryview(d)])
    want = hashlib.sha256(d).hexdigest()
    assert got == [want, want]


# ──────────────────────────────────────────────────────────────────────
# Native peer (skipped when the rc10 symbol is unavailable)
# ──────────────────────────────────────────────────────────────────────

_HAS_BATCH = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_sha256_batch")
)

_skip = pytest.mark.skipif(
    not _HAS_BATCH, reason="native srmech_sha256_batch unavailable")


@_skip
def test_native_batch_matches_single_stream():
    """The native batch digest equals the native single-stream
    sha256_hex_c per message (the C/Python full-parity check)."""
    datas = [_msg(L, seed=11) for L in _LENS]
    got = _native.sha256_batch_c(datas)
    want = [_native.sha256_hex_c(d) for d in datas]
    assert got == want


@_skip
def test_native_batch_matches_hashlib_large_mixed():
    """A big mixed batch through the native SIMD path == hashlib."""
    pool = [0, 1, 56, 63, 64, 65, 120, 129, 200, 511, 512, 1000]
    datas = [_msg(pool[i % len(pool)], seed=i) for i in range(37)]
    got = _native.sha256_batch_c(datas)
    want = [hashlib.sha256(d).hexdigest() for d in datas]
    assert got == want
