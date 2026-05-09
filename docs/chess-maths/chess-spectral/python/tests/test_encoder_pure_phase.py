"""1.14.0 immolation: pure-phase encoder (B-spike-4).

The §20.15 acceptance gate for B-spike-4:
  * Cosine-sim with float baseline ≥ 99% on every position
  * Channel-energy ranking Spearman ρ ≥ 0.99

Tests:
  * Output shape + dtype contract (int32 from
    ``encode_2d_pure_phase``; float64 from
    ``encode_2d_pure_phase_to_float``).
  * D₄ channels (A1/A2/B1/B2/E) are bit-exact integer relative to
    ``encode_640(pos, vals=VALS)`` modulo the documented integer
    representation (the float baseline scales by ``dim_mu/8``;
    the int output scales by 1, dequantization recovers the
    float value).
  * Cosine-sim ≥ 99% across the representative corpus.
  * Channel-energy ranking Spearman ρ across positions ≥ 0.99.
  * Per-channel dequantization scales documented and applied.
  * Quantization tables loaded at module level; sanity-checked
    shapes + dtypes.
  * Empirical bench numbers are NOT locked in tests (CI machine
    variance). They live in §20.21 and the
    ``tests/bench_baselines/`` JSON files.
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

from chess_spectral import fen_to_pos, encode_640   # noqa: E402
from chess_spectral.tables import VALS, BOARD_DIM   # noqa: E402
from chess_spectral.encoder import ENCODING_DIM, CHANNELS   # noqa: E402
from chess_spectral.encoder_pure_phase import (   # noqa: E402
    encode_2d_pure_phase,
    encode_2d_pure_phase_to_float,
    CHANNEL_DEQUANT_SCALES,
    LOCAL_FIBER_3D_INT16,
    PAWN_ANTI_FIBER_INT16,
    DIAG_DEV_INT16,
    LOCAL_ADJ_ROWS_INT8,
)


_REPRESENTATIVE_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
    "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
    "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1",
    "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1",
]


# ─── Output contract ─────────────────────────────────────────────────


def test_immolation_pure_phase_int_shape_and_dtype():
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])
    out = encode_2d_pure_phase(pos)
    assert out.shape == (640,)
    assert out.dtype == np.int32


def test_immolation_pure_phase_float_shape_and_dtype():
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])
    out = encode_2d_pure_phase_to_float(pos)
    assert out.shape == (640,)
    assert out.dtype == np.float64


def test_immolation_dequant_scales_documented_for_all_channels():
    """Every channel name in CHANNELS has a dequantization scale
    in CHANNEL_DEQUANT_SCALES."""
    for name, _start in CHANNELS:
        assert name in CHANNEL_DEQUANT_SCALES
        assert CHANNEL_DEQUANT_SCALES[name] > 0


# ─── Quantized table contracts ──────────────────────────────────────


def test_immolation_local_adj_rows_int8_shape():
    """LOCAL_ADJ_ROWS_INT8 mirrors LOCAL_ADJ_ROWS — naturally 0/1
    integer; cast to int8 for memory + SIMD."""
    assert LOCAL_ADJ_ROWS_INT8.shape == (5, 64, 64)
    assert LOCAL_ADJ_ROWS_INT8.dtype == np.int8
    # 0/1 only.
    unique = np.unique(LOCAL_ADJ_ROWS_INT8)
    assert set(unique.tolist()).issubset({0, 1})


def test_immolation_local_fiber_3d_int16_shape():
    """LOCAL_FIBER_3D_INT16 has shape (5, 64, 3) int16."""
    assert LOCAL_FIBER_3D_INT16.shape == (5, 64, 3)
    assert LOCAL_FIBER_3D_INT16.dtype == np.int16


def test_immolation_pawn_anti_fiber_int16_shape():
    assert PAWN_ANTI_FIBER_INT16.shape == (64, 64)
    assert PAWN_ANTI_FIBER_INT16.dtype == np.int16


def test_immolation_diag_dev_int16_shape():
    assert DIAG_DEV_INT16.shape == (6, 64)
    assert DIAG_DEV_INT16.dtype == np.int16


# ─── §20.15 acceptance gate ─────────────────────────────────────────


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS)
def test_immolation_cosine_sim_with_float_baseline_above_99pct(fen):
    """**The acceptance gate.** For each FEN in the corpus:
    cosine_sim(encode_2d_pure_phase_to_float(pos),
               encode_640(pos, vals=VALS))  ≥ 0.99.

    Empirically observed: ≥ 0.99998 across the corpus. The 99%
    floor in §20.15 is conservative; we lock the much tighter
    0.999 here for regression detection.
    """
    pos = fen_to_pos(fen)
    baseline = encode_640(pos, vals=VALS)
    pure = encode_2d_pure_phase_to_float(pos)
    norm_b = float(np.linalg.norm(baseline))
    norm_p = float(np.linalg.norm(pure))
    if norm_b == 0.0:
        assert norm_p < 1e-6
        return
    cos_sim = float(np.dot(baseline, pure) / (norm_b * norm_p))
    assert cos_sim >= 0.999, (
        f"{fen}: cosine-sim {cos_sim:.6f} below 0.999 regression floor "
        f"(§20.15 acceptance gate is 0.99; this tighter bound is for "
        f"detecting regressions in the quantization tables)"
    )


def test_immolation_d4_channels_match_baseline_exactly():
    """The D₄ channels (A1/A2/B1/B2/E) are pure integer arithmetic
    over integer signals — they should be **bit-exact** relative to
    the float baseline modulo float-precision rounding."""
    pos = fen_to_pos(_REPRESENTATIVE_FENS[4])  # midgame
    baseline = encode_640(pos, vals=VALS)
    pure = encode_2d_pure_phase_to_float(pos)
    # D₄ channels span dims 0..320.
    np.testing.assert_allclose(
        pure[:320], baseline[:320],
        rtol=1e-12, atol=1e-12,
        err_msg="D₄ channels must be bit-exact (pure integer math)",
    )


def test_immolation_channel_energy_ranking_spearman_above_99pct():
    """**Acceptance gate part 2**: channel-energy ranking
    Spearman ρ ≥ 0.99 across the corpus.

    For each FEN, compute per-channel energies on baseline and on
    pure-phase. Then over all (fen, channel) pairs, compare the
    rank correlation. Implementation: collect (baseline_energy,
    pure_energy) pairs across all positions × channels, then
    compute Spearman ρ.
    """
    # Lazy import scipy — it's a test-time dep only.
    try:
        from scipy.stats import spearmanr
    except ImportError:
        pytest.skip("scipy not available")
    from chess_spectral.engine.eval.spectral import channel_energies
    baseline_energies: list[float] = []
    pure_energies: list[float] = []
    for fen in _REPRESENTATIVE_FENS:
        pos = fen_to_pos(fen)
        b = encode_640(pos, vals=VALS)
        p = encode_2d_pure_phase_to_float(pos)
        eb = channel_energies(b)
        ep = channel_energies(p)
        for name, val in eb.items():
            baseline_energies.append(val)
            pure_energies.append(ep[name])
    rho, _pval = spearmanr(baseline_energies, pure_energies)
    assert rho >= 0.99, (
        f"channel-energy ranking Spearman ρ = {rho:.4f} < 0.99 "
        f"acceptance threshold"
    )


# ─── Edge cases ──────────────────────────────────────────────────────


def test_immolation_empty_position():
    """An empty position (no pieces — synthetic, doesn't appear
    in real chess) should encode to all zeros."""
    out = encode_2d_pure_phase({})
    assert (out == 0).all()
    out_float = encode_2d_pure_phase_to_float({})
    assert (out_float == 0.0).all()


def test_immolation_single_piece_position():
    """Single white king at e1 — sanity check that the encoder
    runs without errors and produces nontrivial output."""
    pos = {60: "K"}  # encoder-format sq 60 = e1
    out = encode_2d_pure_phase(pos)
    out_float = encode_2d_pure_phase_to_float(pos)
    assert out.shape == (640,)
    assert (out != 0).any()
    assert (out_float != 0).any()


def test_immolation_int_path_returns_int32():
    """The integer-output entry point returns int32, not float."""
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])
    out = encode_2d_pure_phase(pos)
    assert out.dtype == np.int32
    # And the float-output entry point returns float64.
    out_float = encode_2d_pure_phase_to_float(pos)
    assert out_float.dtype == np.float64


# ─── Determinism ─────────────────────────────────────────────────────


def test_immolation_deterministic_across_calls():
    """Calling encode_2d_pure_phase twice on the same input gives
    bit-exact identical results."""
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])
    a = encode_2d_pure_phase(pos)
    b = encode_2d_pure_phase(pos)
    np.testing.assert_array_equal(a, b)


def test_immolation_str_keyed_pos_dict():
    """NDJSON-style str-keyed pos dict accepted (via
    normalize_pos)."""
    pos_int = fen_to_pos(_REPRESENTATIVE_FENS[0])
    pos_str = {str(k): v for k, v in pos_int.items()}
    out_int = encode_2d_pure_phase(pos_int)
    out_str = encode_2d_pure_phase(pos_str)
    np.testing.assert_array_equal(out_int, out_str)
