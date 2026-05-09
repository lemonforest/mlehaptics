"""1.15.0 immolation: 4D pure-phase encoder (B-spike-4 4D parity).

The 4D analog of ``test_encoder_pure_phase.py``. Mirrors §20.15's
acceptance gate for the 4D pure-phase encoder shipped in 1.15.0:

  * Cosine-sim with ``encode_4d(pos4, vals=PIECE_VALUES_4D)`` baseline
    ≥ 99% on every position.
  * A_1 channel: bit-exact (P_A1 × 384 is lossless).
  * STD4 channels: bit-exact (coord_resid × 4 is lossless).
  * Channel-energy ranking Spearman ρ ≥ 0.99.

Tests:
  * Output shape + dtype contract (int32 / float64).
  * Quantized table contracts (int16 shapes, int8 coord_resid).
  * Lossless channels bit-exact relative to the float baseline.
  * Cosine-sim ≥ 99.9% across the representative corpus.
  * Channel-energy ranking Spearman ρ ≥ 0.99.
  * Per-channel dequantization scales documented for all 11 channels.
  * Edge cases: empty position, single-piece, str-keyed pos dict,
    determinism.
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
    encode_4d, channel_energies_4d,
    PIECE_VALUES_4D, CHANNELS_4D, CHANNEL_DIM, ENCODING_DIM_4D,
)
from chess_spectral.encoder_pure_phase_4d import (   # noqa: E402
    encode_4d_pure_phase,
    encode_4d_pure_phase_to_float,
    CHANNEL_DEQUANT_SCALES_4D,
    _ensure_dequant_scales,
    _build_quant_tables,
    _VALS_INT_SCALE_4D,
)


def _imbalanced_position():
    """Asymmetric mid-board 6-piece position with nonzero A_1 channel
    and exercises STD4 + FIB_SYM + FD_DIAG (no pawns)."""
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _full_channel_position():
    """Mid-board 14-piece position exercising every channel including
    pawns on both axes (FA_PAWN_W and FA_PAWN_Y both nonzero)."""
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


def _sparse_endgame_position():
    """KvK + queen — minimal nontrivial endgame, exercises A_1 + STD4
    + FD_DIAG cleanly."""
    coords = {
        (1, 1, 1, 1): 'K',
        (6, 6, 6, 6): 'k',
        (3, 3, 3, 3): 'Q',
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _asymmetric_white_advantage():
    """Material-advantage white position (heavy white, light black) —
    breaks the central-inversion antisymmetry that zeroes out the A_1
    channel in symmetric positions."""
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
        (5, 4, 3, 2): 'R',  # extra white rook
        (6, 4, 2, 1): 'B',  # extra white bishop
        (1, 1, 1, 2): ('P', 'w'), (2, 2, 1, 2): ('P', 'w'),
        (1, 2, 1, 1): ('P', 'y'),
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


def _opening_dense():
    """Opening-style dense position with all piece types and several
    pawns on both axes."""
    coords = {
        (0, 0, 0, 0): 'K', (7, 0, 0, 0): 'R', (0, 0, 0, 7): 'R',
        (1, 0, 0, 0): 'N', (0, 0, 0, 1): 'N',
        (2, 0, 0, 0): 'B', (0, 0, 0, 2): 'B',
        (3, 0, 0, 0): 'Q',
        (1, 1, 0, 0): ('P', 'w'), (2, 1, 0, 0): ('P', 'w'),
        (3, 1, 0, 0): ('P', 'w'), (4, 1, 0, 0): ('P', 'w'),
        (0, 1, 1, 0): ('P', 'y'), (0, 1, 2, 0): ('P', 'y'),
        (7, 7, 7, 7): 'k', (0, 7, 7, 7): 'r', (7, 7, 7, 0): 'r',
        (6, 7, 7, 7): 'n', (7, 7, 7, 6): 'n',
        (5, 7, 7, 7): 'b', (7, 7, 7, 5): 'b',
        (4, 7, 7, 7): 'q',
        (6, 6, 7, 7): ('p', 'w'), (5, 6, 7, 7): ('p', 'w'),
        (4, 6, 7, 7): ('p', 'w'),
        (7, 6, 6, 7): ('p', 'y'), (7, 6, 5, 7): ('p', 'y'),
    }
    return {t4.sq4(*c): p for c, p in coords.items()}


_REPRESENTATIVE_POSITIONS = [
    ('imbalanced',          _imbalanced_position),
    ('full_channel',        _full_channel_position),
    ('sparse_endgame',      _sparse_endgame_position),
    ('asymmetric_white_adv', _asymmetric_white_advantage),
    ('opening_dense',       _opening_dense),
]


# ─── Output contract ────────────────────────────────────────────────


def test_immolation_4d_pure_phase_int_shape_and_dtype():
    pos4 = _imbalanced_position()
    out = encode_4d_pure_phase(pos4)
    assert out.shape == (45056,)
    assert out.dtype == np.int32


def test_immolation_4d_pure_phase_float_shape_and_dtype():
    pos4 = _imbalanced_position()
    out = encode_4d_pure_phase_to_float(pos4)
    assert out.shape == (45056,)
    assert out.dtype == np.float64


def test_immolation_4d_dequant_scales_documented_for_all_channels():
    """Every channel name in CHANNELS_4D has a dequantization scale
    in CHANNEL_DEQUANT_SCALES_4D, and every scale is positive."""
    _ensure_dequant_scales()
    for name, _start in CHANNELS_4D:
        assert name in CHANNEL_DEQUANT_SCALES_4D, (
            f"channel {name} missing from CHANNEL_DEQUANT_SCALES_4D"
        )
        assert CHANNEL_DEQUANT_SCALES_4D[name] > 0, (
            f"channel {name} scale {CHANNEL_DEQUANT_SCALES_4D[name]} ≤ 0"
        )


def test_immolation_4d_vals_int_scale_handles_all_pieces():
    """``_VALS_INT_SCALE_4D`` (=4) handles every entry in
    ``PIECE_VALUES_4D`` losslessly."""
    for k, v in PIECE_VALUES_4D.items():
        scaled = v * _VALS_INT_SCALE_4D
        assert int(scaled) == scaled, (
            f"PIECE_VALUES_4D[{k!r}] = {v} not exactly representable as "
            f"integer × {_VALS_INT_SCALE_4D}; bishop is the test case "
            f"(B=3.25 needs scale 4)"
        )


# ─── Quantized table contracts ──────────────────────────────────────


def test_immolation_4d_quant_tables_loaded_with_correct_shapes():
    qt = _build_quant_tables()
    # P_A1: sparse 4096×4096 with int data.
    P_A1_INT = qt['P_A1_INT']
    assert P_A1_INT.shape == (4096, 4096)
    # coord_resid: (4, 4096) int8.
    cr = qt['coord_resid_int8']
    assert cr.shape == (4, 4096)
    assert cr.dtype == np.int8
    # FIBER_LOCAL: (5, 4096, 3) int16.
    fl = qt['FIBER_LOCAL_INT16']
    assert fl.shape == (5, 4096, 3)
    assert fl.dtype == np.int16
    # W_ANTI_DCT and Y_ANTI_DCT: 8×8 int16.
    w = qt['W_ANTI_DCT_INT16']
    y = qt['Y_ANTI_DCT_INT16']
    assert w.shape == (8, 8)
    assert y.shape == (8, 8)
    assert w.dtype == np.int16
    assert y.dtype == np.int16
    # DIAG_DEV: (6, 4096) int16.
    dd = qt['DIAG_DEV_INT16']
    assert dd.shape == (6, 4096)
    assert dd.dtype == np.int16


def test_immolation_4d_p_a1_int_entries_are_divisors_of_384():
    """Every P_A1 orbit has size dividing 384, so every nonzero entry
    of the integer projector is 384/orbit_size — a divisor of 384."""
    qt = _build_quant_tables()
    P_A1_INT = qt['P_A1_INT']
    nonzero_data = P_A1_INT.data[P_A1_INT.data != 0]
    # Set of values must all divide 384.
    divisors_384 = {d for d in range(1, 385) if 384 % d == 0}
    actual_values = set(int(v) for v in nonzero_data)
    assert actual_values.issubset(divisors_384), (
        f"P_A1_INT contains entries not dividing 384: "
        f"{actual_values - divisors_384}"
    )


def test_immolation_4d_coord_resid_int8_within_int8_range():
    qt = _build_quant_tables()
    cr = qt['coord_resid_int8']
    assert cr.min() >= -128
    assert cr.max() <= 127
    # Empirical envelope is [-21, 21] on the standard 8^4 lattice.
    assert cr.min() == -21
    assert cr.max() == 21


# ─── §20.15 acceptance gate (4D) ────────────────────────────────────


@pytest.mark.parametrize(
    "name", [n for n, _ in _REPRESENTATIVE_POSITIONS]
)
def test_immolation_4d_cosine_sim_with_float_baseline_above_999pct(name):
    """**The acceptance gate.** For each representative 4D position:
    cosine_sim(encode_4d_pure_phase_to_float(pos4),
               encode_4d(pos4, vals=PIECE_VALUES_4D)) ≥ 0.999.

    The §20.15 floor is 0.99; we lock the much tighter 0.999 here for
    regression detection. Empirically observed on the corpus:
    1.0 within float-rounding for active channels.
    """
    pos4 = dict(
        next(f for n, f in _REPRESENTATIVE_POSITIONS if n == name)()
    )
    baseline = encode_4d(pos4, vals=PIECE_VALUES_4D)
    pure = encode_4d_pure_phase_to_float(pos4)
    norm_b = float(np.linalg.norm(baseline))
    norm_p = float(np.linalg.norm(pure))
    if norm_b == 0.0:
        assert norm_p < 1e-6
        return
    cos_sim = float(np.dot(baseline.astype(np.float64), pure) / (norm_b * norm_p))
    assert cos_sim >= 0.999, (
        f"{name}: 4D cosine-sim {cos_sim:.6f} below 0.999 regression "
        f"floor (§20.15 acceptance gate is 0.99)"
    )


def test_immolation_4d_a1_channel_bit_exact():
    """The A_1 channel is pure-integer arithmetic (P_A1_INT @ sig_int)
    so it should be **bit-exact** after dequantization, modulo the
    float baseline's float64-vs-float32 rounding."""
    pos4 = _imbalanced_position()
    baseline = encode_4d(pos4, vals=PIECE_VALUES_4D)
    pure = encode_4d_pure_phase_to_float(pos4)
    a1_baseline = baseline[0:CHANNEL_DIM].astype(np.float64)
    a1_pure = pure[0:CHANNEL_DIM]
    np.testing.assert_allclose(
        a1_pure, a1_baseline, rtol=1e-6, atol=1e-6,
        err_msg="A_1 channel must be bit-exact (lossless × 384 scaling)",
    )


def test_immolation_4d_std4_channels_bit_exact():
    """STD4_X/Y/Z/W are coord_resid × sig elementwise, both losslessly
    integer-scaled. Must be bit-exact after dequantization."""
    pos4 = _full_channel_position()
    baseline = encode_4d(pos4, vals=PIECE_VALUES_4D)
    pure = encode_4d_pure_phase_to_float(pos4)
    for axis_idx, axis in enumerate('XYZW'):
        start = (1 + axis_idx) * CHANNEL_DIM
        end = start + CHANNEL_DIM
        b = baseline[start:end].astype(np.float64)
        p = pure[start:end]
        np.testing.assert_allclose(
            p, b, rtol=1e-6, atol=1e-6,
            err_msg=(
                f"STD4_{axis} channel must be bit-exact "
                f"(lossless coord_resid × 4 scaling)"
            ),
        )


def test_immolation_4d_channel_energy_ranking_spearman_above_99pct():
    """Channel-energy ranking Spearman ρ ≥ 0.99 across the corpus."""
    try:
        from scipy.stats import spearmanr
    except ImportError:
        pytest.skip("scipy not available")
    baseline_energies: list[float] = []
    pure_energies: list[float] = []
    for _, pos_factory in _REPRESENTATIVE_POSITIONS:
        pos4 = pos_factory()
        b = encode_4d(pos4, vals=PIECE_VALUES_4D)
        p = encode_4d_pure_phase_to_float(pos4)
        eb = channel_energies_4d(b)
        ep = channel_energies_4d(p.astype(np.float32))
        for name in eb:
            baseline_energies.append(eb[name])
            pure_energies.append(ep[name])
    rho, _ = spearmanr(baseline_energies, pure_energies)
    assert rho >= 0.99, (
        f"4D channel-energy Spearman ρ = {rho:.6f} < 0.99 acceptance"
    )


# ─── Edge cases ─────────────────────────────────────────────────────


def test_immolation_4d_empty_position():
    """Empty position → all zeros."""
    out = encode_4d_pure_phase({})
    assert (out == 0).all()
    out_float = encode_4d_pure_phase_to_float({})
    assert (out_float == 0.0).all()


def test_immolation_4d_single_piece_position():
    """Single white king — sanity check that encoder runs and produces
    nontrivial output."""
    pos4 = {t4.sq4(3, 4, 5, 6): 'K'}
    out = encode_4d_pure_phase(pos4)
    out_float = encode_4d_pure_phase_to_float(pos4)
    assert out.shape == (45056,)
    assert (out != 0).any()
    assert (out_float != 0).any()


def test_immolation_4d_int_path_returns_int32():
    pos4 = _imbalanced_position()
    out = encode_4d_pure_phase(pos4)
    assert out.dtype == np.int32
    out_float = encode_4d_pure_phase_to_float(pos4)
    assert out_float.dtype == np.float64


# ─── Determinism + str-keyed pos dict ───────────────────────────────


def test_immolation_4d_deterministic_across_calls():
    pos4 = _imbalanced_position()
    a = encode_4d_pure_phase(pos4)
    b = encode_4d_pure_phase(pos4)
    np.testing.assert_array_equal(a, b)


def test_immolation_4d_str_keyed_pos_dict():
    """NDJSON-style str-keyed pos dict accepted (board_signal_4d's
    int(k) cast handles either int or str keys)."""
    pos_int = _imbalanced_position()
    pos_str = {str(k): v for k, v in pos_int.items()}
    out_int = encode_4d_pure_phase(pos_int)
    out_str = encode_4d_pure_phase(pos_str)
    np.testing.assert_array_equal(out_int, out_str)


def test_immolation_4d_legacy_pawn_str_value_supported():
    """Legacy single-char pawn values 'P'/'p' (without explicit axis)
    still work and default to W-axis (matches v1.0 behavior)."""
    import warnings
    pos4 = {t4.sq4(0, 1, 0, 1): 'P', t4.sq4(7, 6, 7, 6): 'p'}
    with warnings.catch_warnings():
        # Silence the DeprecationWarning expected from _pawn_axis.
        warnings.simplefilter("ignore", DeprecationWarning)
        out = encode_4d_pure_phase(pos4)
    assert out.shape == (45056,)
    # FA_PAWN_W channel should be nonzero (pawns route to W-axis by default).
    fa_w_start = 8 * CHANNEL_DIM
    fa_w_end = 9 * CHANNEL_DIM
    assert (out[fa_w_start:fa_w_end] != 0).any()
