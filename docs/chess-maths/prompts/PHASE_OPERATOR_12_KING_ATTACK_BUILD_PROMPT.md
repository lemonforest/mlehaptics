# Claude Code: §12 parallel king-attack encoder — Phase A build

## Context

The §11 arc is complete. Four experimental findings:

1. **§11.3 / §11.4:** phase-operator move generation is operationally complete
   on 2D chess. Four independent channels (A/B/C/python-chess) converge at
   100% on pseudo-legal moves. The 640-dim encoder's coprime-cyclic
   representation fully captures chess move geometry.

2. **§11.5.6:** phase-tuple similarity between pre-move and post-move
   `encode_640` vectors does **not** correlate with `is_check_unsafe`
   (max |ρ| = 0.097 across 9 slices, n = 3393 transitions). The encoder
   is blind to king-attack geometry at the similarity level.

3. **§11.6.6.1 (three-corpus DRIFT null):** the same encoder produces
   continuous trajectories through game positions rather than discrete
   phase-cells. All 15 drift-ρ measurements strongly positive (+0.46 to
   +0.84), cluster counts rise monotonically with τ without a plateau.
   Validated on 110 games, 14,729 plies, across GM / FM / engine play.

4. **Shared diagnosis:** `encode_640` is a **content descriptor** (what
   pieces are at what phases) rather than a **discontinuity detector**
   (what's dangerous, what's transitional). The construction — D4 irreps
   plus rank-3 fiber SVD plus FA/FD channels — produces bundled-HDC
   superpositions where every piece contributes to every mode. Changes
   accumulate smoothly. None of the constituent derivations produces
   discrete cluster boundaries or king-attack geometry as first-order
   outputs.

§12 asks the follow-on question: **can a parallel HDC instrument,
derived from the same mathematical discipline as `encode_640` but
targeting king-attack structure specifically, expose signal that
`encode_640` does not?**

The answer depends on whether the math supports the construction.
This is genuine research exploration, not engineering. Three outcomes
are in play per §11.7.4 discipline:

- **|ρ(similarity, is_check_unsafe)| > 0.3 on any derivation:**
  king-attack encoder is viable. The HDC family extends to king-attack
  content. §11.5's null was specific to `encode_640`, not structural
  to the encoder family.

- **|ρ| < 0.1 across all three derivations:** the construction
  pattern does not naturally produce king-attack content. The §11.5
  null generalizes to a structural property of the encoder family.
  Three independent derivations failing is strong evidence that the
  mathematics does not support the construction.

- **0.1 ≤ |ρ| < 0.3 on any derivation:** ambiguous. Researcher decides
  whether to refine derivations or accept the ambiguity.

All three outcomes advance the research record. None is wasted effort.

### Why this experiment is motivated now

§11.5's null left open whether a different encoder might carry the
signal. §11.6 sharpened the question: whatever constituent
mathematics would produce **discontinuity structure** on game
trajectories is the same mathematics that would plausibly produce
**king-attack signal** on individual transitions. Both are about the
encoder being sensitive to threshold crossings rather than to
continuous accumulation.

**Derivation A (king-centered Laplacian eigendecomposition) is the
most motivated candidate in this light.** Its eigenstructure is a
property of the position-dependent attack graph. When a piece moves
into or out of an attack line, the attack graph's topology changes
discretely, and the eigenvectors of the resulting Laplacian change
discretely with it. That is exactly the discontinuity mechanism
`encode_640` lacks. Whether it actually correlates with
is_check_unsafe is empirical — but the construction has a structural
reason to expect the correlation to exist, which is more than the
§11.5 experiment could say in advance.

### Architectural constraint — UTLP S3 §14 segmentation

The king-attack encoder must be built as a **separate, concatenated
vector**, not as additional channels superimposed into `encode_640`.
UTLP S3 §14.2 proves that adding a 9th prime to an 8-prime HDC
superposition destroys the existing similarity structure — each
additional prime rotates every dimension's sign-vote independently,
producing ~35% bit disagreement. The same interference applies to
adding king-attack content into `encode_640`'s bundled superposition:
it would break the §11.5 / §11.6 baselines and leave the new signal
entangled with the old.

Segmentation avoids this. Following UTLP S3 §14.3:

```
enc_combined = [enc_640 | enc_king_attack]
```

Each segment maintains its own superposition internally. Cross-tier
interference is eliminated by spatial separation. Downstream code can
choose which segment to consume. `encode_640` remains untouched and
the §11 baselines remain valid.

§12 Phase A builds **only the king-attack segment**. Assembly with
`encode_640` is deferred to Phase B if Phase A produces usable signal.

## Design discipline (non-negotiable)

Each channel in the king-attack encoder must be derivable from a
**specific mathematical object**. Just as `encode_640`'s channels come
from D4 irreps, fiber SVD, pawn antisymmetry, and diagonal deviation —
each with its own derivation — §12's channels must come from named
mathematical objects of the lattice and the attack structure. No
channel may exist because a use case demands it. No channel may be
tuned to produce a desired correlation outcome.

This is the same rule as §11.7.4: record failures, do not repair them.

If the mathematics does not produce a coherent channel, the
construction fails and we record the failure as the finding. Do not
engineer around it.

## Phase 1 — Supplement document

Create `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md` with the
following structure. The §12 stub in `PHASE_OPERATOR_SUPPLEMENT.md`
already points at this file.

Template (fill in content per the derivation specs in Phase 2):

```markdown
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

---

## §12.1 Motivation

[Draft from the Context section above: §11.5 null + §11.6 null +
shared diagnosis. State the §12 question. Enumerate the three
outcomes.]

## §12.2 Derivation discipline

[State the non-negotiable rule: each channel must be derivable from
a specific mathematical object of the lattice + attack structure.
No use-case-driven channels. Record failures rather than repair them.]

## §12.3 Derivation A — King-centered Laplacian eigenchannel

**Mathematical object.** The position-dependent 64×64 attack
Laplacian L_ka, where L_ka[i, j] = -1 if square j is attacked by an
opponent piece on square i (with i ≠ j), L_ka[i, i] = deg(i), and
L_ka[i, j] = 0 otherwise. This is the combinatorial Laplacian of the
opponent-attack graph restricted to the current position.

**Channel derivation.** Compute eigendecomposition of L_ka.
Project the king's unit impulse δ_king (a 64-dim vector with 1 at
the king's square and 0 elsewhere) onto the first k eigenvectors.
The projection magnitudes form a k-dimensional channel.

k is chosen empirically to match `encode_640`'s fiber-channel count
(3 or 5). Report variance explained by the first k eigenvectors on
a representative position sample. If variance-explained is below
~80% at k = 5, the eigenchannel is not a faithful summary and the
derivation may not be viable.

**Why this is structurally motivated.** L_ka is position-dependent;
its topology changes discretely when pieces move into or out of
attack lines. The eigenstructure therefore changes discretely too.
This is the discontinuity mechanism `encode_640` lacks. Whether the
discontinuities correlate with is_check_unsafe is empirical.

## §12.4 Derivation B — D4 decomposition of attack adjacency

**Mathematical object.** The binary attack adjacency A_ka, where
A_ka[i, j] = 1 iff j is attacked by an opponent piece on i, 0
otherwise. Note A_ka is in general **not symmetric** (attack is
directed) and **not D4-invariant** (it depends on the specific
piece positions).

**Channel derivation.** Project A_ka onto the five D4 irreps using
the same Serre character projection formula `encode_640` uses for
the board signal. This produces five channels A1_ka, A2_ka, B1_ka,
B2_ka, E_ka, each 64-dim, paralleling the five D4-irrep channels of
`encode_640`.

**Known tension.** The projection is approximate because A_ka is
not D4-symmetric in general. The projection returns the best-fit
D4-equivariant component in each irrep. Whether that approximation
carries useful signal or degenerates to noise is empirical — §12.6
analysis reports the per-irrep variance explained by the projected
component as a diagnostic.

## §12.5 Derivation C — Attack operator from king's phase

**Mathematical object.** The §11.4.3.1 P_castle pattern generalized
to king-attack: a composite operator on the king's phase that
enumerates, per attacker type and per direction class, whether the
corresponding phase shift from the king lands on an occupied square
of the right attacker type.

**Channel derivation.** For each attacker type t ∈ {N, B, R, Q, K, P}
and each direction class d in t's attack pattern, compute the phase
shift Δ_{t,d} from the king. For the king's current phase φ_K in
the current position, count the number of opponent-t pieces at
phases φ_K + k × Δ_{t,d} mod 640 for k ∈ {1, ..., 7} (or k = 1 for
non-sliders), weighted by piece value.

The (attacker_type × direction_class) enumeration yields ~16
distinct feature components, each an integer-valued or real-valued
scalar. The channel is the concatenation of these scalars, broadcast
across the 64 board squares by tiling or by placing them as a
scalar-valued feature vector of length 16.

**Relationship to path-1 `phasecast_is_check`.** Derivation C is the
vector-valued generalization of what `phasecast_is_check` computes
as a boolean. The boolean reduces 16 scalars to "is any of them
positive"; C keeps them as a continuous signature. C therefore is
expected to correlate with is_check_unsafe because it literally
enumerates the components of is_check_unsafe as continuous values.

**Purpose of including C.** It serves as a **refined baseline**.
Any derivation (A or B) that fails to beat C's correlation is
carrying less signal than a straight enumeration of attack-line
occupation. If A or B beats C, it means those derivations expose
structure the direct enumeration does not — which would be the
genuine §12 finding.

## §12.6 Assembly protocol

Do not prematurely commit to an assembly. Phase A builds A, B, C
independently and measures their pairwise cosines + their
correlations with is_check_unsafe. Only if Phase A produces usable
signal does Phase B address assembly.

Phase A reports:

- Per-derivation |ρ(similarity, is_check_unsafe)| on the §11.5 CSV
  (3393 transitions, existing labels).
- Per-derivation pairwise cosines across a representative sample of
  positions — if cos(A, C) > 0.5 the two are highly correlated and
  A adds little over C; if cos(A, C) < 0.2 they measure different
  things.
- Variance-explained diagnostics per Derivation A's k and per
  Derivation B's irrep.
- Per-call timings for each derivation (µs per position).

Phase B (if Phase A crosses |ρ| > 0.3 for any derivation):

- Concatenation architecture `[encode_640 | enc_king_attack]`.
- Dimensionality budget, channel layout, Serre-projection choices.
- Write-back to `chess_spectral` as a new encoder variant
  (not modification of `encode_640`).

## §12.7 Evaluation — what constitutes success, null, ambiguous

Same three-outcome framework from the main supplement's §11.5 and
§11.6.6.1 results. Transcribe here for reference. Per §11.7.4,
record failures rather than tune derivations.

## §12.8 Infrastructure requirements

Phase A needs:

- `king_attack_encoder/` package as a sibling of `phase_operators/`.
- Three derivation modules, one per §12.3–§12.5.
- Evaluation CLI that reads `results/phase_operator_experiments/
  exp3_phase_similarity.csv` (the §11.5 CSV), recomputes each
  transition's encoder-before and encoder-after for each derivation,
  records the king-attack similarity alongside the existing columns,
  and emits a new CSV.
- Unit tests per derivation covering the underlying graph/matrix
  construction plus a determinism check plus a performance budget
  (<10 ms per encode call).

## §12.9 What success or failure would mean

[Draft from the Context section's three-outcome framing. Use the
same language discipline as §11.9: all outcomes advance the research.]

---

## §12.10 Result

[Placeholder. Filled in after Phase A run.]
```

Grep verification after Phase 1:

```bash
grep -c "Parallel King-Attack Encoder" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "§12.3 Derivation A" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "§12.4 Derivation B" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "§12.5 Derivation C" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md   # expect 1
grep -c "UTLP S3 §14" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT_12.md           # expect 1 or more
```

Commit Phase 1 alone:
`§12 supplement: derivation discipline, three candidate derivations, Phase A scope`

## Phase 2 — Code build

Create `king_attack_encoder/` as a sibling of `phase_operators/` under
`docs/chess-maths/`. This is a fresh package; no modification to
`chess_spectral/`, `phase_operators/`, or any existing module.

Directory layout:

```
docs/chess-maths/
├── king_attack_encoder/
│   ├── __init__.py
│   ├── attack_graph.py              # shared: build attack Laplacian + adjacency
│   ├── derivation_a_laplacian.py    # §12.3 king-centered eigenchannel
│   ├── derivation_b_d4.py           # §12.4 D4 decomposition of attack adjacency
│   ├── derivation_c_operator.py     # §12.5 attack operator from king's phase
│   ├── evaluate_encoder.py          # §12 evaluation CLI
│   ├── README.md
│   └── tests/
│       ├── __init__.py
│       ├── test_attack_graph.py
│       ├── test_derivation_a.py
│       ├── test_derivation_b.py
│       └── test_derivation_c.py
```

### `attack_graph.py` — shared substrate

```python
"""Shared: build opponent-attack graph structures for a board position.

L_ka (Laplacian): D - A, where A[i,j] = 1 iff opponent piece on i
attacks square j. D is the out-degree diagonal.

A_ka (binary adjacency, directed): same A, unprojected.

Both are 64x64 numpy arrays (float64 for Laplacian, int8 for adjacency).

The attack graph is POSITION-DEPENDENT. Its construction consults
python-chess to enumerate which squares each opponent piece attacks.
This is a geometric input, not a phase-arithmetic computation.
§12 operates on the resulting algebraic objects (Laplacian spectrum,
adjacency irrep decomposition); the input graph construction itself
is not phase-native.
"""
import numpy as np
import chess


def attack_adjacency(board: chess.Board) -> np.ndarray:
    """64x64 directed binary attack adjacency.
    
    A[i, j] = 1 iff an opponent piece on square i attacks square j.
    The opponent is the side NOT to move (the side whose king is the
    attack target in is_check_unsafe terms). board.turn is the defender.
    """
    A = np.zeros((64, 64), dtype=np.int8)
    opp_color = not board.turn
    for square, piece in board.piece_map().items():
        if piece.color != opp_color:
            continue
        # python-chess's attacks() returns SquareSet of attacked squares.
        for target in board.attacks(square):
            A[square, target] = 1
    return A


def attack_laplacian(board: chess.Board) -> np.ndarray:
    """64x64 combinatorial Laplacian L = D - A of the attack graph.
    
    Symmetrized via L = D - (A + A.T) / 2. Attack is directional but
    the eigenstructure is more interpretable on the symmetric version;
    per-direction structure is recoverable via A_ka.
    """
    A = attack_adjacency(board).astype(np.float64)
    A_sym = (A + A.T) / 2.0
    deg = A_sym.sum(axis=1)
    L = np.diag(deg) - A_sym
    return L


def king_square(board: chess.Board) -> int | None:
    """Return the square index (0-63) of the side-to-move's king.
    Returns None if no king on board (degenerate position)."""
    return board.king(board.turn)
```

### `derivation_a_laplacian.py` — §12.3

```python
"""Derivation A: king-centered Laplacian eigenchannel.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.3.

Channel derivation: project king's unit impulse onto first k
eigenvectors of the symmetrized attack Laplacian. Return a k-dim
feature vector.

Discontinuity mechanism: L_ka's topology changes discretely when
attack lines open or close; eigenvectors change discretely too.
This is the mechanism encode_640's bundled superposition lacks.
"""
import numpy as np
import chess
from scipy.linalg import eigh

from .attack_graph import attack_laplacian, king_square


DEFAULT_K = 5


def derivation_a_channel(board: chess.Board, k: int = DEFAULT_K) -> np.ndarray:
    """Return k-dim feature vector: projections of king's impulse on
    the first k non-trivial Laplacian eigenvectors.
    
    If no king on board, returns zeros (k-dim).
    If k > 64, raises ValueError.
    Eigenvector ordering: ascending eigenvalue; skip trivial zero-eigenvalue
    eigenvector (constant mode) when it carries no structural information.
    
    Parameters
    ----------
    board : chess.Board
    k : int
        Number of eigenvectors to use. Default 5 matches encode_640's
        fiber-channel count for comparability.
    """
    if k <= 0 or k > 64:
        raise ValueError(f"k must be in [1, 64], got {k}")
    ks = king_square(board)
    if ks is None:
        return np.zeros(k, dtype=np.float64)
    L = attack_laplacian(board)
    # Eigendecomposition of symmetric matrix
    eigvals, eigvecs = eigh(L)
    # The trivial eigenvector (constant) corresponds to eigenvalue 0.
    # We keep it — the constant mode's projection on the king impulse
    # is 1/sqrt(64), which is signal-free but serves as a normalization check.
    # eigvecs[:, i] is the i-th eigenvector.
    delta_king = np.zeros(64, dtype=np.float64)
    delta_king[ks] = 1.0
    projections = eigvecs[:, :k].T @ delta_king  # shape (k,)
    return projections.astype(np.float64)


def derivation_a_similarity(board_before: chess.Board,
                            move: chess.Move,
                            k: int = DEFAULT_K) -> float:
    """Cosine similarity between Derivation A encodings before and after a move.
    
    Returns cosine(A(board_before), A(board_after_move)) ∈ [-1, 1].
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    a_before = derivation_a_channel(board_before, k=k)
    a_after = derivation_a_channel(board_after, k=k)
    norm = float(np.linalg.norm(a_before) * np.linalg.norm(a_after))
    if norm == 0.0:
        return 0.0
    return float(np.dot(a_before, a_after) / norm)


def variance_explained(board: chess.Board, k: int) -> float:
    """Variance-explained diagnostic: what fraction of the king impulse's
    L2 norm is captured by projection onto the first k eigenvectors."""
    ks = king_square(board)
    if ks is None:
        return 0.0
    L = attack_laplacian(board)
    eigvals, eigvecs = eigh(L)
    delta_king = np.zeros(64, dtype=np.float64)
    delta_king[ks] = 1.0
    total = float(np.dot(delta_king, delta_king))  # = 1.0 always
    proj_k = eigvecs[:, :k].T @ delta_king
    captured = float(np.dot(proj_k, proj_k))
    return captured / total if total > 0 else 0.0
```

### `derivation_b_d4.py` — §12.4

```python
"""Derivation B: D4 decomposition of attack adjacency matrix.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.4.

Projects A_ka onto the five D4 irreps using the same Serre character
projection formula encode_640 uses for its board signal. Produces five
64-dim channels A1_ka, A2_ka, B1_ka, B2_ka, E_ka.

Known tension: A_ka is not D4-symmetric in general. The projection
returns the best-fit D4-equivariant component per irrep; whether that
approximation carries signal is empirical.
"""
import numpy as np
import chess

from .attack_graph import attack_adjacency

# Import encode_640's D4 projector. Do NOT modify encode_640 or its
# tables; just consume the projection machinery.
from chess_spectral.tables import project_irrep


D4_IRREPS = ("A1", "A2", "B1", "B2", "E")


def derivation_b_channels(board: chess.Board) -> dict[str, np.ndarray]:
    """Return {name: 64-dim array} for each of the five D4 irreps.
    
    The input signal for Serre projection is derived from A_ka by
    summing rows: row_sum[i] = |{j : square i attacks square j}| for
    opponent pieces. This reduces the directed 64x64 adjacency to a
    64-dim "attack density per source square" signal, which is then
    projected onto the D4 irreps.
    
    Alternative signals (column-sum, diagonal, etc.) can be tested in
    later iterations if row-sum proves uninformative.
    """
    A = attack_adjacency(board).astype(np.float64)
    # Row-sum: total outgoing attacks from each square (0 for non-opponent squares)
    signal = A.sum(axis=1)
    out: dict[str, np.ndarray] = {}
    for irrep in D4_IRREPS:
        out[irrep] = project_irrep(signal, irrep).astype(np.float64)
    return out


def derivation_b_similarity(board_before: chess.Board,
                            move: chess.Move) -> dict[str, float]:
    """Cosine similarity per irrep between before and after a move.
    
    Returns {irrep_name: cosine_similarity}. NaN entries for zero-norm
    channels are replaced with 0.0.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    before = derivation_b_channels(board_before)
    after = derivation_b_channels(board_after)
    out: dict[str, float] = {}
    for irrep in D4_IRREPS:
        b = before[irrep]
        a = after[irrep]
        norm = float(np.linalg.norm(b) * np.linalg.norm(a))
        out[irrep] = (float(np.dot(b, a) / norm) if norm > 0 else 0.0)
    return out


def derivation_b_similarity_concat(board_before: chess.Board,
                                   move: chess.Move) -> float:
    """Cosine similarity of the concatenated 5*64 = 320-dim vector.
    
    This is the single-scalar summary of the per-irrep similarities,
    suitable for direct comparison with derivation_a_similarity.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    before = derivation_b_channels(board_before)
    after = derivation_b_channels(board_after)
    b_concat = np.concatenate([before[i] for i in D4_IRREPS])
    a_concat = np.concatenate([after[i] for i in D4_IRREPS])
    norm = float(np.linalg.norm(b_concat) * np.linalg.norm(a_concat))
    if norm == 0.0:
        return 0.0
    return float(np.dot(b_concat, a_concat) / norm)
```

### `derivation_c_operator.py` — §12.5

```python
"""Derivation C: attack operator from king's phase (vector-valued
generalization of phase_check_detection.phasecast_is_check).

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.5.

Enumerates (attacker_type x direction_class) attack components from
the king's phase as continuous values rather than a single boolean.
Serves as the refined baseline that Derivations A and B must beat
to be considered carrying signal beyond direct attack enumeration.
"""
import numpy as np
import chess

from phase_operators.phase_operators import (
    phi, MODULUS, ROW_GEN, COL_GEN, DIAG_NE_SW_GEN, DIAG_NW_SE_GEN,
    P_king, P_knight,
)
from phase_operators.phase_to_coords import PHI_TO_RC
from phase_operators.occupation_field import occupation_field_from_board


# Feature layout: 16 scalar components
# - 4 sliding-ray attack densities (rook rays) — count of R or Q attackers
#   along each of +row, -row, +col, -col rays, sum-weighted by 1/k.
# - 4 sliding-ray attack densities (bishop rays) — same for B or Q on diagonals.
# - 1 knight attack count — number of opponent knights at knight-shift phases.
# - 1 king-adjacency attack count — number of opponent kings at king-shift phases.
# - 2 pawn attack counts — one per capture-diagonal direction.
# - 4 reserved zero channels — placeholders for future extensions (pinned-piece
#   aware, slider-through-own-piece, etc.). Zero in Phase A.

FEATURE_DIM = 16


def derivation_c_channel(board: chess.Board) -> np.ndarray:
    """Return a 16-dim feature vector summarizing king-attack structure.
    
    Each component is a non-negative real number. Zeros mean "no attacker
    of that type in that direction class."
    """
    out = np.zeros(FEATURE_DIM, dtype=np.float64)
    king_sq = board.king(board.turn)
    if king_sq is None:
        return out
    king_r = chess.square_rank(king_sq)
    king_c = chess.square_file(king_sq)
    king_phi = phi(king_r, king_c)
    mover_color = +1 if board.turn == chess.WHITE else -1
    
    occupation = occupation_field_from_board(board)
    opp_by_type: dict[str, set[int]] = {
        "N": set(), "B": set(), "R": set(),
        "Q": set(), "K": set(), "P": set(),
    }
    opp_color = not board.turn
    for sq, piece in board.piece_map().items():
        if piece.color != opp_color:
            continue
        r = chess.square_rank(sq)
        c = chess.square_file(sq)
        opp_by_type[piece.symbol().upper()].add(phi(r, c))
    
    # Rook-ray densities: +row, -row, +col, -col
    rook_or_queen = opp_by_type["R"] | opp_by_type["Q"]
    for i, d in enumerate((ROW_GEN, -ROW_GEN, COL_GEN, -COL_GEN)):
        density = 0.0
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break
            if p in occupation:
                if p in rook_or_queen:
                    density += 1.0 / k  # closer attackers weight higher
                break  # ray blocked
        out[i] = density
    
    # Bishop-ray densities: +NE, -NE, +NW, -NW
    bishop_or_queen = opp_by_type["B"] | opp_by_type["Q"]
    for i, d in enumerate((DIAG_NE_SW_GEN, -DIAG_NE_SW_GEN,
                           DIAG_NW_SE_GEN, -DIAG_NW_SE_GEN)):
        density = 0.0
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break
            if p in occupation:
                if p in bishop_or_queen:
                    density += 1.0 / k
                break
        out[4 + i] = density
    
    # Knight attack count
    out[8] = float(len(P_knight(king_phi) & opp_by_type["N"]))
    # King adjacency count
    out[9] = float(len(P_king(king_phi) & opp_by_type["K"]))
    
    # Pawn attack counts (color-dependent)
    if mover_color == +1:  # white king
        pawn_threats = frozenset({
            (king_phi + DIAG_NW_SE_GEN) % MODULUS,
            (king_phi + DIAG_NE_SW_GEN) % MODULUS,
        })
    else:
        pawn_threats = frozenset({
            (king_phi - DIAG_NW_SE_GEN) % MODULUS,
            (king_phi - DIAG_NE_SW_GEN) % MODULUS,
        })
    # Count per diagonal (2 separate components)
    diag_phases = list(pawn_threats)
    for i, dp in enumerate(sorted(diag_phases)):  # sort for determinism
        out[10 + i] = 1.0 if dp in opp_by_type["P"] else 0.0
    
    # Components 12-15 reserved for Phase B extensions; zero in Phase A.
    
    return out


def derivation_c_similarity(board_before: chess.Board,
                            move: chess.Move) -> float:
    """Cosine similarity of Derivation C feature vector before/after move."""
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    b = derivation_c_channel(board_before)
    a = derivation_c_channel(board_after)
    norm = float(np.linalg.norm(b) * np.linalg.norm(a))
    if norm == 0.0:
        return 0.0
    return float(np.dot(b, a) / norm)
```

### `evaluate_encoder.py` — §12 evaluation CLI

Reads the existing §11.5 CSV (`exp3_phase_similarity.csv`), adds
Derivation A / B / C similarity columns per transition, computes
Spearman correlations with `is_check_unsafe`, emits a new CSV.

```python
"""§12 evaluation: Derivations A, B, C similarity vs is_check_unsafe.

Reads results/phase_operator_experiments/exp3_phase_similarity.csv
(the §11.5 output with is_check_unsafe labels), recomputes king-attack
similarity for each transition under each derivation, appends those
columns to the CSV, and reports Spearman correlations per derivation
and per polarization slice.

Run from docs/chess-maths/:
    python -m king_attack_encoder.evaluate_encoder \\
        --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \\
        --out results/phase_operator_experiments/exp5_king_attack_correlation.csv
"""
import argparse
import csv
import sys
import time
from pathlib import Path
from typing import Optional

import chess
import numpy as np
from scipy import stats

from .derivation_a_laplacian import derivation_a_similarity, variance_explained
from .derivation_b_d4 import derivation_b_similarity_concat
from .derivation_c_operator import derivation_c_similarity


def process_csv(input_csv: Path, out_csv: Path, sample_for_diagnostics: int = 50) -> dict:
    """Run all three derivations on each row; emit CSV; return summary dict."""
    ...


def print_summary(summary: dict) -> None:
    """Print per-derivation and per-slice correlation summary to stdout."""
    ...


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sample-for-diagnostics", type=int, default=50)
    args = parser.parse_args()
    summary = process_csv(args.input_csv, args.out, args.sample_for_diagnostics)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Summary format (stdout):

```
§12 Phase A: king-attack encoder evaluation
  Input:  results/phase_operator_experiments/exp3_phase_similarity.csv
  Output: results/phase_operator_experiments/exp5_king_attack_correlation.csv
  Transitions evaluated: NNNN

Per-derivation |ρ(similarity, is_check_unsafe)|:

  Derivation A (king-centered Laplacian, k=5):
    all transitions:        X.XXX (n=NNNN)
    knight moves:           X.XXX (n=NNN)
    bishop moves:           X.XXX (n=NNN)
    rook moves:             X.XXX (n=NNN)
    queen moves:            X.XXX (n=NNN)
    king moves:             X.XXX (n=NNN)
    pawn moves:             X.XXX (n=NNN)
    captures:               X.XXX (n=NNN)
    non-captures:           X.XXX (n=NNN)
    variance explained at k=5 (mean over sample): XX.X%

  Derivation B (D4 decomposition of attack adjacency, 5 irreps concatenated):
    [same 9 slices]
    per-irrep |ρ|:
      A1_ka: X.XXX  A2_ka: X.XXX  B1_ka: X.XXX  B2_ka: X.XXX  E_ka: X.XXX

  Derivation C (attack operator from king's phase, 16-dim feature):
    [same 9 slices]

Pairwise cosines (across <sample_for_diagnostics> sampled positions):
  cos(A, B): X.XX
  cos(A, C): X.XX
  cos(B, C): X.XX

Per-call timings (mean over sample):
  Derivation A: X.X µs
  Derivation B: X.X µs
  Derivation C: X.X µs

Phase A decision (per §12.2 + §12.7):
  Best |ρ| across all derivations and slices: X.XXX (<derivation>, <slice>)
  - If > 0.3: king-attack encoder viable; derivation <name> carries signal
    beyond what path-1 phasecast_is_check already captures. Proceed to
    Phase B (assembly decision).
  - If < 0.1: construction pattern does not naturally produce king-attack
    signal. §11.5 null generalizes. Record as validated null.
  - If 0.1-0.3: ambiguous. Researcher decides whether to refine or accept.
  Current: [INTERPRET]
```

The `[INTERPRET]` line is filled in from the actual data. Do not
interpret beyond the threshold categories. Do not tune. The numbers
are the finding.

### Unit tests

Each derivation module gets a test file. Focus on:

1. **Correctness of the underlying graph/matrix.** For a simple
   position (white king e1, black rook e8, empty e-file), does
   `attack_adjacency` correctly mark (e8, {e7, e6, ..., e1}) and
   nothing else for the black rook? Does `attack_laplacian` have
   the correct degree structure?

2. **Determinism.** Same position produces same channel output
   bit-identically across calls.

3. **Edge cases without NaN/crash.** Position with no opposite
   pieces adjacent to king, position with no king on board
   (degenerate FEN), position at checkmate.

4. **Invariance / equivariance.** For Derivation B specifically:
   the A1 projection should be invariant under D4 rotations of
   the same position (or return B_4-equivalent values within
   numerical tolerance); E channel should not be invariant.

5. **Performance budget.** Each derivation's single-call cost
   under 10 ms on a representative middlegame position.

## Phase 3 — Run and handoff

Running order:

1. Apply Phase 1 supplement (`PHASE_OPERATOR_SUPPLEMENT_12.md`).
   Grep checks pass.
2. Build `attack_graph.py` + its unit tests. Run
   `python -m unittest discover king_attack_encoder.tests`.
   Must pass.
3. Build `derivation_a_laplacian.py` + tests. Must pass.
4. Build `derivation_b_d4.py` + tests. Must pass.
5. Build `derivation_c_operator.py` + tests. Must pass.
6. Build `evaluate_encoder.py`.
7. Run the evaluation CLI on the existing §11.5 CSV:
   ```
   python -m king_attack_encoder.evaluate_encoder \\
       --input-csv results/phase_operator_experiments/exp3_phase_similarity.csv \\
       --out results/phase_operator_experiments/exp5_king_attack_correlation.csv
   ```
8. Inspect stdout summary. Record the best |ρ| across derivations.

Do **not** tune any derivation based on the correlation results.
Record what the numbers say.

Do **not** start Phase B (assembly) regardless of outcome. Phase B
is conditional on researcher review of Phase A.

### Commit structure

Branch `chess-spectral-phase-operator-12-phase-a` from main. Five
commits:

1. `§12 supplement: PHASE_OPERATOR_SUPPLEMENT_12.md with derivation discipline and three candidates`
2. `§12 attack_graph: shared Laplacian + adjacency constructors + tests`
3. `§12 Derivation A: king-centered Laplacian eigenchannel + tests`
4. `§12 Derivation B: D4 decomposition of attack adjacency + tests`
5. `§12 Derivation C: attack operator from king's phase + evaluation CLI + tests + run output`

The evaluation CSV belongs in commit 5 if small; commit it to the
tree only if it fits under 1 MB. Otherwise leave it on disk and
note path in the handoff.

### Handoff message

```
Branch chess-spectral-phase-operator-12-phase-a ready for review.
§12 Phase A data collection complete.

Transitions evaluated: NNNN (from exp3_phase_similarity.csv)

Per-derivation |ρ(similarity, is_check_unsafe)|:
  Derivation A (king-centered Laplacian, k=5): max |ρ| = X.XXX (<slice>)
  Derivation B (D4 decomposition):             max |ρ| = X.XXX (<slice>)
  Derivation C (attack operator):              max |ρ| = X.XXX (<slice>)

Best overall |ρ|: X.XXX (<derivation>, <slice>)

Pairwise cosines:
  cos(A, B): X.XX  cos(A, C): X.XX  cos(B, C): X.XX

Decision per §12.7:
  [IF best |ρ| > 0.3] King-attack encoder viable. <derivation> carries
  signal beyond path-1 phasecast_is_check. Phase B (assembly) unblocked
  pending researcher review.
  [IF best |ρ| < 0.1] Validated null. Construction pattern does not
  naturally produce king-attack signal. §11.5 null generalizes to a
  structural property of the encoder family.
  [IF 0.1 ≤ |ρ| < 0.3] Ambiguous. Researcher decides whether to refine
  derivations or accept.

CSV at results/phase_operator_experiments/exp5_king_attack_correlation.csv
(or noted size if uncommitted).

Pausing for researcher review. No PR opened.
```

## Scope guard

- Do not modify `chess_spectral/` or any file under it. `encode_640`
  is frozen; §12 is a parallel instrument.
- Do not modify `phase_operators/` or any file under it. §11
  substrate is frozen. `king_attack_encoder/` may import from
  `phase_operators.*` and `chess_spectral.tables` as read-only.
- Do not start Phase B (assembly / concatenation with encode_640)
  regardless of Phase A outcome.
- Do not tune derivation parameters (k for A, signal choice for B,
  weighting for C) to produce a particular correlation outcome.
  Per §11.7.4, record failures rather than repair them.
- Do not modify the §11.5 CSV. Read-only input.
- Do not write interpretation into the supplement §12.10 beyond the
  three-outcome categorization. Researcher writes the interpretation
  after reviewing numbers.
- Do not open the PR. Hand off for researcher review.

## Success criteria

Phase 1: `PHASE_OPERATOR_SUPPLEMENT_12.md` created with all nine
sections populated per the template; five grep checks pass; commit
landed.

Phase 2: four new modules + four test files created under
`king_attack_encoder/`; `python -m unittest discover
king_attack_encoder.tests` returns zero failures; each derivation
callable on a representative chess.Board without error.

Phase 3: evaluation CLI runs on the §11.5 CSV without error;
output CSV has the expected new columns; stdout summary reports
best |ρ| per derivation across the nine slices plus pairwise cosines
plus per-call timings; branch has five commits; handoff message
printed with actual numbers; PR not opened.

If any phase fails structurally (tests don't pass, CLI crashes,
derivation produces NaN), stop and report rather than patching
around the failure.
