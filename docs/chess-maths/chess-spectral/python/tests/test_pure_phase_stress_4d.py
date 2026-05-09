"""Pedantic non-deterministic stress test for the 4D pure-phase
encoder (1.15.0+).

Mirrors the 1.14.0 2D stress test
(:mod:`tests.test_pure_phase_stress_2d`) and the 1.14.0 4D hybrid-
evaluator stress test (:mod:`tests.test_spectral_hybrid_4d_stress`).
The 1.14.0 2D ship's amendment 1 introduced this stress-test
methodology to address the user's critical feedback that the
hand-picked corpus methodology was unprincipled. This 1.15.0
addition extends that discipline to the 4D pure-phase encoder.

Methodology
-----------

500 random 4D positions (matching the 4D hybrid stress test's corpus
size — the 4D encoder is ~10× more expensive per call than 2D, so
1000 positions would be unnecessarily slow) sampled across piece
counts in [2, 256]. Each position generated with seeded RNG; corpus
reproducible.

Stress assertions
-----------------

  * Per-position cosine-sim with ``encode_4d(pos4, vals=PIECE_VALUES_4D)``
    ≥ 0.99 (matches the §20.15 acceptance gate)
  * Median cosine-sim across the corpus ≥ 0.999
  * A_1 channel: bit-exact (within float64 round-off) on every position
  * STD4 channels: bit-exact on every position
  * Channel-energy ranking Spearman ρ across all (pos, channel) pairs
    ≥ 0.99
  * No NaN / Inf in int32 output
  * int32 output bounded (max abs < 2³⁰; gives ~2× safety margin
    on the worst-case dense king-only-style position)
  * Determinism across calls
  * Corpus reproducibility across calls
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

from chess_spectral.encoder_4d import (   # noqa: E402
    encode_4d, channel_energies_4d,
    PIECE_VALUES_4D, CHANNELS_4D, CHANNEL_DIM,
)
from chess_spectral.encoder_pure_phase_4d import (   # noqa: E402
    encode_4d_pure_phase,
    encode_4d_pure_phase_to_float,
)

from tests._random_positions import (   # noqa: E402
    random_pos_4d, piece_count_distribution_4d,
)


N_STRESS_POSITIONS_4D: int = 500
_ROOT_SEED: int = 20260509


def _generate_4d_corpus(n: int, seed_offset: int) -> list:
    counts = piece_count_distribution_4d(
        n, seed=_ROOT_SEED + seed_offset)
    positions = [
        random_pos_4d(c, seed=_ROOT_SEED + seed_offset + 1 + i)
        for i, c in enumerate(counts)
    ]
    return positions


# ─── Cosine-sim acceptance gate at scale ────────────────────────────


def test_stress_4d_pure_phase_cosine_sim_each_position_above_99pct():
    """Per-position cosine-sim with the float baseline ≥ 0.99 — the
    §20.15 acceptance floor — on every single position in the random
    corpus. No exceptions."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=200)
    failures: list = []
    for i, pos4 in enumerate(positions):
        baseline = encode_4d(pos4, vals=PIECE_VALUES_4D).astype(np.float64)
        pure = encode_4d_pure_phase_to_float(pos4)
        norm_b = float(np.linalg.norm(baseline))
        norm_p = float(np.linalg.norm(pure))
        if norm_b == 0.0:
            if norm_p > 1e-6:
                failures.append((i, len(pos4), 'baseline=0 but pure nonzero'))
            continue
        cs = float(np.dot(baseline, pure) / (norm_b * norm_p))
        if cs < 0.99:
            failures.append((i, len(pos4), cs))
    if failures:
        msg = (
            f"{len(failures)} positions failed the 0.99 cosine-sim floor."
            f" First 5:\n"
        )
        for f in failures[:5]:
            msg += f"  pos[{f[0]}] (n={f[1]}): {f[2]}\n"
        pytest.fail(msg)


def test_stress_4d_pure_phase_median_cosine_sim_above_999pct():
    """Median cosine-sim across the corpus ≥ 0.999 — tighter
    statistical floor on top of the per-position 0.99 floor."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=210)
    sims: list = []
    for pos4 in positions:
        baseline = encode_4d(pos4, vals=PIECE_VALUES_4D).astype(np.float64)
        pure = encode_4d_pure_phase_to_float(pos4)
        norm_b = float(np.linalg.norm(baseline))
        norm_p = float(np.linalg.norm(pure))
        if norm_b == 0.0:
            continue  # skip degenerate
        sims.append(float(np.dot(baseline, pure) / (norm_b * norm_p)))
    median = float(np.median(sims))
    assert median >= 0.999, (
        f"median cosine-sim {median:.6f} < 0.999 across "
        f"{len(sims)} non-degenerate positions"
    )


# ─── Bit-exact A_1 + STD4 channels ──────────────────────────────────


def test_stress_4d_pure_phase_a1_bit_exact_at_scale():
    """The A_1 channel uses purely-integer arithmetic (P_A1 × 384 is
    lossless) so it must be bit-exact (within float64 rounding) on
    EVERY position."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=220)
    failures = 0
    for pos4 in positions:
        baseline = encode_4d(pos4, vals=PIECE_VALUES_4D)
        pure = encode_4d_pure_phase_to_float(pos4)
        a1_b = baseline[0:CHANNEL_DIM].astype(np.float64)
        a1_p = pure[0:CHANNEL_DIM]
        # Allow rtol=1e-5 because float64 vs float32 in baseline.
        if not np.allclose(a1_p, a1_b, rtol=1e-5, atol=1e-5):
            failures += 1
    assert failures == 0, (
        f"{failures} positions had non-bit-exact A_1 channels at scale"
    )


def test_stress_4d_pure_phase_std4_bit_exact_at_scale():
    """STD4 channels use coord_resid × sig elementwise (both losslessly
    integer-scaled), so must be bit-exact on every position."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=230)
    failures: list = []
    for i, pos4 in enumerate(positions):
        baseline = encode_4d(pos4, vals=PIECE_VALUES_4D)
        pure = encode_4d_pure_phase_to_float(pos4)
        for axis_idx, axis in enumerate('XYZW'):
            start = (1 + axis_idx) * CHANNEL_DIM
            end = start + CHANNEL_DIM
            b = baseline[start:end].astype(np.float64)
            p = pure[start:end]
            if not np.allclose(p, b, rtol=1e-5, atol=1e-5):
                failures.append((i, axis))
    if failures:
        pytest.fail(
            f"{len(failures)} (position, axis) pairs had non-bit-exact "
            f"STD4 channels. First 3: {failures[:3]}"
        )


# ─── Spearman ρ on channel-energy ranking at scale ──────────────────


def test_stress_4d_pure_phase_channel_energy_spearman_at_scale():
    """Channel-energy ranking Spearman ρ ≥ 0.99 across all
    (position, channel) pairs in the random 4D corpus."""
    try:
        from scipy.stats import spearmanr
    except ImportError:
        pytest.skip("scipy not available")
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=240)
    baseline_energies: list = []
    pure_energies: list = []
    for pos4 in positions:
        b = encode_4d(pos4, vals=PIECE_VALUES_4D)
        if np.linalg.norm(b) == 0.0:
            continue
        p = encode_4d_pure_phase_to_float(pos4)
        eb = channel_energies_4d(b)
        ep = channel_energies_4d(p.astype(np.float32))
        for name in eb:
            baseline_energies.append(eb[name])
            pure_energies.append(ep[name])
    rho, _ = spearmanr(baseline_energies, pure_energies)
    assert rho >= 0.99, (
        f"4D pure-phase channel-energy Spearman ρ = {rho:.6f} < 0.99 "
        f"across {len(baseline_energies)} (pos, channel) pairs"
    )


# ─── Output integrity ───────────────────────────────────────────────


def test_stress_4d_pure_phase_no_nan_or_inf():
    """int32 output must be NaN/Inf-free (well, integers can't be NaN
    in int representation; but the dequantized float64 output must
    be NaN/Inf-free too)."""
    positions = _generate_4d_corpus(
        N_STRESS_POSITIONS_4D // 2, seed_offset=250)
    for i, pos4 in enumerate(positions):
        int_out = encode_4d_pure_phase(pos4)
        float_out = encode_4d_pure_phase_to_float(pos4)
        assert int_out.dtype == np.int32
        assert float_out.dtype == np.float64
        assert np.all(np.isfinite(float_out)), (
            f"pos[{i}] (n={len(pos4)}): NaN/Inf in dequantized output"
        )


def test_stress_4d_pure_phase_int32_bounded():
    """int32 output should stay well within int32's [-2³¹, 2³¹) range.
    Acceptance: max |int_out| < 2³⁰ (50% safety margin) — at the
    typical 250-piece position, FIB_SYM accumulators reach ~1e9."""
    positions = _generate_4d_corpus(
        N_STRESS_POSITIONS_4D // 2, seed_offset=260)
    INT30 = 1 << 30
    overflow_count = 0
    max_abs = 0
    for pos4 in positions:
        out = encode_4d_pure_phase(pos4)
        m = int(np.abs(out).max())
        if m > max_abs:
            max_abs = m
        if m >= INT30:
            overflow_count += 1
    assert overflow_count == 0, (
        f"{overflow_count} positions had |int_out| ≥ 2³⁰. "
        f"max observed: {max_abs}"
    )


# ─── Determinism + corpus reproducibility ───────────────────────────


def test_stress_4d_pure_phase_random_corpus_reproducible():
    """Same seed → same 4D pure-phase corpus and outputs."""
    a = _generate_4d_corpus(50, seed_offset=270)
    b = _generate_4d_corpus(50, seed_offset=270)
    assert len(a) == len(b)
    for pos_a, pos_b in zip(a, b):
        assert pos_a == pos_b
        out_a = encode_4d_pure_phase(pos_a)
        out_b = encode_4d_pure_phase(pos_b)
        np.testing.assert_array_equal(out_a, out_b)
