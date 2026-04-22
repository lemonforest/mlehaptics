# Claude Code: §11.4 completion — Solution A, castling closure, and supplement promotion

## Context

Two commits on `chess-spectral-phase-operator-11-4` established that:

- §11.3 unobstructed phase operators match python-chess empty-board legal moves at 416/416 (100.00%) — commit `e0a915b`.
- §11.4 Solutions B and C agree with each other at 1153/1153 (100.00%) and match python-chess pseudo-legal moves at 99.48%, with the 0.52% residual being 6 castling moves (§11.2.8 exclusion) — commits `f6a99bb` and `5f1b498`.

The experimental arc of §11.3 / §11.4 has landed. This prompt closes three remaining items so the §11 section can be promoted from "active experimentation" to "validated with known gaps documented":

1. **Add Solution A** (post-hoc geometric pruning) as a third occupation-aware generator, run in parallel with B and C. Purpose: additional grounding. A is not phase-native — it generates the unobstructed phase set, inverts to (r, c), and asks python-chess to filter. But running it alongside B and C gives four independent channels converging on the same answer (A, B, C, and python-chess's own legal_moves), which is stronger validation than three. It also gives a timing baseline against the phase-native solutions.

2. **Close the castling gap.** The 6 castling disagreements are a known finite set covered by §11.2.8. Add a `P_castle` composite operator that handles the king+rook atomic two-piece transition, and extend the occupation-aware generators to call it when the position's castling rights permit. This closes the residual.

3. **Promote §11.3 and §11.4 to validated in the supplement and update the research notebook.** Both decision points (§11.3.6 and §11.4.5) are decided; the supplement currently reads as if they are open. The research notebook §11 stub should be updated with a pointer to the validated results. After this prompt completes, §11.3 and §11.4 are done, and §11.5 is the next experiment to build.

This is the last prompt in the §11.3/§11.4 arc. The next prompt will address §11.5.

---

## Phase 1 — Solution A generator

Add Solution A alongside B and C. Use the existing directory layout; do not modify the §11.3 substrate or the B/C modules.

### New file: `occupation_aware_a.py`

```python
"""Solution A: post-hoc geometric pruning (§11.4.2).

Generates the unobstructed phase set per §11.2, inverts to (r, c) via
phase_to_coords, then filters the resulting candidate destinations against
python-chess's legal move set.

This is explicitly NOT phase-native — the filtering step delegates to
python-chess. Its purpose is threefold:

  1. Cross-validate Solutions B and C. If A, B, C, and python-chess all
     converge on the same answer, we have four independent channels
     rather than three.
  2. Timing baseline. A represents the naive hybrid; B and C represent
     phase-native alternatives. Their speed difference against A is part
     of the §11.4 empirical record.
  3. Castling handling (§11.2.8 exclusion) is easier in the hybrid
     formulation and provides a reference for the phase-native P_castle
     in occupation_aware_castling.py.
"""
```

Required symbol:

```python
def occupation_aware_moves_a(
    board: chess.Board,
    piece_char: str,
    origin_r: int,
    origin_c: int,
    mover_charge: int,
) -> frozenset[tuple[int, int]]:
    """Return legal destination (r, c) set via Solution A.

    1. Generate unobstructed phase set from §11.2 operators.
    2. Invert to candidate (r, c) destinations; drop off-image phases.
    3. Filter candidates by intersecting with python-chess's legal move
       destinations from this origin for this piece.
    
    This is the hybrid — phase-space generation, geometric filtering.
    En passant, promotion, castling are NOT handled here (§11.2.8).
    """
```

Implementation notes:

- The unobstructed phase set for sliding pieces comes from `P_rook`, `P_bishop`, `P_queen` in `phase_operators.py` — already imported.
- For pawns, call both `_advance` and `_capture` phases (the module-private helpers don't exist; inline the advance+capture logic here or refactor to expose them). Decision: do not refactor `phase_operators.py`. Inline the advance+capture phase computation in `occupation_aware_a.py`.
- Use `chess.Board.legal_moves` filtered to `origin_square` for the filter step. This is genuinely the geometric reference path; do not try to make this phase-native.
- Pawn-color: pass the mover_charge through to decide advance direction (+67 for white, -67 for black) and capture diagonals.

### Extend `occupation_equivalence_check.py` to run A, B, and C

Update the CLI to run all three solutions per (position, piece, origin) triple. Parallel to the existing B/C columns, add A columns. New CSV schema:

```
position_fen, game_id, ply, polarization, origin_row, origin_col,
mover_charge,
solution_a_dests, solution_b_dests, solution_c_dests,
python_chess_dests,  # the reference — legal_moves filtered to this origin
a_equals_chess, b_equals_chess, c_equals_chess,
a_equals_b, b_equals_c, a_equals_c,
a_missing, a_extra, b_missing, b_extra, c_missing, c_extra,
solution_a_time_ns, solution_b_time_ns, solution_c_time_ns
```

Rename the existing CSV output to reflect the expanded scope: `exp2_occupation_equivalence_abc.csv` (sibling of the existing `exp2_occupation_equivalence.csv` — do NOT overwrite the B/C-only file; the researcher wants both on disk for comparison).

Stdout summary now prints four agreement rates:
```
§11.4 complete (Solutions A, B, C vs python-chess):
  A matches python-chess: NNNN/NNNN (PP.PP%)
  B matches python-chess: NNNN/NNNN (PP.PP%)
  C matches python-chess: NNNN/NNNN (PP.PP%)
  A matches B:            NNNN/NNNN (PP.PP%)
  B matches C:            NNNN/NNNN (PP.PP%)
  A matches C:            NNNN/NNNN (PP.PP%)
  Mean A time: X.X µs
  Mean B time: X.X µs
  Mean C time: X.X µs
```

**Expected result:** A, B, C should all agree with each other at 100% on non-castling rows. A should match python-chess at 100% (by construction, since A's filtering step IS python-chess). B and C should match python-chess at whatever rate they matched before (99.48% of pseudo-legal, with the 0.52% being castling). A vs python-chess being below 100% would indicate a bug in A; surface immediately.

### New test file: `tests/test_occupation_aware_a.py`

Mirror the structure of `test_occupation_aware_b.py` and `test_occupation_aware_c.py`. Same five test cases:
1. Starting position rook (zero destinations)
2. Open file rook with mixed-charge blocker at a8
3. Bishop with mixed blockers
4. Pawn diagonal capture only with target present
5. Queen from empty center (27 destinations)

A should produce identical sets to B and C for all five tests.

### Run and verify

Run the extended CLI:
```bash
python occupation_equivalence_check.py --n-positions 100 --seed 42
```

Expected outcomes:
- A matches B matches C at 100% (modulo castling, which affects all three equally)
- A matches python-chess at 100% (by construction)
- Timing: A should be slower than both B and C because of the python-chess filter call, but within the same order of magnitude.

If A disagrees with B or C on any non-castling row, stop and surface the disagreement. Per §11.7.4, do not patch.

---

## Phase 2 — Close the castling gap

Add `P_castle` as a composite two-piece phase operator and integrate into A, B, and C.

### Mathematical framing

Castling is a coupled two-polarization transition: king and rook move atomically in a single turn. The phase-arithmetic description:

**Kingside castle (White):**
- King: (0, 4) → (0, 6). Phase shift: +2 × COL_GEN = +14.
- Rook: (0, 7) → (0, 5). Phase shift: -2 × COL_GEN = -14.

**Queenside castle (White):**
- King: (0, 4) → (0, 2). Phase shift: -2 × COL_GEN = -14.
- Rook: (0, 0) → (0, 3). Phase shift: +3 × COL_GEN = +21.

**Kingside castle (Black):**
- King: (7, 4) → (7, 6). Phase shift: +2 × COL_GEN = +14.
- Rook: (7, 7) → (7, 5). Phase shift: -2 × COL_GEN = -14.

**Queenside castle (Black):**
- King: (7, 4) → (7, 2). Phase shift: -2 × COL_GEN = -14.
- Rook: (7, 0) → (7, 3). Phase shift: +3 × COL_GEN = +21.

The **phase arithmetic** is trivial — six integer additions across the four castle types. The **preconditions** are global state:
- Castling rights bit set for this side / direction (board state)
- King and rook on their home squares (verifiable via occupation field)
- No pieces between king and rook (verifiable via phase set intersection with occupation field)
- King not in check, not passing through or into check (genuinely global — requires full position evaluation)

This asymmetry is what §11.2.8 was originally flagging. The phase operators are clean; the legality constraints are not phase-native. The composite operator acknowledges this by requiring the caller to provide the board state for precondition checking, while the phase arithmetic remains pure.

### New file: `castling.py`

```python
"""P_castle composite operator (§11.2.8 closure).

Castling is a coupled king+rook transition. The phase arithmetic per
transition is trivial integer addition; the preconditions are global
state (castling rights, king safety under all intermediate positions).

This module provides the phase-arithmetic component and delegates
precondition checking to python-chess's board state. It is called
from occupation_aware_{a,b,c} when the position's castling rights
permit the corresponding castle type.
"""
from dataclasses import dataclass
import chess

from phase_operators import phi, COL_GEN, MODULUS


@dataclass(frozen=True)
class CastleMove:
    """A castling transition as a phase pair.
    
    king_from, king_to, rook_from, rook_to are all phase integers
    in [0, 640). The (r, c) coordinates are recoverable via invert().
    """
    king_from: int
    king_to: int
    rook_from: int
    rook_to: int
    side: str  # 'kingside' | 'queenside'
    color: int  # +1 white, -1 black


# The four canonical castle moves as phase tuples.
# White king at (0, 4): king_from = phi(0, 4) = 0*67 + 4*7 = 28.
# Adjust as needed — do not trust this comment; compute from phi().
CASTLES: dict[tuple[int, str], CastleMove] = { ... }  # build at module load


def available_castles(board: chess.Board) -> list[CastleMove]:
    """Return the castle moves legal in `board` right now.
    
    Uses python-chess's castling_rights and board state to determine which
    of the four canonical castles are currently legal. Returns a list of
    CastleMove objects (possibly empty).
    
    This IS a geometric check — castling legality requires full position
    evaluation (king safety through all squares). The phase-arithmetic
    description of the move itself is independent of this check.
    """
    ...
```

Build the `CASTLES` dict at module load by computing `phi(r, c)` for each home and destination square. Do not hardcode the phase integers — compute them from `phi`.

### Integrate into occupation-aware generators

A, B, and C each get a small extension: when the origin square is a king's home square AND castling rights permit a castle involving this king, include the king-destination phase(s) from available `CastleMove` objects in the returned destination set.

Concretely, in each of `occupation_aware_moves_a`, `occupation_aware_moves_b`, `occupation_aware_moves_c`:

```python
if piece_char == "K":
    for castle in available_castles(board):
        if castle.color == mover_charge:
            king_dest_phase = castle.king_to
            king_dest_rc = invert(king_dest_phase)
            if king_dest_rc is not None:
                destinations.add(king_dest_rc)
```

The king's destination square is the observable effect of castling from a "what squares does this piece land on" perspective. The rook transition is implicit in the castle operation. python-chess's `legal_moves` represents castling as a king move to the castled-king square (e.g., `e1g1` for white kingside), so this matches its behavior.

### New test file: `tests/test_castling.py`

1. **`CASTLES` contains four entries** keyed by `(color, side)`, with correct phase values computed from `phi`.
2. **Starting position has no castles available** (rights are set, but castling is blocked because python-chess checks for intervening pieces).
3. **Position with kingside castling available for white** (e.g., FEN `r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1`): `available_castles` returns 4 castles (2 per color, but only white's are reachable this move), then specifically the white kingside castle's `king_to` phase equals `phi(0, 6)`.
4. **Position blocked by intervening piece** (knight on f1): white kingside castle is NOT returned.
5. **Integration test for A, B, C**: in the position from test 3, calling `occupation_aware_moves_X(board, "K", 0, 4, +1)` for each X ∈ {A, B, C} returns a destination set that includes `(0, 6)` (kingside castle) AND `(0, 2)` (queenside castle), in addition to the regular king moves.

### Re-run the equivalence CLI

After castling is integrated, re-run:
```bash
python occupation_equivalence_check.py --n-positions 100 --seed 42
```

**Expected:**
- A, B, C each now match python-chess at ~99.96%+ (the residual is only check/pin filters at the legal_moves level; against pseudo_legal_moves, match rate should be 100%).
- A vs B vs C stays at 100% agreement.
- The 6 previous castling disagreements in the CSV are now agreements.

Print a diff summary against the previous run:
```
Castling closure summary:
  Previous B vs pseudo_legal: NNNN/NNNN (99.48%)
  Current  B vs pseudo_legal: NNNN/NNNN (PP.PP%)
  Castling disagreements resolved: 6
```

If any castling cases remain unresolved, the stdout summary should list them with FEN + expected + actual.

---

## Phase 3 — Supplement and notebook updates

After Phases 1 and 2 are committed and the extended equivalence CLI reports the expected success, update the documentation.

### Supplement changes

#### §11.2.8 — add castling as now-handled

OLD:
```
**Not included:** 
- Occupation-based ray truncation (handled separately in §11.4)
- En passant (a temporal couple between two pawn moves)
- Castling (a coupled two-polarization transition)
- Promotion (a polarization-identity change at the horizon boundary)
- Check/checkmate legality (a global constraint on the king's phase tuple)
```

NEW:
```
**Not included:** 
- Occupation-based ray truncation (handled in §11.4 via Solutions A/B/C)
- Castling (handled in §11.4 via P_castle composite operator; see §11.4.3.1)
- En passant (a temporal couple between two pawn moves)
- Promotion (a polarization-identity change at the horizon boundary)
- Check/checkmate legality (a global constraint on the king's phase tuple)

En passant, promotion, and check/checkmate remain as documented exclusions pending future work. Castling was in this list initially and was closed in §11.4.3.1.
```

#### §11.3.6 — promote to validated

OLD:
```
### §11.3.6 Decision point

If §11.3 produces full equivalence, proceed to §11.4 (occupied-board extension).

If §11.3 produces partial or full failure, stop and analyze before proceeding. The failure pattern will indicate whether the phase-operator formulation is fundamentally wrong or just needs refinement.
```

NEW:
```
### §11.3.6 Result

**Validated: 416/416 (100.00%) pairs equivalent.** The phase-operator destinations computed from §11.2 match python-chess's empty-board legal moves exactly for every (polarization, origin) pair. No operator formula was tuned during the experiment — the §11.2 specifications matched the geometric reference on the first CLI run.

Additional structural result verified alongside the equivalence check: for every piece × every origin × every k ∈ {±1, ..., ±7} in the operator's shift set, phase-op destinations never wrap the torus and alias back to an unintended on-board square. The "torus clip" boundary handling in §11.3.3 is a theorem at this problem size, not an approximation.

**Decision:** §11.4 unblocked.
```

#### §11.4.3 — add §11.4.3.1 subsection for castling

Add a new subsection after the existing §11.4.3 body:

```
### §11.4.3.1 Castling as composite phase operator

Castling is a coupled king+rook atomic transition. Its phase-arithmetic description is trivial — four canonical castles, each a pair of integer shifts:

| Castle | King shift | Rook shift |
|---|---|---|
| White kingside  | +2 × COL_GEN = +14 | -2 × COL_GEN = -14 |
| White queenside | -2 × COL_GEN = -14 | +3 × COL_GEN = +21 |
| Black kingside  | +2 × COL_GEN = +14 | -2 × COL_GEN = -14 |
| Black queenside | -2 × COL_GEN = -14 | +3 × COL_GEN = +21 |

The phase arithmetic is clean. The preconditions are not: castling rights bits, no intervening pieces, king not in check at any intermediate square. The first two preconditions are checkable in phase space (bit state + occupation field intersection). The third requires full position evaluation and remains geometric. This asymmetry — phase arithmetic trivial, legality checks global — is the reason castling was initially on §11.2.8's exclusion list. The composite operator formulation accepts the asymmetry: phase arithmetic is pure, legality delegates to python-chess's board state.

Integrated into A, B, C. The 6 castling disagreements observed before §11.4.3.1 was added are resolved.
```

#### §11.4.5 — promote to validated

OLD:
```
### §11.4.5 Decision point

Full equivalence with geometric legal moves means the phase-operator formulation is operationally complete for move generation. We can then ask what the phase-space representation offers that the geometric one does not (§11.5 onward).

Partial or full failure means specific edge cases need special handling. Record which.
```

NEW:
```
### §11.4.5 Result

**Validated.** With the §11.4.3.1 castling closure applied:

| Comparison | Agreement |
|---|---|
| A ≡ B ≡ C (internal cross-check) | 100.00% |
| A vs python-chess pseudo-legal moves | 100.00% |
| B vs python-chess pseudo-legal moves | 100.00% |
| C vs python-chess pseudo-legal moves | 100.00% |
| Any ≡ vs python-chess legal moves | ~99.96% (residual: check/pin filters, §11.2.8) |

Four independent channels converge on the same destination set for every (position, polarization, origin) triple: python-chess's geometric reference, Solution A (hybrid), Solution B (phase-space batch), Solution C (phase-space sequential). The phase-operator formulation is operationally complete for move generation modulo the remaining §11.2.8 exclusions (en passant, promotion, check/checkmate filtering).

**Timing (mean per call on sampled middlegame positions):**
- Solution A: ~X.X µs
- Solution B: ~X.X µs
- Solution C: ~X.X µs

Solution C's early-halt advantage is real and consistent with the lattice-fermion framing — rays terminate at the first scattering site, and most rays in a populated middlegame terminate within 1-3 steps. Solution A's overhead comes from the python-chess filter call.

**Decision:** §11.5 unblocked. The phase-operator move generator is functionally equivalent to the geometric one for the pseudo-legal scope.
```

Fill in the actual timing numbers from the extended CLI run before committing.

### Research notebook changes

Update the §11 stub in `chess_spectral_research_notebook.md`:

OLD (at line ~2063):
```
## 11. Phase-Operator Move Engine

> **Status.** Working supplement — lives in [PHASE_OPERATOR_SUPPLEMENT.md](PHASE_OPERATOR_SUPPLEMENT.md) as a standalone document pending experimental validation. Internal numbering §11.1–§11.9 already matches this slot, so the supplement drops in verbatim once data is collected.
```

NEW:
```
## 11. Phase-Operator Move Engine

> **Status.** §11.3 and §11.4 validated. §11.5 and §11.6 pending.  Full content lives in [PHASE_OPERATOR_SUPPLEMENT.md](PHASE_OPERATOR_SUPPLEMENT.md). Key results:
>
> - **§11.3 (empty-board equivalence):** 416/416 (100.00%) — phase operators match python-chess empty-board legal moves without tuning.
> - **§11.4 (occupation-aware equivalence):** Four independent channels (Solutions A, B, C, and python-chess itself) agree at 100% on pseudo-legal moves once castling is included via a composite `P_castle` operator. Remaining gap against legal_moves is check/pin filtering (§11.2.8).
> - **Structural claim:** The §11.1.2 hypothesis ("2D board coordinates are redundant representation of a coprime phase-tuple structure") is empirically confirmed for pseudo-legal move generation in standard chess.
```

Do NOT rewrite the rest of §11. The supplement remains the canonical document; the notebook stub points at it.

### Update README.md

The README in `docs/chess-maths/phase_operators/` should now mention Solution A, reflect the §11.4 validation, and add a pointer to the committed result numbers. Remove the "results pending commit" TODO from the README (it's now closed).

---

## Phase 4 — Commit structure and handoff

Commit structure (three separate commits on the existing `chess-spectral-phase-operator-11-4` branch):

1. **Solution A addition:** `§11.4 Solution A: post-hoc geometric pruning; four-way equivalence channel`
   - `occupation_aware_a.py`, `tests/test_occupation_aware_a.py`, extended CLI, extended CSV.
   - Headline in commit message: agreement rates A/B/C/chess and timing means.

2. **Castling closure:** `§11.4.3.1 P_castle composite operator; castling gap closed`
   - `castling.py`, `tests/test_castling.py`, A/B/C integration, re-run CLI.
   - Headline in commit message: pseudo-legal agreement now 100%, castling disagreements resolved.

3. **Supplement and notebook update:** `§11.3 / §11.4 promoted to validated; notebook stub updated`
   - Supplement edits (§11.2.8, §11.3.6, §11.4.3.1, §11.4.5), notebook §11 stub, README.
   - All numbers filled in from the actual CLI run.

Three commits, not one, so the revert surface is small if something needs to be backed out.

### Before opening the PR

**Do not open the PR yet.** After the three commits are on the branch, notify the researcher that the branch is ready for Claude Chat review of the supplement and notebook edits. The researcher will review both documents for consistency, catch any framing drift, and confirm the numbers in §11.3.6 and §11.4.5 are reported accurately. Only after that review is complete should the PR be opened.

Suggested handoff message (at the end of your final commit log):
> Branch ready for supplement + notebook review. Pausing before PR.
> §11.3 validated (416/416). §11.4 validated (A/B/C/chess 100% agreement, pseudo-legal). Castling closed.
> Next: researcher reviews supplement and notebook edits in Claude Chat; PR opens after.

---

## Scope guard

- Do not modify `phase_operators.py`, `phase_to_coords.py`, or `equivalence_check.py`. These are the §11.3 substrate.
- Do not modify `occupation_aware_b.py` or `occupation_aware_c.py` except to integrate the castling call. Their existing occupation logic is validated.
- Do not handle en passant, promotion, or check/pin filtering. Still §11.2.8 exclusions.
- Do not start §11.5 or §11.6 scaffolding.
- Do not tune Solution A to match B/C. If A disagrees with B or C on a non-castling row before castling is added, stop and report. B and C are already validated against each other.
- Do not open the PR. Stop at the three commits and hand off.

## Success criteria

Phase 1: A added, extended CLI runs, A ≡ B ≡ C at 100% on non-castling rows, CSV and tests pass.

Phase 2: Castling integrated, pseudo-legal agreement goes from 99.48% to 100.00% for A, B, and C. Six castling disagreements resolved.

Phase 3: Supplement §11.2.8, §11.3.6, §11.4.3.1, §11.4.5 updated with actual numbers. Notebook §11 stub reflects validated status. README reflects current state.

Phase 4: Three commits on branch. Handoff message printed. PR not opened.

If all four phases complete cleanly, §11.3 and §11.4 are closed and §11.5 is the next conversation with the researcher.
