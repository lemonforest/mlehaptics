"""C↔Python parity tests for the pure-phase 4D encoder (1.18.0+).

Verifies bit-exact equivalence between
:func:`chess_spectral.encoder_pure_phase_4d.encode_4d_pure_phase` (the
Python reference) and the native C implementation in
:mod:`chess_spectral._native_pure_phase_4d` (the C port shipped in
1.18.0).

Tolerance is **zero** (np.array_equal): both sides do integer
arithmetic only, so any bit-level disagreement signals a bug.

Three layers:

  * **Hand-crafted positions** — 5 representative positions exercising
    every channel including pawns on both axes.
  * **Pedantic random corpus** — 500 random 4D positions across piece
    counts in [2, 256] (mirrors test_pure_phase_stress_4d.py).
  * **Edge cases** — empty position, single piece, all-pawn variants.

Skips entirely when the native library isn't loadable (sdist install,
Pyodide WASM, etc.); the Python implementation is the correctness
reference and remains the only path in those environments.
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

from chess_spectral import tables_4d as t4   # noqa: E402
from chess_spectral.encoder_4d import (   # noqa: E402
    CHANNELS_4D, CHANNEL_DIM,
)
from chess_spectral.encoder_pure_phase_4d import (   # noqa: E402
    encode_4d_pure_phase,
)
from chess_spectral._native_pure_phase_4d import (   # noqa: E402
    HAS_NATIVE_PURE_PHASE, encode_pure_phase_4d_native,
)

from tests._random_positions import (   # noqa: E402
    random_pos_4d, piece_count_distribution_4d,
)


_skip_no_native = pytest.mark.skipif(
    not HAS_NATIVE_PURE_PHASE,
    reason="native cs_encoder_pure_phase_4d library not loaded; "
    "expected when building sdist without C toolchain.",
)


# ─── Hand-crafted positions covering every channel ──────────────────


def _imbalanced():
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _full_channel():
    coords = {
        (0, 0, 0, 0): 'K', (7, 7, 7, 7): 'k',
        (1, 2, 3, 4): 'Q', (6, 5, 4, 3): 'q',
        (3, 1, 2, 3): 'B', (4, 6, 5, 4): 'b',
        (2, 5, 0, 1): 'N', (5, 2, 7, 6): 'n',
        (4, 3, 1, 2): 'R', (3, 4, 6, 5): 'r',
        (0, 1, 0, 1): ('P', 'w'), (7, 6, 7, 6): ('p', 'w'),
        (0, 1, 0, 0): ('P', 'y'), (7, 6, 7, 7): ('p', 'y'),
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _sparse_endgame():
    coords = {
        (1, 1, 1, 1): 'K', (6, 6, 6, 6): 'k', (3, 3, 3, 3): 'Q',
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _y_axis_pawns_only():
    """Positions with only Y-axis pawns exercise FA_PAWN_Y in
    isolation (FA_PAWN_W stays zero)."""
    coords = {
        (0, 0, 0, 0): 'K', (7, 7, 7, 7): 'k',
        (3, 1, 0, 0): ('P', 'y'), (4, 6, 7, 7): ('p', 'y'),
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _w_axis_pawns_only():
    """Positions with only W-axis pawns exercise FA_PAWN_W in
    isolation (FA_PAWN_Y stays zero)."""
    coords = {
        (0, 0, 0, 0): 'K', (7, 7, 7, 7): 'k',
        (3, 0, 0, 1): ('P', 'w'), (4, 7, 7, 6): ('p', 'w'),
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


_REPRESENTATIVE_POSITIONS = [
    ('imbalanced',          _imbalanced),
    ('full_channel',        _full_channel),
    ('sparse_endgame',      _sparse_endgame),
    ('y_axis_pawns_only',   _y_axis_pawns_only),
    ('w_axis_pawns_only',   _w_axis_pawns_only),
]


# ─── Hand-crafted parity tests ──────────────────────────────────────


@_skip_no_native
@pytest.mark.parametrize(
    "name", [n for n, _ in _REPRESENTATIVE_POSITIONS]
)
def test_c_py_parity_representative_position_bit_exact(name):
    """C output matches Python output exactly on every representative
    position. Tolerance is zero — both are integer arithmetic."""
    pos_factory = next(
        f for n, f in _REPRESENTATIVE_POSITIONS if n == name
    )
    pos4 = pos_factory()
    py_out = encode_4d_pure_phase(pos4)
    c_out = encode_pure_phase_4d_native(pos4)
    assert py_out.shape == c_out.shape == (45_056,)
    assert py_out.dtype == c_out.dtype == np.int32
    if not np.array_equal(py_out, c_out):
        # Diagnostic: per-channel diff breakdown.
        per_channel = []
        for chan_name, start in CHANNELS_4D:
            end = start + CHANNEL_DIM
            n_diff = int((py_out[start:end] != c_out[start:end]).sum())
            if n_diff > 0:
                md = int(np.abs(
                    py_out[start:end].astype(np.int64)
                    - c_out[start:end].astype(np.int64)
                ).max())
                per_channel.append(f"{chan_name}: {n_diff} diffs, max |Δ|={md}")
        pytest.fail(
            f"{name}: C/Python mismatch — "
            f"{', '.join(per_channel) if per_channel else 'unspecified'}"
        )


# ─── Edge cases ─────────────────────────────────────────────────────


@_skip_no_native
def test_c_py_parity_empty_position():
    py_out = encode_4d_pure_phase({})
    c_out = encode_pure_phase_4d_native({})
    assert (py_out == 0).all()
    assert (c_out == 0).all()
    assert np.array_equal(py_out, c_out)


@_skip_no_native
def test_c_py_parity_single_piece():
    pos4 = {t4.sq4(3, 4, 5, 6): 'K'}
    assert np.array_equal(
        encode_4d_pure_phase(pos4),
        encode_pure_phase_4d_native(pos4),
    )


@_skip_no_native
def test_c_py_parity_legacy_pawn_str_value():
    """Legacy single-char pawn 'P' / 'p' (no axis tuple) defaults to
    W-axis on both sides."""
    import warnings
    pos4 = {t4.sq4(0, 1, 0, 1): 'P', t4.sq4(7, 6, 7, 6): 'p'}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        py_out = encode_4d_pure_phase(pos4)
    c_out = encode_pure_phase_4d_native(pos4)
    assert np.array_equal(py_out, c_out)


# ─── Pedantic random corpus ─────────────────────────────────────────


@_skip_no_native
def test_c_py_parity_random_corpus_500_positions_bit_exact():
    """500 random 4D positions across piece counts in [2, 256].
    C output must equal Python output bit-for-bit on EVERY position."""
    counts = piece_count_distribution_4d(500, seed=20260509)
    mismatches: list = []
    for i, n in enumerate(counts):
        pos4 = random_pos_4d(n, seed=20260509 + i)
        py_out = encode_4d_pure_phase(pos4)
        c_out = encode_pure_phase_4d_native(pos4)
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
def test_c_native_deterministic_across_calls():
    pos4 = _imbalanced()
    a = encode_pure_phase_4d_native(pos4)
    b = encode_pure_phase_4d_native(pos4)
    assert np.array_equal(a, b)
