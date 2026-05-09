"""1.13.0 immolation: B-spike-3 spectral evaluator variants.

Tests cover the two new evaluator paths:
  * :mod:`chess_spectral.engine.eval.spectral_hybrid` — channel-
    energy directly from a SpectralBIPHybrid2D, skipping the float
    decode step.
  * :mod:`chess_spectral.engine.eval.spectral_hybrid_cache` — LRU-
    cached wrapper for the search-engine integration shape.

Plus the float32 sibling :mod:`spectral_float32`.

Algebraic identities locked:

  * Channel-energy-from-hybrid agrees with channel-energy-from-
    float64 within the magnitude-quantization envelope (8-bit:
    typically <1% relative; 4-bit: <5% relative).
  * Sign-of-score is preserved: if float64 says white-favorable,
    hybrid says white-favorable too.
  * LRU cache hits return the same value as cache misses.
  * LRU cache hit/miss counters work correctly.
  * Default-weight evaluation matches the existing spectral.evaluate
    in sign and within tolerance in magnitude.

The bench numbers from `tests/bench_spectral_eval.py` are NOT locked
in tests (CI machine variance makes that brittle); they live in the
notebook §20.20 record.
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

from chess_spectral import fen_to_pos   # noqa: E402
from chess_spectral.encoder_bip_hybrid import (   # noqa: E402
    encode_2d_bip_hybrid,
)
from chess_spectral.engine.eval import spectral, spectral_hybrid   # noqa: E402
from chess_spectral.engine.eval import spectral_float32   # noqa: E402
from chess_spectral.engine.eval.spectral_hybrid import (   # noqa: E402
    channel_energies_from_hybrid,
    evaluate_from_hybrid,
)
from chess_spectral.engine.eval.spectral_hybrid_cache import (   # noqa: E402
    HybridCache,
    make_cached_evaluator,
)


_REPRESENTATIVE_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
    "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
    "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1",
]


# ─── channel_energies_from_hybrid: per-channel parity ───────────────


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS)
def test_immolation_hybrid_channel_energies_close_to_float64(fen):
    """The channel energies computed from a hybrid representation
    must agree with the float64 baseline within the 8-bit
    quantization envelope.

    Tolerance: 5% relative error per channel. Tightening this
    further requires per-channel-error analysis; 5% is generous
    enough that 8-bit hybrid easily clears, and the test still
    fails loudly if a regression introduces meaningful drift.
    """
    pos = fen_to_pos(fen)
    h = encode_2d_bip_hybrid(pos, magnitude_bits=8)
    energies_hybrid = channel_energies_from_hybrid(h)
    # Compare to float64 baseline.
    from chess_spectral import encode_640
    v = encode_640(pos)
    energies_baseline = spectral.channel_energies(v)

    for name in energies_baseline:
        e_base = energies_baseline[name]
        e_hyb = energies_hybrid[name]
        if e_base == 0.0:
            assert e_hyb == 0.0 or abs(e_hyb) < 1e-9, (
                f"{fen} channel {name}: baseline=0 but "
                f"hybrid={e_hyb}"
            )
            continue
        rel_err = abs(e_hyb - e_base) / abs(e_base)
        assert rel_err < 0.05, (
            f"{fen} channel {name}: relative error {rel_err:.4f} "
            f">= 5%; baseline={e_base:.4f}, hybrid={e_hyb:.4f}"
        )


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS)
def test_immolation_evaluate_from_hybrid_sign_matches_float64(fen):
    """The sign of the score from evaluate_from_hybrid agrees with
    spectral.evaluate. This is the load-bearing search-correctness
    property — alpha-beta only cares about the relative ordering
    of moves, so as long as sign and magnitude ranking agree, the
    search behaves the same."""
    pos = fen_to_pos(fen)
    side = fen.split()[1] == "w"
    h = encode_2d_bip_hybrid(pos, magnitude_bits=8)
    score_hyb = evaluate_from_hybrid(h, side)
    score_baseline = spectral.evaluate(pos, side)
    if score_baseline == 0.0:
        assert abs(score_hyb) < 1e-6
        return
    assert (score_baseline > 0) == (score_hyb > 0), (
        f"{fen}: sign mismatch — baseline={score_baseline:.4f}, "
        f"hybrid={score_hyb:.4f}"
    )


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS)
def test_immolation_evaluate_from_hybrid_magnitude_within_envelope(fen):
    """The MAGNITUDE of the score should be within 5% relative of
    the float64 baseline. This is tighter than the sign-only check
    and ensures the hybrid evaluator can substitute for the float
    one in evaluator-comparison contexts (move ordering by score
    delta, etc.)."""
    pos = fen_to_pos(fen)
    side = fen.split()[1] == "w"
    h = encode_2d_bip_hybrid(pos, magnitude_bits=8)
    score_hyb = evaluate_from_hybrid(h, side)
    score_baseline = spectral.evaluate(pos, side)
    if abs(score_baseline) < 1e-6:
        return  # No meaningful magnitude to check.
    rel_err = abs(score_hyb - score_baseline) / abs(score_baseline)
    assert rel_err < 0.05, (
        f"{fen}: relative magnitude error {rel_err:.4f} >= 5%; "
        f"baseline={score_baseline:.4f}, hybrid={score_hyb:.4f}"
    )


# ─── 4-bit hybrid: looser tolerance ─────────────────────────────────


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS[:3])
def test_immolation_4bit_hybrid_sign_matches_float64(fen):
    """4-bit hybrid is lossier; sign agreement still expected, but
    magnitude envelope is looser (test does sign only here)."""
    pos = fen_to_pos(fen)
    side = fen.split()[1] == "w"
    h = encode_2d_bip_hybrid(pos, magnitude_bits=4)
    score_hyb = evaluate_from_hybrid(h, side)
    score_baseline = spectral.evaluate(pos, side)
    if score_baseline == 0.0:
        assert abs(score_hyb) < 1e-6
        return
    assert (score_baseline > 0) == (score_hyb > 0)


# ─── HybridCache: LRU semantics ──────────────────────────────────────


def test_immolation_cache_starts_empty():
    cache = HybridCache(max_size=10)
    assert cache.size == 0
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.hit_rate == 0.0


def test_immolation_cache_miss_then_hit():
    cache = HybridCache(max_size=10)
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])

    # First access — miss
    h1 = cache.get_or_compute(
        42, lambda: encode_2d_bip_hybrid(pos, magnitude_bits=8))
    assert cache.misses == 1
    assert cache.hits == 0
    assert cache.size == 1

    # Second access with the same key — hit
    h2 = cache.get_or_compute(
        42, lambda: pytest.fail("compute_fn should not be called on hit"))
    assert cache.misses == 1
    assert cache.hits == 1
    assert h2 is h1  # identity preserved


def test_immolation_cache_lru_eviction():
    """When the cache is full, the LEAST recently used entry is
    evicted on the next miss."""
    cache = HybridCache(max_size=3)
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])

    # Populate keys 1, 2, 3.
    for k in (1, 2, 3):
        cache.get_or_compute(
            k, lambda: encode_2d_bip_hybrid(pos, magnitude_bits=8))
    assert cache.size == 3

    # Touch key 1 (move to most-recent).
    cache.get_or_compute(1, lambda: pytest.fail("hit expected"))

    # Insert key 4 — evicts the least-recent (key 2 — key 1 was
    # touched, key 3 is between, key 2 has not been touched since
    # initial insert and is the LRU).
    cache.get_or_compute(
        4, lambda: encode_2d_bip_hybrid(pos, magnitude_bits=8))
    assert cache.size == 3

    # Key 2 should now be a miss.
    cache.get_or_compute(
        2, lambda: encode_2d_bip_hybrid(pos, magnitude_bits=8))
    # We had: 4 hits + 4 misses (initial 3 fills, hit on 1, fill 4,
    # miss on 2 → 4 misses, 1 hit + tracker).
    # Better to assert specific counters:
    assert cache.misses == 5  # 1, 2, 3, 4, then 2 again
    assert cache.hits == 1     # the touch of 1


def test_immolation_make_cached_evaluator_returns_callable_and_cache():
    fn, cache = make_cached_evaluator(magnitude_bits=8, cache_size=10)
    assert callable(fn)
    assert isinstance(cache, HybridCache)
    pos = fen_to_pos(_REPRESENTATIVE_FENS[0])
    score1 = fn(pos, True)
    score2 = fn(pos, True)  # cache hit
    assert score1 == score2
    assert cache.misses == 1
    assert cache.hits == 1


def test_immolation_make_cached_evaluator_distinct_positions():
    """Different positions hash to different keys; each takes one
    miss + subsequent hits."""
    fn, cache = make_cached_evaluator(magnitude_bits=8, cache_size=10)
    positions = [fen_to_pos(f) for f in _REPRESENTATIVE_FENS]
    # First pass — all misses
    for pos in positions:
        fn(pos, True)
    assert cache.misses == len(positions)
    assert cache.hits == 0
    # Second pass — all hits
    for pos in positions:
        fn(pos, True)
    assert cache.misses == len(positions)
    assert cache.hits == len(positions)


# ─── spectral_float32 sibling ───────────────────────────────────────


@pytest.mark.parametrize("fen", _REPRESENTATIVE_FENS)
def test_immolation_float32_sign_matches_float64(fen):
    """spectral_float32.evaluate gives the same sign as
    spectral.evaluate. Magnitude envelope: float32 → float64 is
    ~7-decimal-digit precision; agreement should be within 1e-4
    relative."""
    pos = fen_to_pos(fen)
    side = fen.split()[1] == "w"
    score_f32 = spectral_float32.evaluate(pos, side)
    score_f64 = spectral.evaluate(pos, side)
    if score_f64 == 0.0:
        assert abs(score_f32) < 1e-3
        return
    assert (score_f64 > 0) == (score_f32 > 0)
    rel_err = abs(score_f32 - score_f64) / abs(score_f64)
    assert rel_err < 1e-4, (
        f"{fen}: float32 vs float64 relative error {rel_err:.6f} "
        f">= 1e-4; should be tighter than this"
    )


# ─── Search-correctness sanity ──────────────────────────────────────


def test_immolation_cached_evaluator_matches_baseline_on_corpus():
    """Building a cached hybrid evaluator and running it across the
    test corpus produces sign-agreement with spectral.evaluate on
    every position. This is the integration-level check — if a
    consumer plugs the cached evaluator into the search core's
    SearchOptions.evaluator slot, search results should be
    sign-consistent with the float64 baseline (modulo magnitude
    quantization, which can affect tie-breaking but not principal
    move selection)."""
    cached_fn, _ = make_cached_evaluator(magnitude_bits=8, cache_size=100)
    for fen in _REPRESENTATIVE_FENS:
        pos = fen_to_pos(fen)
        side = fen.split()[1] == "w"
        cached_score = cached_fn(pos, side)
        baseline = spectral.evaluate(pos, side)
        if baseline == 0.0:
            assert abs(cached_score) < 1e-6
            continue
        assert (baseline > 0) == (cached_score > 0), (
            f"{fen}: cached evaluator sign mismatch — "
            f"baseline={baseline:.4f}, cached={cached_score:.4f}"
        )
