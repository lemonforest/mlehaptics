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

## 1e.5b — Predictive sheaf on tournament trajectories with spectral targets — **POSITIVE with crossover**

Runner: [`research/phase1e_predictive_sheaf_pgn.py`](research/phase1e_predictive_sheaf_pgn.py).
Output: [`results/phase1e_predictive_sheaf_pgn_liveothello_2025_all.json`](results/phase1e_predictive_sheaf_pgn_liveothello_2025_all.json).
Corpus: `liveothello_2025_all.pgn` (2178 tournament games, mean
trajectory length 61.7 plies).  Walltime 50.5 min.  Pair counts
112 k–132 k per Δ.

Extends 1e.5 to (a) real tournament play instead of random-play and
(b) spectral targets (A₁⁻, D₄-A₁(s²), D₄-E(s²)) in addition to the
near-monotone state targets (n_legal, ρ).

**n_legal_moves — sheaf retains predictive power under tournament play:**

| Δ | R²(pred) | R²(pers) | gain_vs_pers |
|---|---|---|---|
| 1  | 0.559 | 0.243 | **+0.316** |
| 3  | 0.565 | 0.187 | **+0.378** |
| 5  | 0.580 | 0.126 | **+0.455** |
| 10 | 0.624 | 0.214 | **+0.410** |

Matches 1e.5's random-play result in magnitude (+0.24 → +0.49 there;
+0.32 → +0.41 here).  **Tournament vs random doesn't change the
qualitative finding — the sheaf's constraint on future move-count
is a state-geometry property, not a play-style artifact.**

**A₁⁻ magnetisation energy — crossover between persistence and
sheaf prediction:**

| Δ | R²(pred) | R²(pers) | gain_vs_pers | gain_vs_snap |
|---|---|---|---|---|
| 1  | 0.443 | 0.789 | **−0.345** | +0.012 |
| 3  | 0.442 | 0.597 | −0.155     | +0.030 |
| 5  | 0.438 | 0.467 | −0.029     | +0.044 |
| 10 | 0.418 | 0.321 | **+0.098** | +0.066 |

**Short-Δ regime: persistence dominates.**  At Δ=1 knowing A₁⁻(t)
alone explains 79 % of A₁⁻(t+1) variance.  The sheaf features at t
explain only 44 % — worse than persistence.

**Long-Δ regime: sheaf beats persistence.**  By Δ=10 persistence R²
has decayed to 0.32 while sheaf R² holds at 0.42.  Crossover is
between Δ=3 and Δ=5.  At Δ=10 the sheaf features at t carry
forward-predictive A₁⁻ information that A₁⁻(t) itself does not.

Additional oddity: `gain_vs_snap` is consistently POSITIVE for A₁⁻
(+0.01 to +0.07).  The sheaf at t predicts A₁⁻(t+Δ) slightly BETTER
than the sheaf at t+Δ does.  Most natural reading: the sheaf's
relationship with A₁⁻ is non-stationary across the game, and the
"past" sheaf encodes the trajectory from which A₁⁻(t+Δ) arose more
faithfully than a momentary snapshot of the future sheaf.  Open
interpretation.

**D₄-A₁(s²) occupation — near-monotone, no sheaf benefit:**
Persistence R² = 0.986–0.999 across Δ; sheaf slightly negative gain.
The occupation channel grows almost deterministically with disc
count, so persistence is near-perfect and nothing can improve it.
As expected; treated as a control.

**D₄-E(s²) occupation — persistence decays, sheaf still flat:**
Persistence R² drops from 0.95 (Δ=1) to 0.18 (Δ=10), confirming
E(s²) is genuinely trajectory-dependent.  But R²(pred) is only
~0.11–0.17 across Δ.  Sheaf features do not predict E(s²)
forward — match persistence at Δ=10 and lose at shorter Δ.
Notable that gain_vs_snap rises sharply (+0.07 at Δ=10): the sheaf
at t is a better predictor of E(s²)(t+10) than the sheaf at t+10
itself, even though both are weak.  Another non-stationary
trajectory signature.

**Summary — tournament-play predictive sheaf findings:**

1. n_legal_moves is the sheaf's best predictive target (grows with
   Δ, matches random-play).
2. A₁⁻ energy shows a persistence-vs-sheaf crossover: persistence
   wins short-term, sheaf wins long-term (Δ ≥ ~5–7).  Novel.
3. D₄-A₁(s²) is a negative control (persistence saturates).
4. D₄-E(s²) persistence decays fast but sheaf doesn't pick up the
   slack; an open question whether a richer fiber model would.
5. The `gain_vs_snap` > 0 oddity for A₁⁻ and E(s²) — sheaf at t
   beats sheaf at t+Δ — is a non-stationary sheaf signature worth
   investigating separately.

The original 1e.5 retraction of the logo L7b MISS **stands and
strengthens**: state-based sheaf structure does carry forward-
predictive content, now demonstrated on both random play (state
targets) and tournament play (spectral targets).

## 1e.6 — Sign-flip decomposition — **Simpson's paradox identified**

Runner: [`research/phase1e_signflip_decomposition.py`](research/phase1e_signflip_decomposition.py).
Output: [`results/phase1e_signflip_decomposition.json`](results/phase1e_signflip_decomposition.json).
Uses per-move CSV from 1e.3.

**The §1e.3 in-book (+0.465) vs out-of-book (−0.755) split is
dominated by Simpson's paradox, not by book coverage.**  Sign flip
is a game-phase effect, not a book-cliff effect.

Within-phase Spearman(I_move, D₄-A₁(s²)) by empties range:

| range | N | all | in-book | out-of-book |
|---|---|---|---|---|
| opening (60–53 empties) | 280 | +0.245 | +0.245 | (all in-book) |
| early midgame (52–45)   | 280 | +0.117 | +0.104 | +0.480 |
| late midgame (44–35)    | 350 | +0.283 | +0.126 | +0.321 |
| endgame entry (34–25)   | 350 | +0.065 | +0.100 | +0.033 |
| deep endgame (24–10)    | 525 | **−0.425** | (no in-book) | **−0.440** |
| terminal (9–0)          | 314 | **−0.616** | (no in-book) | **−0.616** |

**Within-phase in-book correlations are small (+0.10–0.25),** far
from the +0.465 aggregate.  The aggregate amplification comes from
Simpson-style between-phase structure — D₄-A₁(s²) and I_move both
grow with filling density, so the between-phase trend boosts rank
correlation on the pooled in-book subset.

**Out-of-book covers mostly post-book deep endgame** (30–0 empties).
Within deep endgame and terminal, within-phase ρ is strongly
negative (−0.44, −0.62).  The aggregate out-of-book −0.755 is
compatible with this floor plus between-phase amplification in the
opposite direction.

**Sign flip occurs at ~24 empties, not ~20.**  The WTHOR book
coverage cliff is at empties ≈ 20 (see §2c.2), but the spectral
sign flip happens 4 plies earlier.  The two are nearby but not
coincident — confirms flip is phase-driven, not coverage-driven.

**D₄-E(s²) has a double sign flip**: +0.128 (opening) → +0.263
(early midgame) → **−0.264** (endgame entry) → **+0.525** (terminal).
A more complex phase trajectory than A₁, motivates a longitudinal
analysis rather than a single aggregate ρ.

**A₁⁻ magnetisation is consistently NEGATIVE within every phase**
(opening in-book −0.274, late midgame in-book −0.419).  The §2c.2
reported aggregate of +0.213 is a pure Simpson's paradox artifact
of between-phase structure; within any single phase A₁⁻ correlates
NEGATIVELY with Shannon info.  **This is a material retraction of
§2c.2's framing**: A₁⁻ does NOT track strategic divergence from
tournament-empirical policy; it tracks game phase.

**Takeaway.**  For trajectory-based claims (Shannon info, move-by-move
analyses) the notebook's previous in-book / out-of-book split is
misleading as a between-group comparison.  Within-phase
decomposition is the cleaner analysis.  The static-50-empty results
(§2d / §1e.1) are unaffected because they are single-phase.

## 1e.7 — Open item follow-ups (Z holonomy, T4 T_eff, T5 chains, faithful-sheaf gain, chess A1/E, engine dispatch)

Seven open items closed in a single session (commits `0f7a74f` …
`345a50e` …`0ace888`), plus the encoder engine-dispatch wiring.

### 1e.7.1 — §2.H5 holonomy characterisation at corpus scale

Runner: [`research/phase1e_holonomy_plaquettes.py`](research/phase1e_holonomy_plaquettes.py).
Output: [`results/phase1e_holonomy_plaquettes.{csv,json}`](results/).

Enumerated **1192 loops** across 7 shape families (unit plaquettes,
2×2 and 3×3 squares, m×1 / 1×m bars, corner triangles, long-jump
rectangles).  Clean structural rule:

  **Z₂ holonomy exists iff the loop is a long-jump W×1 rectangle
  with W ≥ 3** (105/105 such loops non-trivial).

All other 1087 loops are trivial (cos = +1).  The §2.H5 hand-picked
loop (rectangle (0,0)-(0,3)-(1,3)-(1,0)-(0,0), i.e. one of the 35
lj_rect_3x1 instances) is one example of this class.  The effect
is **path-orientation-dependent, not homotopy-invariant**:
lj_rect_1x3 (transpose) is trivial.  Connection form's curvature
concentrates on horizontal long-jumps of width ≥ 3.

### 1e.7.2 — T4 (T_eff, D_eff) thermodynamic trajectory

Runner: [`research/phase1e_t4_thermodynamic_trajectory.py`](research/phase1e_t4_thermodynamic_trajectory.py).
Robust variant: [`research/phase1e_t4_robust.py`](research/phase1e_t4_robust.py).
Outputs: [`results/phase1e_t4_thermodynamic_*.json`](results/), [`results/phase1e_t4_robust_*.json`](results/).

Per-ply T_eff = dE_tot / dS_eff where E_tot = ||enc||² and
S_eff = Shannon entropy of the 12-channel energy distribution:

  Barcelona (N=2184 plies, finite-diff): T_eff median = −11 k
  WC 2005    (N=1418 plies, finite-diff): T_eff median = −12 k
  Barcelona (windowed OLS, window=8, r²≥0.3): T_eff median = −22 k,
                                               IQR [−35 k, −14 k]

Negative T_eff is **robust across both 20-year-apart corpora and
both estimation methods**.  Reading: spectral-energy ANTI-correlates
with Shannon entropy over the channel distribution — as total
energy grows (disc count rises), channel distribution concentrates
(fewer effective channels carry the norm).  Structurally
consistent with the A₁/E Plancherel-budget story (§2d.c).

Mean/outliers are heavy-tailed (|dS|→0 outliers dominate); median
is the honest summary.

### 1e.7.3 — T5 FK-BC flank-cluster size distribution

Runner: [`research/phase1e_t5_cluster_distribution.py`](research/phase1e_t5_cluster_distribution.py).
Output: [`results/phase1e_t5_cluster_distribution.json`](results/).

Extracts maximal same-colour chain lengths (≥ 2) along every ray
from every ply; fits exponential vs power-law.

  corpus                        N chains    mean  max   tau   lambda  preferred
  Barcelona_EGP_2026            141 584     2.94  8     2.67   0.72   exponential
  World_Championships_2005       93 950     2.86  8     2.73   0.77   exponential
  liveothello-2026-APR        1 646 532     2.95  8     2.67   0.72   exponential
  liveothello_2025_all        8 754 052     2.94  8     2.68   0.73   exponential

**All 4 corpora prefer exponential** by ΔAIC of 3 k–221 k.
§10.10 T5's critical FK-BC power-law is rejected.  Remarkable
cross-corpus stability (mean 2.86–2.95, tau 2.67–2.73) across 20
years.  Echoes T1's per-move flip-count result (also exponential).

### 1e.7.4 — Faithful sheaf restriction maps + predictive validation

Runners: [`research/faithful_sheaf.py`](research/faithful_sheaf.py),
[`research/phase1e_predictive_sheaf_faithful.py`](research/phase1e_predictive_sheaf_faithful.py),
[`research/phase1e_faithful_gain_investigation.py`](research/phase1e_faithful_gain_investigation.py).

Replaces the endpoint-only crude restriction maps with bracket-
aware ones.  Edges only exist across active flanks (R2 stable
or R3 pending); restriction maps have α = 1.0 (pending) or
α = 0.5 (stable).  Breaks §3.4's constant-128 kernel dim
artifact: faithful kernel varies **141–188** with state on the
seed=123 trajectory.  λ₂ differs from crude by mean +0.29.

Predictive-sheaf re-run on Barcelona (see §1e.5) now with faithful
restrictions.  `gain_vs_snap > 0` is **ubiquitous**:

  target                    Δ=10 gain_vs_snap
  d4_e_occupation_energy       +0.086
  rho / empty_count            +0.060
  d4_a1_occupation_energy      +0.050
  a1_minus_energy              +0.028

**Investigation of the gain signature** (Probe 1–3 in
phase1e_faithful_gain_investigation.py):

  1. Δ sweep: gain_vs_snap GROWS monotonically with Δ on
     persistence-saturated targets (rho 0.045 @ Δ=7 → 0.104 @ Δ=20).

  2. Train/test split (17/18 games): out-of-sample gain is LARGER
     than in-sample for every target:

       target                    OOS gain_vs_snap
       a1_minus_energy              +0.244  (in-sample +0.028)
       d4_e_occupation              +0.105  (in-sample +0.086)
       rho                          +0.105  (in-sample +0.060)

     **Rules out overfit / survivorship (H2).**

  3. Per-feature ablation: EVERY feature has delta_gain < 0
     (removing any one feature makes predictive lose less than
     snapshot).  No single feature drives the gain; it's a **joint
     feature decorrelation** effect.

**Mechanistic reading (H1, confirmed):**  at time t, the 8 faithful-
sheaf features encode diverse trajectory-relevant info — λ₂
(connectivity), entropy (spectral spread), kernel_dim (bracket-
graph sparsity), λ_max (largest mode).  These features are more
INDEPENDENT at t, so the multivariate regression picks up unique
predictive content per feature.  At time t + Δ, the same features
collapse onto "current state summary" — they become redundant with
each other, and with features of the target.  Hence predictive
regression at t outperforms snapshot regression at t + Δ.

**This is a non-trivial signature of temporal structure in the
faithful sheaf.**  The crude sheaf's constant kernel dim (§3.4)
hid it; the faithful sheaf's position-dependent kernel dim exposes
it.

### 1e.7.5 — Chess A1/E pair check + Simpson's paradox

Runners: [`research/phase1e_chess_a1_e_pair.py`](research/phase1e_chess_a1_e_pair.py),
[`research/phase1e_chess_a1_e_bootstrap.py`](research/phase1e_chess_a1_e_bootstrap.py),
[`research/phase1e_othello_a1_e_per_game.py`](research/phase1e_othello_a1_e_per_game.py).
Outputs: [`results/phase1e_chess_a1_e_{pair,bootstrap}.json`](results/),
[`results/phase1e_othello_a1_e_per_game.json`](results/).

Chess pooled Pearson(E_A1, E_E) = +0.0414 (p = 2e-5) on N=10 729
plies across 3 corpora.  Looks like the Othello -0.834 mirror is
Othello-specific.  **But per-game analysis reveals Simpson's paradox:**

  chess corpus                   pooled     per-game median
  ashchess_N50                   +0.011          -0.178
  drnykterstein_N10              -0.201          -0.582
  hf_N50                         +0.116          -0.171

Chess DOES have within-game anticorrelation (A1/E mirror).  It's
hidden by between-game variation when pooled.  Bootstrap: drnykterstein
sits at 3.3rd percentile of ashchess 10-game resamples — unusual
but within the 95 % null.

**Othello per-game (N = 2177 games, 2025 corpus):**

  pair                       per-game median     pooled
  magn_A1⁻ vs magn_E⁻         **+0.481**          +0.330
  occ_A1⁺  vs occ_E⁺           −0.046            −0.072
  magn_A1⁻ vs magn_B2⁻         +0.310
  occ_A1⁺  vs occ_B2⁺          +0.093
  fiber_ortho_s vs fiber_diag_s +0.799

**Chess and Othello have OPPOSITE-signed per-game A1/E structure.**
Chess (piece-value signal) is −0.18 to −0.58 median (anti-correlation).
Othello magnetisation (Z₂-odd) is **+0.48** median (co-correlation).
Othello occupation (Z₂-even) is weakly negative (−0.05).

The Othello 50-empty static −0.834 is a **phase-specific structural
property** (14-disc configuration), not a general trajectory
signature.  Trajectory-level A1/E structure is game-specific and
differently-signed between chess and Othello.

### 1e.7.5b — A1⁻ drift by phase at 2025 corpus scale

Runner: [`research/phase1e_a1_drift_by_phase.py`](research/phase1e_a1_drift_by_phase.py).
Output: [`results/phase1e_a1_drift_by_phase_2025.json`](results/phase1e_a1_drift_by_phase_2025.json).
Corpus: 2178 games, 132 k pairs at Δ=1.  Walltime ~55 min.

Barcelona (35 games) showed a messy picture — small N per bucket
couldn't cleanly localise the `gain_vs_snap > 0` signature.  2025
resolves it:

  gain_vs_snap (crude sheaf → A1⁻ energy) at Δ=10, by phase:

  phase               N_pairs   R²_pred   R²_snap   R²_pers  gain_snap
  opening              17 403    +0.024    +0.084    +0.006   **−0.060**
  early_midgame        17 374    +0.024    +0.086    +0.010   −0.062
  late_midgame         21 661    +0.034    +0.050    +0.045   −0.016
  endgame_entry        21 609    +0.039    +0.062    +0.090   −0.023
  **deep_endgame**     32 308    +0.120    +0.074    +0.109   **+0.047**
  terminal              2 173    +0.146    +0.390    +0.028   −0.244

**The non-stationary sheaf signature is concentrated in deep
endgame** (24–10 empties).  Opening/midgame have `gain_vs_snap < 0`
(snapshot beats predictive — standard expectation).  Deep endgame
reverses it.

**Interpretation:** deep endgame is where the board is densely
populated with latent bracket structures.  The sheaf at time t
captures the full bracket network; by t + 10 many brackets have
resolved (flipped into stable flanks or disappeared).  The
"which brackets were pending at t" information is gone at t + Δ,
leaving the snapshot sheaf's features only describing current
state.

Consistent with §1e.7.4's faithful-sheaf finding: H1 (trajectory
memory) holds on the crude sheaf too, but only in the phase where
bracket-structure dynamics dominate the A1⁻ signal.  At opening,
A1⁻ is dominated by the initial 4-disc configuration's D₄×Z₂
structure, which has no trajectory memory to encode.

Terminal (N=2173) is a small-sample outlier; games that reach
Δ+10 past terminal are a small self-selected subset.

**This finding tightens §1e.5b's (+0.066) pooled 2025 result:**
the effect is phase-localised, not diffuse.  Future predictive-
sheaf work should segment analyses by n_empties.

### 1e.7.7 — Simpson's paradox mechanism (chess vs Othello)

Runner: [`research/phase1e_simpson_mechanism.py`](research/phase1e_simpson_mechanism.py).
Output: [`results/phase1e_simpson_mechanism.json`](results/phase1e_simpson_mechanism.json).

Law-of-total-covariance decomposition of pooled Pearson into
within-game and between-game components:

  corpus                                      pooled   within   between
  chess/ashchess_N50                          +0.011   −0.117   **+0.667**
  chess/drnykterstein_N10                     −0.201   −0.315   **+0.605**
  chess/hf_N50                                +0.116   +0.022   **+0.663**
  othello/Barcelona magn_A1⁻ × E⁻             +0.353   +0.386   **−0.431**
  othello/2025 magn_A1⁻ × E⁻                  +0.330   +0.385   **−0.479**
  othello/2025 occ_A1⁺ × E⁺                   −0.072   −0.051   **−0.592**

**Clean mechanism:** the between-game component (correlation of
per-game means of A1 and E) is **tightly +0.60 to +0.67 for all
three chess corpora**.  Chess games with high mean A1 also have
high mean E — game-to-game baseline variation co-varies strongly.
Within any single chess game, A1 and E mildly anti-correlate
(mean −0.15).  Pooled Pearson reflects both: near-zero, because
the positive between and negative within partially cancel.

**Othello magnetisation reverses the sign structure:** between-
game is strongly NEGATIVE (−0.48 on 2025), within-game is
strongly POSITIVE (+0.39).  Games whose mean A1⁻ is high tend to
have low mean E⁻ — **opposite direction from chess**.  Pooled is
positive because the within-game positive is the larger
contribution here.

**Othello occupation:** both within and between are negative
(weak −0.05 and strong −0.59).  Pooled weakly negative because
within-game variance dominates the occupation signal.

The chess "mirror" that §1e.7.5 identified at per-game median
(−0.18 to −0.58) reflects the within-game component with
medium-range noise.  The between-game +0.67 is the larger
statistical effect when pooling.

### 1e.7.8 — T4 log-transform robust variant

Runner: [`research/phase1e_t4_logtransform.py`](research/phase1e_t4_logtransform.py).
Output: [`results/phase1e_t4_logtransform_*.json`](results/).

Three variants compared on Barcelona:

  variant     slope_all median       slope_hi_r2 median    IQR (hi_r2)
  raw         −14 726                −22 188                [−34 803, −14 008]
  **log_E**   **−4.33**              **−6.04**              [−8.48, −4.28]
  log_both    −3.40                  −4.85                  [−6.70, −3.37]

`log_E` (regress log(E_tot) on S_eff) compresses the raw slope's
heavy tail while preserving the negative sign.  Interpretation:
a unit increase in Shannon entropy corresponds to a factor of
exp(−6.04) ≈ 0.002 change in total spectral energy (high-r² wins).

`log_both` (log-log / elasticity): a 1 % change in S_eff
corresponds to a −4.85 % change in E_tot.  Same sign, similar
magnitude.  Either log variant is a dramatically more stable
estimator than the raw slope, without changing the qualitative
conclusion (negative T_eff).

### 1e.7.9 — C encoder ctypes path

Scripts: [`research/othello_spectral/runtime.py`](research/othello_spectral/runtime.py)
gains `find_c_dll()`, `_load_dll()`, `encode_768_c_ctypes()`,
`encode_768_c_ctypes_batch()`.

The subprocess-based C path was 7.6 s on APR 2026 (25 k states)
vs Python's 2.7 s — the stdio round-trip dominated single-threaded
encoding.

Building `othello_spectral.dll` and calling via `ctypes` bypasses
the subprocess entirely.  Benchmarks:

  path                    encode time (25k states)    wall total
  python                  3.0 s                        18.4 s
  c (ctypes DLL)          3.1 s                        17.8 s
  c (subprocess exe)      7.6 s                        21.7 s

`ctypes` is 2.5× faster than the subprocess path and matches
Python on this corpus.  Bit-identical .spectralz body SHA
matches between py and ctypes (`dd8f68cc20c2f65a` on APR 2026).
Parity verified at float64 precision on 8 random states via
`tests/test_c_py_parity.py::test_ctypes_dll_parity_if_present`.

CLI engine dispatch prefers ctypes when the DLL is present and
falls back to the subprocess binary when only the exe is built.
Both paths respect the VERSION string match + smoke test in
`auto` mode.

Build: `clang -std=c17 -O2 -shared -I c_encoder/include
c_encoder/src/othello_spectral.c -o c_encoder/othello_spectral.dll`.
Windows exports are gated by `__declspec(dllexport)` in
`othello_spectral.h` (via the `OTHELLO_API` macro).

### 1e.7.6 — C encoder body + engine dispatch

Scripts: [`research/othello_spectral/c_encoder/src/othello_spectral.c`](research/othello_spectral/c_encoder/src/othello_spectral.c),
[`research/othello_spectral/runtime.py`](research/othello_spectral/runtime.py).

  - ANSI C17 encoder body filled in, bit-identical to Python at
    float32 precision on 9 test states (starting + 8 random seeds).
  - Codegen brace-count bug fixed: emit_c_tables was generating one
    extra brace level; clang silently truncated each row to its
    first value (all-zero channels).  After fix, clang -Wall
    builds with zero warnings.
  - Engine dispatch: `--engine {py, c, auto}` on the `encode-pgn`
    CLI; env vars `OTHELLO_SPECTRAL_BIN` (path), `OTHELLO_SPECTRAL_ENGINE`
    (default mode).  `auto` mode **verifies** the C binary (version
    string + byte-identical starting-position encoding) before
    selection; silent fallback to py on verification failure.
  - End-to-end parity: Barcelona 35-game corpus encoded via py and
    c gives byte-identical .spectralz bodies (SHA256 match on all
    2184 frames).

Perf note: Python 2.7 s vs C 7.6 s on 25 k state encodes (APR
2026).  C subprocess stdio round-trip dominates single-threaded
encoding; C would win with direct memory sharing or multi-worker
orchestration.  Filed as perf improvement for a later revision.

## Revised open items / sequel work

1. **1e.5 multivariate predictive gain on richer targets.**  See
   1e.7.4 — this is substantially closed.
2. **Chess-side A₁/E pair check.**  See 1e.7.5 — CLOSED.
3. **Harden h9_strict_runner against filename collision.** Fixed —
   `--out-prefix` flag landed in commit `fd6246e`.
4. **A1-drift on 2025 corpus** (queued, running as of this write).
   Barcelona result (§1e.5b's A1⁻ drift signature decomposed by
   phase bucket, 2099 plies, N=35 games) was statistically thin.
   2025 rerun at N=2178 games promises meaningful per-bucket
   effect sizes.
5. **T4 outlier robustification** — windowed variant
   (phase1e_t4_robust.py) now lands median −22 k with IQR
   [−35 k, −14 k].  Still heavy-tailed if windows are too short;
   worth a log-transform follow-up.
6. **Faithful sheaf gain investigation on 2025 corpus** — §1e.7.4's
   Barcelona result is qualitatively consistent with §1e.5b's 2025
   result; a 2025 rerun of the OOS probe would confirm the
   joint-feature-decorrelation interpretation at statistical power
   1–2 orders of magnitude higher.
7. **C encoder batch perf.**  Current subprocess pipe is
   single-threaded and stdio-bound.  Shared-memory or direct-PGN
   ingest in the C layer would make the C path actually faster than
   Python for large corpora.
8. **Chess Simpson's paradox mechanism.**  Why are chess games'
   A1/E per-game correlations tightly negative (−0.18 to −0.58
   median) while pooling flattens them?  Likely between-game
   baseline variation (game-to-game shifts in mean A1 and mean E)
   dominates within-game anticorrelation.  Worth factoring with a
   mixed-effects model.

## Files

Scripts added (this phase):
- [phase1e_multivariate.py](research/phase1e_multivariate.py)
- [phase1e_shannon_observables.py](research/phase1e_shannon_observables.py)
- [phase1e_edax_d20_tasklist.py](research/phase1e_edax_d20_tasklist.py)
- [phase1e_edax_d20_correlations.py](research/phase1e_edax_d20_correlations.py)
- [phase2_predictive_sheaf.py](research/phase2_predictive_sheaf.py)
- [phase1e_signflip_decomposition.py](research/phase1e_signflip_decomposition.py)
- [phase1e_predictive_sheaf_pgn.py](research/phase1e_predictive_sheaf_pgn.py)
- [phase1e_holonomy_plaquettes.py](research/phase1e_holonomy_plaquettes.py) (Open-4)
- [phase1e_a1_drift_by_phase.py](research/phase1e_a1_drift_by_phase.py) (Open-1)
- [phase1e_t5_cluster_distribution.py](research/phase1e_t5_cluster_distribution.py) (Open-3)
- [phase1e_predictive_sheaf_faithful.py](research/phase1e_predictive_sheaf_faithful.py) (Open-5)
- [phase1e_faithful_gain_investigation.py](research/phase1e_faithful_gain_investigation.py) (iii MAIN EVENT)
- [faithful_sheaf.py](research/faithful_sheaf.py)
- [phase1e_t4_thermodynamic_trajectory.py](research/phase1e_t4_thermodynamic_trajectory.py) (Open-2)
- [phase1e_t4_robust.py](research/phase1e_t4_robust.py) (ii)
- [phase1e_chess_a1_e_pair.py](research/phase1e_chess_a1_e_pair.py) (Open-7)
- [phase1e_chess_a1_e_bootstrap.py](research/phase1e_chess_a1_e_bootstrap.py) (iv)
- [phase1e_othello_a1_e_per_game.py](research/phase1e_othello_a1_e_per_game.py) (iv+)
- [phase1e_replay_from_features.py](research/phase1e_replay_from_features.py)
- [phase1e_flipcount_distribution.py](research/phase1e_flipcount_distribution.py) (T1)
- [phase1e_wthor_scale_retest.py](research/phase1e_wthor_scale_retest.py) (1c.3 retest)

Encoder package:
- [othello_spectral/](research/othello_spectral/) — v0.2.0 with
  py/c/auto engine dispatch, bit-identical C17 reference encoder
  (Open-6 + engine wiring)

Result files (1e.5b, 1e.6):
- [phase1e_signflip_decomposition.json](results/phase1e_signflip_decomposition.json)
- [phase1e_predictive_sheaf_pgn_liveothello_Barcelona_EGP_2026.json](results/phase1e_predictive_sheaf_pgn_liveothello_Barcelona_EGP_2026.json)
- [phase1e_predictive_sheaf_pgn_liveothello_2025_all.json](results/phase1e_predictive_sheaf_pgn_liveothello_2025_all.json)

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
