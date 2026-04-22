# Parallel King-Attack Encoder: Notebook Supplement

**Status:** working supplement. Triggered by §11.5.6's validated null
for path-2 check filtering and §11.6.6.1's three-corpus DRIFT null on
`encode_640`. Asks whether a parallel HDC instrument targeting
king-attack structure can carry the signal `encode_640` does not.

**Framing:** this is not an extension of `encode_640`. It is a parallel
instrument built from the same mathematical discipline that produced
`encode_640`. Per UTLP S3 §14's segmentation result, the combined
representation is `[encode_640 | encode_king_attack]` with the two
segments concatenated rather than superimposed.

**Language discipline.** Same as the main supplement: polarization,
lattice domain, phase transition, coprime cyclic phase space. The
"king" in "king-attack encoder" is the royal polarization state
under attack; the encoder measures the field-theoretic structure of
attack relationships against that polarization.

**Architectural constraint — UTLP S3 §14.** Adding a new channel by
superposition into `encode_640` would rotate every dimension's
sign-vote and destroy the existing similarity structure (Frady et al.
2022 cross-tier interference; see UTLP S3 §14.2). Segmentation —
concatenating a parallel vector rather than mixing channels — avoids
this. The §11 baselines remain valid; the new signal lives in a
disjoint subspace.

---

## §12.1 Motivation

Three findings from the §11 arc frame the §12 question:

1. **§11.3 / §11.4.** The phase-operator move generator reproduces
   python-chess's `pseudo_legal_moves` at 100% across four independent
   channels (A/B/C/python-chess) after the §11.4.3.1 castling fix and
   the §11.4.3.2/3 en passant + promotion wrappers. The 640-dim
   encoder's coprime-cyclic representation fully captures chess move
   geometry.

2. **§11.5.6.** Phase-tuple similarity between pre-move and post-move
   `encode_640` vectors does **not** correlate with `is_check_unsafe`.
   Max |ρ| = 0.097 across nine polarization/capture slices, n = 3393
   transitions. The encoder is blind to king-attack geometry at the
   similarity level.

3. **§11.6.6.1.** The same encoder produces continuous trajectories
   through game positions rather than discrete phase-cells. Across
   three structurally orthogonal corpora (110 games, 14,729 plies,
   GM classical / FM blitz / engine blitz), all 15 drift-ρ measurements
   are strongly positive (+0.46 to +0.84) and cluster counts rise
   monotonically with τ without a plateau.

**Shared diagnosis.** `encode_640` is a **content descriptor** (what
pieces are at what phases) rather than a **discontinuity detector**
(what's dangerous, what's transitional). The construction — D4
irreps plus rank-3 fiber SVD plus FA/FD channels — produces
bundled-HDC superpositions where every piece contributes to every
mode. Changes accumulate smoothly. None of the constituent
derivations produces discrete cluster boundaries or king-attack
geometry as a first-order output.

**The §12 question.** Can a parallel HDC instrument, derived from
the same mathematical discipline as `encode_640` but targeting
king-attack structure specifically, expose signal that `encode_640`
does not?

**Three possible outcomes** (per §11.7.4 discipline):

- **|ρ| > 0.3 on any derivation:** king-attack encoder viable. The
  HDC family extends to king-attack content. §11.5's null was
  specific to `encode_640`, not structural to the encoder family.

- **|ρ| < 0.1 across all three derivations:** the construction
  pattern does not naturally produce king-attack content. The §11.5
  null generalizes to a structural property of the encoder family.
  Three independent derivations failing is strong evidence that the
  mathematics does not support the construction.

- **0.1 ≤ |ρ| < 0.3 on any derivation:** ambiguous. Researcher
  decides whether to refine derivations or accept the ambiguity.

All three outcomes advance the research record. None is wasted effort.

**Why now.** §11.5's null left open whether a different encoder might
carry the signal. §11.6 sharpened the question: whatever constituent
mathematics would produce **discontinuity structure** on game
trajectories is the same mathematics that would plausibly produce
**king-attack signal** on individual transitions. Both are about the
encoder being sensitive to threshold crossings rather than to
continuous accumulation. Derivation A (king-centered Laplacian
eigendecomposition) is the most motivated candidate in this light;
its eigenstructure is a property of the position-dependent attack
graph, and topology changes discretely when a piece moves into or
out of an attack line. Whether that discontinuity actually correlates
with `is_check_unsafe` is empirical — but the construction has a
structural reason to expect the correlation, which is more than §11.5
could say in advance.

## §12.2 Derivation discipline

Each channel in the king-attack encoder must be derivable from a
**specific mathematical object**. Just as `encode_640`'s channels
come from D4 irreps, fiber SVD, pawn antisymmetry, and diagonal
deviation — each with its own derivation — §12's channels must come
from named mathematical objects of the lattice and the attack
structure. No channel may exist because a use case demands it. No
channel may be tuned to produce a desired correlation outcome.

This is the same rule as §11.7.4: record failures, do not repair them.

If the mathematics does not produce a coherent channel, the
construction fails and we record the failure as the finding. Do not
engineer around it.

## §12.3 Derivation A — King-centered Laplacian eigenchannel

**Mathematical object.** The position-dependent 64×64 attack
Laplacian L_ka, where L_ka[i, j] = −1 if square j is attacked by an
opponent piece on square i (with i ≠ j), L_ka[i, i] = deg(i), and
L_ka[i, j] = 0 otherwise. This is the combinatorial Laplacian of the
opponent-attack graph restricted to the current position. Because the
attack relation is directed but the eigenstructure is more
interpretable on the symmetric version, the working definition
symmetrizes via L = D − (A + Aᵀ)/2; the directional content is
retained in the unsymmetrized A_ka consumed by Derivation B.

**Channel derivation.** Compute eigendecomposition of L_ka. Project
the king's unit impulse δ_king (a 64-dim vector with 1 at the king's
square and 0 elsewhere) onto the first k eigenvectors (ascending
eigenvalue order). The projection magnitudes form a k-dimensional
feature vector.

k is chosen empirically to match `encode_640`'s fiber-channel count
(3 or 5). Phase A defaults k = 5. Variance-explained at k = 5 is
reported as a diagnostic on a representative position sample; if
below ~80%, the eigenchannel is not a faithful summary and the
derivation's utility is limited by its information capture.

**Why this is structurally motivated.** L_ka is position-dependent;
its topology changes discretely when pieces move into or out of
attack lines. The eigenstructure therefore changes discretely too.
This is the discontinuity mechanism `encode_640` lacks. Whether the
discontinuities correlate with `is_check_unsafe` is empirical.

## §12.4 Derivation B — D4 decomposition of attack adjacency

**Mathematical object.** The binary attack adjacency A_ka, where
A_ka[i, j] = 1 iff j is attacked by an opponent piece on i, 0
otherwise. Note A_ka is in general **not symmetric** (attack is
directed) and **not D4-invariant** (it depends on the specific piece
positions).

**Channel derivation.** Reduce A_ka to a 64-dim signal via row-sum —
the total outgoing attacks from each source square (0 for squares
not occupied by an opponent piece). Project that 64-dim signal onto
the five D4 irreps using the same Serre character projection formula
`encode_640` uses for its board signal
(`chess_spectral.tables.project_irrep`). This produces five 64-dim
channels A1_ka, A2_ka, B1_ka, B2_ka, E_ka, paralleling the five
D4-irrep channels of `encode_640`.

**Known tension.** The projection is approximate because the source
signal derived from A_ka is not D4-symmetric in general. The
projection returns the best-fit D4-equivariant component in each
irrep. Whether that approximation carries useful signal or degenerates
to noise is empirical — §12.6 analysis reports per-irrep variance
explained by the projected component as a diagnostic.

**Alternative signal choices** (deferred). Column-sum (total incoming
attacks per square) or an attacker-type-weighted row-sum could be
substituted for the plain row-sum. Phase A uses row-sum as the
simplest first choice; if Phase A crosses the viability threshold
on a different signal, that would be a finding about *which*
projection carries the information.

## §12.5 Derivation C — Attack operator from king's phase

**Mathematical object.** The §11.4.3.1 P_castle pattern generalized
to king-attack: a composite operator on the king's phase that
enumerates, per attacker type and per direction class, whether the
corresponding phase shift from the king lands on an occupied square
of the right attacker type.

**Channel derivation.** For each attacker type t ∈ {N, B, R, Q, K, P}
and each direction class d in t's attack pattern, compute the phase
shift Δ_{t,d} from the king. For the king's current phase φ_K in
the current position, count the number of opponent-t pieces at phases
φ_K + k · Δ_{t,d} mod 640 for k ∈ {1, …, 7} (sliders, weighted by 1/k
so closer attackers count more and the ray stops at the first
blocker) or k = 1 (non-sliders). Pawn attack squares use the §11.5
diagonal scheme, split per diagonal for a 2-component pawn signal.

The (attacker_type × direction_class) enumeration yields 16 scalar
components in Phase A, packed into a 16-dim feature vector:

- 4 rook-ray densities (+row, −row, +col, −col) — rooks and queens
- 4 bishop-ray densities (+NE, −NE, +NW, −NW) — bishops and queens
- 1 knight attack count
- 1 king adjacency count
- 2 pawn attack counts (per diagonal)
- 4 reserved zero channels for future extensions

**Relationship to path-1 `phasecast_is_check`.** Derivation C is the
vector-valued generalization of `phasecast_is_check` from the §11.5
substrate. The boolean answer to "is the king attacked?" reduces
these 16 components to "is any of them positive"; C keeps them as a
continuous signature. C therefore is *expected* to correlate with
`is_check_unsafe` because it literally enumerates the components of
`is_check_unsafe` as continuous values.

**Purpose of including C.** It serves as a **refined baseline**. Any
derivation (A or B) that fails to beat C's correlation is carrying
less signal than a straight enumeration of attack-line occupation.
If A or B beats C, it means those derivations expose structure the
direct enumeration does not — which would be the genuine §12 finding.

## §12.6 Assembly protocol

Do not prematurely commit to an assembly. Phase A builds A, B, C
independently and measures their pairwise cosines plus their
correlations with `is_check_unsafe`. Only if Phase A produces
usable signal does Phase B address assembly.

Phase A reports:

- Per-derivation |ρ(similarity, is_check_unsafe)| on the §11.5 CSV
  (3393 transitions, existing labels).
- Per-derivation pairwise cosines across a representative sample
  of positions — if cos(A, C) > 0.5 the two are highly correlated
  and A adds little over C; if cos(A, C) < 0.2 they measure
  different things.
- Variance-explained diagnostics per Derivation A's k and per
  Derivation B's irrep.
- Per-call timings for each derivation (µs per position).

Phase B (conditional on Phase A crossing |ρ| > 0.3 for any derivation):

- Concatenation architecture `[encode_640 | encode_king_attack]`,
  per UTLP S3 §14.3 segmentation.
- Dimensionality budget, channel layout, Serre-projection choices.
- Write-back to `chess_spectral` as a new encoder variant — not a
  modification of `encode_640`. §11 baselines must remain reproducible
  against the unchanged `encode_640`.

## §12.7 Evaluation — success, null, ambiguous

Same three-outcome framework from §11.5 and §11.6.6.1:

- **|ρ| > 0.3 on any derivation:** king-attack encoder is viable.
  Record as validated finding. Phase B is unblocked pending
  researcher review.

- **|ρ| < 0.1 across all three derivations:** validated null. The
  construction pattern does not naturally produce king-attack signal.
  §11.5's null generalizes to a structural property of the encoder
  family.

- **0.1 ≤ |ρ| < 0.3 on any derivation:** ambiguous. Researcher
  decides whether to refine derivations (Phase A2 with alternative
  signal choices for B, different k values for A, different
  reductions for C) or accept the ambiguity as the §12.10 finding.

Per §11.7.4, record failures; do not tune derivations to produce
desired outcomes. The numbers are the finding.

### §12.7.1 Phase A2 — evaluation refinements

Phase A's three-corpus extension produced an AMBIGUOUS categorical
result with two evaluation-harness bugs that prevented a clean test
of Derivations A and C:

**Derivation A at k=5 did not test the eigenchannel hypothesis.**
Variance-explained on δ_king at k=5 was 7–11% across the three
corpora. The first five eigenvectors of the attack Laplacian carry
almost none of the king-impulse energy; attack-line structure lives
in higher-frequency modes. A's measured |ρ|=0.161–0.179 tested "the
smoothest 5 of 64 modes carry some signal," not the full eigenchannel
hypothesis. Phase A2 re-runs Derivation A at k=16 (and reports
variance-explained at that k as a diagnostic). If variance-explained
at k=16 is still below 0.8, the CLI accepts `--k-for-a` values up to
32; the first k that achieves ≥0.8 variance-explained on a
representative position sample is the honest test of A.

**Derivation C's cosine metric did not measure corpus-relevant
change.** Every sampled position in the three corpora has a king not
under direct attack, so `derivation_c_channel` returns all-zeros on
every row, and cosine of two zero vectors collapses to 0.0. C's
feature vector is correct; the cosine summary wrapped around it was
the wrong reduction for corpora where both sides of the transition
have zero-magnitude C vectors. Phase A2 adds two alternative scalar
summaries alongside cosine:

- `delta_c`: L2 norm of (C_after − C_before). Nonzero whenever the
  move changes any component of the king-attack vector, even when
  both endpoints are near-zero.
- `mag_c_after`: L2 norm of C_after alone. Captures the post-move
  attack density directly; its correlation with `is_check_unsafe` is
  expected to be near-1 by construction (`is_check_unsafe` is
  literally "some component of C_after is positive"), and serves as
  a sanity check that the evaluation pipeline recovers the
  tautological baseline.

The three C metrics together let us distinguish:

- "C's derivation does not carry signal" (all three near zero)
- "C's derivation carries signal but cosine is the wrong metric"
  (cosine near zero, `delta_c` and/or `mag_c_after` above threshold)
- "C's evaluation pipeline has a bug beyond the metric choice"
  (`mag_c_after` fails to recover the near-1 tautological baseline)

**Derivation B is not refined.** Its current three-corpus evaluation
is methodologically sound. Its ambiguous result (single corpus
crosses 0.3 on a single slice; does not replicate on other corpora)
is the honest research finding. Per §11.7.4, alternative B signals
are not explored in Phase A2.

Phase A2 emits new CSVs with `_a2` suffix on disk; Phase A CSVs
remain unchanged as part of the research record.

### §12.7.1.1 Turn-flip wrapper fix

Phase A2's tautological-baseline check (|C_after| correlation with
`is_check_unsafe` should be near 1.0 by construction) halted the
three-corpus re-run when the baseline failed on drnykterstein. The
diagnosis was a missing `board.turn` flip in all six similarity
wrappers across Derivations A, B, and C: after `board.push(move)`,
python-chess flips `board.turn` to the opponent, and the subsequent
call to `derivation_*_channel(board_after)` queries the wrong king
(for A and C via `board.king(board.turn)`) or the wrong attacker
color (for B via `opp_color = not board.turn` inside
`attack_adjacency`). The correct pattern — established in
`phase_operators/phase_check_detection.move_leaves_king_in_check` —
flips `board.turn` back before the post-move channel computation.

The fix is one line per wrapper: `board_after.turn = not
board_after.turn` after the push. The channel functions themselves
(`derivation_a_channel`, `derivation_b_channels`,
`derivation_c_channel`) and the underlying `attack_graph`
primitives are unchanged.

Consequence for the research record: the original Phase A
three-corpus numbers (B's 0.332 single-corpus crossing, A's
0.161–0.179 across corpora, C's NaN) were computed on wrong-side
measurements. The three-corpus protocol still detected
non-replication of B, but the quantity being measured was not the
one the derivation was designed to produce. Phase A2 (post-fix)
supplies the fresh three-corpus matrix that §12.10.1 interprets.

The tautological-baseline design pattern is preserved as a reusable
check for any future evaluation harness: any derivation whose
correlation with its target is provably near 1.0 by construction
should be included and asserted, to catch exactly this class of
wrapper-layer bug before it contaminates interpretation.

## §12.8 Infrastructure requirements

Phase A needs:

- `king_attack_encoder/` package as a sibling of `phase_operators/`.
- Three derivation modules, one per §12.3–§12.5, plus an
  `attack_graph.py` shared substrate.
- Evaluation CLI that reads
  `results/phase_operator_experiments/exp3_phase_similarity.csv`
  (the §11.5 CSV), recomputes each transition's encoder-before and
  encoder-after for each derivation, records the king-attack
  similarities alongside the existing columns, and emits a new CSV.
- Unit tests per derivation covering the underlying graph/matrix
  construction, a determinism check, edge cases (no king, no
  opponent pieces), and a performance budget of <10 ms per encode
  call.

Frozen dependencies (read-only imports):

- `phase_operators.phase_operators` — phase arithmetic constants.
- `phase_operators.phase_to_coords` — PHI_TO_RC inversion lookup.
- `phase_operators.occupation_field` — occupation dict builder.
- `chess_spectral.tables.project_irrep` — D4 irrep projector.

§12 imports from these packages but does not modify them.

## §12.9 What success or failure would mean

**If any derivation carries signal at |ρ| > 0.3:** the HDC encoder
family extends to king-attack content. §11.5's null on `encode_640`
reflects a choice of construction (bundled content descriptor), not
an inherent limit of the family. The parallel instrument architecture
(segmentation per UTLP S3 §14) validates as a path to adding specific
structural capabilities without disturbing existing baselines.

**If all three derivations produce |ρ| < 0.1:** three independent
mathematical objects (position-dependent Laplacian, D4 projection of
directed adjacency, composite phase operator) have each failed to
produce king-attack similarity signal. That is strong evidence that
king-attack structure is not representable as a similarity-based
measurement in the HDC encoder family — whatever signal it carries
lives at a different algebraic layer than similarity (e.g., at the
polarization-identity level, which §11 has not addressed).

**If the outcome is ambiguous (0.1 ≤ |ρ| < 0.3):** the construction
pattern carries partial signal. The researcher decides whether
refinement is justified or whether the partial signal is the finding.

All three outcomes advance the research. The experiment is worth
running regardless of which occurs.

---

## §12.10 Result (Phase A — three-corpus evaluation)

**Three-corpus §12 Phase A outcome: AMBIGUOUS.**

Ran `evaluate_encoder.py` against three §11.5-style CSVs generated
from the same three corpora used in §11.6.6.1's durability check. Each
CSV contains ~3200 pseudo-legal transitions labeled with
`is_check_unsafe`, plus path-1 reference correctness validated at
100%. The §12 CLI re-encodes every transition under Derivations A,
B, C and reports Spearman ρ per slice.

| Derivation               | drnykterstein (GM cls, N=10)   | ashchess (FM blitz, N=50)      | fishtest (engines blitz, N=50) |
|--------------------------|-------------------------------:|-------------------------------:|-------------------------------:|
| A (Laplacian, k=5)       | max \|ρ\| = 0.161 (knight)     | max \|ρ\| = 0.172 (captures)   | max \|ρ\| = 0.179 (captures)   |
| B (D4 concat, all rows)  | +0.116                         | +0.094                         | +0.210                         |
| B best slice             | **+0.332 (king moves)**        | +0.172 (pawn, E_ka)            | +0.256 (bishop)                |
| B per-irrep \|ρ\| (A1)   | −0.200                         | −0.145                         | −0.238                         |
| B per-irrep \|ρ\| (E_ka) | +0.174                         | +0.172                         | +0.259                         |
| C (attack op cosine)     | NaN (all-zero vectors)         | NaN                            | NaN                            |
| Transitions evaluated    | 3393                           | 3203                           | 3211                           |

**Durability finding.** Derivation B's single-corpus "viable" result
(|ρ|=0.332 on drnykterstein's king-moves slice) **does not replicate**
across the other two corpora. The king-moves |ρ| drops to +0.123
(ashchess) and +0.228 (fishtest). The all-transitions ρ ranges
+0.094 to +0.210 — consistent ambiguous-zone, never crossing 0.3.
Per-irrep shape is stable across corpora (A1 consistently negative,
E_ka consistently largest positive) which is structurally meaningful
but not a viability signal.

Per §12.7 thresholds on the three-corpus aggregate:
- |ρ| > 0.3 occurs only on one slice of one corpus.
- |ρ| < 0.1 is not met (all-transitions ρ on fishtest = +0.210).
- The honest categorical label is **AMBIGUOUS**.

**Derivation C's structural degeneracy.** On all three corpora, the
16-dim feature vector is identically zero for every position's
pre-move and post-move snapshot. The cosine metric returns 0.0 (zero-
norm fallback) for every row. Spearman is NaN across every slice.
The finding is not "C carries no signal" — it is "cosine similarity
on attack-density-before-vs-after is structurally degenerate as a
metric when the pre-move vector is almost always zero." A different
summary statistic (L2 norm of Δ-vector, attack density at destination
square, sign-flip counts) might work; per §11.7.4 this is not tuned
within Phase A.

**Derivation A's fidelity deficit.** Variance explained by the first
k=5 eigenvectors of the symmetrized attack Laplacian averages 7.3%
(drnykterstein), 11.1% (ashchess), 10.4% (fishtest) across rows.
The eigenchannel is not capturing δ_king's L2 norm at k=5. A would
need k ≥ 16 for a faithful summary, which the prompt scope forbids
retuning in Phase A. This is noted as a prerequisite for any Phase
A2 reconsideration.

**Timing (consistent across corpora):**
- Derivation A: ~2000 µs/call (dominated by scipy.linalg.eigh on 64×64)
- Derivation B: ~1350 µs/call (dominated by project_irrep)
- Derivation C: ~250 µs/call (phase-arithmetic only)

**Pairwise cosines (50-position samples, zero-padded common space):**
- cos(A, B) ≈ 0.0 across all corpora — A and B measure orthogonal things.
- cos(A, C) ≈ +0.25 (drnykterstein), ≈ 0 (ashchess), ≈ +0.25 (fishtest) — moderate similarity on two of three.
- cos(B, C) ≈ 0.0 — B and C also orthogonal.

**CSVs on disk** (all gitignored per existing `docs/chess-maths/results/*/` policy):
- `exp5_king_attack_correlation.csv` (drnykterstein N=10)
- `exp5_king_attack_correlation_ashchess.csv` (ashchess N=50)
- `exp5_king_attack_correlation_hf.csv` (fishtest N=50)

Regenerate via the three-line recipe:
```sh
python similarity_experiment.py --corpus ../results/<CORPUS> --out exp3_<tag>.csv
python -m king_attack_encoder.evaluate_encoder --input-csv exp3_<tag>.csv --out exp5_<tag>.csv
```

**Decision per §12.7.** Phase A is AMBIGUOUS. The researcher decides
whether to:
1. Accept the ambiguity as the §12 finding — the HDC construction
   pattern produces partial king-attack signal (per-irrep structure
   in B is stable across corpora) that does not durably cross the
   viability threshold. §11.5's null does not quite generalize to
   a structural property of the encoder family, but the family also
   does not obviously extend to king-attack content.
2. Commission Phase A2 with specific refinements:
   - Derivation A at k = 16 or 32 (the current k = 5 captures <15%
     of δ_king's norm).
   - Derivation C with a non-cosine metric (L2 of Δ-vector, or
     attack density at destination square).
   - Derivation B with alternative signal choices (column-sum,
     attacker-value-weighted row-sum) to test whether row-sum
     is the limiting factor on B's signal.
3. Promote Phase B (assembly) only if a specific refined derivation
   crosses 0.3 durably across all three corpora.

Per §11.7.4 discipline, the AMBIGUOUS label is recorded as the Phase
A finding regardless of which follow-up (if any) the researcher
chooses.
