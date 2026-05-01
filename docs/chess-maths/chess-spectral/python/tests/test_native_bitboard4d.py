"""1.7.0 D2 M2.1: native fast-path foundation tests.

Verifies that the ctypes wrapper:
- imports cleanly even when the C library isn't built
- exposes a ``HAS_NATIVE`` flag callers can guard on
- when native IS available, the bound functions match the pure-Python
  ``Bitboard4D`` for identical inputs (correctness — perf wins land in
  M2.2)
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral._native_bitboard4d import (   # noqa: E402
    EXPECTED_ABI_VERSION, HAS_NATIVE, LIB, LIB_PATH, LOAD_ERROR,
    N_SQUARES, N_WORDS,
)
from chess_spectral.spatial_4d import Bitboard4D       # noqa: E402
from chess_spectral.spatial_4d.bitboard import HAS_NATIVE_BITBOARD  # noqa: E402


def test_module_always_imports():
    """The wrapper must import even if the C library isn't shipped."""
    # If we got here, import didn't raise. That's the test.
    assert N_WORDS == 64
    assert N_SQUARES == 4096
    assert isinstance(EXPECTED_ABI_VERSION, int)


def test_has_native_flag_consistent():
    """``HAS_NATIVE`` and ``HAS_NATIVE_BITBOARD`` agree."""
    assert HAS_NATIVE == HAS_NATIVE_BITBOARD


def test_load_error_set_when_native_missing():
    """If HAS_NATIVE is False, LOAD_ERROR explains why."""
    if not HAS_NATIVE:
        assert LOAD_ERROR is not None
        assert isinstance(LOAD_ERROR, str)
        assert len(LOAD_ERROR) > 10
    else:
        # When native loaded successfully, LOAD_ERROR may still be set
        # (e.g. ABI mismatch path). Just verify LIB itself is callable.
        assert LIB is not None
        assert LIB_PATH is not None
        assert LIB_PATH.exists()


# ----------------------------------------------------------------------
# Native-only correctness tests. Skipped when HAS_NATIVE is False
# (sdist install, Pyodide WASM-less, etc.).
# ----------------------------------------------------------------------

requires_native = pytest.mark.skipif(
    not HAS_NATIVE, reason="cs_bitboard4d shared library not built"
)


@requires_native
def test_native_abi_version_matches():
    """The library's reported ABI version must match what Python expects."""
    import ctypes
    actual = LIB.cs_bb4_abi_version()
    assert actual == EXPECTED_ABI_VERSION


@requires_native
def test_native_popcount_matches_python():
    """Native popcount returns the same value as int.bit_count() for
    several test bitboards."""
    import ctypes

    rng = np.random.default_rng(seed=1)
    for trial in range(8):
        # Generate a random 4096-bit pattern.
        words = rng.integers(0, 2**63, size=N_WORDS, dtype=np.uint64)
        bb = _bb_from_words(words)
        py_pop = bb.popcount()

        words_p = words.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        c_pop = LIB.cs_bb4_popcount(words_p)
        assert c_pop == py_pop, (
            f"trial {trial}: native popcount {c_pop} != Python {py_pop}"
        )


@requires_native
def test_native_and_or_xor_match_python():
    import ctypes

    rng = np.random.default_rng(seed=2)
    for op in ("and", "or", "xor"):
        a_words = rng.integers(0, 2**63, size=N_WORDS, dtype=np.uint64)
        b_words = rng.integers(0, 2**63, size=N_WORDS, dtype=np.uint64)
        out_words = np.zeros(N_WORDS, dtype=np.uint64)

        bb_a = _bb_from_words(a_words)
        bb_b = _bb_from_words(b_words)
        if op == "and":
            expected = bb_a & bb_b
            fn = LIB.cs_bb4_and
        elif op == "or":
            expected = bb_a | bb_b
            fn = LIB.cs_bb4_or
        else:
            expected = bb_a ^ bb_b
            fn = LIB.cs_bb4_xor

        a_p = a_words.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        b_p = b_words.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        out_p = out_words.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        fn(out_p, a_p, b_p)

        # Reassemble out_words into a Bitboard4D for comparison.
        bb_out = _bb_from_words(out_words)
        assert bb_out == expected, f"native {op} produced wrong result"


@requires_native
def test_native_set_clear_test_square():
    """Per-square ops match Bitboard4D's behaviour."""
    import ctypes

    words = np.zeros(N_WORDS, dtype=np.uint64)
    words_p = words.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))

    LIB.cs_bb4_set_square(words_p, 42)
    assert LIB.cs_bb4_test_square(words_p, 42) == 1
    assert LIB.cs_bb4_test_square(words_p, 41) == 0
    assert LIB.cs_bb4_test_square(words_p, 43) == 0

    LIB.cs_bb4_set_square(words_p, 4095)  # last square
    assert LIB.cs_bb4_test_square(words_p, 4095) == 1

    LIB.cs_bb4_clear_square(words_p, 42)
    assert LIB.cs_bb4_test_square(words_p, 42) == 0
    # 4095 still set.
    assert LIB.cs_bb4_test_square(words_p, 4095) == 1

    LIB.cs_bb4_toggle_square(words_p, 4095)
    assert LIB.cs_bb4_test_square(words_p, 4095) == 0
    LIB.cs_bb4_toggle_square(words_p, 4095)
    assert LIB.cs_bb4_test_square(words_p, 4095) == 1


@requires_native
def test_native_predicates():
    """is_empty / is_full / equals / intersects on canonical bitboards."""
    import ctypes

    zero = np.zeros(N_WORDS, dtype=np.uint64)
    full = np.full(N_WORDS, np.iinfo(np.uint64).max, dtype=np.uint64)

    zero_p = zero.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
    full_p = full.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))

    assert LIB.cs_bb4_is_empty(zero_p) == 1
    assert LIB.cs_bb4_is_empty(full_p) == 0
    assert LIB.cs_bb4_is_full(zero_p) == 0
    assert LIB.cs_bb4_is_full(full_p) == 1
    assert LIB.cs_bb4_equals(zero_p, zero_p) == 1
    assert LIB.cs_bb4_equals(zero_p, full_p) == 0
    assert LIB.cs_bb4_intersects(zero_p, zero_p) == 0
    assert LIB.cs_bb4_intersects(zero_p, full_p) == 0
    assert LIB.cs_bb4_intersects(full_p, full_p) == 1


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _bb_from_words(words: np.ndarray) -> Bitboard4D:
    """Reconstruct a Bitboard4D from a (64,) uint64 array.

    Uses ``Bitboard4D.from_numpy_uint64`` so we exercise the canonical
    Python projection. Avoids drift between the test and production
    paths.
    """
    if words.dtype != np.uint64:
        words = words.astype(np.uint64)
    return Bitboard4D.from_numpy_uint64(words)
