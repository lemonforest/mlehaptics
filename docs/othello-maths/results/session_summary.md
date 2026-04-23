# Othello Spectral — Session Summary

**Date:** 2026-04-22
**Branch:** `othello-spectral-foundations-v0.1.0`
**Scope:** Phase 0 scaffold + Phase 1 H1-H9 + E1-E8 + Phase 2 minimal
sheaf + Phase 3 preflight.  Phase 4 (WTHOR empirical) scoped but not
executed.

## What passed

- **H1 (KNOWN / CONFIRMED)** Grid Laplacian vs 2D DCT: subspace gap
  3.4e-14, eigenvalue residual 7.1e-15.  Identical to chess §2.
- **H2 (NOVEL / CONFIRMED)** 8-ray D4 decomposition `2 A1 + B1 + B2 +
  2 E` verified exactly by character projection.
- **H3 (NOVEL / CONFIRMED, stronger than stated)** B1 and B2 ray modes
  are not just distinct — they lift to 64x64 operators that are
  **Frobenius-orthogonal** (inner product 0 exactly).  This is a
  stronger structural statement than the prompt's "detectable
  factor" criterion.
- **H4 (NOVEL / CONFIRMED)** `L_ortho` vs `L_diag` spectra differ at
  mean degree (1.75 vs 1.53, rel diff 0.125) and bandwidth (7.72 vs
  6.83, rel diff 0.116); lambda_2 matches.
- **H5 (NOVEL / CONFIRMED)** Static ray bundle has a Z_2 holonomy
  around at least one small loop (rectangle loop
  (0,0)-(0,3)-(1,3)-(1,0): cos = -1.0 exactly).  Cleaner signal
  than chess -0.016 because Othello Z_2 is exact.
- **H7 (KNOWN / CONFIRMED)** Coprime (row, col) generators exist for
  all three candidate encoder dimensions.  For D = 768 (rank-2 fiber),
  (7, 11) gives 64 distinct phases.  Caveat: must verify phase
  uniqueness, not just individual coprimality.
- **H8 (KNOWN / CONFIRMED)** D_4 x Z_2 invariance of the encoder
  verified at 1e-10: A1- is D_4-invariant and Z_2-odd; A1+ on
  occupation s^2 is fully D_4 x Z_2-invariant.
- **E1 (CONFIRMED absence)** Undirected ray operators have zero
  antisymmetric content; no knight-style DCT orthogonality (no
  knight move); no rank-5 piece-species fiber (single disc type).

## What came back PARTIAL

- **H6 (PARTIAL, open exploration by design)** Four candidate ranks
  from four constructions: rank-2 (orbit count), rank-4 (undirected
  stack — pairs coincide), rank-8 (directed or D4xZ2-projected
  degree signatures).  **Rank-6 did not fall out as an operator rank
  from any construction** — it is an irrep multiplicity, not a
  stacked-matrix rank.  Recommendation: production encoder at
  D = (2 + 10) * 64 = 768 with rank-2 fiber.
- **E2 (PARTIAL, structural sketch only)** Local Z_2 grading on the
  3-state Blume-Capel fiber via parity operator
  `diag(-1, +1, -1)` — CP^2 sigma model structure on occupied cells.
  Full Jordan-Wigner deferred.
- **E3 (PARTIAL, suggestive)** Spearman(rho, A1- energy) = +0.671,
  p = 1.5e-40 over 300 positions from 5 games.  Disc density tracks
  magnetisation spectra monotonically but not perfectly.
- **E4 (PARTIAL)** Compass-model ground states are reachable as
  Othello 64-0 terminal states.  Distance from random-play terminal
  is large (hamming 16 for a 48-16 split); distance from optimal
  play deferred.
- **E5 (PARTIAL)** Flank-cluster histogram collected from 20 random
  games (N = 7216 candidate flip counts, mean 2.28, std 1.81, max
  13).  Distribution-fit (power-law vs exponential vs FK-BC) deferred
  to tournament data.
- **E6 (PARTIAL)** Dynamic sheaf — see Phase 2 section below.
- **E7 (PARTIAL)** Disc-count monotone as T-breaker probed on one
  game; no clean signal at N=1.  Needs aggregate statistics.

## What came back UNDETERMINED

- **H9 (UNDETERMINED)** A1 depth-gap transfer from chess to Othello.
  Requires Takizawa 2023 Zenodo dataset and an Othello engine for
  variable-depth evaluation.  Surrogate "is A1- energy non-trivial
  across positions" confirms the protocol is sensible (mean 3.64,
  std 7.84 across 30 positions).
- **E8 (UNDETERMINED)** Takizawa perfect-play correlations — blocked
  on the same dataset.

## Phase 2 — Dynamic sheaf Laplacian

Played one random game to terminal (60 moves).  At each state built
the minimal sheaf Laplacian (3-state Blume-Capel vertex stalks,
3-dim edge stalks, crude bracket-in-progress restriction maps).
Per-move spectrum:

    rho range:          0.062 to 0.984
    lambda_2:           0.223 to 0.934 (mean 0.571)
    entropy:            3.881 to 4.029
    kernel dim:         constant 128 (artefact of simplified restrictions)
    legal-move count:   1 to 18

    Spearman(rho, lambda_2)           = -0.008  (null)
    Spearman(legal_moves, lambda_2)   = +0.765  (p = 1.1e-12)

**Headline finding:** the sheaf spectral gap tracks **legal-move
count**, not disc density.  The observable is non-trivial and has a
structural interpretation (more legal placements -> more connected
flank graph -> wider spectral gap).

**L7b caveat applies.**  This is a SNAPSHOT correlation.  We have NOT
tested whether the sheaf spectrum at time `t` predicts the spectrum
or game state at `t + delta`.  Following the logo-maths L7b
retraction template, the sequel must test predictive claims
explicitly before asserting them.

## Bugs fixed along the way

1. **D4 character table misalignment.**  Initial B1/B2 rows inherited
   from chess convention were not constant on conjugacy classes
   `{g4, g5}` and `{g6, g7}` in our element numbering.  Idempotence
   failed with error 0.64 on E- projection; fixed by conjugacy
   verification and correct class assignment.  Corrected values:
   `B1 = [1, -1, 1, -1, +1, +1, -1, -1]`,
   `B2 = [1, -1, 1, -1, -1, -1, +1, +1]`.
2. **Coprime generator search.**  First admissible prime pair
   (3, 7) for D = 1024 collides because `(7, -3)` is a Diophantine
   solution to `r*p + c*q = 0` in the 8x8 range.  Fixed: exhaustive
   64-phase uniqueness check, not just gcd.
3. **Z_2 group action on Z_2-even functionals.**  E3's initial
   formulation used `project_irrep(s^2, "A1+")` which is trivially 0
   under our Z_2-odd group action.  Replaced with D_4-only A1
   projection of `s^2`, giving the expected Spearman +0.998 with
   disc density.

## What's scoped to the sequel

1. Phase-operator move engine — full construction against
   `OTHELLO_PHASE_OP_PREFLIGHT.md`.
2. WTHOR empirical tests T1-T5 (flip-count power-law fit, B1 vs B2
   trajectory populations, Shannon info per move, (T_eff, D_eff)
   trajectory, flank-cluster FK-BC fit).
3. H9 A1 depth-gap against Takizawa perfect play.
4. E7 disc-count T-breaker at N = many games.
5. E8 perfect-play correlation with spectral observables.
6. Refinement of the sheaf restriction maps to be segment-bracket-
   aware rather than endpoint-based.  Expected to reduce the
   constant kernel dimension of 128.
7. Predictive validation of the sheaf spectrum (L7b template).

## Reproducibility

All Phase 0-2 code is at `research/`.  Run order is in
`OTHELLO_SPECTRAL_INSTRUCTIONS.md`.  Total wall time under 30
seconds on a laptop with NumPy / SciPy.  Deterministic: explicit
seeds in every random-draw test.
