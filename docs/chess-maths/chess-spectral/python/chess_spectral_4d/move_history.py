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
from typing import Dict, Iterator, List, Optional, Tuple, Union

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
    # 1.8.0: FEN4 of the position before any moves were appended.
    # Captured at ``record_initial_position`` time so ``GameState4D.pop()``
    # can restore the position when the history empties out (i.e. when
    # the consumer pops the very first move).
    initial_fen4: Optional[str] = None
    initial_side_to_move: int = SIDE_WHITE

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
        self.initial_fen4 = _fen_4d.serialize(pos)
        self.initial_side_to_move = side_to_move
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

    # ─── 1.8.0: short-name aliases (chess4D-OC wishlist 1.3) ────────

    @classmethod
    def from_fen(
        cls, fen4: str, side_to_move: int = SIDE_WHITE,
    ) -> "GameState4D":
        """Alias for :meth:`from_fen4`. Symmetric with python-chess's
        ``Board.from_fen`` and the chess4D-OC visualizer's expected
        consumer surface (1.8.0 wishlist tier 1.3). The slash-tolerant
        FEN4 form (1.7.1+, e.g. ``P/w@``) is accepted on this path.
        """
        return cls.from_fen4(fen4, side_to_move=side_to_move)

    def to_fen(self) -> str:
        """Alias for :meth:`to_fen4`. The serializer always emits the
        canonical no-slash form regardless of how the input was
        parsed; round-tripping a slash-form FEN4 collapses it to the
        canonical form on output (1.8.0 wishlist tier 1.3)."""
        return self.to_fen4()

    # ─── 1.8.0: push / pop (chess4D-OC wishlist 1.1) ────────────────
    #
    # ``push`` is a thin wrapper around :func:`apply_move` that accepts
    # either a :class:`Move4D` (we read its ``from_sq`` / ``to_sq`` /
    # ``promote_to``) or a 2-tuple of coordinates. Returns the recorded
    # ``Move4D`` so callers can grab capture / promotion metadata.
    #
    # ``pop`` rewinds the last ply by re-parsing the FEN4 the move
    # records as ``fen4_after`` of the *previous* move (or the initial
    # FEN4 if this was the first ply). The recorded ``Move4D`` is
    # returned for callers that need to undo / re-encode.

    def push(
        self,
        move: "Union[Move4D, Tuple[Coord4D, Coord4D], Tuple[Coord4D, Coord4D, Optional[str]]]",
        *,
        promote_to: Optional[str] = None,
    ) -> Move4D:
        """Apply a move, mutating the state in place. Returns the
        recorded :class:`Move4D`.

        The 2- or 3-tuple form lets the chess4D-OC worker do
        ``state.push((from_sq, to_sq))`` without constructing a Move4D
        on the JS side; promote_to defaults to ``'Q'`` (matching the
        v1.3.x silent auto-queen behaviour).

        Raises ``ValueError`` for any of the same conditions as
        :func:`apply_move` (no piece on origin, bad coord, bad
        promote_to, etc.). The chess4D-OC tracker references this as
        wishlist tier 1.1.
        """
        # Local import avoids a circular dependency with apply_move.
        from chess_spectral_4d.apply_move import apply_move

        if isinstance(move, Move4D):
            from_sq = move.from_sq
            to_sq = move.to_sq
            recorded_promote = move.promote_to or promote_to or "Q"
        elif isinstance(move, tuple) and 2 <= len(move) <= 3:
            from_sq = move[0]
            to_sq = move[1]
            tup_promote = move[2] if len(move) == 3 else None
            recorded_promote = tup_promote or promote_to or "Q"
        else:
            raise TypeError(
                "push: move must be a Move4D or a "
                "((fx,fy,fz,fw), (tx,ty,tz,tw)[, promote_to]) tuple; "
                f"got {type(move).__name__}: {move!r}"
            )
        return apply_move(self, from_sq, to_sq, promote_to=recorded_promote)

    def pop(self) -> Move4D:
        """Undo the last move; returns the popped :class:`Move4D` so
        callers can recover capture / promotion metadata.

        Restores ``self.position`` to the snapshot before the popped
        move, decrements the threefold-repetition count for the
        position we just left, restores the half-move clock, and
        flips ``side_to_move`` back. The popped ``Move4D`` is removed
        from ``self.history.moves``.

        Raises
        ------
        IndexError
            If the history is empty (no prior move to undo). The
            chess4D-OC consumer should treat this as the bottom of
            its undo stack, parallel to ``chess.Board.pop()``'s
            behaviour at game start.
        """
        if not self.history.moves:
            raise IndexError(
                "pop from empty move history (no prior move to undo)"
            )

        last_move = self.history.moves[-1]

        # 1. Decrement repetition counter for the current (post-last-move)
        #    position. The key is keyed on the *side-to-move* AT the
        #    state we're leaving, which is the post-flip side stored in
        #    self.history.side_to_move right now.
        leave_key = position_hash_key(
            self.position, self.history.side_to_move,
        )
        cur = self.history.position_counts.get(leave_key, 0)
        if cur <= 1:
            self.history.position_counts.pop(leave_key, None)
        else:
            self.history.position_counts[leave_key] = cur - 1

        # 2. Pop the move from the history list.
        self.history.moves.pop()

        # 3. Restore the prior position. If the popped move was the
        #    first ply, restore from the recorded initial FEN4. If the
        #    initial_fen4 is missing (old MoveHistory4D constructed
        #    pre-1.8.0 without record_initial_position calling the
        #    serializer), fall back to re-deriving from a fresh empty
        #    state — the consumer can always re-load via from_fen4.
        if self.history.moves:
            prev = self.history.moves[-1]
            self.position = _fen_4d.parse(prev.fen4_after)
            self.history.half_move_clock = prev.half_move_clock_after
        else:
            init_fen = self.history.initial_fen4
            if init_fen is None:
                # Should be unreachable for any GameState4D constructed
                # via the public API (from_fen4 always records the
                # initial FEN4). Belt-and-suspenders only.
                raise RuntimeError(
                    "GameState4D.pop: history has no moves and "
                    "no recorded initial_fen4; this state was "
                    "not constructed via from_fen4 / from_fen."
                )
            self.position = _fen_4d.parse(init_fen)
            self.history.half_move_clock = 0

        # 4. Flip side-to-move back. The popped move was played by the
        #    side OPPOSITE the current self.history.side_to_move; after
        #    pop, that opposite side is once again to move.
        self.history.side_to_move = _other_side(self.history.side_to_move)

        return last_move

    # ─── 1.8.0: piece accessors (chess4D-OC wishlist 1.2) ───────────

    @property
    def board(self) -> "_BoardView4D":
        """A read-only view of the current piece placement, exposing
        the ``occupant`` / ``pieces_of`` accessors the chess4D-OC
        worker uses (wishlist tier 1.2).

        The view is a thin facade over ``self.position`` — it does
        not copy or freeze the dict, so changes to ``self.position``
        (e.g. via :meth:`push` / :meth:`pop`) are reflected
        immediately. Construct a new view per access; the
        construction cost is negligible.
        """
        return _BoardView4D(self)

    def occupant(
        self, sq: "Union[int, Coord4D]",
    ) -> Optional["PieceValue"]:
        """Piece value at ``sq`` (linear index *or* (x,y,z,w) coord),
        or ``None`` if empty. Wishlist tier 1.2."""
        if isinstance(sq, tuple):
            sq = coord_to_sq(sq)
        return self.position.get(sq)

    def pieces_of(
        self, side: int,
    ) -> "List[Tuple[Coord4D, PieceValue]]":
        """Return all (coord, piece-value) pairs for ``side``
        (``SIDE_WHITE`` or ``SIDE_BLACK``). The list is materialized
        eagerly so the consumer can iterate without caring about
        concurrent mutation. Wishlist tier 1.2."""
        if side not in (SIDE_WHITE, SIDE_BLACK):
            raise ValueError(
                f"side must be SIDE_WHITE (0) or SIDE_BLACK (1), got {side!r}"
            )
        out: List[Tuple[Coord4D, PieceValue]] = []
        for sq, value in self.position.items():
            # Pawn values are (color, axis) tuples; non-pawn values are
            # single-char strings. Color is uppercase = white, lowercase
            # = black.
            if isinstance(value, tuple):
                color = value[0]
            else:
                color = value
            piece_color = SIDE_WHITE if color.isupper() else SIDE_BLACK
            if piece_color == side:
                out.append((sq_to_coord(sq), value))
        return out

    # ─── 1.8.0: encoder-shaped iter (chess4D-OC wishlist 1.6) ───────

    def iter_pieces(self) -> "Iterator[Tuple[int, PieceValue]]":
        """Yield ``(sq_idx, piece_value)`` pairs in the format
        ``chess_spectral.encoder_4d.encode_4d`` consumes — the
        chess4D-OC worker's ``_state_to_pos4`` collapses to
        ``dict(state.iter_pieces())``. Wishlist tier 1.6.

        The iteration order matches the underlying ``self.position``
        dict's order (insertion order on CPython 3.7+); callers that
        need a deterministic ordering can sort by ``sq_idx``.
        """
        for sq, value in self.position.items():
            yield sq, value

    @property
    def side_to_move(self) -> int:
        """Side that will play the next move (``SIDE_WHITE`` or
        ``SIDE_BLACK``). Forwarded from ``self.history.side_to_move``
        for the chess4D-OC ``state.side_to_move`` consumer surface."""
        return self.history.side_to_move

    # ─── 1.8.0: check / mate / stalemate predicates (wishlist 3.2) ──
    #
    # Implemented via a transient :class:`chess_spectral.spatial_4d.
    # Board4D` constructed from the live ``self.position``. The
    # Board4D is GC-eligible right after the call returns; we do not
    # cache it on ``self`` because legal-move generation depends on
    # board state freshness and we'd rather pay a small construction
    # cost than gate cache invalidation through every ``push`` /
    # ``pop`` / ``apply_move`` call site.

    def _to_board(self) -> "object":
        """Return a fresh Board4D mirroring this state's position +
        side-to-move. Used by the check / mate / stalemate predicates;
        not exposed publicly because the engine-level Board4D
        consumes its own private API surface (legal_moves, push, pop)
        that diverges from this module's GameState4D conventions."""
        from chess_spectral.spatial_4d import Board4D  # noqa: WPS433
        return Board4D.from_position_dict(
            self.position, turn=(self.history.side_to_move == SIDE_WHITE),
        )

    def is_check(self) -> bool:
        """True iff the side-to-move has any king attacked. Mirrors
        :meth:`chess_spectral.spatial_4d.Board4D.is_check`. Wishlist
        tier 3.2."""
        return self._to_board().is_check()

    def is_checkmate(self) -> bool:
        """True iff the side-to-move is in check AND has no legal
        move out of it. Wishlist tier 3.2.

        Cost: O(legal-move generation) — at the dense 28-king start
        this is ~2s after 1.7.0's native bitboard + algorithmic
        fast-path. Cache the result if calling repeatedly on the
        same state.
        """
        board = self._to_board()
        if not board.is_check():
            return False
        # No need to fully materialize the move list — the first
        # legal move is enough to falsify checkmate. ``next(iter, None)``
        # bails early.
        return next(iter(board.legal_moves()), None) is None

    def is_stalemate(self) -> bool:
        """True iff the side-to-move is NOT in check AND has no legal
        move (so the only "options" would all be illegal — typically
        because every move leaves a king attacked). Wishlist tier
        3.2. Cost is the same as :meth:`is_checkmate`."""
        board = self._to_board()
        if board.is_check():
            return False
        return next(iter(board.legal_moves()), None) is None


# ─── 1.8.0: lightweight Board view (wishlist tier 1.2) ───────────────


class _BoardView4D:
    """Read-only view over a :class:`GameState4D`'s current
    placement, exposing the wishlist's tier 1.2 access surface
    (``board.occupant(sq)`` and ``board.pieces_of(color)``).

    Implemented as a thin proxy over the underlying
    ``GameState4D.position`` dict so iteration / lookup don't copy.
    The chess4D-OC worker only reads from this view — there is
    intentionally no setter; mutation of the board goes through
    :meth:`GameState4D.push` / :meth:`GameState4D.pop`.
    """

    __slots__ = ("_state",)

    def __init__(self, state: "GameState4D") -> None:
        self._state = state

    def occupant(
        self, sq: "Union[int, Coord4D]",
    ) -> Optional["PieceValue"]:
        """Piece value at ``sq`` (linear index *or* (x,y,z,w) coord),
        or ``None`` if empty."""
        return self._state.occupant(sq)

    def pieces_of(
        self, side: int,
    ) -> "List[Tuple[Coord4D, PieceValue]]":
        """All ``(coord, piece-value)`` pairs for ``side``."""
        return self._state.pieces_of(side)

    def __contains__(self, sq: "Union[int, Coord4D]") -> bool:
        return self.occupant(sq) is not None

    def __len__(self) -> int:
        """Number of occupied squares."""
        return len(self._state.position)
