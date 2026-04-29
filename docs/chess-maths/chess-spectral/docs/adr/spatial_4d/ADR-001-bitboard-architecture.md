# ADR-001: Bitboard Architecture for In-House 4D Spatial Operators

**Status:** Proposed
**Date:** 2026-04-29
**Context:** v1.6 Phase 6 work, surfaced during the 4D move-gen
backend question
**Decision driver:** Steven's call: "we will make spatial operator
here for 4d-oana-chiru but we will use bitboard style, python-chess
style. and python-chess4d-oana-chiru contains unoptimized spatial
operators"

## Context

The §16 search and tournament harness need a 4D move generator. Two
options were considered:

1. **Promote `python-chess4d-oana-chiru` to a runtime dependency.**
   Closed: creates a circular dependency with the consumer side
   (the reason it lives in `[test]` extras today).

2. **Use the v1.6 PR-6 graph-Laplacian eigenbasis oracle
   (`spectral_legality_4d`).** This works for the *empty-board reach
   predicate*, but lacks occupation-aware legality, special moves
   (castling, en passant, promotion), and game-state tracking
   (threefold, 50-move, draw rules). It's a research / cross-check
   tool, not a production move generator.

Both options leave the engine without a fast, complete 4D move
generator. Hence this ADR: build one in-house, in chess-spectral,
using the same bitboard architecture python-chess uses for 2D.

`python-chess4d-oana-chiru` itself is acknowledged to have
**unoptimized spatial operators** (per Steven). We don't want to
import that performance ceiling into our search loop. The upstream
library remains useful as a **cross-validation oracle** at test time
(via `[test]` extras) but is not in the runtime path.

## Decision

Build `chess_spectral.spatial_4d` as a bitboard-based 4D move
generator, mirroring python-chess's design for 2D. Components:

### Core primitive: `Bitboard4D`

A 4096-bit set of squares. Storage options weighed:

| Option | Bytes | Bitwise ops | Iteration speed |
|---|---|---|---|
| `int` (Python's bigint) | varies | native `&` `|` `^` | fast `int.bit_length`, `popcount` via `bin().count('1')` |
| `np.uint64[64]` array | 512 | element-wise via numpy | fast vectorized; awkward iteration |
| `np.uint8[512]` array | 512 | element-wise | slower than uint64 |
| `numpy.bool[4096]` | 4096 | broadcast | wasteful but readable |

**Decision:** Python's native `int` as the canonical representation,
with optional `np.uint64[64]` projection for SIMD-friendly attack
table lookups. Python ints support arbitrary-precision bitwise ops
out of the box, and `int.bit_count()` (3.10+) gives O(1) popcount.
The numpy projection is for hot inner loops only.

```python
class Bitboard4D:
    """4096-bit set of 4D squares. Indexed by sq4(x, y, z, w)."""
    __slots__ = ('_bits',)

    def __init__(self, bits: int = 0):
        self._bits = bits & ((1 << 4096) - 1)

    def __or__(self, other) -> 'Bitboard4D':  ...
    def __and__(self, other) -> 'Bitboard4D':  ...
    def __xor__(self, other) -> 'Bitboard4D':  ...
    def shift_axis(self, axis: int, delta: int) -> 'Bitboard4D':  ...
    def squares(self) -> Iterator[int]:  ...   # bit positions
    def popcount(self) -> int:  ...
    def to_numpy_uint64(self) -> np.ndarray:  ...   # (64,) uint64
```

### Attack-table generation

Static (built once at import time) per-piece per-square attack
bitboards. For the non-sliding pieces (knight, king, pawn-pushes)
this is trivial — compute the move set for each of the 4096 source
squares, store as a flat `Bitboard4D` array.

For the sliding pieces (rook, bishop, queen) we have a choice:

**Option A (magic bitboards):** precompute a hash table per source
square keyed by axis-aligned occupancy. ~10× faster lookup but
1500+ LOC of complexity (magic constants, mask generation, blocker
permutations).

**Option B (on-the-fly ray casting):** per-axis bitboard shift
loops. Simpler (~50 LOC per piece) but 5-10× slower than magic
bitboards. Still ~20-50× faster than python-chess4d-oana-chiru's
Python coordinate enumeration.

**Decision: A.** Build the right thing once. Magic bitboards are the
canonical fast-path approach for sliding-piece move generation; the
2D version (python-chess) uses them, the 4D analogue should too.
"Minimum viable now, optimize later" is a scope trap when the
optimization is the user-facing default — see
[`memory/feedback_no_mvp_as_final_product.md`](#) for the operating
principle. Magic bitboards get built as part of this arc, not
deferred.

The public API for sliding-piece attacks (`attacks_rook_4d(sq,
occupancy)`, `attacks_bishop_4d`, `attacks_queen_4d`) is the same
either way; the internals are magic-table-based from PR-D onward.

### Game state: `Board4D`

Mirror of python-chess's `chess.Board` for 4D:

```python
class Board4D:
    # Per-piece-type bitboards.
    pawns_w: Bitboard4D
    pawns_y: Bitboard4D
    knights: Bitboard4D
    bishops: Bitboard4D
    rooks: Bitboard4D
    queens: Bitboard4D
    kings: Bitboard4D
    # Per-color occupancy.
    occupied_white: Bitboard4D
    occupied_black: Bitboard4D
    # Game state.
    turn: bool                        # True = white
    castling_rights: int              # bitmask
    en_passant: Optional[int]         # square or None
    halfmove_clock: int               # 50-move rule
    fullmove_number: int
    move_history: List[Move4D]
    repetition_hashes: List[int]      # for threefold

    def legal_moves(self) -> Iterator[Move4D]:
        """All legal moves for side-to-move."""
    def push(self, move: Move4D) -> None:
        """Apply move; record undo info."""
    def pop(self) -> Move4D:
        """Reverse the last push."""
    def is_check(self) -> bool: ...
    def is_checkmate(self) -> bool: ...
    def is_stalemate(self) -> bool: ...
    def is_threefold_repetition(self) -> bool: ...
    def is_fifty_moves(self) -> bool: ...
    def is_insufficient_material(self) -> bool: ...
    def is_game_over(self) -> bool: ...
    def fen(self) -> str:
        """FEN4 round-trip via fen_4d.serialize."""
    @classmethod
    def from_fen(cls, fen: str) -> 'Board4D':
        """FEN4 parse via fen_4d.parse."""
```

### Validation

`tests/test_spatial_4d_vs_oana_chiru.py` runs the new generator
against `python-chess4d-oana-chiru` (via the `[test]` extras) on a
curated corpus (~50 positions × ~200 plies):

* **Exact agreement** on `legal_moves()` set membership per ply.
* **Exact agreement** on `is_check()`, `is_checkmate()`,
  `is_stalemate()` predicates.
* **Exact agreement** on draw-rule predicates (threefold, 50-move,
  insufficient material).

Same parity-discipline pattern that gates the 2D / 4D encoder
between Python and C: byte-for-byte agreement on a corpus,
cross-validated against an external reference (here Oana &
Chiru's published rule library).

The graph-Laplacian eigenbasis oracle (`spectral_legality_4d`) is
a third independent check on the empty-board reach predicate
specifically — it exists separately and runs as its own gate.
Three oracles converging on every move is a strong correctness
signal.

## Consequences

**Positive:**
* Engine search has a fast, complete 4D move generator. §16
  tournament harness becomes feasible at depth 4-8.
* No circular dependency on the upstream rule library.
* Cross-validation via `python-chess4d-oana-chiru` (test-time
  only) and `spectral_legality_4d` (research module) catches
  drift between any of the three implementations.
* Bitboard primitives can be reused for any future 4D analysis
  (HUD heat maps, training-data preparation, etc.).

**Negative:**
* Substantial new code: 1500-3000 LOC across ~5 PRs.
* Maintenance burden — chess-spectral now owns the 4D rule
  semantics, not just the spectral encoding. If Oana & Chiru
  publish an updated rule set, we have to track it.
* Risk of subtle disagreement with python-chess4d-oana-chiru in
  edge cases — the cross-validation gate must run on every PR.

**Open questions / deferred:**
* Whether to absorb python-chess4d-oana-chiru entirely later —
  separate decision (already captured in the ROADMAP).
* SIMD acceleration via numpy uint64[64] arrays — only if
  profiling shows the inner loop dominated by single-bitboard ops.
  This is true SIMD on top of an already-fast magic-bitboard
  baseline, not a "minimum-viable-then-optimize" deferral.
* C-side port of the bitboard generator: similar parity-discipline
  pattern as the encoder's C/Python parity gate. Captured for
  v1.7+; not in scope for v1.6.

## Phasing (PR breakdown for v1.6)

1. **PR-A (this ADR)**: design record, no code.
2. **PR-B**: `Bitboard4D` primitive + bitwise ops + axis shifts +
   square iteration + tests.
3. **PR-C**: non-sliding piece attack tables (knight, king, pawn
   pushes) + tests against `python-chess4d-oana-chiru`.
4. **PR-D**: sliding piece attack generators (option B: ray
   casting; rook, bishop, queen) + tests.
5. **PR-E**: pawn captures (W-axis and Y-axis) + en-passant +
   promotion + tests.
6. **PR-F**: `Board4D` game state, legal-move generation
   (filtering pseudo-legal by check), `push`/`pop`, FEN4
   round-trip + tests.
7. **PR-G**: draw rules (threefold, 50-move, insufficient,
   stalemate, checkmate) + tests.
8. **PR-H**: corpus parity gate against
   `python-chess4d-oana-chiru` (50 positions × 200 plies).
9. **PR-I**: 4D search core (was originally planned as PR-7)
   built on `Board4D`. Mirrors the 2D search core.

This is a real investment; it's worth doing right. The §16
tournament needs it.

## References

* `docs/chess-maths/chess-spectral/python/chess_spectral/phase_operators_4d/` —
  the existing 4D phase-operator move generator (slow, modular-
  arithmetic-based; will remain as a third oracle).
* `docs/chess-maths/chess-spectral/python/chess_spectral/spectral_legality_4d.py` —
  graph-Laplacian eigenbasis oracle (PR-6).
* `python-chess` source — reference implementation of the bitboard
  architecture for 2D.
* Oana & Chiru, *AppliedMath* 6(3):48 (2026) — the 4D chess rule
  reference.
