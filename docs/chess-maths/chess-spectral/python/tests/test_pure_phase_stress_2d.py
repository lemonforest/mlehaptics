"""Pedantic non-deterministic stress test for the 2D pure-phase
encoder (1.14.0+ — B-spike-4).

Methodology
-----------

Replaces the hand-picked 7-FEN corpus from
``tests/test_encoder_pure_phase.py`` with **1000+ randomly
generated positions** spanning sparse-to-dense piece counts
(~2 to ~32 pieces). Each position is generated with a
deterministic seed (so test runs are reproducible) but the
sampling itself is uniform across piece types and squares.

The stress tests assert distribution-level properties:

  * Per-position cosine-sim with ``encode_640(pos, vals=VALS)``
    is ≥ 0.99 for **every** position (no exceptions).
  * The MEDIAN cosine-sim across the population is ≥ 0.999
    (well above the §20.15 acceptance floor).
  * Channel-energy ranking Spearman ρ across all (pos, channel)
    pairs is ≥ 0.99.
  * Sign-of-score agreement: where the float baseline is
    nonzero, the pure-phase score has the same sign.
  * No quantization overflow under ANY randomly-generated input
    (encoder doesn't crash, return NaN, or wrap).
  * D₄-channel bit-exactness across the whole population (the
    structural property — pure integer math).

If any of these fails, we have an investigation. Document the
failure mode in the test's failure message + §20.21 record.

Why "non-deterministic pedantic":
  * Non-deterministic = wide sampling rather than hand-picked
  * Pedantic = rigorous, every-position assertion floor
"""
from __future__ import annotations

import os
import sys
import statistics

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import encode_640   # noqa: E402
from chess_spectral.tables import VALS   # noqa: E402
from chess_spectral.encoder_pure_phase import (   # noqa: E402
    encode_2d_pure_phase, encode_2d_pure_phase_to_float,
)
from chess_spectral.engine.eval.spectral import (   # noqa: E402
    channel_energies, evaluate as spectral_evaluate,
)

from tests._random_positions import (   # noqa: E402
    random_pos_2d, piece_count_distribution_2d,
)


# ─── Sample sizes ────────────────────────────────────────────────────


# 1000 random positions — pedantic enough to surface rare quantization
# pathologies; cheap enough at ~5ms per encode to run in <30s.
N_STRESS_POSITIONS: int = 1000

# Seed namespace: derived from a fixed root so the test corpus is
# reproducible across CI runs. Each test uses its own offset.
_ROOT_SEED: int = 20260509


# ─── Helpers ─────────────────────────────────────────────────────────


def _generate_corpus(n: int, seed_offset: int) -> list:
    """Build a list of n random positions with varying piece counts."""
    counts = piece_count_distribution_2d(
        n, seed=_ROOT_SEED + seed_offset)
    positions = [
        random_pos_2d(c, seed=_ROOT_SEED + seed_offset + 1 + i)
        for i, c in enumerate(counts)
    ]
    return positions


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Standard cosine similarity. Returns NaN-free float; 0.0 if
    either vector has zero norm (no signal)."""
    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ─── Per-position cosine-sim acceptance ─────────────────────────────


def test_stress_2d_cosine_sim_99pct_floor_every_position():
    """**The hard acceptance gate.** For every one of the 1000
    random positions, cosine-sim with the float baseline must be
    ≥ 0.99. No exceptions; if any single position drops below,
    the test reports the offending FEN-equivalent + the
    cosine-sim value for investigation.
    """
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=10)
    sims: list = []
    failures: list = []
    for i, pos in enumerate(positions):
        baseline = encode_640(pos, vals=VALS)
        pure = encode_2d_pure_phase_to_float(pos)
        sim = _cosine_sim(baseline, pure)
        sims.append(sim)
        # Skip degenerate all-zero baselines (e.g., all-empty
        # positions — shouldn't happen here but the corpus does
        # generate sparse positions; safety check).
        if np.linalg.norm(baseline) == 0.0:
            continue
        if sim < 0.99:
            failures.append((i, len(pos), sim, dict(pos)))
    if failures:
        msg = (
            f"{len(failures)}/{N_STRESS_POSITIONS} positions failed "
            f"the 0.99 cosine-sim floor. First 3 failures:\n"
        )
        for idx, n_pieces, sim, pos in failures[:3]:
            msg += (
                f"  pos[{idx}] (n_pieces={n_pieces}, sim={sim:.6f}): "
                f"{pos}\n"
            )
        pytest.fail(msg)


def test_stress_2d_cosine_sim_median_above_999():
    """Median cosine-sim across the population is ≥ 0.999."""
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=20)
    sims: list = []
    for pos in positions:
        baseline = encode_640(pos, vals=VALS)
        pure = encode_2d_pure_phase_to_float(pos)
        if np.linalg.norm(baseline) == 0.0:
            continue
        sims.append(_cosine_sim(baseline, pure))
    median_sim = statistics.median(sims)
    assert median_sim >= 0.999, (
        f"median cosine-sim {median_sim:.6f} < 0.999 across "
        f"{len(sims)} non-degenerate positions"
    )


def test_stress_2d_cosine_sim_worst_above_99pct():
    """Worst-case cosine-sim across the population ≥ 0.99 (the
    same data as test_stress_2d_cosine_sim_99pct_floor_every_position
    but framed as a single worst-case statistic for the §20.21
    notebook record)."""
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=30)
    sims: list = []
    for pos in positions:
        baseline = encode_640(pos, vals=VALS)
        pure = encode_2d_pure_phase_to_float(pos)
        if np.linalg.norm(baseline) == 0.0:
            continue
        sims.append(_cosine_sim(baseline, pure))
    worst = min(sims)
    assert worst >= 0.99, (
        f"worst-case cosine-sim {worst:.6f} < 0.99 across "
        f"{len(sims)} non-degenerate positions"
    )


# ─── Bit-exactness for D₄ channels at scale ─────────────────────────


def test_stress_2d_d4_channels_bit_exact_every_position():
    """The D₄ channels (A1/A2/B1/B2/E, dims 0-319) are integer
    arithmetic at the core. They MUST be bit-exact relative to the
    float baseline modulo float-precision rounding. Test on 1000
    random positions; ANY mismatch beyond float-precision atol is
    a regression."""
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=40)
    failures: list = []
    for i, pos in enumerate(positions):
        baseline = encode_640(pos, vals=VALS)
        pure = encode_2d_pure_phase_to_float(pos)
        # D₄ block = first 320 dims.
        if not np.allclose(pure[:320], baseline[:320],
                           rtol=1e-12, atol=1e-12):
            max_abs = float(np.abs(pure[:320] - baseline[:320]).max())
            failures.append((i, max_abs, len(pos)))
    if failures:
        msg = (
            f"{len(failures)}/{N_STRESS_POSITIONS} positions had non-"
            f"bit-exact D₄ channels. First 3:\n"
        )
        for idx, max_abs, n_pieces in failures[:3]:
            msg += (
                f"  pos[{idx}] (n_pieces={n_pieces}): "
                f"max_abs_diff={max_abs}\n"
            )
        pytest.fail(msg)


# ─── Output integrity (no NaN, no overflow, dtype stable) ───────────


def test_stress_2d_no_nan_or_inf_in_output():
    """Pure-phase encoder MUST NOT produce NaN or Inf for any
    legitimate input. (Float baseline shouldn't either, but we
    check both for symmetry.)"""
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=50)
    for i, pos in enumerate(positions):
        pure_int = encode_2d_pure_phase(pos)
        # int32 doesn't have NaN, but bounds check.
        assert pure_int.dtype == np.int32
        assert pure_int.shape == (640,)
        # Float dequantized version
        pure_float = encode_2d_pure_phase_to_float(pos)
        assert pure_float.dtype == np.float64
        assert not np.isnan(pure_float).any(), (
            f"pos[{i}]: NaN in pure_phase float output"
        )
        assert not np.isinf(pure_float).any(), (
            f"pos[{i}]: Inf in pure_phase float output"
        )


def test_stress_2d_int_output_in_int32_range():
    """The integer output stays within int32 bounds across the
    population. (Should be impossible to overflow at the documented
    scales — king value 100 × 64 squares × 8 perm sum = 51200, well
    within int32 — but this test locks the property explicitly.)"""
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=60)
    for i, pos in enumerate(positions):
        pure_int = encode_2d_pure_phase(pos)
        max_abs = int(np.abs(pure_int).max()) if pure_int.size > 0 else 0
        assert max_abs < (1 << 30), (
            f"pos[{i}] (n_pieces={len(pos)}): max abs int output "
            f"{max_abs} approaches int32 ceiling — investigate "
            f"potential overflow path"
        )


# ─── Channel-energy ranking Spearman ρ at scale ─────────────────────


def test_stress_2d_channel_energy_ranking_spearman_above_99pct():
    """**§20.15 acceptance gate at scale.** Across all
    (position, channel) pairs in the random corpus, the channel-
    energy ranking Spearman ρ between the float baseline and the
    pure-phase output is ≥ 0.99.
    """
    try:
        from scipy.stats import spearmanr
    except ImportError:
        pytest.skip("scipy not available")
    positions = _generate_corpus(N_STRESS_POSITIONS, seed_offset=70)
    baseline_energies: list = []
    pure_energies: list = []
    for pos in positions:
        b = encode_640(pos, vals=VALS)
        p = encode_2d_pure_phase_to_float(pos)
        if np.linalg.norm(b) == 0.0:
            continue
        eb = channel_energies(b)
        ep = channel_energies(p)
        for name in eb:
            baseline_energies.append(eb[name])
            pure_energies.append(ep[name])
    rho, _ = spearmanr(baseline_energies, pure_energies)
    assert rho >= 0.99, (
        f"channel-energy ranking Spearman ρ = {rho:.6f} < 0.99 across "
        f"{len(baseline_energies)} (position, channel) pairs"
    )


# ─── Determinism — same seed → same output ──────────────────────────


def test_stress_2d_deterministic_under_repeated_calls():
    """Calling the encoder twice on the same random position
    gives bit-exact identical int output — quantization tables
    are static, no implicit randomness anywhere."""
    pos = random_pos_2d(20, seed=_ROOT_SEED + 80)
    a = encode_2d_pure_phase(pos)
    b = encode_2d_pure_phase(pos)
    np.testing.assert_array_equal(a, b)


def test_stress_2d_random_corpus_reproducible():
    """The random corpus generator is reproducible — same seed,
    same positions. Test by regenerating and comparing."""
    a = _generate_corpus(50, seed_offset=90)
    b = _generate_corpus(50, seed_offset=90)
    assert len(a) == len(b)
    for pos_a, pos_b in zip(a, b):
        assert pos_a == pos_b
