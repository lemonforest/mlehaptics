# Phase 1e findings — notebook §2e draft

**Status:** All five sub-phases complete.
**Date:** 2026-04-23

Follow-up to §1d.c (twin-channel A₁(s²) / E(s²) headline) and §2c.2
(Shannon×A₁⁻ in-book ρ = +0.213).  Five sub-phases:

1. **1e.1** — edax d=20 on 2587 tasklist, for Reading A vs B separation.
2. **1e.2** — multivariate OLS + rotated sweep on A₁(s²) + E(s²).
3. **1e.3** — Shannon info × full D₄ occupation battery (generalises §2c.2).
4. **1e.4** — accuracy-100 archive re-aggregation.
5. **1e.5** — L7b-style predictive sheaf validation on 30-seed trajectories.

---

## 1e.2 — Multivariate A₁(s²) + E(s²) joint predictor — **CONFIRMED**

Runner: [`research/phase1e_multivariate.py`](research/phase1e_multivariate.py).
Input: [`results/phase1d_spectral_vs_perfectplay.csv`](results/phase1d_spectral_vs_perfectplay.csv).
Output: [`results/phase1e_multivariate.json`](results/phase1e_multivariate.json).

**Univariate reproduces §2d.c exactly** at N = 2587:

| channel | raw ρ | partial ρ |
|---|---|---|
| D₄-A₁(s²) | −0.498 | **−0.331** |
| D₄-E(s²)  | +0.484 | **+0.304** |
| D₄-A₂(s²) | +0.151 | +0.120 |
| D₄-B₁(s²) | +0.148 | +0.059 |
| D₄-B₂(s²) | +0.034 | −0.013 |

**Joint (A₁+E) OLS:**
- Raw R² = **0.155**
- Partial-on-|disc_diff| R² = **0.100**

**Full D₄ 5-channel (A₁+A₂+B₁+B₂+E):**
- Raw R² = **0.160** (only ~0.005 gain over A₁+E)
- Partial R² = **0.112** (~0.012 gain)

Confirms A₁+E soak up essentially all of the D₄-occupation signal.
A₂ contributes a tiny residual (partial +0.133 univariate), B₁/B₂
effectively nothing.

**Rotated single-dim sweep** (standardised coordinates, θ on [0°, 180°]):
- Best raw: ρ = **+0.515 at θ = 151.75°** (≈ `0.88·E − 0.47·A₁`)
- Best partial: ρ = **+0.340 at θ = 156.25°**

**Canonical directions:**

| direction | raw ρ | partial ρ |
|---|---|---|
| a1 only (θ=0°) | −0.498 | −0.331 |
| a1 + e (θ=45°) | **−0.049** | **−0.038** |
| e only (θ=90°) | +0.437 | +0.299 |
| **a1 − e (θ=135°)** | **+0.510** | **+0.337** |

The (A₁ + E) direction is **near-null** (ρ ≈ 0), confirming the §2d.c
Plancherel/mirror reading: A₁ and E trade off against each other.
The (A₁ − E) combination is *slightly* stronger than either channel
individually (partial +0.337 vs A₁ alone −0.331).  The gain is modest
(≈ 2 %), so the rotated observable is a clean univariate summary
without being a dramatic improvement.

**Saturated reference:** 10 spectral channels + |disc_diff| → R² = 0.462,
meaning the spectral battery plus disc count explains almost half of
`archive_mean_lb` variance.  |disc_diff| alone (from residualising Y
on DD) explains R² = 0.288 — so the spectral 10-channel component
adds ~0.17 incremental R² on top of disc count.  Most of that
incremental content is in the D₄-A₁/E pair.

---

## 1e.3 — Shannon-info × full spectral battery — **STRONGER THAN §2c.2**

Runner: [`research/phase1e_shannon_observables.py`](research/phase1e_shannon_observables.py).
Output: [`results/phase1e_shannon_observables.json`](results/phase1e_shannon_observables.json).
N = 2099 played plies over 35 Barcelona EGP 2026 games.

**Headline:** the §2c.2 in-book correlation (ρ = +0.213 for A₁⁻
magnetisation) **more than doubles** when the observable is swapped
for the Z₂-invariant occupation projection.

Per-observable Spearman(I_move, observable) by phase:

| observable | all plies | in-book | out-of-book |
|---|---|---|---|
| a1_minus (§2c.2 baseline) | −0.065 | **+0.213** | −0.465 |
| e_minus                   | −0.011 | +0.426   | −0.508 |
| **d4_a1_occ**             | −0.115 | **+0.465** | **−0.755** |
| d4_a2_occ                 | +0.366 | +0.124   | +0.335 |
| d4_b1_occ                 | +0.403 | +0.345   | +0.327 |
| d4_b2_occ                 | +0.244 | +0.237   | +0.183 |
| **d4_e_occ**              | **+0.508** | +0.422   | +0.438 |

Control ρ(I_move, n_legal_moves) = +0.814 (matches §2c.2).

**Readings:**

1. **D₄-A₁(s²) in-book ρ = +0.465** (vs §2c.2's +0.213 for A₁⁻).
   More than 2× the effect size.  The §2c.2 A₁⁻ correlation captured
   the D₄ part of the A₁⁻ = D₄ · Z₂⁻ projection but was weakened by
   the Z₂-odd component (which the single-disc-type play doesn't
   modulate strongly in-book).  Moving to the Z₂-invariant
   D₄-A₁(s²) projection lets the full D₄-symmetric occupation
   structure track Shannon-info.

2. **D₄-A₁(s²) sign-flips between in-book (+0.465) and out-of-book
   (−0.755).**  A very strong effect with opposite signs.  In-book:
   positions where the chosen move "diverges" more from WTHOR
   empirical also have higher D₄-symmetric occupation ("more evenly
   spread" stones).  Out-of-book: the spectral-info relationship
   inverts sharply — deeper / less-surveyed positions with high
   D₄-symmetric occupation have LOWER I_move bits.  Likely reading:
   Shannon info in the out-of-book tail is dominated by the `log₂|M|`
   term (ρ(I_move, n_legal) = +0.81), and n_legal is itself
   negatively correlated with D₄-symmetric fill in late-game (when
   few legal moves exist, the board is dense and occupation is more
   symmetric).

3. **D₄-E(s²) all-plies ρ = +0.508.**  Strongest single-observable
   correlation across the full corpus.  Matches the §2d.c twin-
   channel story — the "oriented anisotropy" component of occupation
   tracks Shannon-info in the same direction across book and
   out-of-book phases.  Unlike A₁, E doesn't sign-flip.

4. **D₄-B₁(s²) all-plies ρ = +0.403.**  Unexpectedly strong, beats
   the rank among "moderate" channels in §2d.c.  In Takizawa
   archive_mean_lb correlation B₁ was a "ghost signal" (partial 0.074).
   Against Shannon info it becomes a substantive correlation.
   Probably reflects the edge/corner vs centre occupation asymmetry
   that Takizawa proved-bounds didn't care about but tournament
   move-choice does.

5. **D₄-A₂(s²) all-plies ρ = +0.366.**  A₂ is the pure rotation
   channel (transforms as Rz); it captures "spin" of the occupation
   pattern.  Also substantive against Shannon info, another novel
   result vs §2c.2.

---

## 1e.5 — Predictive sheaf spectrum (L7b analog) — **POSITIVE, contra logo L7b**

Runner: [`research/phase2_predictive_sheaf.py`](research/phase2_predictive_sheaf.py).
30 random-play trajectories (seeds 100–129), mean length 60.4 moves,
~1750 pairs per Δ.

R² summary (multivariate OLS, all 8 sheaf features → target):

| Δ | target | R²(pred t→t+Δ) | R²(snap t+Δ) | R²(pers target t→target t+Δ) | gain_vs_pers |
|---|---|---|---|---|---|
| 1  | n_legal | 0.562 | 0.577 | 0.325 | +0.237 |
| 3  | n_legal | 0.551 | 0.559 | 0.250 | +0.301 |
| 5  | n_legal | 0.544 | 0.551 | 0.167 | +0.377 |
| 10 | n_legal | 0.561 | 0.562 | 0.070 | **+0.490** |
| 10 | ρ       | 0.972 | 0.954 | 1.000 | −0.028 |
| 10 | empties | 0.972 | 0.954 | 1.000 | −0.028 |

**Key observations:**

1. **Sheaf at time t predicts n_legal_moves at t + Δ almost as well
   as the sheaf at t + Δ itself.**  R²(pred) ≈ R²(snap) across all
   Δ; the gap is < 0.02 at Δ=10.  This is the cleanest positive
   predictive result in the notebook so far.

2. **Gain vs persistence baseline grows with Δ**: +0.237 at Δ=1
   rising to **+0.490 at Δ=10**.  At Δ=10 the sheaf features
   explain R² = 0.56 of n_legal_moves(t+10) variance while knowing
   just n_legal_moves(t) explains R² = 0.07.  The sheaf carries
   substantial forward-predictive content for legal-move count
   beyond simple temporal persistence.

3. **Rho and empty_count have negligible predictive gain.**  They
   are near-monotone with move number (persistence R² ≈ 1.0), so
   the test is uninformative for those targets.  A more interesting
   target would be ΔA₁⁻(t → t+Δ) or an emerging-flanking indicator,
   left for sequel work.

4. **Direct contrast with logo L7b.5** (gain = −0.855 vs snapshot):
   Othello sheaf extrapolation gain near 0 vs snapshot, but
   dramatic positive gain vs persistence.  Why the divergence?
   - Logo L7b used a COMPLEX program's fiber built from its full
     trace at step N, asked to predict geometry at step N+Δ.  The
     fiber was built from "this specific program's trace so far";
     the target was that SAME program's geometry.  A fiber
     summarising a specific program's partial trace has no predictive
     lever over just using the current snapshot.
   - Othello sheaf is built from CURRENT BOARD STATE only (no
     trajectory memory).  The sheaf implicitly encodes geometric
     connectivity of the current flank structure, which constrains
     the set of reachable positions Δ moves ahead.  Predictive
     content comes from current-state structure that bounds the
     near-future, not from trajectory memory.
   - The two systems differ structurally: logo L7b tested
     trajectory-based fiber prediction; 1e.5 tested state-based
     sheaf constraint propagation.  Both gave different verdicts
     because they're different experiments in spirit.

**L7b caveat upgrade:** the "does snapshot extrapolate forward?"
question has a different answer in Othello sheaves than in logo
fibers.  §3 should note that the sheaf λ₂ at move t usefully
predicts legal-move count at move t + 10.  Open question: does this
generalise to tournament-play trajectories (where the move choice
correlates with future trajectory) or is it a random-play artifact?

**Caveats.**
- The sheaf kernel_dim is constant (128) across every position
  (§3.4), so correlations involving kernel_dim as a feature are
  ignored by OLS (effectively NaN warnings in the log).
- Targets ρ and empty_count are trivially predictable, included
  only as controls.
- 30 trajectories may be too few to detect seed-variance; re-run at
  M=100 would tighten the effect size estimate.

---

## 1e.1 — edax d=20 Reading A vs B verdict — **CONFIRMED, Reading B**

Runner: [`research/phase1e_edax_d20_tasklist.py`](research/phase1e_edax_d20_tasklist.py).
Analyzer: [`research/phase1e_edax_d20_correlations.py`](research/phase1e_edax_d20_correlations.py).
Walltime: 986 s ≈ 16.4 min (vs 4 h worst-case estimate — edax at
level 20 on 50-empty positions is faster than expected because
many positions resolve as full WLD-level endgame proofs).
Status: **complete, N = 2587 (2587/2587 parse_ok)**.

Final headline Spearmans:

| channel | raw vs preproof | raw vs **edax_d20** | raw vs archive_mean_lb |
|---|---|---|---|
| **D₄-A₁(s²)** | −0.349 | **−0.342** | −0.498 |
| D₄-E(s²)     | +0.346 | +0.341 | +0.484 |
| D₄-A₂(s²)    | +0.119 | +0.118 | +0.151 |

| channel | partial vs preproof | partial vs **edax_d20** | partial vs archive_mean_lb |
|---|---|---|---|
| **D₄-A₁(s²)** | −0.284 | **−0.277** | −0.331 |
| D₄-E(s²)     | +0.254 | +0.247 | +0.304 |
| D₄-A₂(s²)    | +0.129 | +0.129 | +0.120 |

**The d=20 correlation is indistinguishable from the pre-proof
correlation — they differ by 0.007 raw and 0.007 partial on the
headline channel, well within sampling noise at N = 2587.**  Going
from pre-proof to d=20 does not bridge ANY of the 43 % gap to
archive_mean_lb.

**a_position metric** (0 = aligned with pre-proof, 1 = aligned with
archive bounds):

| scope | pre-proof | d=20 | archive_mean_lb | a_position |
|---|---|---|---|---|
| raw     | −0.349 | −0.342 | −0.498 | **−0.043** |
| partial | −0.284 | −0.277 | −0.331 | **−0.142** |

a_position ≈ 0 means d=20 sits right at pre-proof; negative means
d=20 is even SLIGHTLY further from archive_mean_lb than the
pre-proof value is (0.001-level random drift).

**Verdict: Reading B is load-bearing.**  The spectral D₄-A₁(s²)
channel carries ground-truth-aligned information that even a
strong deep-search engine at d=20 does not capture.  Reading A
(noise floor on y-variable) explains essentially 0 % of the gain.

**Interpretation caveat.**  A Reading-C is worth stating: the
archive bounds aggregate over 300 k–600 k 36-empty sub-problems per
50-empty parent.  Each sub-problem is 14 ply deeper than the 50-
empty parent, so the archive effectively integrates a much deeper
search volume than any single-position d=20 call could reach
(edax at d=20 evaluates leaves heuristically — a 50-empty position
would require ~50 ply to truly solve).  So "alignment" here may
mean "the spectral channel captures structural content that only
emerges at full-solve depth, not at d=20 heuristic-leaf depth."
That is still Reading B in spirit (spectral > engine heuristic)
but frames the mechanism as "structural truth emerges at
game-theoretic resolution" rather than "spectral magically aligns
with ground truth."

---

## 1e.4 — Accuracy-100 archive re-aggregation — **NULL (as predicted)**

Runner: [`research/takizawa_archive_loader.py`](research/takizawa_archive_loader.py)
with the new `--min-accuracy 100` flag.
Outputs:
- [`results/phase1d_archive_summary_exact100.csv`](results/phase1d_archive_summary_exact100.csv)
- [`results/phase1e_correlations_exact100.json`](results/phase1e_correlations_exact100.json)
- [`results/phase1e_spectral_vs_perfectplay_exact100.csv`](results/phase1e_spectral_vs_perfectplay_exact100.csv)

Archive walltime: 4959 s ≈ 83 min (matches §2d.b's ~80 min estimate
almost exactly).  Rate 0.52 files/s.

**Side-by-side with the §2d.b unfiltered baseline (N = 2587):**

| correlation | unfiltered (§2d.b) | exact100 (1e.4) | Δ |
|---|---|---|---|
| D₄-A₁(s²) raw vs archive_mean_lb | −0.4984 | −0.5017 | −0.003 |
| D₄-A₁(s²) partial | −0.3185 | −0.3196 | −0.001 |
| D₄-E(s²) raw | +0.4839 | +0.4864 | +0.003 |
| D₄-E(s²) partial | +0.3101 | +0.3109 | +0.001 |
| D₄-A₂(s²) raw | +0.1506 | +0.1513 | +0.001 |
| D₄-B₁(s²) raw | +0.1482 | +0.1494 | +0.001 |

**All deltas are well under 1 % relative and all tighten in the
predicted direction.**  The §2d.b signal is robust to the
accuracy=99 residual.  The archive was already ~99.3 % exact by
child-row per §2d.b (`exact_fraction` median 0.994), and filtering
out the remaining ~0.7 % shifts correlations by less than the
third decimal place.

Re-analysis protocol (reproducible):

    mkdir -p /tmp/h9_exact100
    python research/h9_strict_runner.py \
        --archive-summary ../results/phase1d_archive_summary_exact100.csv \
        --results-dir /tmp/h9_exact100
    cp /tmp/h9_exact100/phase1d_spectral_vs_perfectplay.csv \
       ../results/phase1e_spectral_vs_perfectplay_exact100.csv
    cp /tmp/h9_exact100/phase1d_correlations.json \
       ../results/phase1e_correlations_exact100.json

(The `--results-dir /tmp/...` redirect is important — `h9_strict_runner.py`
hardcodes its output filenames as `phase1d_*`, which would clobber
§2d.b's originals if pointed at `../results/`.)

**Headline: §2d.b's D₄-A₁(s²) and D₄-E(s²) correlations are NOT an
accuracy-99 artefact.**  They survive the accuracy=100 restriction
with negligible drift.

---

## Phase 1e summary

Five sub-phases, all landing clean numerics:

1. **1e.1 — Reading B confirmed at N = 2587.**  edax at d=20 gives
   ρ = −0.342 (raw) / −0.277 (partial) for D₄-A₁(s²), essentially
   identical to pre-proof edax_score (−0.349 / −0.284, difference
   0.007).  Archive_mean_lb gives −0.498 / −0.319.  a_position
   metric = −0.04 raw, −0.14 partial: d=20 sits at pre-proof, NOT
   between pre-proof and archive.  The 43 % gain in §2d.b is not
   explained by noise averaging.  The spectral channel carries
   ground-truth-aligned content beyond deep-search heuristic eval.
2. **1e.2 — A₁ and E are a Plancherel-locked pair.**  (A₁ + E)
   direction is near-null (partial ρ = −0.038), (A₁ − E) direction
   slightly stronger than either alone (partial ρ = +0.337 vs
   A₁ alone −0.331).  Joint (A₁ + E) R² = 0.100 partial.  Full
   5-channel D₄ battery adds only +0.012 over A₁+E, confirming
   A₁/E soak up essentially all D₄-occupation signal.
3. **1e.3 — Shannon-info correlations strengthen dramatically.**
   §2c.2 in-book A₁⁻ ρ = +0.213 becomes D₄-A₁(s²) ρ = +0.465, and
   D₄-E(s²) all-plies ρ = +0.508 is the strongest Shannon-info
   correlation in the notebook.  D₄-A₁(s²) sign-flips between
   in-book (+0.465) and out-of-book (−0.755) — novel, open for
   interpretation.
4. **1e.4 — accuracy=99 residual is not the story.**  Restricting
   to accuracy=100 children shifts all D₄-occupation correlations
   by < 0.003.  §2d.b stands.
5. **1e.5 — Othello sheaf extrapolation is positive, contra logo
   L7b.5.**  Sheaf at t predicts n_legal_moves at t+10 with R² =
   0.56, essentially matching sheaf at t+10 (R² = 0.56).  Gain vs
   persistence baseline +0.24 (Δ=1) → +0.49 (Δ=10).  Opposite sign
   from logo L7b.5; interpreted as "state-based sheaf constraint
   propagation" vs logo's "trajectory-fiber extrapolation".

**Single-line headline for the notebook §2e:** the D₄-A₁(s²) and
D₄-E(s²) channels are ground-truth-aligned in a Reading-B sense
(edax at d=20 does not capture them), their "A₁ − E" rotated
combination is the marginally strongest univariate Othello summary,
the accuracy=99 archive residual is a non-issue, the Shannon-info
coupling to these channels is 2× stronger than §2c.2 reported, and
the Othello sheaf spectrum carries non-trivial forward-predictive
content for legal-move count.

## Open items / sequel work

1. **1e.3 sign-flip of D₄-A₁(s²) between in-book (+0.465) and
   out-of-book (−0.755)** is novel and unexplained.  Worth:
   - Decomposing out-of-book by `n_empties` bucket (early/mid/late).
   - Checking whether the sign flip happens at the book-coverage
     cliff (empties ≈ 30) or gradually.
2. **1e.5 multivariate predictive gain on richer targets.**  Random
   play makes ρ/empties trivially persistent.  A better trajectory
   target is the A₁⁻ or D₄-A₁(s²) energy Δ moves into the future
   (which is NOT monotone) — that would make persistence weaker and
   give the sheaf features more to predict.  Also: re-run on a
   tournament-play corpus (Barcelona) instead of random play.
3. **Chess-side A₁/E pair check.**  The Othello D₄-A₁(s²) vs
   D₄-E(s²) correlation is the Plancherel-mirror result.  Chess's
   analogous pair was not yet computed at time of §2d.e; the
   corpus-scale Stockfish re-correlation batch in flight should
   produce the chess A₁ vs E cross-channel Pearson.
4. **Harden h9_strict_runner against filename collision.**  It
   hardcodes `phase1d_*` output names; re-running with a different
   archive summary overwrites §2d.b originals if pointed at the
   shared results dir.  An `--out-prefix` flag would prevent this
   footgun.

## Files

Scripts added (this phase):
- [phase1e_multivariate.py](research/phase1e_multivariate.py)
- [phase1e_shannon_observables.py](research/phase1e_shannon_observables.py)
- [phase1e_edax_d20_tasklist.py](research/phase1e_edax_d20_tasklist.py)
- [phase1e_edax_d20_correlations.py](research/phase1e_edax_d20_correlations.py)
- [phase2_predictive_sheaf.py](research/phase2_predictive_sheaf.py)

Scripts modified:
- [takizawa_archive_loader.py](research/takizawa_archive_loader.py) —
  `--min-accuracy` flag + per-row flush.

Result files:
- [phase1e_multivariate.json](results/phase1e_multivariate.json)
- [phase1e_shannon_observables.json](results/phase1e_shannon_observables.json)
- [phase1e_shannon_per_move_observables.csv](results/phase1e_shannon_per_move_observables.csv)
- [phase1e_predictive_sheaf.json](results/phase1e_predictive_sheaf.json)
- [phase1e_predictive_sheaf_pairs.csv](results/phase1e_predictive_sheaf_pairs.csv)
- [phase1e_edax_d20.csv](results/phase1e_edax_d20.csv)
- [phase1e_edax_d20_correlations.json](results/phase1e_edax_d20_correlations.json)
- [phase1d_archive_summary_exact100.csv](results/phase1d_archive_summary_exact100.csv)
- [phase1e_correlations_exact100.json](results/phase1e_correlations_exact100.json)
- [phase1e_spectral_vs_perfectplay_exact100.csv](results/phase1e_spectral_vs_perfectplay_exact100.csv)

Per-seed cache for sheaf trajectories (30 files, ~60 KB each) at
[results/phase1e_sheaf_cache/](results/phase1e_sheaf_cache/).
