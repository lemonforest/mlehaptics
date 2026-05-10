"""C↔Python parity tests for the pure-phase 2D encoder (1.19.0+).

Verifies bit-exact equivalence between
:func:`chess_spectral.encoder_pure_phase.encode_2d_pure_phase` (the
Python reference) and the native C implementation in
:mod:`chess_spectral._native_pure_phase_2d` (the C port shipped in
1.19.0).

Tolerance is **zero** (np.array_equal): both sides do integer
arithmetic only, so any bit-level disagreement signals a bug.

Three layers:

  * **Hand-crafted positions** — 5 representative positions exercising
    every channel (D₄ irreps, symmetric fiber, FA pawn, FD diag).
  * **Pedantic random corpus** — 500 random 2D positions across piece
    counts in [2, 32].
  * **Edge cases** — empty position, single piece, all-pawn variants.

Skips entirely when the native library isn't loadable (sdist install,
Pyodide WASM, etc.); the Python implementation is the correctness
reference and remains the only path in those environments.

Closes the chess2d/chess4d C-port parity gap noted in the 1.18.0
CHANGELOG.
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

from chess_spectral.encoder import CHANNELS   # noqa: E402
from chess_spectral.encoder_pure_phase import (   # noqa: E402
    encode_2d_pure_phase,
)
from chess_spectral._native_pure_phase_2d import (   # noqa: E402
    HAS_NATIVE_PURE_PHASE_2D, encode_pure_phase_2d_native,
)

from tests._random_positions import (   # noqa: E402
    random_pos_2d, piece_count_distribution_2d,
)


_skip_no_native = pytest.mark.skipif(
    not HAS_NATIVE_PURE_PHASE_2D,
    reason="native cs_encoder_pure_phase_2d library not loaded; "
    "expected when building sdist without C toolchain.",
)


# ─── Hand-crafted positions covering every channel ──────────────────


def _imbalanced():
    # Mostly white, single black king. Exercises D₄ asymmetric
    # signal and DIAG_DEV asymmetric coefficients.
    return {
        0: 'K', 63: 'k',
        9: 'Q', 18: 'B', 27: 'N', 36: 'R', 45: 'P',
    }


def _full_channel():
    # All 12 piece chars present; balanced colors. Exercises every
    # channel (D₄, fiber-sym for N/B/R/Q/K, FA pawns both colors,
    # FD all 6 piece types).
    return {
        0: 'R', 1: 'N', 2: 'B', 3: 'Q', 4: 'K', 5: 'B', 6: 'N', 7: 'R',
        8: 'P', 9: 'P', 10: 'P', 11: 'P', 12: 'P', 13: 'P', 14: 'P', 15: 'P',
        48: 'p', 49: 'p', 50: 'p', 51: 'p', 52: 'p', 53: 'p', 54: 'p', 55: 'p',
        56: 'r', 57: 'n', 58: 'b', 59: 'q', 60: 'k', 61: 'b', 62: 'n', 63: 'r',
    }


def _sparse_endgame():
    # Just kings + one queen. Exercises sparse fiber-sym and FA
    # near-zero (no pawns).
    return {1: 'K', 62: 'k', 27: 'Q'}


def _all_pawns():
    """Pawns on both colors only — exercises FA in isolation
    (fiber-sym/FD pawn-row gets 0 except FD pawn coef)."""
    return {
        8: 'P', 9: 'P', 10: 'P', 11: 'P',
        12: 'P', 13: 'P', 14: 'P', 15: 'P',
        48: 'p', 49: 'p', 50: 'p', 51: 'p',
        52: 'p', 53: 'p', 54: 'p', 55: 'p',
    }


def _knights_only():
    """Knights on both colors only — exercises fiber-sym for
    knights without other piece interference."""
    return {
        0: 'N', 7: 'N', 56: 'n', 63: 'n',
        18: 'N', 21: 'n', 42: 'N', 45: 'n',
    }


_REPRESENTATIVE_POSITIONS = [
    ('imbalanced',     _imbalanced),
    ('full_channel',   _full_channel),
    ('sparse_endgame', _sparse_endgame),
    ('all_pawns',      _all_pawns),
    ('knights_only',   _knights_only),
]


# ─── Hand-crafted parity tests ──────────────────────────────────────


@_skip_no_native
@pytest.mark.parametrize(
    "name", [n for n, _ in _REPRESENTATIVE_POSITIONS]
)
def test_c_py_parity_2d_representative_position_bit_exact(name):
    """C output matches Python output exactly on every representative
    position. Tolerance is zero — both are integer arithmetic."""
    pos_factory = next(
        f for n, f in _REPRESENTATIVE_POSITIONS if n == name
    )
    pos = pos_factory()
    py_out = encode_2d_pure_phase(pos)
    c_out = encode_pure_phase_2d_native(pos)
    assert py_out.shape == c_out.shape == (640,)
    assert py_out.dtype == c_out.dtype == np.int32
    if not np.array_equal(py_out, c_out):
        # Diagnostic: per-channel diff breakdown.
        per_channel = []
        channel_dim = 64
        for chan_name, start in CHANNELS:
            end = start + channel_dim
            n_diff = int((py_out[start:end] != c_out[start:end]).sum())
            if n_diff > 0:
                md = int(np.abs(
                    py_out[start:end].astype(np.int64)
                    - c_out[start:end].astype(np.int64)
                ).max())
                per_channel.append(
                    f"{chan_name}: {n_diff} diffs, max |Δ|={md}"
                )
        pytest.fail(
            f"{name}: C/Python mismatch — "
            f"{', '.join(per_channel) if per_channel else 'unspecified'}"
        )


# ─── Edge cases ─────────────────────────────────────────────────────


@_skip_no_native
def test_c_py_parity_2d_empty_position():
    py_out = encode_2d_pure_phase({})
    c_out = encode_pure_phase_2d_native({})
    assert (py_out == 0).all()
    assert (c_out == 0).all()
    assert np.array_equal(py_out, c_out)


@_skip_no_native
def test_c_py_parity_2d_single_piece():
    pos = {27: 'Q'}
    assert np.array_equal(
        encode_2d_pure_phase(pos),
        encode_pure_phase_2d_native(pos),
    )


@_skip_no_native
def test_c_py_parity_2d_single_pawn_each_color():
    """Two pawns (one each color) only — the FA channel should have
    a non-trivial signature, all other channels low magnitude. Bit
    parity must hold."""
    pos = {8: 'P', 55: 'p'}
    py_out = encode_2d_pure_phase(pos)
    c_out = encode_pure_phase_2d_native(pos)
    assert np.array_equal(py_out, c_out)


@_skip_no_native
def test_c_py_parity_2d_str_keyed_dict():
    """NDJSON-style str-keyed dicts are accepted and produce the
    same encoding as int-keyed dicts."""
    pos = {"0": "K", "63": "k", "27": "Q"}
    py_out = encode_2d_pure_phase(pos)
    c_out = encode_pure_phase_2d_native(pos)
    assert np.array_equal(py_out, c_out)


# ─── Pedantic random corpus ─────────────────────────────────────────


@_skip_no_native
def test_c_py_parity_2d_random_corpus_500_positions_bit_exact():
    """500 random 2D positions across piece counts in [2, 32].
    C output must equal Python output bit-for-bit on EVERY position."""
    counts = piece_count_distribution_2d(500, seed=20260509)
    mismatches: list = []
    for i, n in enumerate(counts):
        pos = random_pos_2d(n, seed=20260509 + i)
        py_out = encode_2d_pure_phase(pos)
        c_out = encode_pure_phase_2d_native(pos)
        if not np.array_equal(py_out, c_out):
            md = int(np.abs(
                py_out.astype(np.int64) - c_out.astype(np.int64)
            ).max())
            mismatches.append((i, n, md))
            if len(mismatches) >= 5:
                break
    assert mismatches == [], (
        f"{len(mismatches)} mismatches in random corpus; first 5: "
        f"{mismatches}"
    )


# ─── Determinism ────────────────────────────────────────────────────


@_skip_no_native
def test_c_native_2d_deterministic_across_calls():
    pos = _imbalanced()
    a = encode_pure_phase_2d_native(pos)
    b = encode_pure_phase_2d_native(pos)
    assert np.array_equal(a, b)
