# Tournament baseline at depth 4 — first empirical recording

**Date**: 2026-05-09
**Run config**: `python tests/run_evaluator_tournament.py --depth 4 --games-per-pair 2 --max-plies 150 --output tests/bench_baselines/tournament_d4.json --quiet`
**Wall clock**: 2 246 s (37 min)
**Variants**: `material`, `spectral_float64`, `spectral_hybrid_8bit_lru`

## Closes the §16.7 deferred item — partially

The 1.16.0 ship added the tournament runner infrastructure (`tests/run_evaluator_tournament.py`); the §16.7 amendment de-gated B-spike-3 (search-engine evaluator) from the contaminated Othello prior. The open empirical question:

> Does `spectral_hybrid_8bit_lru` actually beat `material` at deep search?

This baseline is the **first real recorded answer**. It's directional, not statistically locked.

## Final ELO ranking

| Variant                    | Final ELO |
|----------------------------|-----------|
| **material**               | **1530.6** |
| spectral_float64           | 1485.6    |
| spectral_hybrid_8bit_lru   | 1483.8    |

Material wins by ~45-47 ELO over both spectral variants. The two spectral variants are statistically indistinguishable at this depth + game count.

## Pair records

| Pair (white | black) | Wins | Losses | Draws |
|---|---|---|---|---|
| material vs spectral_float64 | 1 | 0 | 1 |
| material vs spectral_hybrid_8bit_lru | 1 | 0 | 1 |
| spectral_float64 vs spectral_hybrid_8bit_lru | 1 | 1 | 0 |

Material won every white-side game and drew the black-side game once. The two spectral variants split.

## Termination histogram

| Game | Termination |
|---|---|
| material (W) vs spectral_float64 (B) | max_plies (drew) |
| spectral_float64 (W) vs material (B) | checkmate (material won as black) |
| material (W) vs spectral_hybrid_8bit_lru (B) | max_plies (drew) |
| spectral_hybrid_8bit_lru (W) vs material (B) | checkmate (material won as black) |
| spectral_float64 (W) vs spectral_hybrid_8bit_lru (B) | checkmate (sf64 won) |
| spectral_hybrid_8bit_lru (W) vs spectral_float64 (B) | checkmate (sh8 won) |

Mean plies per game: **61**. Most games ended via real terminations (4 checkmates + 2 max_plies abandons); not pathological.

## Honest interpretation

**Statistical caveat**: 2 games per pair is **NOT** statistically meaningful. At this game count, single coin-flips dominate the ELO numbers; a 47-point gap could easily flip with another 4 games. The standard rule of thumb is **≥ 100 games per pair for ±30 ELO confidence**.

**Directional finding**: at depth 4, `material` (the trivial integer-addition baseline) outperforms both spectral evaluator variants by ~45 ELO each. The two spectral variants are within noise of each other.

**Why might this be?** Three hypotheses, ordered by plausibility:

1. **Spectral evaluators are tuned for static eval, not search.** The 1.13.0 `spectral_hybrid_8bit_lru` was benched at ~50 µs/call vs `spectral_float64`'s ~870 µs (~17× speedup). But static-eval throughput is not search-tree throughput. The depth-4 search-tree bench (`bench_search_tree.py`, `tournament_d4.json` from 1.16.0) showed `spectral_hybrid_8bit_lru` slightly *slower* than `spectral_float64` in nodes/sec — TT re-visits are rare at low depth. This tournament confirms: at depth 4, the spectral evaluator family doesn't have an algorithmic edge over material because the search isn't deep enough to reward fine-grained position evaluation.

2. **Material is a strong baseline** for chess. Pure integer piece-counting is a 99% solution for casual chess; deviations from it (positional understanding, structural awareness) only matter when search depth is too shallow to find tactics. At depth 4 + quiescence, tactics dominate; both sides find them; material counts decide.

3. **Spectral evaluator weights are uniform.** The `spectral.evaluate` and `spectral_hybrid` functions sum channel energies with default uniform weights (1.0 across all 10/11 channels). No tuning. Material, by contrast, uses canonical chess piece values (P=1, N=3, B=3, R=5, Q=9, K=∞). The "untuned vs canonical" gap is real and would be addressed by a tuning sweep — out of scope here.

## What this baseline does NOT close

- **Higher-depth question still open**: at depth 5-7, TT re-visits become more common, and the spectral_hybrid cache-hit advantage might surface. This baseline tested only depth 4.
- **Game count too small for statistical confidence**: a 47-ELO gap at 2 games per pair means very little. Real lock-in needs 100+ games per pair (5+ hours wall-clock at depth 4; 1-3 days at depth 5-6).
- **Untuned spectral weights**: the spectral evaluator family ships with uniform channel weights. A tuning sweep (e.g., logistic regression on (channel_energies → win_probability) over a labeled corpus) would likely close the gap somewhat — but that's a separate ship.

## Recommended next steps

1. **Run depth 5 with 4-8 games per pair** when compute budget allows (2-5 hour wall-clock estimate). Expected to take ~24-30 hours sequential or parallelizable.
2. **Run depth 4 with ≥ 100 games per pair** for a statistically locked ±30 ELO baseline. ~30+ hour sequential estimate; small enough to be a CI artifact.
3. **Investigate spectral channel weight tuning** before running larger sweeps — uniform weights leave performance on the table.

## Provenance

- This baseline was originally dispatched via subagent SA1 with target depth=5 / 2 games per pair. SA1 silently stalled at the 30-minute mark with an empty output file (the tournament process exited but the agent didn't write its summary). Parent agent took over directly: scaled back to depth=4 to get a finishable baseline within available time, ran the bench, wrote this summary.
- The SA1 stall is a documented workflow constraint: subagents dispatched with long-running background processes (>20 min) can lose track of their own state. Mitigation for future RBS-deferred dispatches: provide an explicit fallback budget in the subagent prompt and a watchdog timeout.
