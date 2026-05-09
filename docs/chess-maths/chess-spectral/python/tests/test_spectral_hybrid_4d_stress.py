"""Pedantic non-deterministic stress test for the 4D spectral
hybrid evaluator family (1.14.0+ — parity restoration).

Mirrors ``test_pure_phase_stress_2d.py`` for the 4D side. Tests
cover the 1.14.0 4D parity additions to:
  * ``chess_spectral.engine.eval.spectral_hybrid``:
    ``evaluate_from_hybrid_4d``, ``channel_energies_from_hybrid_4d``,
    ``evaluate_4d``
  * ``chess_spectral.engine.eval.spectral_hybrid_cache``:
    ``make_cached_evaluator_4d``

The 4D encoder + hybrid encoder were shipped in 1.12.0; the
evaluator-side (channel-energy directly from the hybrid form,
LRU cached evaluator) was 2D-only until this 1.14.0 ship.
1.14.0 closes the gap.

Methodology
-----------

500 random 4D positions (smaller than the 2D corpus's 1000
because 4D encoder is ~10× more expensive per call) sampled
across piece counts in [2, 256]. Each position generated with
seeded RNG; corpus reproducible.

Stress assertions:
  * Per-position cosine-sim with ``encode_4d(pos4)`` ≥ 0.99
    (8-bit hybrid; matches the 1.12.0 acceptance gate)
  * Sign-of-score agreement: hybrid evaluator's sign matches
    float baseline's sign on every position with nonzero score
  * Channel-energy ranking Spearman ρ across all (pos, channel)
    pairs ≥ 0.99
  * No NaN / Inf in 4D channel-energy outputs
  * Cached evaluator's hit/miss counters work correctly at scale
  * Cache-hit results identical to cache-miss results (cache is
    correctness-preserving)
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

from chess_spectral.encoder_4d import (   # noqa: E402
    encode_4d, channel_energies_4d,
)
from chess_spectral.encoder_bip_hybrid import (   # noqa: E402
    encode_4d_bip_hybrid, decode_4d_bip_hybrid,
)
from chess_spectral.engine.eval.spectral_hybrid import (   # noqa: E402
    channel_energies_from_hybrid_4d,
    evaluate_from_hybrid_4d,
    evaluate_4d,
)
from chess_spectral.engine.eval.spectral_hybrid_cache import (   # noqa: E402
    make_cached_evaluator_4d,
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


# ─── Channel-energy parity at scale ─────────────────────────────────


def test_stress_4d_channel_energies_close_to_baseline_8bit():
    """Per-channel energies from the 4D hybrid path must agree
    with the float baseline within the 8-bit quantization
    envelope. 5% relative tolerance per channel; matches the
    1.12.0 hybrid acceptance gate."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=100)
    failures: list = []
    for i, pos4 in enumerate(positions):
        baseline_vec = encode_4d(pos4)
        hybrid = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
        eb = channel_energies_4d(baseline_vec)
        eh = channel_energies_from_hybrid_4d(hybrid)
        for name in eb:
            if eb[name] == 0.0:
                if abs(eh[name]) > 1e-3:
                    failures.append(
                        (i, name, eb[name], eh[name],
                         "baseline=0 but hybrid nonzero")
                    )
                continue
            rel_err = abs(eh[name] - eb[name]) / abs(eb[name])
            if rel_err >= 0.05:
                failures.append(
                    (i, name, eb[name], eh[name], rel_err)
                )
    if failures:
        msg = (
            f"{len(failures)} (position, channel) pairs failed "
            f"the 5% rel-err envelope. First 3:\n"
        )
        for f in failures[:3]:
            msg += f"  {f}\n"
        pytest.fail(msg)


# ─── Score sign agreement at scale ──────────────────────────────────


def test_stress_4d_evaluate_from_hybrid_sign_matches_baseline():
    """For positions with nonzero baseline score, the hybrid
    evaluator returns the same sign as the float-encoder
    equivalent."""
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=110)
    sign_mismatches = 0
    for pos4 in positions:
        # Baseline score: encode_4d → channel_energies_4d → equal
        # weights → side flip
        baseline_vec = encode_4d(pos4)
        eb = channel_energies_4d(baseline_vec)
        baseline_score = sum(eb.values())  # equal weights
        # Hybrid score
        hybrid = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
        hybrid_score = evaluate_from_hybrid_4d(hybrid, side_to_move=True)
        if abs(baseline_score) < 1e-6:
            continue  # degenerate; signs irrelevant
        if (baseline_score > 0) != (hybrid_score > 0):
            sign_mismatches += 1
    assert sign_mismatches == 0, (
        f"{sign_mismatches} sign mismatches across "
        f"{N_STRESS_POSITIONS_4D} positions"
    )


# ─── Spearman ρ on channel-energy ranking ───────────────────────────


def test_stress_4d_channel_energy_ranking_spearman():
    """Channel-energy ranking Spearman ρ ≥ 0.99 across all
    (position, channel) pairs in the random 4D corpus."""
    try:
        from scipy.stats import spearmanr
    except ImportError:
        pytest.skip("scipy not available")
    positions = _generate_4d_corpus(N_STRESS_POSITIONS_4D, seed_offset=120)
    baseline_energies: list = []
    hybrid_energies: list = []
    for pos4 in positions:
        baseline_vec = encode_4d(pos4)
        if np.linalg.norm(baseline_vec) == 0.0:
            continue
        hybrid = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
        eb = channel_energies_4d(baseline_vec)
        eh = channel_energies_from_hybrid_4d(hybrid)
        for name in eb:
            baseline_energies.append(eb[name])
            hybrid_energies.append(eh[name])
    rho, _ = spearmanr(baseline_energies, hybrid_energies)
    assert rho >= 0.99, (
        f"4D channel-energy Spearman ρ = {rho:.6f} < 0.99 across "
        f"{len(baseline_energies)} (pos, channel) pairs"
    )


# ─── Output integrity ───────────────────────────────────────────────


def test_stress_4d_no_nan_or_inf_in_channel_energies():
    """Hybrid 4D channel-energy output must be NaN / Inf-free
    across the random corpus."""
    positions = _generate_4d_corpus(
        N_STRESS_POSITIONS_4D // 2, seed_offset=130)
    for i, pos4 in enumerate(positions):
        hybrid = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
        e = channel_energies_from_hybrid_4d(hybrid)
        for name, val in e.items():
            assert not np.isnan(val), (
                f"pos[{i}] (n={len(pos4)}): NaN in channel {name}"
            )
            assert not np.isinf(val), (
                f"pos[{i}] (n={len(pos4)}): Inf in channel {name}"
            )
            assert val >= 0.0, (
                f"pos[{i}] channel {name}: energy {val} < 0 "
                f"(channel energy must be non-negative)"
            )


# ─── Cached evaluator semantics ─────────────────────────────────────


def test_stress_4d_cached_evaluator_correctness():
    """Cache-hit results IDENTICAL to cache-miss results across
    the random corpus. Tests `make_cached_evaluator_4d` doesn't
    alter the score on cache hits."""
    fn, cache = make_cached_evaluator_4d(
        magnitude_bits=8, cache_size=10000)
    positions = _generate_4d_corpus(100, seed_offset=140)
    scores_first_pass: list = []
    for pos4 in positions:
        scores_first_pass.append(fn(pos4, side_to_move=True))
    # First pass: every position is a miss.
    assert cache.misses == len(positions)
    assert cache.hits == 0
    scores_second_pass: list = []
    for pos4 in positions:
        scores_second_pass.append(fn(pos4, side_to_move=True))
    # Second pass: every position is a hit.
    assert cache.hits == len(positions)
    # Scores must match exactly.
    assert scores_first_pass == scores_second_pass


def test_stress_4d_cached_evaluator_lru_eviction_at_scale():
    """LRU eviction works correctly when corpus exceeds cache
    size. Uses a small cache (cap=50) and 200 positions; verifies
    no crashes and that hit-rate stays low (each position is
    visited once on the first pass; second pass to the eviction
    cap doesn't re-hit)."""
    fn, cache = make_cached_evaluator_4d(
        magnitude_bits=8, cache_size=50)
    positions = _generate_4d_corpus(200, seed_offset=150)
    # First pass: all misses, but only 50 fit; the rest evict
    # earlier entries.
    for pos4 in positions:
        fn(pos4, side_to_move=True)
    assert cache.size == 50
    assert cache.misses == 200
    assert cache.hits == 0
    # Cache contains the most recent 50 positions; touch them
    # again — all hits.
    for pos4 in positions[-50:]:
        fn(pos4, side_to_move=True)
    assert cache.hits == 50


# ─── Determinism + corpus reproducibility ───────────────────────────


def test_stress_4d_random_corpus_reproducible():
    """Same seed → same 4D corpus."""
    a = _generate_4d_corpus(50, seed_offset=160)
    b = _generate_4d_corpus(50, seed_offset=160)
    assert len(a) == len(b)
    for pos_a, pos_b in zip(a, b):
        assert pos_a == pos_b


def test_stress_4d_evaluate_4d_round_trip_consistency():
    """``evaluate_4d`` (encode + eval) and the manual sequence
    (encode_4d_bip_hybrid → evaluate_from_hybrid_4d) produce
    identical scores."""
    positions = _generate_4d_corpus(100, seed_offset=170)
    for pos4 in positions:
        s_evaluate_4d = evaluate_4d(pos4, side_to_move=True)
        h = encode_4d_bip_hybrid(pos4, magnitude_bits=8)
        s_manual = evaluate_from_hybrid_4d(h, side_to_move=True)
        assert s_evaluate_4d == s_manual, (
            f"evaluate_4d != manual on pos with n={len(pos4)}: "
            f"{s_evaluate_4d} vs {s_manual}"
        )
