# Claude Code: §11.4 gap closure — en passant + promotion

## Context

After §11.3/§11.4 castling closure and §11.5/§11.6 nulls, Claude Code's
status read (via researcher audit) identified two remaining gaps in the
phase-operator wrapper layer that prevent bitwise equality with
python-chess's legal-move enumeration:

**Gap 1 — en passant capture generation.** `occupation_field.pawn_destinations`
only emits a diagonal destination when that square is occupied by
opposite charge:

```python
charge = occupation.get(cap_phase)
if charge is not None and charge != mover_charge:
    out.add(rc)
```

En passant targets an *empty* square (the captured pawn sits on a
different square from the capture destination). The phase layer never
emits ep moves because the information that "this empty diagonal is a
capturable phantom" is not in the occupation dict — it lives in the
FEN's `ep_square` field.

**Gap 2 — promotion piece enumeration.** Phase operators return
destination phases (or `(r, c)` tuples). When a pawn reaches the last
rank, python-chess emits four moves (`=Q`, `=R`, `=B`, `=N`) with
`Move.promotion` set; the phase layer emits a single destination.
Expanding one destination into four `chess.Move` objects is a wrapper-
layer concern, not phase math — the destination square is already
correct, it is just under-specified as a move.

These are both small, well-scoped, and additive. Neither touches the
phase operator specifications in §11.2, the occupation field, or the
sliding-ray logic in Solutions A/B/C. They close the 0.52% residual
against `pseudo_legal_moves` that remained after §11.4.3.1 castling
closure.

## Design discipline (unchanged from §11.4)

Both fixes are **wrapper-layer pass-through of board state that is not
in the occupation field**. Neither introduces new phase arithmetic;
both surface state that python-chess tracks (`board.ep_square`,
last-rank detection via coord parity) into the phase-space destination
enumeration.

Research-record honesty: these are not "phase-native" in the same
sense as P_castle (which *did* introduce a composite phase operator).
They are **state-dependent filters** on destinations the existing
operators already produce. The supplement should document them as such.

## Phase 1 — Supplement patches

Apply three small patches to `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`.

### PATCH 1 — §11.2.8 remove ep and promotion from exclusions

Locate the §11.2.8 exclusion list (after the §11.4.3.1 castling closure
edits). The list currently reads something like:

OLD:
```
**Not included:**
- Occupation-based ray truncation (handled in §11.4 via Solutions A/B/C)
- Castling (handled in §11.4 via P_castle composite operator; see §11.4.3.1)
- En passant (a temporal couple between two pawn moves)
- Promotion (a polarization-identity change at the horizon boundary)
- Check/checkmate legality (a global constraint on the king's phase tuple)
```

NEW:
```
**Not included:**
- Occupation-based ray truncation (handled in §11.4 via Solutions A/B/C)
- Castling (handled in §11.4 via P_castle composite operator; see §11.4.3.1)
- En passant (handled in §11.4 via ep_square pass-through; see §11.4.3.2)
- Promotion (handled in §11.4 via last-rank move expansion; see §11.4.3.3)
- Check/checkmate legality (a global constraint on the king's phase tuple)

Of the original five exclusions, four have been closed. Check/checkmate
legality remains — it requires the full king-safety filter (the §11.5
is_check check we validated in two paths) and is structurally distinct
from per-piece move generation.
```

### PATCH 2 — add §11.4.3.2 en passant subsection

Add a new subsection after §11.4.3.1 (castling closure):

```
### §11.4.3.2 En passant as ep_square pass-through

En passant is a state-dependent capture where the destination square is
empty but capturing is nevertheless legal because the opposite side's
pawn just moved two squares and is on an adjacent file. The destination
is the phantom square the two-step pawn would have occupied if it had
only advanced one.

The phase arithmetic is identical to an ordinary diagonal pawn capture —
the destination phase is (φ_origin ± DIAG_NE_SW_GEN) or
(φ_origin ± DIAG_NW_SE_GEN) per §11.2.7. What differs is the
occupation-field predicate: the diagonal is empty, not occupied by
opposite charge.

**Integration.** The `pawn_destinations` generator accepts an optional
ep_phase parameter. When present, it matches against the two capture
diagonals; if a match is found, that diagonal is added to destinations
even though the occupation field shows the square as empty. The ep_phase
is derived from python-chess's `board.ep_square` — an `int | None`
field on the Board object that is part of FEN state, not HDC state.

This is a **state-dependent filter**, not a new phase operator: the
phase arithmetic was already producing the capture phase; the ep_square
pass-through is what lifts it from "drop if empty" to "keep if empty
and equals ep_phase."
```

### PATCH 3 — add §11.4.3.3 promotion subsection

Add:

```
### §11.4.3.3 Promotion as last-rank move expansion

When a pawn advances or captures onto the last rank (row 7 for white,
row 0 for black), the move is structurally a single phase transition
whose destination corresponds to a polarization-identity change: the
pawn becomes a queen, rook, bishop, or knight. python-chess represents
this as four distinct `chess.Move` objects, one per promotion piece,
sharing the same (from, to) pair.

The phase operators produce the destination correctly in a single call —
the diagonal capture phase or the forward advance phase per §11.2.7.
The phase arithmetic does not distinguish "pawn arriving on last rank"
from "pawn arriving anywhere else"; the distinction is a boundary
property of the destination coordinate.

**Integration.** A small wrapper at the move-emission boundary (where
destinations become `chess.Move` objects) tests whether the destination
row is the last rank for the mover's charge. If yes, the single
destination expands into four Move objects with `promotion` set to
each of QUEEN, ROOK, BISHOP, KNIGHT. This matches python-chess's
emission order.

This is **not a phase-native operation**. The encoder's polarization-
identity change (pawn → queen) is a separate structural question that
§11 does not address. The expansion here is a wrapper-layer formality
that makes the phase generator's output set-equal to python-chess's
legal move enumeration; the underlying phase destination is a single
point per advance, and the four promotion variants are the same point
with four different "tag" values.

Promotion under-promotion (emitting =N/=B/=R when =Q is usually best)
is always included because python-chess's legal_moves emits all four;
whether the move is *good* is a search question, not a move-generation
question.
```

### Grep verification

```bash
grep -c "§11.4.3.2" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 2
grep -c "§11.4.3.3" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 2
grep -c "ep_square pass-through" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md  # expect 2
grep -c "last-rank move expansion" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md  # expect 2
grep -c "En passant (a temporal couple" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md  # expect 0
```

Commit Phase 1 as: `§11.4.3.2 / §11.4.3.3 supplement: document en passant and promotion wrapper closures`

## Phase 2 — Code changes

All changes are additive to existing files. Do not create new modules
for these — they are small enough that new module overhead would be
noise. Follow the pattern established in §11.4.3.1 where P_castle got
its own `castling.py` but the A/B/C integration was a small union into
the king destinations.

### Change 1 — `occupation_field.py::pawn_destinations` signature + ep logic

Change the `pawn_destinations` function to accept an optional
`ep_phase` keyword argument.

```python
def pawn_destinations(origin_r: int, origin_c: int,
                      occupation: dict[int, int],
                      mover_charge: int,
                      ep_phase: int | None = None,
                      ) -> frozenset[tuple[int, int]]:
    """White/black pawn destinations with occupation-aware advance + capture
    and optional en passant.

    Advance cannot land on any occupied square; two-step advance also
    requires the intermediate square to be empty. Captures require the
    diagonal destination to be occupied by opposite charge — UNLESS
    ep_phase is set and equals the capture diagonal phase, in which case
    the capture is allowed even though the square is empty (en passant).

    ep_phase: optional phase of the en passant target square, derived from
    board.ep_square. None when no ep capture is available.
    """
```

Implementation: the existing two-capture loop appends a diagonal phase
if (a) the square is occupied by opposite charge, OR (b) ep_phase is
not None and ep_phase equals the diagonal phase. The second branch is
a single `or` clause added to the existing condition.

### Change 2 — `occupation_aware_{a,b,c}.py::occupation_aware_moves_*` ep_phase pass-through

For each of A, B, and C, when the piece is a pawn, compute ep_phase
from `board.ep_square` and pass it to `pawn_destinations`.

```python
# inside occupation_aware_moves_a / b / c, in the pawn branch:
ep_phase = None
if board.ep_square is not None:
    ep_r = chess.square_rank(board.ep_square)
    ep_c = chess.square_file(board.ep_square)
    ep_phase = phi(ep_r, ep_c)
# ... pass ep_phase=ep_phase to pawn_destinations call
```

All three solutions delegate pawn logic to the same
`pawn_destinations` call, so this is the only place that needs the
change — but because each of A, B, C has its own `pc == "P"` branch,
the ep_phase pass-through must be added to all three. (Alternative:
factor the ep_phase computation into `occupation_field.py` and let the
solutions call it. Pick whichever is simpler; the latter is marginally
cleaner since it keeps python-chess imports centralized.)

Recommended: add a helper in `occupation_field.py`:

```python
def ep_phase_from_board(board: chess.Board) -> int | None:
    if board.ep_square is None:
        return None
    r = chess.square_rank(board.ep_square)
    c = chess.square_file(board.ep_square)
    return phi(r, c)
```

and call it from each solution's pawn branch.

### Change 3 — promotion expansion at the equivalence-check boundary

Promotion is a wrapper-layer concern. It does not belong inside A/B/C
themselves (which correctly return destination squares). It belongs at
the point where destinations are compared against python-chess's
`legal_moves`, or wherever the phase-space destinations are turned
into `chess.Move` objects for external consumption.

Inside `occupation_equivalence_check.py`, there is a comparison between
phase-space destinations and python-chess destinations. Audit that
comparison:

- If phase-space destinations are represented as `set[(r, c)]` and
  python-chess destinations are collapsed to `set[(to_r, to_c)]` for
  comparison, **promotion is already handled** — a pawn reaching the
  last rank produces one (to_r, to_c) in the phase side and four
  `Move` objects on the python-chess side, all sharing the same
  (to_r, to_c). Collapsing to the set of destination squares makes
  them equal. Verify that this is in fact how the existing comparison
  is done; if yes, Gap 2 is closed by virtue of the comparison shape
  and no code change is needed.

- If the comparison is move-level (comparing `Move` objects or UCI
  strings), add a promotion expansion helper that, for each pawn
  destination on the last rank, emits four (destination, piece)
  tuples instead of one.

Read `occupation_equivalence_check.py`'s comparison code and pick the
right path.

### Tests

Extend `tests/test_occupation_aware_a.py`, `test_occupation_aware_b.py`,
`test_occupation_aware_c.py` each with two new tests:

1. **En passant test.** FEN: `rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3`.
   - White pawn on e5 (origin row 4, col 4).
   - Black pawn on d5 (row 4, col 3).
   - ep_square is d6 (row 5, col 3).
   - Expected destinations for white pawn on e5: `{(5, 4)}` (e6 advance) + `{(5, 3)}` (ep capture of d5 pawn, destination d6).
   - Total: `{(5, 4), (5, 3)}`. Assert equality.

2. **Promotion test.** FEN: `8/P7/8/8/8/8/8/k3K3 w - - 0 1`.
   - White pawn on a7 (row 6, col 0). Empty a8.
   - Expected destination for white pawn: `{(7, 0)}` — single destination square (a8).
   - Promotion expansion into four moves is tested at the wrapper layer
     (see test_occupation_equivalence_check below), not here.

Add `tests/test_occupation_equivalence_check.py` if not present, and
add one test for promotion expansion:

3. **Promotion move expansion.** Same FEN as above. Call the wrapper
   that turns phase-destinations into `chess.Move` objects. Assert
   that the pawn-on-a7 produces four Move objects with
   `.promotion ∈ {QUEEN, ROOK, BISHOP, KNIGHT}` all sharing
   `.from_square == a7` and `.to_square == a8`.

### Running order

1. Apply the three supplement patches. Verify grep.
2. Add `ep_phase_from_board` helper in `occupation_field.py`.
3. Update `pawn_destinations` signature to accept `ep_phase` kwarg.
4. Update A/B/C pawn branches to call the helper and pass ep_phase.
5. Audit `occupation_equivalence_check.py` comparison code; if
   promotion expansion is needed, add it; if not, note in the commit
   message that Gap 2 is closed by comparison shape.
6. Add the six new unit tests (two per solution plus one for wrapper).
7. Run full test suite: `python -m unittest discover`. Must pass.
8. Re-run `occupation_equivalence_check.py --n-positions 100 --seed 42`
   against the drnykterstein corpus. Expected: all four channels match
   python-chess pseudo-legal moves at 100%, closing the 0.52% residual.

### Commit structure

Three commits on a new branch `chess-spectral-phase-operator-ep-promotion`:

1. `§11.4.3.2/3.3 supplement: en passant and promotion wrapper closures`
2. `§11.4.3.2: ep_square pass-through in pawn_destinations; A/B/C integration`
3. `§11.4.3.3: promotion expansion audit + tests; residual closed`

### Handoff

Stop after the three commits. Print handoff:

```
Branch chess-spectral-phase-operator-ep-promotion ready for review.
§11.4 gap closure complete.

  Before: A/B/C match pseudo_legal_moves at NN.NN% (residual = ep + promotion)
  After:  A/B/C match pseudo_legal_moves at 100.00% on all sampled positions

Six new unit tests passing. Supplement updated with §11.4.3.2 and §11.4.3.3.

Remaining §11.2.8 exclusion: check/checkmate legality filter (validated
separately in §11.5 path-1 phasecast_is_check).

Pausing for researcher review. No PR opened.
```

## Scope guard

- Do not modify any file outside `phase_operators/` except the
  supplement.
- Do not touch `phase_operators.py`, `phase_to_coords.py`, or
  `castling.py` — these are frozen.
- Do not add new experiments, no §12, no Phase B.
- Do not open the PR. Hand off for researcher review.
- If the comparison in `occupation_equivalence_check.py` is move-level
  and promotion expansion requires non-trivial refactoring, stop and
  report rather than making large changes — this prompt assumes the
  expansion is small.

## Success criteria

Phase 1: three supplement patches applied, five grep checks pass.

Phase 2: `pawn_destinations` accepts `ep_phase` kwarg; A/B/C pass ep
state through; promotion expansion handled at the right layer; six
new tests pass; full test suite passes; equivalence CLI reports
100.00% A/B/C vs pseudo_legal_moves match on the drnykterstein
corpus.

If the equivalence CLI shows anything less than 100%, stop and report
the disagreement rows rather than tuning — per §11.7.4.
