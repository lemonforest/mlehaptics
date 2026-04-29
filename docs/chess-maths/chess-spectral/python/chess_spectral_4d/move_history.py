"""Move-history plumbing for 4D chess game state.

This module is the **chess-spectral 1.4.0** addition that records the
ply-by-ply move history needed for threefold-repetition detection,
50-move-rule detection, and the consumer-facing ``getMoveHistory()``
bridge surface (§17.3 of the research notebook).

The position object produced by :func:`chess_spectral.fen_4d.parse`
captures only **piece placement** — it has no notion of side-to-move,
half-move clock, or castling/EP rights. A *game* needs all of those
to terminate correctly under tournament rules. Rather than retrofit
that state into the position dict (which would break the encoder's
input contract), we keep position-as-snapshot semantics and add this
explicit ``MoveHistory4D`` container alongside it.

A ``GameState4D`` ties the two together: a position snapshot plus a
``MoveHistory4D`` instance. Both ``apply_move`` and the bridge methods
operate on the ``GameState4D`` so all per-ply bookkeeping happens in
one place.

Design constraints:
    * No dependency on numpy or scipy — the history is a pure-Python
      list of plain records, Pyodide-bridge-friendly without
      serialization shims.
    * Position-hashing for threefold detection uses SHA-256 of a
      canonical key (FEN4 placement plus side-to-move byte). This is
      deterministic, collision-resistant in practice, and avoids the
      complexity of a Zobrist table (which would need rebuilding
      whenever castling/EP rights are added in a future minor).
    * The half-move clock follows FIDE Article 9.3: it resets to 0 on
      any pawn move OR any capture, and otherwise increments by 1.
      Threefold and 50-move detection thresholds match python-chess /
      USCF rule-of-thumb defaults (3 occurrences, 100 half-moves).

This module ships with v1.4.0 alongside the FEN4 ``serialize`` and
``apply_move`` (with promotion-piece) additions; together they close
§16.9's five gaps and §17.3's five additional edge cases.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from chess_spectral import fen_4d as _fen_4d


# ─── Type aliases ────────────────────────────────────────────────────

Coord4D = Tuple[int, int, int, int]
"""(x, y, z, w) tuple, each component in [0, 7]."""

PieceValue = _fen_4d.PieceValue
"""Forwarded from chess_spectral.fen_4d for symmetry with the parser."""

Position4D = Dict[int, PieceValue]
"""Mapping of linear square index → piece value (encoder input)."""


# ─── Side-to-move encoding ──────────────────────────────────────────

SIDE_WHITE: int = 0
SIDE_BLACK: int = 1


def _other_side(side: int) -> int:
    """Flip the side-to-move byte. Constant-time, no branch."""
    return SIDE_WHITE if side == SIDE_BLACK else SIDE_BLACK


# ─── Coord ↔ linear-square conversion (mirrors fen_4d) ─────────────

def coord_to_sq(coord: Coord4D) -> int:
    """Pack ``(x, y, z, w)`` to ``((x*8+y)*8+z)*8+w``.

    Inverse of :func:`sq_to_coord`. Accepts a 4-tuple of ints in
    ``[0, 7]``; raises ``ValueError`` on out-of-range components.
    """
    if len(coord) != 4:
        raise ValueError(
            f"coord must be a 4-tuple, got {coord!r} of length {len(coord)}"
        )
    x, y, z, w = coord
    for name, c in (("x", x), ("y", y), ("z", z), ("w", w)):
        if not isinstance(c, int) or c < 0 or c > 7:
            raise ValueError(
                f"coord component {name}={c!r} out of range [0, 7]"
            )
    return ((x * 8 + y) * 8 + z) * 8 + w


def sq_to_coord(sq: int) -> Coord4D:
    """Unpack a linear square index to ``(x, y, z, w)``.

    Inverse of :func:`coord_to_sq`. Raises ``ValueError`` if
    ``sq`` is outside ``[0, 4096)``.
    """
    if not isinstance(sq, int) or sq < 0 or sq >= 4096:
        raise ValueError(f"square index {sq!r} out of range [0, 4096)")
    w = sq % 8
    z = (sq // 8) % 8
    y = (sq // 64) % 8
    x = (sq // 512) % 8
    return (x, y, z, w)


# ─── Move record ────────────────────────────────────────────────────

@dataclass(frozen=True)
class Move4D:
    """One ply-record. Frozen so a list of ``Move4D`` is safely
    sharable across the bridge boundary.

    Attributes
    ----------
    ply
        0-indexed ply number (the half-move count at which this move
        was *played*; the first move of a game has ply=0).
    from_sq
        Origin square as ``(x, y, z, w)``.
    to_sq
        Destination square as ``(x, y, z, w)``.
    piece
        Piece value moved (single-char for non-pawns, ``(color, axis)``
        tuple for pawns).
    promote_to
        Promotion target piece letter for the promoting side (``'Q'``,
        ``'R'``, ``'B'``, or ``'N'`` — color is inferred from the
        moving pawn). ``None`` for non-promotion moves.
    captured_piece
        Piece value captured by this move (single-char or pawn tuple),
        or ``None`` for a non-capture move.
    fen4_after
        FEN4 v1 placement literal of the position **after** the move.
        Stored verbatim so position hashing for threefold detection
        does not have to re-serialize on every check.
    half_move_clock_after
        FIDE Article 9.3 half-move clock value after this ply (0 if
        this move was a pawn move or capture; otherwise previous +1).
    """

    ply: int
    from_sq: Coord4D
    to_sq: Coord4D
    piece: PieceValue
    promote_to: Optional[str]
    captured_piece: Optional[PieceValue]
    fen4_after: str
    half_move_clock_after: int

    def to_dict(self) -> Dict[str, object]:
        """Render this record as a plain dict suitable for
        Pyodide-bridge serialization. Keys mirror the consumer-facing
        ``getMoveHistory()`` schema (§17.3).
        """
        out: Dict[str, object] = {
            "ply": self.ply,
            "from": list(self.from_sq),
            "to": list(self.to_sq),
            "halfMoveClock": self.half_move_clock_after,
        }
        if isinstance(self.piece, tuple):
            color, axis = self.piece
            out["piece"] = color + axis
        else:
            out["piece"] = self.piece
        if self.promote_to is not None:
            out["promoteTo"] = self.promote_to
        if self.captured_piece is not None:
            if isinstance(self.captured_piece, tuple):
                color, axis = self.captured_piece
                out["capturedPiece"] = color + axis
            else:
                out["capturedPiece"] = self.captured_piece
        return out


# ─── History container ──────────────────────────────────────────────

@dataclass
class MoveHistory4D:
    """Append-only ply history plus per-game-state tracking.

    Attributes
    ----------
    moves
        Ordered list of :class:`Move4D` records, oldest first.
    side_to_move
        Side that will play the next move (``SIDE_WHITE`` or
        ``SIDE_BLACK``). Initialized to ``SIDE_WHITE`` per FIDE.
    half_move_clock
        Current FIDE Article 9.3 half-move clock. Reset to 0 on pawn
        moves and captures; incremented otherwise.
    position_counts
        ``{sha256_key → occurrence_count}`` for the position-hash
        table. The starting position is recorded with count=1 when
        :func:`record_initial_position` is called.
    """

    moves: List[Move4D] = field(default_factory=list)
    side_to_move: int = SIDE_WHITE
    half_move_clock: int = 0
    position_counts: Dict[str, int] = field(default_factory=dict)

    def record_initial_position(
        self, pos: Position4D, side_to_move: int = SIDE_WHITE,
    ) -> None:
        """Record the starting position in the repetition table.

        Must be called once before any moves are appended; the starting
        position counts as one occurrence for threefold-repetition
        detection (FIDE Article 9.2).
        """
        if self.moves:
            raise ValueError(
                "record_initial_position must be called before any "
                "moves are appended"
            )
        self.side_to_move = side_to_move
        key = position_hash_key(pos, side_to_move)
        self.position_counts[key] = 1

    def append(
        self,
        *,
        from_sq: Coord4D,
        to_sq: Coord4D,
        piece: PieceValue,
        promote_to: Optional[str],
        captured_piece: Optional[PieceValue],
        fen4_after: str,
        position_after: Position4D,
        is_pawn_move: bool,
        is_capture: bool,
    ) -> Move4D:
        """Append a ply, updating the half-move clock, side-to-move,
        and position-hash table. Returns the recorded :class:`Move4D`.

        Note: callers are responsible for passing both the rendered
        ``fen4_after`` (for the move record) and the live
        ``position_after`` dict (for hashing). Both must describe the
        same post-move state.
        """
        if is_pawn_move or is_capture:
            self.half_move_clock = 0
        else:
            self.half_move_clock += 1

        ply = len(self.moves)
        record = Move4D(
            ply=ply,
            from_sq=from_sq,
            to_sq=to_sq,
            piece=piece,
            promote_to=promote_to,
            captured_piece=captured_piece,
            fen4_after=fen4_after,
            half_move_clock_after=self.half_move_clock,
        )
        self.moves.append(record)

        # Side-to-move flips after each ply.
        self.side_to_move = _other_side(self.side_to_move)

        # Position-repetition tracking is keyed on the position AS SEEN
        # by the side about to move — i.e. with the post-flip side byte.
        key = position_hash_key(position_after, self.side_to_move)
        self.position_counts[key] = self.position_counts.get(key, 0) + 1
        return record

    def repetition_count(self, pos: Position4D) -> int:
        """Number of times ``pos`` (with the current side-to-move) has
        occurred in this history. Returns 0 if the position has never
        appeared, 1 for the position currently on the board (counted
        when it was recorded), 2 or 3+ for repeats.
        """
        key = position_hash_key(pos, self.side_to_move)
        return self.position_counts.get(key, 0)

    def to_list(self) -> List[Dict[str, object]]:
        """Render the full history as a list of plain dicts. Used by
        the ``getMoveHistory()`` bridge method (§17.3)."""
        return [m.to_dict() for m in self.moves]


# ─── Position-hash key ──────────────────────────────────────────────

def position_hash_key(pos: Position4D, side_to_move: int) -> str:
    """Return a deterministic, collision-resistant key for the
    (position, side-to-move) pair.

    The key is the hexadecimal SHA-256 of:

        b"<side>:" + <canonical FEN4>.encode("ascii")

    where the canonical FEN4 is the output of :func:`fen_4d.serialize`
    on ``pos`` (which sorts pieces by ascending square index).
    """
    if side_to_move not in (SIDE_WHITE, SIDE_BLACK):
        raise ValueError(
            f"side_to_move must be SIDE_WHITE (0) or SIDE_BLACK (1), "
            f"got {side_to_move!r}"
        )
    canon = _fen_4d.serialize(pos).encode("ascii")
    side_byte = b"W:" if side_to_move == SIDE_WHITE else b"B:"
    return hashlib.sha256(side_byte + canon).hexdigest()


# ─── GameState4D ────────────────────────────────────────────────────

@dataclass
class GameState4D:
    """Position + history container. The unit on which
    :func:`chess_spectral_4d.bridge.get_draw_status`,
    :func:`chess_spectral_4d.bridge.get_move_history`, and the
    move-application surface operate.

    Attributes
    ----------
    position
        Current position dict (live; mutated by ``apply_move``).
    history
        Per-game move history plus side-to-move and clock state.
    """

    position: Position4D
    history: MoveHistory4D = field(default_factory=MoveHistory4D)

    @classmethod
    def from_fen4(
        cls, fen4: str, side_to_move: int = SIDE_WHITE,
    ) -> "GameState4D":
        """Construct a fresh game from a FEN4 placement literal. The
        side-to-move byte defaults to White (FIDE Article 4.7)."""
        pos = _fen_4d.parse(fen4)
        gs = cls(position=pos)
        gs.history.record_initial_position(pos, side_to_move)
        return gs

    def to_fen4(self) -> str:
        """Serialize the current position to a FEN4 v1 placement
        literal. Inverse of :meth:`from_fen4` at the placement-literal
        level (side-to-move is *not* encoded by FEN4 v1, intentionally
        — Phase 5b keeps that out of the wire format)."""
        return _fen_4d.serialize(self.position)
