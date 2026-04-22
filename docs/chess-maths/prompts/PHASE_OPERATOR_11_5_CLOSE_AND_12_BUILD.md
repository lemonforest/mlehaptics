# Claude Code: §11.5 PR close-out + parallel king-attack encoder derivation

## Context

§11.5 landed a clean null result on branch `chess-spectral-phase-operator-11-5`: path 1 reverse phase-cast matched python-chess at 3393/3393, path 2 phase-tuple similarity correlated with is_check_unsafe at |ρ|=0.097 max across all slices. Under the §11.5.6 rule (|ρ| < 0.1 → path-2 for check filtering closed), this is a validated null. The current 640-dim encoder does not expose king-attack geometry in its phase-similarity measurements.

The researcher's decision on what to do about the null result:

**Build a parallel king-attack encoder.** Not extend the existing encoder. Not bolt a new channel onto `encode_640`. Derive a *separate* encoder instrument, following the same mathematical pattern that produced the 10 channels of C17, specifically targeted at king-attack structure. Then test it.

The reasoning: the C17 encoder's channels are all derivable from specific mathematical objects — D4 irreps from the board's symmetry group, fiber channels from SVD of stacked piece Laplacians, FA from the antisymmetric pawn adjacency, FD from diagonal deviation. Each channel exists because the mathematics *produces* it, not because a use case demands it. If king-attack structure belongs in a bound co-cyclic HDC instrument, there is a derivation that produces it naturally. If no such derivation exists, or if the derivation produces something that decouples weirdly from the existing C17 structure, that is itself informative — we learn what the encoder family does and does not support.

The researcher is explicit: "The mathematics either support it or they don't, and the only way to know is to build it and see what breaks." Parallel construction preserves optionality. If it works, we have a second instrument. If it fails, we have a principled reason why king-attack structure is not in the same mathematical family as the C17 channels.

This prompt has three phases:

1. **Phase 1 — Close §11.5.** Update the supplement with the null result, clarify the pseudo-legal switch, note that Stockfish-dependent columns remain empty. Open PR #44 as a clean close of §11.5 for the C17 encoder.

2. **Phase 2 — Derive a king-attack encoder as a separate instrument.** Build `king_attack_encoder.py` following the same derivation discipline as C17's channels (structural, not teleological). Test it against the same §11.5 CSV to see whether it carries the king-attack signal that C17 did not.

3. **Phase 3 — Handoff.** Do not merge, do not decide. Report what the king-attack encoder produces, let the researcher interpret. If the math refuses, the failure mode is the finding. If the math works, it is the finding.

---

## Phase 1 — §11.5 PR close-out

### Supplement patches

Apply four patches to `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`. These document the §11.5 result and prepare §11.5.6 for researcher interpretation.

#### PATCH 1A — §11.5.3 clarify pseudo_legal iteration

**Rationale:** The build-prompt wording "for each legal transition" would have given is_check_unsafe ≡ False (zero variance, NaN Spearman). The experiment correctly iterated pseudo_legal_moves. Document this for future readers.

Locate the current §11.5.3 protocol block. Add a short explanatory note at the end of the section:

```
**Population note.** The experiment iterates over `pseudo_legal_moves`, not `legal_moves`. Using `legal_moves` would give `is_check_unsafe ≡ False` by construction (python-chess's `legal_moves` already filters out king-unsafe moves), producing zero variance in the correlation target. Pseudo-legal is the correct population: it is the candidate set that a hypothetical check-filter would operate on, and it has meaningful variance in `is_check_unsafe`. This matches the operational framing in §11.5.1.
```

#### PATCH 1B — §11.5.4 empty-columns note

**Rationale:** delta_v1, stockfish_eval, kappa_annihilate, kappa_threat require a prior Stockfish sweep. If that data was not available at build time, the columns are empty in this run. Note the absence so the null result is not over-interpreted.

At the end of §11.5.4, add:

```
**Columns from prior experiments.** The `delta_v1`, `stockfish_eval`, `kappa_annihilate`, and `kappa_threat` columns require a pre-computed Stockfish sweep with κ-quantity extraction. If that data is not attached to the corpus at experiment run time, those columns remain empty in the CSV and their correlations with phase_similarity are not answered by this run. A follow-up experiment with the full Stockfish sweep attached is the appropriate vehicle for that analysis; it is not a blocker for the §11.5.6 decision on the check-filter path.
```

#### PATCH 1C — §11.5.6 promote to validated null result

Locate the current §11.5.6 section:

OLD:
```
### §11.5.6 Decision point

If phase_similarity correlates strongly (|ρ| > 0.3) with any existing thermodynamic quantity, the phase representation is capturing the same signal. If it correlates only with specific components (say, high correlation with kappa_annihilate but low with delta_v1), the phase representation is revealing a decomposition of the thermodynamic gradient we have not explicitly computed.

If phase_similarity correlates with nothing (|ρ| < 0.1 across the board), the phase representation is capturing an orthogonal quantity — potentially the "field geometry" that Stockfish does not measure but that we suspected in the κ_position experiments.

All three outcomes are informative.
```

NEW (fill in actual numbers from the CSV summary):
```
### §11.5.6 Result — validated null for path-2 check filtering

**Run parameters:** 100 positions sampled from `sweep_chain_lichess_drnykterstein_2026-04-14_N10`, 3393 pseudo-legal transitions total.

**Path-1 reference correctness.** phasecast_matches_chess: 3393/3393 (100.00%). The reverse phase-cast is_check detector matches python-chess across every sampled transition by construction. Path 1 is validated as a correct phase-space reformulation of the geometric check operation; it is not faster than python-chess's bitboard is_check (138 µs vs 22 µs in the run's naive-Python benchmark), but correctness is unimpeachable.

**Path-2 correlation result.** Max |Spearman ρ(phase_similarity, is_check_unsafe)| across all nine slices: **0.097** (king-move slice). All other slices (knight, bishop, rook, queen, pawn, captures, non-captures, all-transitions) fell below this value. Per the §11.5.6 threshold of |ρ| < 0.1 for "no correlation," this is a validated null: **phase-tuple similarity between pre-move and post-move `encode_640` vectors does not carry information about whether the move leaves the mover's king in check.**

**Structural interpretation.** The 640-dim encoder's ten channels — five D4 irreps, three symmetric fiber channels, FA antisymmetric pawn fiber, FD diagonal deviation — are each derived from a specific mathematical object of the lattice and its piece operator content. None of those derivations produces king-attack geometry as a first-order output. The null result is consistent with the encoder's construction: it faithfully represents the board's field-theoretic structure and its symmetry content, and king-attack relationships happen to not be field-theoretic in the same sense. A move that exposes the king changes the encoding by roughly the same amount as any other move of the same piece type; the differential signal is below the 0.1 threshold.

**What remains open.** This result closes path 2 *for the check-filter use case*. It does not close the broader §11.5 hypothesis for thermodynamic gradients — phase_similarity's correlation with delta_v1, stockfish_eval, kappa_annihilate, kappa_threat is untested in this run because those columns require a pre-computed Stockfish sweep that was not attached. A follow-up experiment with the full sweep attached is the appropriate vehicle for that analysis.

**What this motivates.** The null result raises a structural research question independent of §11.5's stated scope: *should the encoder family be extended to include king-attack content, and is there a principled derivation that produces such a channel naturally?* This question is addressed in a parallel experiment (§12 — to be documented after the parallel king-attack encoder returns data). It is not a modification of the C17 encoder; it is a separate instrument built from the same mathematical discipline, tested against the same CSV produced by §11.5.

**Timing (mean per call, naive Python, same positions):**
- python-chess `is_check` (reference): 22 µs
- path-1 phasecast `is_check`: 138 µs (~6× slower, consistent with naive-Python-vs-bitboard gap)
- path-2 `phase_similarity`: 1190 µs (dominated by two encode_640 calls)

The path-1 timing extends the §11.4.5 table with check-filter cost explicitly; the path-2 timing is a data point about the encoder's per-call cost at the current implementation level, not a claim about phase similarity being fast.

**Decision:** §11.6 unblocked. §12 (parallel king-attack encoder) added as a sibling experiment.
```

#### PATCH 1D — add §12 stub

After the §11.9 section (end of §11), before the appendix, add a new top-level §12 stub:

```
## §12. Parallel King-Attack Encoder

> **Status.** Working experiment. Triggered by §11.5.6's validated null for path-2 check filtering in the C17 encoder. Asks whether a separate HDC instrument, derived from the same mathematical discipline that produced C17 but targeting king-attack structure specifically, can expose the signal that C17 does not.
>
> Lives in [PHASE_OPERATOR_SUPPLEMENT_12.md](PHASE_OPERATOR_SUPPLEMENT_12.md) as a standalone document pending experimental validation. See that file for derivation, construction, and comparison protocol.
>
> **Important scoping.** §12 does not modify C17. C17 remains the validated 640-dim encoder for §9 and §11's experiments. §12 is a parallel instrument built to answer a specific question C17 did not answer. If §12 succeeds, the HDC encoder family has a king-attack member; if §12 fails, C17's construction pattern does not support king-attack content naturally and the null result from §11.5 reflects a structural property of that construction pattern, not a gap.
```

### Grep verification for Phase 1

```bash
grep -c "Population note" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md                      # expect 1
grep -c "Columns from prior experiments" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md       # expect 1
grep -c "validated null for path-2 check filtering" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md  # expect 1
grep -c "Parallel King-Attack Encoder" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md         # expect 1
grep -c "PHASE_OPERATOR_SUPPLEMENT_12.md" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md      # expect 1
```

### Phase 1 commit and PR

Commit the four patches as one commit:
```
§11.5 promoted to validated null; §12 sibling experiment stub added
```

Push the branch. Open PR #44 titled: `§11.5 phase-tuple similarity: validated null + path-1 reference correctness`

PR body:

```markdown
## Summary

Closes §11.5 with a validated null result for path-2 phase similarity as a
check-filter signal. Validates path-1 reverse phase-cast as a correct
phase-space reformulation of is_check. Extends the supplement with a §12
stub for the parallel king-attack encoder (derivation and construction
in PHASE_OPERATOR_SUPPLEMENT_12.md, experiment in a separate branch).

## Results

**Path 1 (reverse phase-cast is_check):** 3393/3393 match against python-chess.
Correct by construction in phase space. Naive Python implementation runs at
138 µs vs python-chess's bitboard 22 µs; the ~6× gap is the Python-vs-C and
dict-vs-bitboard gap, not an algorithmic gap.

**Path 2 (phase_similarity vs is_check_unsafe):** max |ρ| = 0.097 across 9
slices; below the §11.5.6 threshold of 0.1 for "no correlation." Phase-tuple
similarity between pre- and post-move `encode_640` encodings does not carry
king-safety information.

## Structural finding

The C17 encoder's channels are derived from specific mathematical objects
(D4 irreps, piece-Laplacian SVD, pawn antisymmetry, diagonal deviation).
None of those derivations produces king-attack geometry as a first-order
output. The null result is consistent with the encoder's construction.

The null **does not** close the broader §11.5 thermodynamic hypothesis —
correlations with delta_v1 / stockfish_eval / kappa_* remain untested
because those columns require a pre-computed Stockfish sweep not attached
to this run. A follow-up experiment attaching the sweep can answer that
question; it is out of scope for this PR.

## Next

- **§12 — Parallel king-attack encoder.** A separate HDC instrument derived
  from the same mathematical discipline as C17, targeting king-attack
  structure. Answers "should the encoder family extend to king-attack
  content, and does a principled derivation produce such an object?"
  Built and tested on a sibling branch.
- **§11.6 — Aliasing horizon as partition detection.** Still queued; runs
  independently of §12.

## Commits

- `40cd851` — supplement patches (path 1 / path 2 distinction, schema extension)
- `0d61701` — phase_check_detection.py (path 1 reverse phase-cast) + 10 unit tests
- `5b20adc` — phase_similarity.py, similarity_experiment.py, 5 unit tests
- (this commit) — §11.5.6 promoted to validated null; §12 stub added

## Scope

This PR does not modify C17. It does not extend the encoder. It records
§11.5's finding, validates path 1, and opens §12 as a parallel experimental
track. Reviewer focus: the §11.5.6 numbers and interpretation, the §12 stub's
scoping language ("does not modify C17").
```

Do not merge. The researcher will review and merge manually.

---

## Phase 2 — Parallel king-attack encoder (branch `chess-spectral-phase-operator-12`)

After PR #44 is opened, branch from main (not from the §11.5 branch — §12 is independent) and build the king-attack encoder as a separate instrument.

### Derivation discipline

The C17 encoder's 10 channels are each derived from a specific mathematical object. The king-attack encoder must follow the same pattern. Each channel must be derivable from the lattice structure + piece operators + (for king-attack specifically) the king's position + attack relationships. No channel may be tuned to produce desired downstream correlations; no channel may exist because a use case demands it; every channel must exist because the mathematics produces it.

This is the non-negotiable design constraint. If the mathematics does not produce a coherent channel, the construction fails and we record the failure as the result. Do not engineer around it.

### Candidate derivation paths

Three candidate derivations, each motivated by a specific mathematical object. Build all three, let each produce whatever channel count it produces, assemble into a single encoder only if the channels are mutually orthogonal or cleanly decomposable. If they are not, that is the §12 finding.

**Derivation A: King-centered Laplacian eigendecomposition.**

For each position, construct a 64×64 "king-attack Laplacian" L_ka where L_ka[i, j] is nonzero iff square j attacks square i via some opponent piece on the board. This is a *position-dependent* graph Laplacian, unlike the C17 board Laplacian which is position-independent. Its eigendecomposition yields a spectral fingerprint of the king's attack environment.

Channel derivation: project the king's board signal (unit impulse at king's square) onto the first k eigenvectors of L_ka. The projection magnitudes form a k-dim channel. Pick k by the same criterion used for C17's fiber channels: variance explained by the first k components across a representative position set (target: ≥95%).

If k comes out ≤ 5, the channel is compact and comparable in scale to C17's fiber channels. If k > 10, the channel is unwieldy and the derivation is probably not capturing the right structure.

**Derivation B: D4 decomposition of the king-attack adjacency matrix.**

For each position, construct a 64×64 binary matrix A_ka where A_ka[i, j] = 1 iff j attacks i via an opponent piece. Project A_ka onto the five D4 irreps using Serre's character projection formula (the same projection C17 uses for the board signal). This produces five channels, one per irrep, with the same dimensional structure as C17's A1/A2/B1/B2/E.

Natural test: is the king-attack adjacency matrix symmetry-rich? The board Laplacian is D4-symmetric (verified in §9a: `||P_g L P_g^T − L|| = 0`). The king-attack matrix is position-dependent and will not in general be D4-symmetric — it depends on the specific king position and the specific attacker positions. The D4 projection is therefore an *approximation*, not a clean decomposition. The §12 finding includes whether that approximation is useful or degenerate.

**Derivation C: Attack operator from king's phase.**

Following the §11.4.3.1 P_castle pattern for multi-piece coupled operators: define a phase-space "attack operator" as a composite relationship between king phase and attacker phase. For each opponent attacker type t, for each direction d in the attacker's move pattern, compute the phase shift Δ_t,d that would carry an attacker on the king's attack line to the king. The set of (t, d, Δ_t,d) forms the attack-operator spec. The *channel value* is the count, weighted by attacker value, of currently-occupied phases at Δ_t,d positions from the king's phase.

This is less a spectral channel and more a structured integer signature of the king's attack environment. It is closest to what path 1 already computes in phase_check_detection.py — that module's outputs are essentially a boolean summary of this channel.

### Construction plan

Build each derivation as a separate module. Do not combine prematurely.

```
docs/chess-maths/king_attack_encoder/
├── __init__.py
├── derivation_a_laplacian.py      # king-centered Laplacian eigenchannel
├── derivation_b_d4.py             # D4 decomp of attack adjacency
├── derivation_c_operator.py       # attack-operator channel
├── king_attack_encoder.py         # assemble A/B/C into single encoder IFF channels decouple
├── evaluate_encoder.py            # CLI: compute correlations against §11.5 CSV
└── tests/
    ├── __init__.py
    ├── test_derivation_a.py
    ├── test_derivation_b.py
    ├── test_derivation_c.py
    └── test_encoder_assembly.py
```

### Derivation A implementation

```python
"""Derivation A: king-centered Laplacian eigendecomposition.

For a given position, constructs a 64×64 Laplacian where edges encode
attack relationships (j -> i iff an opponent piece on j attacks square i).
Projects the king's unit impulse onto the first k eigenvectors; the
projection magnitudes are the channel values.

This derivation asks: does the king's position have a spectral fingerprint
in the position-dependent attack graph?
"""
import numpy as np
import chess
from scipy.linalg import eigh


def attack_laplacian(board: chess.Board) -> np.ndarray:
    """64×64 position-dependent Laplacian encoding opponent attack edges.
    
    L_ka = D - A where A[i, j] = 1 iff square j is occupied by an opponent
    and its piece attacks square i. D is the degree diagonal.
    
    The opponent is the side NOT to move (the side whose king is the
    'defender' in king-attack terms). board.turn is the defender.
    """
    ...


def derivation_a_channel(board: chess.Board, k: int = 5) -> np.ndarray:
    """Project king's unit impulse onto the first k eigenvectors of the
    attack Laplacian. Returns k-dim vector; if no king on board, returns
    zeros.
    
    k chosen to match C17's fiber-channel count for comparability (3 or 5);
    make this a parameter so the §12 writeup can explore the variance
    explained as k increases.
    """
    ...
```

### Derivation B implementation

```python
"""Derivation B: D4 decomposition of the king-attack adjacency matrix.

Projects the attack adjacency matrix onto the five D4 irreps using the
same character projection formula C17 uses for the board signal. Produces
A1_ka, A2_ka, B1_ka, B2_ka, E_ka channels, each with the same 64-dim
structure as C17's D4 irrep channels.

This derivation asks: does the attack adjacency matrix have meaningful
D4 irrep content, despite being position-dependent and not D4-symmetric
in general?
"""
import numpy as np
import chess

# Import the D4 projection machinery from chess_spectral.tables.
# This is re-use, not modification — we are calling the same projection
# operator C17 uses, applied to a different input signal.
from chess_spectral.tables import project_irrep  # or equivalent; adjust import


def attack_adjacency(board: chess.Board) -> np.ndarray:
    """64×64 binary matrix encoding opponent attack edges (not Laplacian,
    not symmetric)."""
    ...


def derivation_b_channels(board: chess.Board) -> dict[str, np.ndarray]:
    """Return {'A1_ka', 'A2_ka', 'B1_ka', 'B2_ka', 'E_ka'} each as 64-dim
    arrays.
    
    Project attack_adjacency onto each D4 irrep via Serre's character
    projection formula. The irrep decomposition is *not* exact (the
    adjacency is not D4-symmetric) — the projection is the best-fit
    D4-invariant / D4-equivariant component in each irrep.
    """
    ...
```

### Derivation C implementation

```python
"""Derivation C: attack operator from king's phase.

Following the §11.4.3.1 P_castle pattern — a composite operator on the
king's phase that captures king-attack structure as a structured integer
signature. For each opponent attacker type t and each attack direction d,
compute whether the corresponding phase shift from the king lands on an
occupied square of type t.

This is the most 'engineered' of the three derivations — it is motivated
directly by path-1's phasecast_is_check computation — and is included as
a baseline: any channel that beats C derivation's correlation with
is_check_unsafe is at least as informative as path-1's boolean summary.
"""
from phase_operators.phase_operators import phi, MODULUS, ...


def derivation_c_channel(board: chess.Board) -> np.ndarray:
    """Return a ~16-dim vector encoding count-by-type of attackers at
    each direction class relative to the king. Dimension depends on
    (attacker_type × direction_class) enumeration.
    """
    ...
```

### Encoder assembly

After all three derivations are implemented, build `king_attack_encoder.py`:

```python
"""Parallel king-attack encoder.

Combines derivations A, B, C into a single vector. If the derivations
produce orthogonal or near-orthogonal signals (pairwise cosine < 0.2
across a sample position set), concatenate them. If they produce highly
correlated signals (pairwise cosine > 0.5), document the redundancy and
choose the most informative single derivation.

This assembly decision IS data, not engineering. Report the pairwise
cosines and let the researcher choose the final encoder form.
"""
import numpy as np
import chess

from .derivation_a_laplacian import derivation_a_channel
from .derivation_b_d4 import derivation_b_channels
from .derivation_c_operator import derivation_c_channel


def encode_king_attack(board: chess.Board, mode: str = "concat") -> np.ndarray:
    """Return a king-attack encoding vector.
    
    mode='a', 'b', 'c': single derivation only.
    mode='concat': concatenate all three.
    mode='best': use whichever the assembly analysis picked.
    """
    ...


def assembly_report(sample_positions: list[str]) -> dict:
    """Compute pairwise cosines between derivations A, B, C across
    sample_positions. Return a report with correlations and a
    recommendation."""
    ...
```

### Evaluation CLI

`evaluate_encoder.py` computes the king-attack encoder's similarity signal for each transition in the existing §11.5 CSV and correlates it with is_check_unsafe. If any derivation produces |ρ| > 0.3 with is_check_unsafe, §12 has found the signal C17 did not. If all derivations produce |ρ| < 0.1, the construction pattern does not naturally produce king-attack content.

```python
"""§12 evaluation: compute king-attack encoder similarity for each §11.5
transition; correlate with is_check_unsafe.

Input: the CSV written by similarity_experiment.py
   (results/phase_operator_experiments/exp3_phase_similarity.csv)
Output: a new CSV with king-attack similarities appended, plus a summary
   of Spearman correlations per derivation.
"""
```

CLI flags:
- `--input-csv PATH` — the §11.5 CSV; default `../results/phase_operator_experiments/exp3_phase_similarity.csv`
- `--corpus PATH` — the corpus (needed to reload FENs and compute encodings); default same as §11.5
- `--out PATH` — output CSV; default `../results/phase_operator_experiments/exp4_king_attack_correlation.csv`
- `--derivation {a,b,c,concat,all}` — which derivation to evaluate; default `all`

Stdout summary:

```
§12 king-attack encoder evaluation:
  Transitions evaluated: NNNN
  
  Path-1 correctness (re-check): NNNN/NNNN (100%)
  
  Derivation A (king-centered Laplacian, k=5):
    |ρ(similarity_a, is_check_unsafe)|: X.XXX
    variance explained by k=5 eigenchannel: XX.X%
  Derivation B (D4 decomposition of attack adjacency):
    |ρ(similarity_b, is_check_unsafe)|: X.XXX
    per-irrep: A1=X.XXX A2=X.XXX B1=X.XXX B2=X.XXX E=X.XXX
  Derivation C (attack operator):
    |ρ(similarity_c, is_check_unsafe)|: X.XXX
  Concatenated A+B+C:
    |ρ(similarity_abc, is_check_unsafe)|: X.XXX
  
  Assembly analysis:
    cosine(A, B) across N positions: X.XX
    cosine(A, C): X.XX
    cosine(B, C): X.XX
    Recommendation: [INTERPRET]
  
  Timing per encoding call (mean):
    Derivation A: X.X µs
    Derivation B: X.X µs
    Derivation C: X.X µs
  
  Decision (§12.6 preliminary):
    If max |ρ| > 0.3: king-attack encoder viable; derivation _ is the winner
    If max |ρ| < 0.1: king-attack encoder construction does not produce
                      the signal; mathematics does not naturally support
    If 0.1 < max |ρ| < 0.3: ambiguous; requires deeper investigation
    Current result: [INTERPRET]
```

### Tests

Each derivation gets a test file. Focus tests on:

1. **Correctness of the underlying graph/matrix.** For a simple position (e.g., white king e1, black rook e8, empty e-file), does `attack_laplacian` correctly identify the e-file squares as attacked? Does `attack_adjacency` match? Do the derivation outputs make sense on that simple input?
2. **Invariance / equivariance properties.** Derivation B's D4 projection: does it produce the same output for the 8 D4 rotations of the same position? (Should, for A1 channel; should not, for E channel.)
3. **No NaN / no divide-by-zero.** On positions with no opposite-color pieces adjacent to the king (e.g., endgame with isolated king), do all derivations return well-formed outputs?
4. **Performance budget.** Each derivation must complete in <10 ms per call. C17's encode_640 runs in a few hundred µs; §12 derivations can be slower (no bitboards, per-position graph construction) but should not be catastrophically slow.

### Phase 2 commit structure

On branch `chess-spectral-phase-operator-12`:

1. `§12 supplement document (PHASE_OPERATOR_SUPPLEMENT_12.md) with derivation discipline and protocol`
2. `§12 derivation A: king-centered Laplacian eigenchannel`
3. `§12 derivation B: D4 decomposition of attack adjacency`
4. `§12 derivation C: attack operator from king's phase`
5. `§12 encoder assembly and evaluation CLI`

Each commit passes its own unit tests before the next begins. No §12 code ships before the §11.5 PR #44 is reviewed and merged (or until the researcher explicitly green-lights concurrent work).

### §12 supplement document

Create `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md` with the same structure as `PHASE_OPERATOR_SUPPLEMENT.md`:

- §12.1 Motivation (why a parallel encoder, triggered by §11.5.6's null)
- §12.2 Derivation discipline (the non-negotiable design constraint)
- §12.3 Derivation A (king-centered Laplacian)
- §12.4 Derivation B (D4 decomposition of attack adjacency)
- §12.5 Derivation C (attack operator)
- §12.6 Assembly protocol
- §12.7 Evaluation: what would constitute success, what would constitute failure, what would constitute a null
- §12.8 Infrastructure requirements
- §12.9 Open questions (what does success tell us; what does failure tell us)

Fill in content from the above spec. Use the same language discipline as the main supplement (polarization state, lattice domain, phase transition, etc. where applicable).

---

## Phase 3 — Handoff

Do not merge PR #44. Do not open PR #45 for §12. The researcher will review both in Claude Chat after Phase 2 completes.

Handoff message at end of Phase 2:

```
§11.5 PR #44 open, not merged (per researcher directive).
§12 branch chess-spectral-phase-operator-12 committed, not pushed.

§12 headline (fill in from evaluate_encoder.py output):
  Derivation A |ρ|: X.XXX
  Derivation B |ρ|: X.XXX  
  Derivation C |ρ|: X.XXX
  Concatenated |ρ|: X.XXX
  Decision: [INTERPRET]

§12 assembly analysis:
  cos(A,B)=X.XX cos(A,C)=X.XX cos(B,C)=X.XX
  Recommendation: [INTERPRET]

Pausing for researcher interpretation of §12 outcome. 
Next action: researcher decides whether §12 supplement gets promoted to
validated / null / ambiguous, and whether §11.6 proceeds in parallel.
```

---

## Scope guard

- Do not modify C17 (`chess-spectral/python/chess_spectral/encoder.py`, `tables.py`). C17 is validated and frozen; §12 is a parallel instrument, not an extension.
- Do not modify any file in `phase_operators/`. That package is the §11 substrate.
- Do not tune any derivation to produce a particular correlation outcome. If a derivation fails to produce a meaningful channel, record the failure; do not repair. Per §11.7.4 and the researcher's explicit "the math either supports it or it doesn't" framing.
- Do not ship §12 code as part of PR #44. §12 is a separate branch and separate PR, conditional on §11.5 merging and researcher review.
- Do not merge PR #44. Do not open PR #45.
- Do not start §11.6.

## Success criteria

### Phase 1
- Four supplement patches applied, five grep checks pass.
- Commit landed on `chess-spectral-phase-operator-11-5`.
- PR #44 opened with the body above. Not merged.

### Phase 2
- Branch `chess-spectral-phase-operator-12` created from main (not from §11.5).
- `PHASE_OPERATOR_SUPPLEMENT_12.md` exists with §12.1–§12.9 sections populated.
- Three derivations implemented in separate modules, each with unit tests passing.
- Encoder assembly module computes pairwise cosines and reports them.
- `evaluate_encoder.py` runs against the §11.5 CSV and produces correlation numbers for each derivation and the concatenation.
- Five commits on the branch. Branch not pushed.

### Phase 3
- Handoff message printed with actual §12 correlation numbers.
- Researcher review pending. PR #45 not opened.

If §12's max |ρ| comes out above 0.3, the king-attack encoder has the signal C17 did not and the researcher will decide whether §12 promotes to a validated finding with a follow-up integration path. If below 0.1, the construction pattern does not naturally produce king-attack content and the researcher will record that as a structural property of the encoder family. If between 0.1 and 0.3, the finding is ambiguous and the researcher will decide whether to refine the derivations or accept the ambiguity.
