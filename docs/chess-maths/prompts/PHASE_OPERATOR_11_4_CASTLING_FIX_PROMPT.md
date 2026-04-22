# Claude Code: §11.4.3.1 castling availability bug fix

## Context

While verifying the §11.4 ep/promotion gap closure
(`chess-spectral-phase-operator-ep-promotion` branch), the researcher
and Claude Code's inline check against `pseudo_legal_moves` exposed a
pre-existing bug in `castling.py::available_castles`:

```
on 100 positions against pseudo_legal_moves + castling:
  1124/1129 (99.56%) pieces match
  residual 5 pieces = phantom castle destinations
```

The phantom destinations come from `available_castles` delegating
condition 4–5 (king-not-in-check, king-path-not-attacked) to
`board.is_legal(Move.from_uci(castle.uci))`. The delegation is correct
*when* the king is on its canonical castling home square. It is
incorrect when the king has moved and a rook has since arrived at the
canonical king square — in which case python-chess parses the UCI
(e.g., `"e1c1"`) as a rook slide, returns True, and
`available_castles` erroneously adds the castle-king destination (e.g.,
(0, 2)) to the king's move set regardless of where the actual king
sits.

Verified scenario (reproducible outside the test suite):

```
FEN: 4k3/8/8/8/8/3K4/8/4R3 w - - 0 1
  - white king on d3, white rook on e1, no castling rights
  - board.is_legal(Move.from_uci("e1c1")) → True  (parsed as rook slide)
  - board.is_legal(Move.from_uci("e1g1")) → True
  - available_castles(board) returns [white queenside, white kingside]
  - castle_king_destinations(board, WHITE) returns {(0, 2), (0, 6)}
```

python-chess's own `legal_moves` emits `e1c1` as a rook move, not a
king move, so this phantom is masked by the check filter in
`board.legal_moves` but shows up cleanly against `pseudo_legal_moves`
where the 0.52% residual lives.

This is a **delegation-layer bug, not a phase-math bug.** The
mathematical castling operator P_castle is correct; its availability
predicate is what broke. The fix is a one-sentence guard before the
`is_legal` call: verify that the actual king sits on the canonical
king-from square (and, defensively, the actual rook on its canonical
rook-from square) before trusting `is_legal`. If those preconditions
don't hold, the position is definitionally not a castling situation
regardless of what `is_legal` returns about the same UCI.

## Design discipline

The fix is **additive guards**, not a reformulation. It preserves:

- The §11.4.3.1 mathematical claim (phase shifts and composite
  operator structure) — unchanged.
- The delegation pattern for attack-check legality — unchanged.
- CASTLES dict, CastleMove, castle_king_destinations API — unchanged.

What changes:

- `available_castles` adds two guard clauses (king-on-home,
  rook-on-home) before invoking `is_legal`.
- One sentence in §11.4.3.1 clarifies that the guards were missing
  from the original reference implementation and describes why they
  matter.

No new supplement subsection. No new module. No new operator. This is
a bugfix within the existing §11.4.3.1 scope.

## Phase 1 — Supplement one-line clarification

Locate the sentence in §11.4.3.1 that describes the `is_legal`
delegation:

OLD:
```
The reference implementation delegates conditions 4–5 to python-chess's
`board.is_legal()` on the canonical castling UCI move, making P_castle
a composite operator in the §11.4-scoped sense: its geometry is
expressed by φ() arithmetic, but its full legality predicate borrows
one attack-check primitive from the geometric reference.
```

NEW:
```
The reference implementation delegates conditions 4–5 to python-chess's
`board.is_legal()` on the canonical castling UCI move — after
explicitly verifying that the king and rook sit on their canonical
home squares. Without the home-square guards, python-chess may parse
the castling UCI as a non-castling piece slide (e.g., a rook on e1
makes `"e1c1"` a legal rook move), and `is_legal` returns True for
reasons unrelated to castling. The home-square guards turn the
delegation into an unambiguous castling check. This makes P_castle a
composite operator in the §11.4-scoped sense: its geometry is
expressed by φ() arithmetic, its home-square preconditions are
phase-native (set-membership in the occupation field with piece-type
discrimination), and only its full attack-map predicate borrows one
primitive from the geometric reference.
```

Grep verification:
```bash
grep -c "home-square guards" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 2
grep -c "unambiguous castling check" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 1
```

Commit Phase 1 alone, message:
`§11.4.3.1 supplement: document home-square guards on is_legal delegation`

## Phase 2 — Fix `castling.py::available_castles`

Change the `available_castles` function to add two guards. Current
implementation:

```python
def available_castles(board: chess.Board) -> list[CastleMove]:
    out: list[CastleMove] = []
    for (color, _side), castle in CASTLES.items():
        if board.turn != color:
            continue
        try:
            move = chess.Move.from_uci(castle.uci)
        except ValueError:
            continue
        if board.is_legal(move):
            out.append(castle)
    return out
```

New implementation:

```python
def available_castles(board: chess.Board) -> list[CastleMove]:
    """Return the castles currently legal for the side to move.

    Uses board.is_legal() on the canonical UCI move for each candidate,
    after verifying the king and rook sit on their canonical home
    squares. Without those guards, python-chess may accept the
    castling UCI as a non-castling slide of whatever piece happens to
    occupy the from-square (e.g., a rook on e1 makes "e1c1" a legal
    rook move, which would otherwise be mistaken for a legal castle).
    """
    out: list[CastleMove] = []
    for (color, _side), castle in CASTLES.items():
        if board.turn != color:
            continue
        # Guard 1: the actual king must be on its castling home square.
        # Otherwise is_legal may accept the UCI as a piece slide by
        # whatever is actually sitting there.
        king_sq = chess.square(castle.king_from_rc[1], castle.king_from_rc[0])
        piece = board.piece_at(king_sq)
        if piece is None or piece.piece_type != chess.KING or piece.color != color:
            continue
        # Guard 2: the actual rook must be on its castling home square.
        # Castling rights can be set while the rook has already moved or
        # been captured (rare FEN-construction edge cases); the presence
        # check is defensive and inexpensive.
        rook_sq = chess.square(castle.rook_from_rc[1], castle.rook_from_rc[0])
        rpiece = board.piece_at(rook_sq)
        if rpiece is None or rpiece.piece_type != chess.ROOK or rpiece.color != color:
            continue
        try:
            move = chess.Move.from_uci(castle.uci)
        except ValueError:
            continue
        if board.is_legal(move):
            out.append(castle)
    return out
```

Note: `chess.square(file, rank)` takes `(file, rank)` in that order;
`king_from_rc` is `(row, col) = (rank, file)`. The guard code above
passes `(col, row) = (file, rank)` in that order, matching
python-chess's API. Double-check this when writing — off-by-axis here
would produce a no-op guard that silently passes everything, which is
exactly the kind of bug that led us here.

## Phase 3 — Tests

Add to `tests/test_castling.py`:

```python
class TestAvailableCastlesGuards(unittest.TestCase):
    """§11.4.3.1 fix — is_legal delegation is only trustworthy when
    the king and rook sit on their canonical castling home squares."""

    def test_rook_on_e1_without_king_does_not_produce_phantom_castle(self):
        # White rook on e1, white king on d3, no castling rights.
        # is_legal("e1c1") returns True (rook slide), but that must NOT
        # translate into a phantom king-side castle destination.
        board = chess.Board("4k3/8/8/8/8/3K4/8/4R3 w - - 0 1")
        self.assertEqual(available_castles(board), [])
        self.assertEqual(
            castle_king_destinations(board, chess.WHITE), frozenset())

    def test_rook_on_e8_without_king_does_not_produce_phantom_castle(self):
        # Mirror of the above for black.
        board = chess.Board("4r3/8/3k4/8/8/8/8/4K3 b - - 0 1")
        self.assertEqual(available_castles(board), [])
        self.assertEqual(
            castle_king_destinations(board, chess.BLACK), frozenset())

    def test_rook_on_a1_without_king_does_not_produce_queenside_phantom(self):
        # White rook on a1 with no castling rights and king moved.
        # Ensures the rook-home guard also protects against
        # has_castling_rights=False FENs where the king and rook happen
        # to coincidentally be on home squares but rights are lost.
        board = chess.Board("r3k3/8/8/8/8/3K4/8/R7 w q - 0 1")
        # No white castling rights, no castle available for white.
        self.assertEqual(available_castles(board), [])

    def test_king_on_home_rook_missing_does_not_produce_castle(self):
        # White king on e1 with castling rights flag set, but rook
        # absent from a1 and h1. Guards should reject both sides.
        board = chess.Board("4k3/8/8/8/8/8/8/4K3 w KQ - 0 1")
        self.assertEqual(available_castles(board), [])

    def test_both_on_home_with_rights_still_produces_castle(self):
        # Regression check: the normal case still works.
        board = chess.Board(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        castles = available_castles(board)
        self.assertEqual(len(castles), 2)
        sides = {c.side for c in castles}
        self.assertEqual(sides, {"kingside", "queenside"})
```

Run the updated `test_castling.py`:
```bash
cd docs/chess-maths/phase_operators
python -m unittest tests.test_castling -v
```

All previous tests in `test_castling.py` must still pass — the fix is
additive; it tightens the availability predicate but does not relax
it, so cases that were legal before remain legal.

## Phase 4 — Verification

Re-run the occupation equivalence CLI against pseudo-legal moves on
the same 100 positions that showed 1124/1129 before the fix:

```bash
cd docs/chess-maths/phase_operators
python occupation_equivalence_check.py \
    --corpus ../results/sweep_chain_lichess_drnykterstein_2026-04-14_N10 \
    --n-positions 100 --seed 42
```

Expected:
- A matches python-chess pseudo-legal moves: 100.00% (was whatever it
  was before; should now be 100% modulo §11.5 check-unsafe residual
  which is a separate concern measured against `board.legal_moves`).
- B/C match python-chess pseudo-legal moves: 100.00%.
- A ≡ B ≡ C internal cross-check: 100.00% (should already be 100%
  from PR #45).
- No new regressions in the `board.legal_moves` match rate (which is
  check-unsafe-filtered and unrelated to this fix).

If any rate is below 100% against pseudo-legal moves, stop and report
the disagreement rows. Per §11.7.4, do not tune around remaining
disagreements; surface them.

## Phase 5 — Commit and handoff

Three commits on a new branch `chess-spectral-phase-operator-11-4-castling-fix`
branched **from main** (not from the ep/promotion branch, which is
separately merging):

1. `§11.4.3.1 supplement: document home-square guards on is_legal delegation`
   — supplement edit only.
2. `§11.4.3.1 fix: home-square guards in available_castles`
   — `castling.py` change plus new unit tests.
3. `§11.4 equivalence CLI re-run: pseudo-legal match now 100.00%`
   — if the CLI emits a summary file, commit it; if not, the re-run
   validates on its own and this commit can be skipped (and the
   branch ends with 2 commits).

Do NOT open the PR. Print handoff:

```
Branch chess-spectral-phase-operator-11-4-castling-fix ready for review.
§11.4.3.1 bugfix complete.

Before (pseudo_legal_moves match, n=100, seed=42):
  A/B/C vs python-chess pseudo-legal: <previous rate>/1129 (<previous %>)

After (same CLI, same command):
  A/B/C vs python-chess pseudo-legal: 1129/1129 (100.00%)

Five new unit tests passing in test_castling.py.
Total castling tests: <total count> passing.

§11.4 is now fully closed against pseudo-legal moves. The remaining
gap vs board.legal_moves (check-unsafe filtering) is structurally
§11.5 territory and validated separately via the path-1 reverse
phase-cast is_check detector.

Supplement §11.4.3.1 updated with the home-square-guard clarification.

Commits on branch (<N> total, not pushed, no PR):
  <sha1> supplement patch
  <sha2> castling.py guards + tests
  <sha3> (if present) equivalence CLI re-run output

Pausing for researcher review. No PR opened per scope guard.
```

## Scope guard

- Do not modify any file outside `castling.py`, the supplement, and
  `tests/test_castling.py`. The rest of the substrate is frozen.
- Do not refactor `available_castles` beyond adding the two guards.
  Keep the `is_legal` delegation pattern as the attack-check primitive;
  the guards are additive.
- Do not touch `occupation_aware_{a,b,c}.py` — they consume
  `castle_king_destinations` which is unchanged.
- Do not open the PR. Hand off for researcher review.
- Do not bundle into the ep/promotion PR. This is a separate concern
  with its own commit trail.

## Success criteria

Phase 1: supplement §11.4.3.1 has the home-square-guard clarification;
two grep checks pass.

Phase 2: `available_castles` has the two guards; the existing public
API (`CASTLES`, `CastleMove`, `castle_king_destinations`,
`available_castles`) is unchanged in signature and behavior for every
case where the guards pass.

Phase 3: five new unit tests pass; all previous `test_castling.py`
tests still pass.

Phase 4: pseudo-legal match rate on the standard 100-position sample
reaches 100.00% for A, B, and C.

Phase 5: branch sits with 2–3 commits ready for PR, handoff message
printed, PR not opened.

If Phase 4 shows anything less than 100% pseudo-legal match, report
the disagreements — do not adjust the guards. The whole point of
§11.7.4 discipline is that surprise residuals become research findings,
not code patches.
