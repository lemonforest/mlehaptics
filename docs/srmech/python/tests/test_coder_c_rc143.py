"""BATCH B6a (rc143) — byte-identical C parity for the 5 EXACT sp_coder_dp ops.

The `sp_coder_dp` batch (10 exact coder/DP ops) is split by complexity into two
rcs. **B6a = the 5 simpler EXACT ops** — memoryless quantizers + run-length +
Huffman — that had no C peer earn same-rc C twins. These are integer / exact
coders, so the C is BYTE-IDENTICAL to the pure-Python kernel — NO float
tolerance, no libm, no `abs()` (Class-K sign is a pin-slot boundary).

The 5 ops (all move ``python_only_debt`` → ``c_dispatched``, ceiling 77 → 72;
4 C symbols — the two sign_quantise paths share ``srmech_sign_quantise``):
  1. closed_form_ops.sign_quantise.op      \\
  2. path_b_ops.sign_quantise.op            } -> srmech_sign_quantise
  3. closed_form_ops.vector_quantisation.op -> srmech_vector_quantise_encode
  4. closed_form_ops.rle.op                 -> srmech_rle_encode
  5. closed_form_ops.huffman.op             -> srmech_huffman_build_codes

Each op dispatches its forward/compute path to its C peer when native is present
and falls back to the byte-identical pure kernel otherwise; the test proves
native == FORCED-pure for every op, and cross-checks each against an INDEPENDENT
pure oracle (+ encode→decode round-trips).

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""
from __future__ import annotations

import contextlib
import random

import pytest

from srmech.amsc import _native
from srmech.signal_processing.closed_form_ops import huffman as cf_huffman
from srmech.signal_processing.closed_form_ops import rle as cf_rle
from srmech.signal_processing.closed_form_ops import sign_quantise as cf_sign
from srmech.signal_processing.closed_form_ops import (
    vector_quantisation as cf_vq,
)
from srmech.signal_processing.path_b_ops import sign_quantise as pb_sign


# The 4 native gates B6a introduces (the two sign_quantise paths share one).
_B6A_GATES = (
    "sign_quantise",
    "vector_quantise_encode",
    "rle_encode",
    "huffman_build_codes",
)

requires_native = pytest.mark.skipif(
    not all(getattr(_native, "has_native_" + g)() for g in _B6A_GATES),
    reason="rc143 B6a coder/quantizer C peers not loaded (no-C host — the "
    "pure-Python kernel is the complete, byte-identical alternative)",
)


@contextlib.contextmanager
def force_pure(*gate_names):
    """Temporarily make the named ``_native.has_native_<gate>`` return False so
    the op takes its pure-Python fallback (the forced-pure reference)."""
    saved = {}
    for name in gate_names:
        attr = "has_native_" + name
        saved[attr] = getattr(_native, attr)
        setattr(_native, attr, lambda: False)
    try:
        yield
    finally:
        for attr, fn in saved.items():
            setattr(_native, attr, fn)


# ── independent oracles (never touch native; no abs) ──────────────────────────
def _oracle_sign(sig, threshold, dead_band):
    arr = [float(x) for x in sig]
    if dead_band <= 0.0:
        return [1 if x >= threshold else -1 for x in arr]
    hi, lo = threshold + dead_band, threshold - dead_band
    out = []
    for x in arr:
        out.append(1 if x > hi else (-1 if x < lo else 0))
    return out


def _oracle_vq(rows, cb):
    out = []
    for x in rows:
        best_k, best = 0, None
        for k, c in enumerate(cb):
            dist = 0.0
            for j in range(len(c)):
                diff = x[j] - c[j]
                dist += diff * diff
            if best is None or dist < best:
                best, best_k = dist, k
        out.append(best_k)
    return out


def _oracle_rle(data, max_run):
    data = bytes(data)
    out, i, n = [], 0, len(data)
    while i < n:
        sym, count = data[i], 1
        while i + count < n and data[i + count] == sym and count < max_run:
            count += 1
        out.append((sym, count))
        i += count
    return out


# ─────────────────────────── sign_quantise (both paths) ──────────────────────
_SIGN_CASES = [
    ([], 0.0, 0.0),
    ([0.0], 0.0, 0.0),
    ([-1.0, 0.0, 1.0, 0.5, -0.5], 0.0, 0.0),
    ([-1.0, 0.0, 1.0, 0.5, -0.5], 0.25, 0.0),
    ([-2.0, -0.3, -0.1, 0.0, 0.1, 0.3, 2.0], 0.0, 0.2),
    ([3.14, -2.7, 0.0, 1e-9, -1e-9], 0.0, 1e-9),
    ([5.0, 5.0, 5.0], 5.0, 0.0),        # exactly-at-threshold → +1 (>=)
]


def test_sign_quantise_semantics_pure_always_correct():
    with force_pure(*_B6A_GATES):
        for sig, th, db in _SIGN_CASES:
            want = _oracle_sign(sig, th, db)
            assert cf_sign.op(sig, threshold=th, dead_band=db) == want
            assert pb_sign.op(sig, threshold=th, dead_band=db) == want


@requires_native
def test_sign_quantise_native_equals_pure():
    for sig, th, db in _SIGN_CASES:
        for mod in (cf_sign, pb_sign):
            native = mod.op(sig, threshold=th, dead_band=db)
            with force_pure(*_B6A_GATES):
                pure = mod.op(sig, threshold=th, dead_band=db)
            assert native == pure == _oracle_sign(sig, th, db)


@requires_native
def test_sign_quantise_random_native_equals_pure():
    rng = random.Random(174)
    for _ in range(50):
        n = rng.randrange(0, 40)
        sig = [rng.uniform(-3.0, 3.0) for _ in range(n)]
        th = rng.choice([0.0, 0.5, -0.7, 1.3])
        db = rng.choice([0.0, 0.1, 0.4])
        native = cf_sign.op(sig, threshold=th, dead_band=db)
        with force_pure(*_B6A_GATES):
            pure = cf_sign.op(sig, threshold=th, dead_band=db)
        assert native == pure == _oracle_sign(sig, th, db)
        # the two paths are algebra-identical
        assert pb_sign.op(sig, threshold=th, dead_band=db) == native


# ─────────────────────────── vector_quantisation ─────────────────────────────
def _vq_case(rng, n_vec, n_codes, d):
    rows = [[rng.uniform(-5, 5) for _ in range(d)] for _ in range(n_vec)]
    cb = [[rng.uniform(-5, 5) for _ in range(d)] for _ in range(n_codes)]
    return rows, cb


def test_vq_semantics_pure_always_correct():
    rng = random.Random(1980)
    with force_pure(*_B6A_GATES):
        for _ in range(20):
            rows, cb = _vq_case(rng, rng.randrange(1, 8), rng.randrange(1, 6),
                                rng.randrange(1, 5))
            assert cf_vq.op(rows, cb) == _oracle_vq(rows, cb)


@requires_native
def test_vq_native_equals_pure():
    rng = random.Random(84)
    for _ in range(60):
        rows, cb = _vq_case(rng, rng.randrange(1, 10), rng.randrange(1, 8),
                            rng.randrange(1, 6))
        native = cf_vq.op(rows, cb)
        with force_pure(*_B6A_GATES):
            pure = cf_vq.op(rows, cb)
        assert native == pure == _oracle_vq(rows, cb)


@requires_native
def test_vq_ties_go_to_lowest_index():
    # Two identical codebook entries: every input must pick the LOWER index.
    cb = [[0.0, 0.0], [0.0, 0.0], [10.0, 10.0]]
    rows = [[0.0, 0.0], [1.0, 1.0], [10.0, 10.0]]
    native = cf_vq.op(rows, cb)
    with force_pure(*_B6A_GATES):
        pure = cf_vq.op(rows, cb)
    assert native == pure == [0, 0, 2]


@requires_native
def test_vq_single_vector_and_decode():
    cb = [[1.0, 2.0], [3.0, 4.0]]
    # a single (d,) vector is accepted as one row
    native = cf_vq.op([2.9, 3.9], cb)
    with force_pure(*_B6A_GATES):
        pure = cf_vq.op([2.9, 3.9], cb)
    assert native == pure == [1]
    # decode stays pure (trivial gather) — round-trips the index → codebook row
    assert cf_vq.op([1], cb, decode=True) == [[3.0, 4.0]]


# ─────────────────────────────────── rle ─────────────────────────────────────
_RLE_CASES = [
    b"",
    b"A",
    b"AAAA",
    b"AAABBBCCCCD",
    bytes([7] * 300),                    # run longer than max_run splits
    bytes([1, 1, 2, 3, 3, 3, 3, 4]),
    bytes(range(256)),                   # all distinct
]


def test_rle_semantics_pure_always_correct():
    with force_pure(*_B6A_GATES):
        for data in _RLE_CASES:
            for mr in (255, 4, 1):
                assert cf_rle.op(data, max_run=mr) == _oracle_rle(data, mr)


@requires_native
def test_rle_native_equals_pure():
    for data in _RLE_CASES:
        for mr in (255, 16, 4, 1):
            native = cf_rle.op(data, max_run=mr)
            with force_pure(*_B6A_GATES):
                pure = cf_rle.op(data, max_run=mr)
            assert native == pure == _oracle_rle(data, mr)


@requires_native
def test_rle_random_and_roundtrip():
    rng = random.Random(7)
    for _ in range(60):
        n = rng.randrange(0, 200)
        # a small alphabet makes real runs likely
        data = bytes(rng.randrange(3) for _ in range(n))
        mr = rng.choice([255, 8, 3])
        native = cf_rle.op(data, max_run=mr)
        with force_pure(*_B6A_GATES):
            pure = cf_rle.op(data, max_run=mr)
        assert native == pure == _oracle_rle(data, mr)
        # decode replays the pairs back to the original bytes
        assert cf_rle.op(native, decode=True) == data


# ─────────────────────────────────── huffman ─────────────────────────────────
_HUFF_CASES = [
    b"",
    b"A",
    b"AAAA",                             # single symbol → code "0"
    b"AAAABBBCCD",
    b"abracadabra",
    bytes([1, 2, 3]),                    # equal frequencies (tie-break by counter)
    bytes(range(16)),
    b"the quick brown fox jumps over the lazy dog",
]


def _assert_huff_equal(a, b):
    """Byte-identical: same bit-string, same code-dict values AND key order."""
    bits_a, codes_a = a
    bits_b, codes_b = b
    assert bits_a == bits_b
    assert codes_a == codes_b
    assert list(codes_a.keys()) == list(codes_b.keys())


def test_huffman_semantics_pure_always_correct():
    with force_pure(*_B6A_GATES):
        for data in _HUFF_CASES:
            bit_string, codes = cf_huffman.op(data)
            # round-trip: decode(encode) == original
            assert cf_huffman.op(bit_string, decode=True, codes=codes) == bytes(data)
            # prefix-free: no code is a prefix of another
            cs = sorted(codes.values())
            for i in range(len(cs) - 1):
                assert not cs[i + 1].startswith(cs[i])


@requires_native
def test_huffman_native_equals_pure():
    for data in _HUFF_CASES:
        native = cf_huffman.op(data)
        with force_pure(*_B6A_GATES):
            pure = cf_huffman.op(data)
        _assert_huff_equal(native, pure)
        # native encode round-trips through the pure decode too
        assert cf_huffman.op(native[0], decode=True, codes=native[1]) == bytes(data)


@requires_native
def test_huffman_random_native_equals_pure():
    rng = random.Random(1952)
    for _ in range(80):
        n = rng.randrange(0, 120)
        # varied alphabet widths exercise many distinct tree shapes
        width = rng.choice([1, 2, 3, 5, 17, 256])
        data = bytes(rng.randrange(width) for _ in range(n))
        native = cf_huffman.op(data)
        with force_pure(*_B6A_GATES):
            pure = cf_huffman.op(data)
        _assert_huff_equal(native, pure)
        assert cf_huffman.op(native[0], decode=True, codes=native[1]) == data


@requires_native
def test_huffman_str_input_matches_bytes():
    native = cf_huffman.op("hello world")
    with force_pure(*_B6A_GATES):
        pure = cf_huffman.op("hello world")
    _assert_huff_equal(native, pure)
    assert native == cf_huffman.op(b"hello world")
