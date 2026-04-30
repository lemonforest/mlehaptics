"""Move4D dataclass for spatial_4d.

Represents a single move in 4D chess. Mirrors python-chess's
``chess.Move`` with extensions for the 4D-specific move types
defined in Oana-Chiru §3-4:

  * Standard moves (knight / king / slider single-target).
  * Pawn single push.
  * **Pawn double push** -- from "rank 2" plane (w=1 or y=1 for
    white, w=6 or y=6 for black).
  * Pawn diagonal capture.
  * **En passant capture** -- diagonal capture into the square the
    opponent's just-double-pushed pawn skipped over.
  * **Promotion** -- pawn reaching the opposite-end plane (w=7
    for white-Pw, w=0 for black-pw, y=7 for white-Py, y=0 for
    black-py) chooses a target piece type.
  * Castling -- not in Oana-Chiru ruleset; raised on attempt.

A ``Move4D`` is **immutable** (``__slots__`` + frozen-by-convention
fields). Equality + hashing work, so moves are usable as dict keys
in transposition tables.
"""
from __future__ import annotations

from typing import Optional


# Piece characters -- single uppercase letter for white, lowercase for
# black. Pawns use 'P'/'p' here (no axis tag); the axis is implicit
# from the source square's pawn-type bitboard in Board4D.
PIECE_CHARS = frozenset({
    'P', 'p', 'N', 'n', 'B', 'b', 'R', 'r', 'Q', 'q', 'K', 'k',
})

# Promotion targets (no king or pawn).
PROMOTION_TARGETS = frozenset({'N', 'B', 'R', 'Q'})


class Move4D:
    """Single 4D chess move.

    Fields
    ------
    from_sq : int
        Source square index in [0, 4096).
    to_sq : int
        Destination square index in [0, 4096).
    promotion : Optional[str]
        Target piece type for pawn promotion, one of {'N', 'B', 'R',
        'Q'} (always uppercase regardless of moving color; the side
        is determined by the source pawn). None for non-promotion
        moves.
    is_double_push : bool
        True iff this is a pawn's two-square initial push. Used by
        Board4D to set the en-passant target square for the next
        ply.
    is_ep_capture : bool
        True iff this is an en-passant capture. The pawn captured
        is at a square different from to_sq (specifically, the
        square that was the previous ply's en-passant target's
        "destination if ep is taken" -- see Board4D.push for the
        exact removal).
    """

    __slots__ = ("from_sq", "to_sq", "promotion",
                 "is_double_push", "is_ep_capture")

    from_sq: int
    to_sq: int
    promotion: Optional[str]
    is_double_push: bool
    is_ep_capture: bool

    def __init__(self,
                 from_sq: int,
                 to_sq: int,
                 *,
                 promotion: Optional[str] = None,
                 is_double_push: bool = False,
                 is_ep_capture: bool = False):
        # Frozen via __slots__ + object.__setattr__ pattern.
        if promotion is not None and promotion not in PROMOTION_TARGETS:
            raise ValueError(
                f"promotion must be one of {sorted(PROMOTION_TARGETS)} "
                f"or None; got {promotion!r}"
            )
        object.__setattr__(self, "from_sq", from_sq)
        object.__setattr__(self, "to_sq", to_sq)
        object.__setattr__(self, "promotion", promotion)
        object.__setattr__(self, "is_double_push", is_double_push)
        object.__setattr__(self, "is_ep_capture", is_ep_capture)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move4D):
            return NotImplemented
        return (self.from_sq == other.from_sq
                and self.to_sq == other.to_sq
                and self.promotion == other.promotion
                and self.is_double_push == other.is_double_push
                and self.is_ep_capture == other.is_ep_capture)

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        return result if result is NotImplemented else not result

    def __hash__(self) -> int:
        return hash((self.from_sq, self.to_sq, self.promotion,
                     self.is_double_push, self.is_ep_capture))

    def __repr__(self) -> str:
        parts = [f"from_sq={self.from_sq}", f"to_sq={self.to_sq}"]
        if self.promotion is not None:
            parts.append(f"promotion={self.promotion!r}")
        if self.is_double_push:
            parts.append("is_double_push=True")
        if self.is_ep_capture:
            parts.append("is_ep_capture=True")
        return f"Move4D({', '.join(parts)})"


__all__ = ["Move4D", "PIECE_CHARS", "PROMOTION_TARGETS"]
