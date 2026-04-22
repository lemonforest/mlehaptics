# Claude Code: §11.4 Occupation-Aware Phase Operators — Parallel B + C Build

## Context

§11.3 passed at 416/416 (commit `e0a915b` on `chess-spectral-phase-operator-code-phase2`). The unobstructed phase operators reproduce python-chess legal moves exactly for every piece and every origin on an empty board.

§11.4 is the next step. Sliding pieces need occupation handling: a rook at d1 in the starting position cannot reach d8 because d2 is occupied. The phase operators from §11.2 do not know about other pieces.

The supplement (§11.4.2) names three candidate solutions:
- **Solution A** — post-hoc geometric pruning. Generate the unobstructed phase set, convert to (r,c), hand to python-chess for filtering. Phase-space generation + geometric filter hybrid.
- **Solution B** — phase-space occupation field. Represent occupancy as a set of phases. For each ray, generate the full k ∈ {1..7} candidate phase set, intersect against the occupation-phase set to find the first blocker along that ray in phase arithmetic, truncate there.
- **Solution C** — incremental phase operator. Iterate k = 1, 2, 3, ... and halt when the generated phase matches an occupied node's phase. Step-by-step with early halt.

The original prompt (the §11.4 one that got deferred) asked for Solution C only. This prompt asks for **both B and C, run in parallel on the same positions, compared against each other and against python-chess as ground truth.** The researcher is in exploration mode and wants to learn what the comparison reveals.

This is a sanity check. The goals are:
1. Confirm both B and C reproduce python-chess legal moves (primary success criterion)
2. Confirm B and C agree with each other on every (position, piece, origin) triple (if they disagree, one is buggy, and the disagreement pattern tells us which)
3. Measure whether B or C is faster on chess positions (minor question; both should be fast)
4. Produce data for the supplement to cite when §11.4 gets promoted to validated

No new PGN fetching is needed. The existing `sweep_chain_lichess_drnykterstein_2026-04-14_N10` corpus on disk has ~1000 positions across 10 games — more than enough for sanity. Use it.

---

## Phase 1 — Supplement patch (the one that was deferred)

The four patches from the previous prompt went into the code commit but not the supplement. Before this build, apply them. They are reproduced here for reference — do not re-apply if you already did. Grep first:

```bash
grep -c "Subgroup structure" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md
grep -c "knight-offset θ class" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md
grep -c "Empty-board comparison caveat" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md
grep -c "Mathematical honesty caveat" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md
```

If all four return 1, skip to Phase 2. If any return 0, apply the patches from the earlier `PHASE_OPERATOR_BUILD_PROMPT.md` (sibling file in this directory) before proceeding.

Additionally, patch §11.4 to reflect that we're running both B and C:

### PATCH — §11.4.3 retitle and expand

**Rationale:** The current §11.4.3 is titled "Protocol for Solution C" and only specifies C. This prompt builds B and C in parallel. Expand the section to cover both.

OLD:
```
### §11.4.3 Protocol for Solution C

For each sliding polarization p ∈ {R, B, Q} and for each origin φ_origin in a position with other excitations present:

1. For each ray direction d (e.g., +row, −column) defined by the polarization's phase-shift unit u_d:
2. Initialize k = 1.
3. Compute candidate phase φ_k = φ_origin + k × u_d mod 640.
4. Check if φ_k corresponds to a valid lattice node (inside [0, 7]²). If not, halt the ray (boundary reached).
5. Check if φ_k corresponds to an occupied node in the current position. If occupied by same Z₂ charge, halt the ray before φ_k (cannot capture own charge). If occupied by opposite Z₂ charge, include φ_k (capture) and halt. If unoccupied, include φ_k and continue to k = k + 1.

The occupation check in step 5 is the only geometric operation. All phase generation is pure arithmetic.
```

NEW:
```
### §11.4.3 Protocol for Solutions B and C

Both solutions represent occupancy as a **set of phases** Φ_occ = {φ(r, c) : (r, c) is occupied in the current position}, annotated with the Z₂ charge at each occupied phase. Both are phase-native in the specific sense that the blocker check is a set-membership test on Φ_occ, not a lookup on a python-chess Board object. They differ in how the truncation happens.

**Solution B — Phase-space occupation field (batch / set-intersection).**

For each sliding polarization p ∈ {R, B, Q} and for each origin φ_origin:

1. For each ray direction d with phase-shift unit u_d:
2. Generate the full candidate phase set Φ_ray = {(φ_origin + k × u_d) mod 640 : k ∈ {1, ..., 7}} in order of increasing k.
3. Clip Φ_ray at the first on-board phase that is off-lattice (boundary halt) — all k beyond that are dropped regardless of occupation.
4. Find Φ_ray ∩ Φ_occ. The lowest-k intersection is the blocker.
5. Destinations are: all pre-blocker phases from Φ_ray, plus the blocker itself *if* its Z₂ charge is opposite (capture allowed), plus nothing if the blocker's charge matches (own-charge block).

**Solution C — Incremental phase operator (sequential / early halt).**

For each sliding polarization p ∈ {R, B, Q} and for each origin φ_origin:

1. For each ray direction d with phase-shift unit u_d:
2. Initialize k = 1.
3. Compute φ_k = (φ_origin + k × u_d) mod 640.
4. Check if φ_k corresponds to a valid lattice node (inside [0, 7]²). If not, halt the ray (boundary reached).
5. Check Φ_occ for membership. If absent (unoccupied), include φ_k in destinations and continue with k := k + 1. If present with same Z₂ charge, halt before φ_k. If present with opposite Z₂ charge, include φ_k (capture) and halt.

**Equivalence claim.** B and C must produce identical destination sets for every (position, polarization, origin) triple where both are well-defined. Their difference is the order of operations, not the answer. Any observed disagreement is a bug in one or the other, not a property of chess.

**Non-sliding pieces.** King, knight, and pawn operators from §11.2 are already localized (k = ±1 only for king/pawn; discrete shell for knight). The occupation-aware version of these is the unobstructed set minus own-charge-occupied destinations, plus opposite-charge destinations as captures. Both B and C reduce to the same localized filter for these pieces; the B vs C distinction only matters for {R, B, Q}.
```

Apply this patch before building code. Grep to verify:
```bash
grep -c "Solution B — Phase-space occupation field" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 1
grep -c "Solution C — Incremental phase operator" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md    # expect 1
```

Commit Phase 1 with message: `§11.4 supplement: specify Solutions B and C as parallel protocols`

---

## Phase 2 — Code build

Add to the existing `docs/chess-maths/phase_operators/` package. Do not modify the three files that were just committed (`phase_operators.py`, `phase_to_coords.py`, `equivalence_check.py`) — they are the §11.3-validated substrate and should remain unchanged. Extend by adding new files.

### New directory layout

```
docs/chess-maths/phase_operators/
├── __init__.py                           # unchanged
├── phase_operators.py                    # unchanged (§11.3 substrate)
├── phase_to_coords.py                    # unchanged (§11.3 substrate)
├── equivalence_check.py                  # unchanged (§11.3 CLI)
├── occupation_field.py                   # NEW — Φ_occ representation
├── occupation_aware_b.py                 # NEW — Solution B generator
├── occupation_aware_c.py                 # NEW — Solution C generator
├── occupation_equivalence_check.py       # NEW — §11.4 CLI, runs A/B/C against all three
├── README.md                             # UPDATE to reference new files
└── tests/
    ├── __init__.py                       # unchanged
    ├── test_phase_operators.py           # unchanged
    ├── test_occupation_field.py          # NEW
    ├── test_occupation_aware_b.py        # NEW
    └── test_occupation_aware_c.py        # NEW
```

### File-level specifications

#### `occupation_field.py`

The phase-native occupation representation, shared by both B and C.

Required symbols:

```python
from dataclasses import dataclass
from typing import Iterable
import chess

from phase_operators import phi, MODULUS
from phase_to_coords import PHI_TO_RC


@dataclass(frozen=True)
class OccupiedPhase:
    """A phase corresponding to an occupied square, annotated with Z2 charge.

    charge: +1 for white, -1 for black. Matches the §9m / §11.2 sign convention.
    """
    phase: int
    charge: int  # +1 or -1


def occupation_field_from_board(board: chess.Board) -> dict[int, int]:
    """Return {phase: charge} mapping for every occupied square on `board`.

    The mapping domain is a subset of the 64-point board image of phi.
    Empty squares do not appear in the mapping.
    """
    ...


def is_own_charge(occupation: dict[int, int], phase: int, mover_charge: int) -> bool | None:
    """Three-valued: True if phase is occupied by same charge, False if
    opposite charge, None if phase is empty (not in occupation field)."""
    ...
```

Implementation notes:

- Use `dict[int, int]` (phase → charge) as the primary occupation representation, not `set[int]`. B and C both need to distinguish own-charge-blocker from opposite-charge-blocker.
- `occupation_field_from_board` iterates python-chess's piece map and converts each occupied square to its phase via `phi(rank, file)`. One pass through the 64 squares max.
- Do NOT expose a `set[int]` of occupied phases as the public interface. Always carry the charge information. If B wants a pure set for intersection, it can `set(occupation.keys())` internally.
- Type annotations: use the `int | None` return pattern from the Python 3.10+ syntax, consistent with `phase_to_coords.invert`.

#### `occupation_aware_b.py`

Solution B generator — batch phase generation, set-intersection truncation.

Required symbols:

```python
def occupation_aware_moves_b(
    board: chess.Board,
    piece_char: str,  # 'N', 'B', 'R', 'Q', 'K', 'P'
    origin_r: int,
    origin_c: int,
    mover_charge: int,
) -> frozenset[tuple[int, int]]:
    """Return legal destination (r, c) set via Solution B.
    
    Sliding pieces (R, B, Q): generate full unobstructed phase set per direction,
    compute ray-ordered occupation intersections, truncate at first blocker.
    Localized pieces (K, N, P): unobstructed set minus own-charge-occupied,
    plus opposite-charge captures.
    
    Pawn handling: include_captures is determined by the board state — any
    diagonal phase landing on an opposite-charge occupation is a capture;
    absent that, the diagonal is dropped. En passant, promotion, castling
    are NOT handled here (§11.2.8).
    """
    ...
```

Implementation notes:

- **Ray direction unit tuples** must be explicit data, not magic numbers scattered through the function. Define at module level:
  ```python
  _ROOK_RAYS = (67, -67, 7, -7)
  _BISHOP_RAYS = (74, -74, 60, -60)
  _QUEEN_RAYS = _ROOK_RAYS + _BISHOP_RAYS
  ```
- **Ray generation** for a sliding piece returns a list `[(k, phase_k) for k in 1..7]` in order of increasing k. Trim where `invert(phase_k) is None` (boundary halt) by breaking the list at the first None — all later k values are off-board regardless of occupation.
- **Intersection truncation:** iterate the trimmed `[(k, phase_k)]` list. The first `phase_k` that is in `occupation` is the blocker. Pre-blocker phases all go in; blocker goes in iff charge differs; post-blocker phases are dropped.
- **Pawn captures** via B: compute the two diagonal capture phases and add each to destinations iff that phase is in `occupation` with opposite charge.
- **En passant, promotion, castling** are explicitly out of scope per §11.2.8. If a mismatch with python-chess is traceable to one of these, record it — don't try to handle it.

#### `occupation_aware_c.py`

Solution C generator — sequential step with early halt.

Required symbols:

```python
def occupation_aware_moves_c(
    board: chess.Board,
    piece_char: str,
    origin_r: int,
    origin_c: int,
    mover_charge: int,
) -> frozenset[tuple[int, int]]:
    """Return legal destination (r, c) set via Solution C.
    
    Sliding pieces: step k = 1, 2, ... along each ray; halt when phase
    inverts to None (boundary) or matches an occupied phase (blocker).
    Localized pieces: same filter as Solution B (they share the K/N/P
    localized logic; the B/C distinction only affects sliding pieces).
    """
    ...
```

Implementation notes:

- **The sliding loop is the interesting code.** Inner loop:
  ```python
  for k in range(1, 8):
      phase_k = (origin_phase + k * u_d) % MODULUS
      dest = invert(phase_k)
      if dest is None:
          break  # boundary halt
      charge_at = occupation.get(phase_k)
      if charge_at is None:
          destinations.add(dest)  # unoccupied, continue
          continue
      if charge_at == mover_charge:
          break  # own-charge blocker, stop before
      destinations.add(dest)  # opposite-charge capture
      break
  ```
- **Localized-piece logic** (K, N, P) should be extracted into a shared helper in `occupation_field.py` so B and C both call it, since they agree on this case. Name it `_localized_filter(candidate_phases, occupation, mover_charge)` or similar.
- **Pawn advance cannot capture**: the advance phase (forward one or two) is included iff not occupied at all. The two-square advance additionally requires the intermediate square (forward one) to be unoccupied.
- **Pawn capture only captures**: the diagonal capture phases are included iff occupied by opposite charge.

#### `occupation_equivalence_check.py`

The CLI that drives both B and C against python-chess (Solution A reference) across sampled positions. This is the sanity check itself.

Required shape:

```python
"""§11.4 Occupation-Aware Phase Operators — parallel B + C experiment.

Samples positions from a corpus, runs Solutions B and C for every
(polarization, origin) pair, compares each against python-chess's legal
moves (Solution A reference), and records agreements/disagreements.

Run from phase_operators/ directory:
    python occupation_equivalence_check.py \\
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

from occupation_field import occupation_field_from_board
from occupation_aware_b import occupation_aware_moves_b
from occupation_aware_c import occupation_aware_moves_c


def sample_positions_from_corpus(corpus_dir: Path, n: int, seed: int) -> list[tuple[str, str, int]]:
    """Return [(fen, game_id, ply), ...] sampled uniformly from the
    corpus's ndjson files.
    
    corpus_dir is expected to contain ndjson/game_001.ndjson, game_002.ndjson,
    etc. Each line (after the first two metadata lines) is a ply record with
    a 'fen' field. Sample `n` ply records uniformly across all games.
    """
    ...


def legal_moves_for_piece(board: chess.Board, piece_char: str,
                         origin_r: int, origin_c: int,
                         mover_charge: int) -> frozenset[tuple[int, int]]:
    """Solution A reference: python-chess legal_moves filtered to this piece
    and origin. Honors the current side to move."""
    ...


def run(corpus_dir: Path, n_positions: int, seed: int, out_path: Path) -> dict:
    """Run the full experiment. Returns a summary dict."""
    ...


def main() -> int:
    ...
```

CSV schema (one row per (position, polarization, origin) triple):
```
position_fen, game_id, ply, polarization, origin_row, origin_col,
mover_charge, solution_a_dests, solution_b_dests, solution_c_dests,
b_equals_a, c_equals_a, b_equals_c,
b_missing_vs_a, b_extra_vs_a, c_missing_vs_a, c_extra_vs_a,
b_minus_c, c_minus_b,
solution_b_time_ns, solution_c_time_ns
```

Columns `*_dests` serialize set contents as `"(r,c);(r,c)"` — same format as §11.3 CSV. Columns `*_missing_*`, `*_extra_*`, `b_minus_c`, `c_minus_b` are also set-as-string serializations.

Per-position iteration:

1. Parse FEN into `chess.Board`.
2. Build `occupation = occupation_field_from_board(board)`.
3. For each piece type currently on the board whose color matches `board.turn`, for each occupying square:
   - Run Solution A, B, C.
   - Record timings for B and C (A is the reference; its timing is not compared).
   - Compare as sets and fill in the CSV columns.

Positions where the game is in checkmate or stalemate yield no legal moves for some pieces — that's fine, the sets will all be empty and equivalent.

Expected output:

```
$ python occupation_equivalence_check.py --n-positions 100 --seed 42
Sampled 100 positions across 10 games.
Per-position iteration: ~20-30 polarization-origin pairs.
Total rows: ~2500.

§11.4 complete:
  B matches A: 2487/2500 (99.48%)
  C matches A: 2487/2500 (99.48%)
  B matches C: 2500/2500 (100.00%)
  Mean B time: 12.3 µs
  Mean C time:  8.7 µs

CSV written to: results/phase_operator_experiments/exp2_occupation_equivalence.csv
```

If B and C agree on all rows but both disagree with A, the disagreement is either (a) a genuine gap in the phase-operator formulation, (b) en passant / promotion / castling (§11.2.8 exclusions), or (c) a bug shared by B and C. Record and surface; do not patch.

If B and C disagree with each other on any row, one of them is wrong. Print the first 5 such rows to stderr with full context so the researcher can debug.

CLI flags:
- `--corpus PATH` — corpus directory. Default: `../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10`.
- `--n-positions N` — number of positions to sample. Default: 100.
- `--seed N` — RNG seed. Default: 42.
- `--out PATH` — CSV output. Default: `../results/phase_operator_experiments/exp2_occupation_equivalence.csv`.
- `--fail-on-disagreement` — exit 1 if B ≠ C anywhere, or if A ≠ B ≠ C except for §11.2.8 exclusions. Default off.

### Tests

Extend the test battery. Each of the three new test files covers one module in isolation; the cross-module integration test is the CLI itself.

#### `test_occupation_field.py`

1. `occupation_field_from_board(Board())` on the starting position returns 32 entries.
2. `occupation[phi(0, 0)] == +1` (white rook on a1) and `occupation[phi(7, 0)] == -1` (black rook on a8).
3. After `1. e4`, the old e2 phase is not in occupation and the new e4 phase has charge +1.
4. `is_own_charge(occupation, phi(0, 0), +1) is True`.
5. `is_own_charge(occupation, phi(7, 0), +1) is False`.
6. `is_own_charge(occupation, phi(4, 4), +1) is None` in the starting position (e5 empty).

#### `test_occupation_aware_b.py` and `test_occupation_aware_c.py`

Parallel structure. For each of B and C:

1. **Starting position rook:** a1 rook has zero destinations (own pawns block everything at k=1). b1 knight has two destinations (a3, c3).
2. **Open file rook:** construct a position with white rook at a1, clear a-file, black rook at a8. Destinations from a1 are a2..a7 (six non-captures) plus a8 (capture of black rook) = 7 total.
3. **Bishop with mixed blockers:** white bishop at c1, white pawn at e3, black queen at a3. Destinations: b2 (unblocked), d2 (unblocked), a3 (capture) = 3 total. Note the bishop's path to e3 is blocked by own pawn (cannot capture own), and c1→d2→e3 would require passing through d2 which is empty, so d2 is reachable but e3 is not.
4. **Pawn diagonal capture only with target present:** white pawn at e4, black pawn at d5. Destinations from e4: e5 (advance), d5 (capture). Without the black pawn on d5, destinations would be just {e5}.
5. **Queen from empty center:** queen at d4 on empty board. Destinations = 27 squares (the full queen set minus origin).

Both B and C must produce identical sets for all five tests. Write the assertions against a single `_expected` dict per test to make the parallel structure obvious.

### Running order

1. Apply the Phase 1 supplement patches. Verify with grep.
2. Build `occupation_field.py` + its tests. Run `python -m unittest discover` — must pass.
3. Build `occupation_aware_b.py` + its tests. Run tests — must pass.
4. Build `occupation_aware_c.py` + its tests. Run tests — must pass.
5. Build `occupation_equivalence_check.py`. Run it on the corpus with `--n-positions 100 --seed 42`.
6. Inspect the output. Expected headline: `B matches C: 2500/2500 (100.00%)`. B and C match rates against A should be identical (if not, one of them has a bug).
7. If B and C disagree anywhere, stop and report the first disagreement in detail before attempting fixes. If both agree but both disagree with A, the researcher will analyze the disagreement pattern — your job is to record it faithfully.

Commit Phase 2 with message: `§11.4 parallel B + C occupation-aware phase operators`

---

## Scope guard

- Do not modify `phase_operators.py`, `phase_to_coords.py`, or `equivalence_check.py`. These are §11.3's validated substrate.
- Do not handle en passant, promotion, or castling. They are §11.2.8 exclusions. If they show up as disagreements with python-chess, record them in the CSV and let the researcher analyze.
- Do not fetch new PGNs. The corpus on disk is sufficient.
- Do not tune B or C operator logic to match A. The point of the comparison is to surface disagreements, not hide them. Per §11.7.4.
- Do not build §11.5 or §11.6 scaffolding. Stop at the end of §11.4.
- Do not add dependencies. stdlib + python-chess + (optionally) existing corpus NDJSON readers only.
- Do not optimize. Timing instrumentation is for observation, not for hitting a target. Each position processes in milliseconds; wall-clock is not the point of this experiment.

## Success criteria

Phase 1: supplement §11.4.3 rewritten, grep checks pass, commit landed.

Phase 2: four new modules + three new test files created, unit tests pass, CLI runs on 100 positions from the corpus, CSV populates at the default path, stdout summary reports B/A, C/A, and B/C agreement rates. The ideal stdout line is `B matches C: 2500/2500 (100.00%)` — if that line says anything else, one of B or C is buggy and the bug must be found before commit. The researcher expects B and C to agree with each other perfectly; their match rate against A is what's empirically interesting and what §11.4.5's decision point hinges on.

If B matches A at 100% and C matches A at 100%, §11.4 is green and §11.5 is unblocked. If they match at 95–99%, analyze the gap — likely §11.2.8 exclusions — and decide whether to extend the operators or document the known gaps. If they match below 95%, something is structurally wrong and we revisit before going further.
