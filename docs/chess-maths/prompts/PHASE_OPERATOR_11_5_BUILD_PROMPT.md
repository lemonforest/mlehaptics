# Claude Code: §11.5 Phase-Tuple Similarity + Check Prediction Comparison

## Context

§11.3 and §11.4 shipped in PR #43 and are validated. The phase-operator
move generator matches python-chess pseudo-legal moves at 100% across all
four channels (A/B/C/python-chess). The benchmark split revealed that check-
filtering dominates legal-scope runtime by roughly 10× over move generation,
setting up §11.5's operational target.

§11.5 asks whether phase-tuple similarity — cosine similarity between the
pre-transition and post-transition 640-dim encodings — reveals thermodynamic
structure that the geometric representation does not. The supplement already
has this framed as a correlation experiment against delta_v1, stockfish_eval,
kappa_annihilate, kappa_threat.

This prompt extends §11.5 in two ways before the code build:

1. **Add `is_check_unsafe` as a correlation target.** A phase-native quantity
   that correlates with "move leaves own king in check" at |ρ| > 0.3 would
   offer a fast approximate pre-filter for the 60 µs check filter that
   dominates legal-scope runtime. This tests whether phase similarity
   encodes a king-safety signal.

2. **Add a reference-path implementation alongside.** A separate Claude
   conversation verified that a straight phase-space reformulation of
   python-chess's `is_check` operation (Gemini's "reverse phase-cast":
   apply inverse operators outward from the king, intersect with
   opponent-occupation-by-type, handle ray truncation for sliders) is
   mathematically correct but ~38× slower than python-chess's bitboard-
   backed `is_check` in the same language. This is useful as a reference
   point, not as a production path. Implementing it gives §11.5 a third
   channel — a phase-space check detector that answers is_check correctly
   by construction — against which any phase-similarity-based signal can
   be compared. If phase_similarity predicts is_check_unsafe at a
   correlation strength comparable to or better than what the reference
   phase-cast already achieves by construction, phase similarity is
   carrying information the straight reformulation does not. If it
   underperforms, phase similarity is a weaker signal than direct
   geometric computation and the §11.5 hypothesis fails for the check
   filter use case (though the broader thermodynamic correlations may
   still be informative).

The two paths — **phase-native check detection** (reverse-cast, path 1)
and **phase-native check prediction via similarity** (correlation, path 2)
— are different research questions and must stay distinguished in the
experimental record. Conflating them was the risk flagged in the Gemini
review and is what this prompt is guarding against.

Research notebook §9r polarization framing, §9f coprime roll binding, and
§11.4.5 benchmark table are the relevant antecedents.

---

## Phase 1 — Supplement patches

Apply three patches to `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`. These
extend §11.5 to accommodate the additions above while keeping the original
experimental question intact.

### PATCH 1 — §11.5.1 distinguish the two paths

OLD:
```
### §11.5.1 Motivation

If §11.3 and §11.4 succeed, we have a phase-space move generator that reproduces the geometric one. The next question is whether phase-space operations reveal thermodynamic structure that geometric operations do not.

Specifically: for any candidate transition (φ_origin → φ_dest) under polarization operator P_p, does the **phase-tuple similarity** between the pre-transition and post-transition 640-dim encodings correlate with the thermodynamic gradient Δ from the earlier experiments?
```

NEW:
```
### §11.5.1 Motivation

§11.3 and §11.4 succeeded — we have a phase-space move generator that reproduces python-chess's pseudo-legal move set across four independent channels at 100% agreement, with the 0.52% residual against `legal_moves` accounted for by check/pin filtering (§11.2.8). The next question is whether phase-space operations reveal thermodynamic structure that geometric operations do not.

Specifically: for any candidate transition (φ_origin → φ_dest) under polarization operator P_p, does the **phase-tuple similarity** between the pre-transition and post-transition 640-dim encodings correlate with the thermodynamic gradient Δ from the earlier experiments?

**Two paths, one experiment.** The §11.4.5 benchmark showed check-filtering dominates legal-scope runtime by roughly 10× over move generation. Two distinct research paths target this cost:

- **Path 1: phase-native check detection.** Reformulate python-chess's `is_check` operation in phase space. The natural formulation ("reverse phase-cast") casts inverse attack operators outward from the king and intersects with opponent-occupation-by-type. This is mathematically equivalent to bitboard-based attack detection — same asymptotic complexity, same correctness. It offers no algorithmic advantage over what optimized engines already do, and in a naive Python implementation runs ~38× slower than python-chess's bitboard `is_check`. Its value is as a *reference path*: a phase-space operation with known-correct answer by construction.

- **Path 2: phase-native check prediction via similarity.** If phase-tuple similarity between pre-move and post-move encodings correlates with is_check_unsafe at usable precision (|ρ| > 0.3 as a loose threshold), phase space contributes a cheap approximate signal that the geometric filter does not provide — a pre-filter for the expensive geometric confirmation step. This is structurally different from path 1; it is not a faster reimplementation of an existing operation, it is a new signal whose presence or absence the experiment must determine.

§11.5 runs both paths in the same experiment: path 1 as a reference channel with known correct answers, path 2 as the correlation target with unknown outcome. Having the path-1 reference in the CSV lets us compare any path-2 signal against what a straight phase-space reformulation already achieves by construction. If phase_similarity correlates with is_check_unsafe at a strength comparable to or exceeding what path 1 achieves at its correctness level, phase similarity is carrying information that the direct geometric computation does not expose. If it underperforms, phase similarity is a weaker signal than direct computation and the §11.5.6 decision for the check-filter use case is negative (though the broader thermodynamic correlations may still be informative).
```

### PATCH 2 — §11.5.4 extend data schema

OLD:
```
### §11.5.4 Data to collect

Per legal transition:
- position_fen
- transition_uci
- polarization_type
- phase_similarity (cosine in [−1, 1])
- delta_v1 (from prior experiment, if available)
- stockfish_eval (from prior experiment, if available)
- kappa_annihilate, kappa_threat (from prior experiment)
- was_played (boolean)
```

NEW:
```
### §11.5.4 Data to collect

Per legal transition:
- position_fen
- transition_uci
- polarization_type
- phase_similarity (cosine in [−1, 1])
- delta_v1 (from prior experiment, if available)
- stockfish_eval (from prior experiment, if available)
- kappa_annihilate, kappa_threat (from prior experiment)
- is_check_unsafe (boolean: does applying this transition leave mover's king in check, per python-chess; the geometric reference)
- is_check_unsafe_phasecast (boolean: same question, computed via path-1 reverse phase-cast; correct-by-construction reference channel)
- phasecast_matches_chess (boolean: is_check_unsafe == is_check_unsafe_phasecast; expected to be True for every row)
- was_played (boolean)
```

### PATCH 3 — §11.5.5 extend analysis

OLD:
```
### §11.5.5 Analysis

Compute Spearman ρ between phase_similarity and each of: delta_v1, stockfish_eval, kappa_annihilate, kappa_threat. Break down by polarization type and by capture/non-capture.
```

NEW:
```
### §11.5.5 Analysis

Compute Spearman ρ between phase_similarity and each of: delta_v1, stockfish_eval, kappa_annihilate, kappa_threat, is_check_unsafe. Break down by polarization type and by capture/non-capture.

**Path-1 reference correctness.** Assert phasecast_matches_chess == True for every row before running any correlation. If any row disagrees, the path-1 implementation has a bug that must be fixed before the path-2 analysis is trustworthy. Record the mismatched rows in the summary and halt analysis.

**Path-2 correlation analysis.** The |ρ(phase_similarity, is_check_unsafe)| value answers the operational question from §11.5.1. If |ρ| > 0.3 in any polarization slice, phase similarity is a candidate component of a faster-than-geometric check filter at approximate precision. If |ρ| < 0.1 across all slices, the §11.4.5 optimization path via phase similarity is closed; the check filter remains strictly a geometric operation and path-1's 38× slowdown in naive Python is the floor without bitboard-level engineering.

**Timing comparison.** Record the per-call cost of (a) python-chess is_check and (b) path-1 phase-cast is_check on the same positions. This extends the §11.4.5 table to include check-filter costs explicitly. The expected result: python-chess wins by ~30-40× in naive Python because its is_check is bitboard-backed. This is a reference datum, not a research finding.
```

Grep verification:
```bash
grep -c "Two paths, one experiment" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 1
grep -c "is_check_unsafe_phasecast" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 3
grep -c "phasecast_matches_chess" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md     # expect 3
```

Commit Phase 1 with message: `§11.5 supplement: distinguish path-1 reverse-cast reference from path-2 phase-similarity correlation target`

---

## Phase 2 — Code build

Add to the existing `docs/chess-maths/phase_operators/` package. As before, do not modify the §11.3/§11.4 substrate — it is the validated foundation and remains frozen.

### New files

```
docs/chess-maths/phase_operators/
├── (existing files — do not modify)
├── phase_check_detection.py       # NEW — path-1 reverse phase-cast is_check
├── phase_similarity.py            # NEW — path-2 phase-tuple similarity
├── similarity_experiment.py       # NEW — §11.5 CLI combining both paths
└── tests/
    ├── (existing tests — do not modify)
    ├── test_phase_check_detection.py   # NEW
    └── test_phase_similarity.py        # NEW
```

### `phase_check_detection.py` — Path 1 reference

The reverse phase-cast implementation. Correct by construction (verified against python-chess in preflight: 2500/2500 positions match). Its value is as a reference channel, not a production path.

Required symbol:

```python
"""§11.5 Path 1: phase-native is_check via reverse phase-cast.

Casts inverse attack operators outward from the king's phase and intersects
with opponent-occupation-by-type. Equivalent in structure to bitboard-based
attack detection; runs in naive Python at ~35 µs per call vs python-chess's
~1 µs bitboard implementation.

This module exists as a REFERENCE CHANNEL for §11.5's experimental record,
not as a production check detector. It answers 'is the mover's king in check'
in pure phase space with a known-correct answer by construction. §11.5 uses
it to validate that any phase-similarity-based signal (path 2) carries
information beyond what a direct phase-space reformulation already provides.

See PHASE_OPERATOR_SUPPLEMENT.md §11.5.1 for the path-1 / path-2 distinction.
"""
import chess

from phase_operators import (
    phi, MODULUS,
    P_king, P_knight,
    DIAG_NE_SW_GEN, DIAG_NW_SE_GEN, ROW_GEN, COL_GEN,
)
from phase_to_coords import PHI_TO_RC
from occupation_field import occupation_field_from_board


def _pawn_threat_phases_on_king(king_phi: int, king_color: int) -> frozenset[int]:
    """Phases from which an opposite-color pawn could attack the king.
    
    White king is attacked by black pawns diagonally forward-from-black,
    i.e., diagonally above the king in phase terms: king_phi + 60 and + 74.
    Black king is attacked by white pawns diagonally below: - 60 and - 74.
    """
    if king_color == +1:  # white king
        return frozenset({
            (king_phi + DIAG_NW_SE_GEN) % MODULUS,
            (king_phi + DIAG_NE_SW_GEN) % MODULUS,
        })
    return frozenset({
        (king_phi - DIAG_NW_SE_GEN) % MODULUS,
        (king_phi - DIAG_NE_SW_GEN) % MODULUS,
    })


def _sliding_ray_hits_king(
    king_phi: int,
    occupation: dict[int, int],
    directions: tuple[int, ...],
    attacker_phases: frozenset[int],
) -> bool:
    """Walk each ray outward from king_phi; return True if first blocker
    on any ray is in attacker_phases.
    
    Handles the ray-truncation that 'reverse phase-cast' cannot avoid
    for sliding pieces. Bounded at 7 steps per ray, 8 directions max,
    so worst-case 56 iterations regardless of board population.
    """
    for d in directions:
        for k in range(1, 8):
            p = (king_phi + k * d) % MODULUS
            if p not in PHI_TO_RC:
                break  # off-board, stop this ray
            if p in occupation:
                if p in attacker_phases:
                    return True
                break  # blocked by some piece
    return False


def phasecast_is_check(board: chess.Board) -> bool:
    """Return True if the side-to-move's king is under attack.
    
    Path 1 reference: reverse phase-cast from the king's phase across all
    attacker types. Matches python-chess's is_check by construction.
    """
    mover_color = +1 if board.turn == chess.WHITE else -1
    king_sq = board.king(board.turn)
    if king_sq is None:
        return False
    king_r = chess.square_rank(king_sq)
    king_c = chess.square_file(king_sq)
    king_phi = phi(king_r, king_c)
    
    occupation = occupation_field_from_board(board)
    
    # Separate opponent occupation by piece type
    opp_by_type: dict[str, set[int]] = {
        'N': set(), 'B': set(), 'R': set(), 'Q': set(), 'K': set(), 'P': set()
    }
    opp_color = not board.turn
    for sq, piece in board.piece_map().items():
        if piece.color == opp_color:
            r = chess.square_rank(sq)
            c = chess.square_file(sq)
            opp_by_type[piece.symbol().upper()].add(phi(r, c))
    
    # Knight threats
    if P_knight(king_phi) & opp_by_type['N']:
        return True
    
    # King adjacency (kings can't actually attack kings in legal chess, but
    # include for completeness and to match python-chess's is_attacked_by semantics)
    if P_king(king_phi) & opp_by_type['K']:
        return True
    
    # Pawn threats (color-dependent)
    pawn_threats = _pawn_threat_phases_on_king(king_phi, mover_color)
    if pawn_threats & opp_by_type['P']:
        return True
    
    # Sliding threats (must respect ray truncation)
    rook_rays = (ROW_GEN, -ROW_GEN, COL_GEN, -COL_GEN)
    bishop_rays = (DIAG_NE_SW_GEN, -DIAG_NE_SW_GEN, DIAG_NW_SE_GEN, -DIAG_NW_SE_GEN)
    
    rook_or_queen = frozenset(opp_by_type['R'] | opp_by_type['Q'])
    bishop_or_queen = frozenset(opp_by_type['B'] | opp_by_type['Q'])
    
    if _sliding_ray_hits_king(king_phi, occupation, rook_rays, rook_or_queen):
        return True
    if _sliding_ray_hits_king(king_phi, occupation, bishop_rays, bishop_or_queen):
        return True
    
    return False


def move_leaves_king_in_check(board: chess.Board, move: chess.Move) -> bool:
    """Return True if applying `move` to `board` leaves the mover's king
    attacked. Uses phasecast_is_check.
    
    This is the per-transition check-unsafe predicate used by §11.5.
    """
    board.push(move)
    try:
        # after push, board.turn is the OPPONENT; we want to check the mover's
        # king, which is now the non-turn side. phasecast_is_check reads
        # board.turn, so temporarily flip.
        board.turn = not board.turn
        result = phasecast_is_check(board)
        board.turn = not board.turn
    finally:
        board.pop()
    return result
```

Implementation notes:
- The ray-truncation loop is the only non-trivial part. Knight/king/pawn threats are single set intersections.
- Two helper exports (`_pawn_threat_phases_on_king`, `_sliding_ray_hits_king`) are underscore-prefixed because they are implementation details; only `phasecast_is_check` and `move_leaves_king_in_check` are the module's public API.
- The `move_leaves_king_in_check` helper does the push/pop pattern. Do NOT rebuild the occupation field inside the push — `phasecast_is_check` rebuilds it per call, which is wasteful but matches the "naive Python reference" framing. Optimization is out of scope.

### `phase_similarity.py` — Path 2 signal

Cosine similarity between the 640-dim encodings of the pre-move and post-move positions. Reuses the existing spectral encoder.

Required symbol:

```python
"""§11.5 Path 2: phase-tuple similarity as field gradient indicator.

Computes cosine similarity between encode_640(position_before) and
encode_640(position_after_move). A candidate phase-native signal whose
correlation with thermodynamic quantities (including is_check_unsafe)
§11.5 is set up to measure.

See PHASE_OPERATOR_SUPPLEMENT.md §11.5.2 for the underlying field-theoretic
motivation.
"""
import sys
from pathlib import Path

import chess
import numpy as np


def _locate_encoder():
    """Add the chess_spectral package to sys.path if not already importable."""
    try:
        import chess_spectral  # noqa: F401
        return
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "chess-spectral" / "python",
        here.parent.parent / "chess-spectral" / "python",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise ImportError(
        "Cannot locate chess_spectral package. Expected relative to "
        f"{here}"
    )


_locate_encoder()
from chess_spectral import encode_640, fen_to_pos  # type: ignore


def phase_similarity(board_before: chess.Board, move: chess.Move) -> float:
    """Cosine similarity between encode_640 before and after `move`.
    
    Returns a float in [-1, 1]. 1.0 means the 640-dim encoding is identical
    (impossible for any real move since at least one piece's phase changes).
    Higher values mean the field configuration changes less.
    """
    fen_before = board_before.fen()
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    fen_after = board_after.fen()
    
    enc_before = encode_640(fen_to_pos(fen_before))
    enc_after = encode_640(fen_to_pos(fen_after))
    
    # cosine
    num = float(np.dot(enc_before, enc_after))
    den = float(np.linalg.norm(enc_before) * np.linalg.norm(enc_after))
    if den == 0.0:
        return 0.0
    return num / den
```

Implementation notes:
- The `_locate_encoder()` helper handles the awkward path relationship — `chess_spectral` lives under `chess-spectral/python/` as a sibling of `phase_operators/`. If Claude Code finds a different layout at build time, adjust the candidate list.
- `encode_640` expects a position dict; `fen_to_pos` is the standard conversion.
- Return a raw cosine float. Downstream analysis (Spearman ρ) handles the distribution shape.

### `similarity_experiment.py` — the §11.5 CLI

Combines path 1 + path 2 into a single experiment that emits the §11.5.4 CSV schema per sampled transition.

Required shape:

```python
"""§11.5 CLI: phase-tuple similarity experiment with path-1 reference channel.

Samples positions from a corpus, enumerates legal transitions per position,
computes phase_similarity (path 2) and is_check_unsafe_phasecast (path 1)
for each transition, compares path-1 against python-chess's geometric
is_check (reference), and emits the §11.5.4 CSV plus Spearman ρ summary
per §11.5.5.

Run from phase_operators/ directory:
    python similarity_experiment.py \\
        --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \\
        [--n-positions 100] [--seed 42] [--out PATH]
"""
import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

import chess
import numpy as np

from phase_check_detection import move_leaves_king_in_check
from phase_similarity import phase_similarity


def _move_leaves_king_in_check_geom(board: chess.Board, move: chess.Move) -> bool:
    """Reference: same predicate computed via python-chess's is_check."""
    board.push(move)
    try:
        board.turn = not board.turn
        result = board.is_check()
        board.turn = not board.turn
    finally:
        board.pop()
    return result


def sample_positions_from_corpus(corpus_dir: Path, n: int, seed: int):
    """Yield (fen, game_id, ply) tuples sampled uniformly from the corpus."""
    ...


def run(corpus_dir: Path, n_positions: int, seed: int, out_path: Path) -> dict:
    """Return summary dict with correlation coefficients and timings."""
    ...


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path,
                        default=Path("../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10"))
    parser.add_argument("--n-positions", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path,
                        default=Path("../results/phase_operator_experiments/exp3_phase_similarity.csv"))
    parser.add_argument("--fail-on-mismatch", action="store_true",
                        help="Exit 1 if path-1 phasecast disagrees with python-chess on any row.")
    args = parser.parse_args()
    ...
```

CSV columns (one row per (position, legal transition) pair):

```
position_fen, game_id, ply, polarization_type, transition_uci,
phase_similarity,
is_check_unsafe, is_check_unsafe_phasecast, phasecast_matches_chess,
path1_time_ns, path2_time_ns,
is_capture, delta_material  # simple thermodynamic proxies available without Stockfish
```

The supplement lists `delta_v1`, `stockfish_eval`, `kappa_annihilate`, `kappa_threat` as optional fields "from prior experiment, if available." These require a pre-computed sweep with Stockfish evaluations and κ quantities. If those are not readily available at build time, emit the columns but leave them empty; note the absence in the stdout summary. Do NOT block the §11.5 experiment on re-running the full corpus pipeline.

Stdout summary format:

```
§11.5 complete:
  Positions sampled:           NN
  Total transitions:           NNNN
  
  Path 1 reference validation:
    phasecast_matches_chess:   NNNN/NNNN (100.00%)  <-- must be 100%
  
  Path 2 correlation analysis:
    Spearman ρ(phase_similarity, is_check_unsafe):
      all transitions:         X.XXX (n=NNNN)
      knight moves:            X.XXX (n=NNN)
      bishop moves:            X.XXX (n=NNN)
      rook moves:              X.XXX (n=NNN)
      queen moves:             X.XXX (n=NNN)
      king moves:              X.XXX (n=NNN)
      pawn moves:              X.XXX (n=NNN)
      captures:                X.XXX (n=NNN)
      non-captures:            X.XXX (n=NNN)
  
  Timing:
    python-chess is_check (reference):    N.N µs
    path-1 phasecast is_check:             N.N µs   (S.Sx slower)
    path-2 phase_similarity:               N.N µs   (encoder call dominates)
  
  Decision (§11.5.6):
    If |ρ| > 0.3 in any slice: phase similarity is a candidate check-filter signal
    If |ρ| < 0.1 across all slices: path 2 for check filtering is closed
    Current result: [INTERPRET]
```

The `[INTERPRET]` line is filled in from the actual data: `"phase similarity correlates with check-unsafety at |ρ|=X.XX in the <slice> slice — path 2 viable"` or `"phase similarity does not correlate with check-unsafety (max |ρ|=X.XX); path 2 for check filtering closed"`.

Per §11.7.4: do NOT interpret beyond what the numbers support. Do NOT optimize. Data-collection run only.

If `--fail-on-mismatch` is set and phasecast_matches_chess < 100%, exit 1 after printing the first 5 mismatches. This catches any bug in the path-1 implementation before it contaminates the path-2 analysis.

### `tests/test_phase_check_detection.py`

Unit tests for path 1:

1. **Empty board + lone king:** `phasecast_is_check(Board)` for a position with only a king is False.
2. **Knight check:** construct FEN with only white king on e1 and black knight on d3 (knight attacks e1); `phasecast_is_check` returns True. This is a spot check of the knight path.
3. **Rook check with clear file:** white king on e1, black rook on e8, empty e-file; True.
4. **Rook blocked by own pawn:** white king on e1, white pawn on e2, black rook on e8; False (pawn blocks).
5. **Rook blocked by enemy piece (would-be discover):** white king on e1, black knight on e4, black rook on e8; the knight blocks the rook's attack but the knight is not itself attacking e1 (knight attacks from (d2,f2,c3,g3,c5,g5,d6,f6), not e1). False.
6. **Bishop check on diagonal:** white king on e1, black bishop on h4; attacks via e1-h4 diagonal. True.
7. **Pawn check (white king):** white king on e4, black pawn on d5; pawn attacks e4 diagonally forward. True.
8. **Pawn check (black king):** black king on e5, white pawn on d4; True.
9. **No-check baseline on starting position:** `chess.Board()` has no check for white to move; False.
10. **Matches python-chess across 500 random-play positions:** use the pattern from the §11.4 equivalence check. For every position, assert `phasecast_is_check(board) == board.is_check()`.

### `tests/test_phase_similarity.py`

Unit tests for path 2:

1. **Null move returns 1.0:** encoding before and after a no-op should be identical. chess.Move.null() doesn't change the position; if `phase_similarity` supports it, similarity is 1.0. If not, skip with a comment noting the framework does not define similarity for null moves.
2. **Trivial move (e2-e4) from starting position:** cosine is high but strictly less than 1.0 (the pawn moves two squares, changing encoder output).
3. **Same move computed twice gives same similarity:** determinism check.
4. **Similarity is in [-1, 1]:** bound check across 20 random positions.
5. **Capture changes similarity more than quiet move** (probabilistic; run 20 trials and assert mean_capture_similarity < mean_quiet_similarity with a reasonable margin). This is NOT a correctness test — the actual §11.5 finding is whether this pattern holds at the population level. The test checks the implementation returns something reasonable on representative inputs.

---

## Phase 3 — Run, verify, commit

### Running order

1. Apply the Phase 1 supplement patches. Verify with grep.
2. Build `phase_check_detection.py` + tests. Run `python -m unittest discover`. Test 10 must pass; path-1 is the reference channel and any bug here contaminates everything downstream.
3. Build `phase_similarity.py` + tests. Ensure the encoder path is correctly resolved.
4. Build `similarity_experiment.py`. Run it against the corpus with defaults: `python similarity_experiment.py --n-positions 100 --seed 42`.
5. Inspect the stdout summary. Expected: `phasecast_matches_chess: NNNN/NNNN (100.00%)`. If below 100%, stop and report — path-1 has a bug.
6. Inspect the correlation results. Do NOT tune anything based on the correlation values. Whatever they are is the answer.

### Commit structure

Three commits on a new branch `chess-spectral-phase-operator-11-5`:

1. `§11.5 supplement: path 1 / path 2 distinction and data schema extension`
   (the three patches from Phase 1)
2. `§11.5 path 1: phase-native is_check via reverse phase-cast (reference channel)`
   (phase_check_detection.py + tests)
3. `§11.5 path 2 + CLI: phase-tuple similarity with path-1 reference comparison`
   (phase_similarity.py, similarity_experiment.py, remaining tests, CSV run output)

### Handoff

After the three commits, do NOT open the PR. Print the handoff message:

```
Branch chess-spectral-phase-operator-11-5 ready for review.
§11.5 data collection complete.
Path 1 correctness: NNNN/NNNN (100%).
Path 2 correlation headline: |ρ|=X.XXX (best slice: SLICE)
Timing: py-chess is_check NN µs; path-1 phasecast NN µs; path-2 similarity NN µs.
CSV at results/phase_operator_experiments/exp3_phase_similarity.csv.
Pausing for researcher review and interpretation before PR.
```

The researcher will review the correlation results, decide whether the path-2 finding justifies promotion into §11.5 as "validated" or as "null result recorded," and draft the §11.5.6 decision-point update accordingly.

---

## Scope guard

- Do not modify any file in `phase_operators/` that already exists. The §11.3/§11.4 substrate is frozen.
- Do not start §11.6 (partition detection / aliasing horizon). That's the next experiment.
- Do not optimize path-1's phase_check_detection. The ~35 µs naive-Python speed is expected per the preflight benchmark; a bitboard phase implementation is out of scope.
- Do not interpret the correlation data in code. Report numbers, let the researcher interpret.
- Do not run the full Stockfish sweep to populate delta_v1 / stockfish_eval / kappa_* columns. If those are not pre-computed, leave them empty and note the absence.
- Do not open the PR. Hand off for researcher review of the correlation outcome first.

## Success criteria

1. Supplement §11.5.1, §11.5.4, §11.5.5 patched per Phase 1; three grep checks pass.
2. `phase_check_detection.py` passes 10 unit tests; the 500-position random-play cross-check against python-chess returns 0 mismatches.
3. `phase_similarity.py` passes its 5 unit tests; encoder is correctly located and called.
4. `similarity_experiment.py` runs on the corpus without error. CSV file exists at the default path with expected columns.
5. Stdout summary reports path-1 correctness at 100%. If below 100%, stop.
6. Stdout summary reports Spearman ρ values per slice. Do not interpret them.
7. Three commits on `chess-spectral-phase-operator-11-5`. Handoff message printed. PR not opened.

If all pass, §11.5 data is collected, path-1 reference is validated against python-chess by construction, path-2 correlation outcome is recorded for researcher interpretation, and the §11.5.6 decision can be made on empirical grounds.
