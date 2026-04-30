"""Board4D -- 4D chess game state with bitboard storage.

Mirror of python-chess's :class:`chess.Board` for 4D chess on the
8^4 lattice. Stores per-(piece-type, color) bitboards, the side to
move, en-passant target square, halfmove clock, fullmove number,
and a move history for ``push`` / ``pop``. Generates legal moves
via the spatial_4d attack tables (PR-7-B/C/D/E).

Storage
-------
14 piece-type bitboards (4D pawns are axis-typed: Pw/Py per Oana-Chiru
Definition 11):

  white: pawn_w, pawn_y, knight, bishop, rook, queen, king
  black: pawn_w, pawn_y, knight, bishop, rook, queen, king

Plus game-state scalars: turn, ep_square, halfmove_clock,
fullmove_number, and a move_history list of UndoInfo for pop()
to restore previous state.

Castling
--------
4D Oana-Chiru chess does not include castling in the ruleset
(per the published rules; revisit if a future ruleset extension
adds it). The Board4D class does NOT generate or accept castle
moves; ``castling_rights`` field is reserved for forward
compatibility but always zero.

Move types covered in ``legal_moves()``
---------------------------------------
* Knight, king (single-target jumps).
* Rook, bishop, queen (slider walks via ray-cast).
* Pawn single push (one square forward along axis).
* Pawn double push (from "rank 2" plane: w=1 / y=1 for white,
  w=6 / y=6 for black).
* Pawn diagonal capture (forward step + ±1 on one of the other
  three axes).
* En passant capture (immediately following an opponent's double
  push; captures the pushed pawn even though not at to_sq).
* Pawn promotion (when reaching the opposite-end plane along the
  pawn's axis: w=7 / y=7 for white, w=0 / y=0 for black). All four
  target piece types (N, B, R, Q) generated as separate Move4D
  instances.

Out of scope for this module
----------------------------
* **Draw rules** -- threefold repetition, 50-move rule, insufficient
  material, stalemate predicate, mate predicate. These ship in
  :mod:`chess_spectral.spatial_4d.draws` (PR-7-G); Board4D exposes
  the data they need (move history, halfmove clock, position hash)
  but doesn't compute them itself.

Public API summary
------------------
  Board4D(...)
  Board4D.empty() / .from_position_dict(d) / .from_fen(s)
  bb.legal_moves() -> Iterator[Move4D]
  bb.push(move) -> None         (with undo info pushed to history)
  bb.pop() -> Move4D            (restores prior state)
  bb.is_check() -> bool
  bb.piece_at(sq) -> Optional[str]
  bb.set_piece(sq, piece) -> None  (helper for fen-load / tests)
  bb.turn, bb.ep_square, bb.halfmove_clock, bb.fullmove_number
  bb.position_hash() -> int     (Zobrist-style hash for tt / repetition)
  bb.fen() -> str               (FEN4 v1 placement; game-state suffix
                                  is captured in Board4D fields, not
                                  yet round-tripped through fen_4d v1)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

from .. import tables_4d as _t4
from .. import fen_4d as _fen4
from .bitboard import Bitboard4D, BOARD_SIDE, N_SQUARES
from .move import Move4D
from .attacks_nonsliding import (
    KNIGHT_ATTACKS_4D, KING_ATTACKS_4D,
)
from .attacks_sliding import (
    attacks_rook_4d, attacks_bishop_4d, attacks_queen_4d,
)
from .attacks_pawn import (
    PAWN_PUSH_W_WHITE, PAWN_PUSH_W_BLACK,
    PAWN_PUSH_Y_WHITE, PAWN_PUSH_Y_BLACK,
    PAWN_ATTACKS_W_WHITE, PAWN_ATTACKS_W_BLACK,
    PAWN_ATTACKS_Y_WHITE, PAWN_ATTACKS_Y_BLACK,
)


# Piece-bitboard slots: (color, piece_kind). 7 kinds * 2 colors = 14.
# kind ∈ {'pawn_w', 'pawn_y', 'knight', 'bishop', 'rook', 'queen', 'king'}.
_PIECE_KINDS = (
    'pawn_w', 'pawn_y', 'knight', 'bishop', 'rook', 'queen', 'king',
)


def _piece_char(color: bool, kind: str) -> str:
    """Return the canonical piece char for (color, kind).

    White is uppercase, black is lowercase. Pawns use 'P'/'p' --
    the axis is implicit from the bitboard slot.
    """
    base = {
        'pawn_w': 'P', 'pawn_y': 'P',
        'knight': 'N', 'bishop': 'B',
        'rook': 'R', 'queen': 'Q', 'king': 'K',
    }[kind]
    return base if color else base.lower()


@dataclass
class UndoInfo:
    """State to restore on pop()."""
    move: Move4D
    moving_kind: str
    captured_kind: Optional[str]
    captured_color: Optional[bool]
    captured_sq: Optional[int]
    prev_ep_square: Optional[int]
    prev_halfmove_clock: int
    prev_fullmove_number: int


class Board4D:
    """4D chess board with bitboard storage."""

    __slots__ = (
        # Per-piece bitboards (14 slots).
        '_white_pawn_w', '_white_pawn_y', '_white_knight',
        '_white_bishop', '_white_rook', '_white_queen', '_white_king',
        '_black_pawn_w', '_black_pawn_y', '_black_knight',
        '_black_bishop', '_black_rook', '_black_queen', '_black_king',
        # Game state.
        '_turn', '_ep_square',
        '_halfmove_clock', '_fullmove_number',
        '_history',
    )

    # ---- Construction ---------------------------------------------

    def __init__(self):
        self._white_pawn_w = Bitboard4D.empty()
        self._white_pawn_y = Bitboard4D.empty()
        self._white_knight = Bitboard4D.empty()
        self._white_bishop = Bitboard4D.empty()
        self._white_rook = Bitboard4D.empty()
        self._white_queen = Bitboard4D.empty()
        self._white_king = Bitboard4D.empty()
        self._black_pawn_w = Bitboard4D.empty()
        self._black_pawn_y = Bitboard4D.empty()
        self._black_knight = Bitboard4D.empty()
        self._black_bishop = Bitboard4D.empty()
        self._black_rook = Bitboard4D.empty()
        self._black_queen = Bitboard4D.empty()
        self._black_king = Bitboard4D.empty()
        self._turn = True   # White to move.
        self._ep_square: Optional[int] = None
        self._halfmove_clock = 0
        self._fullmove_number = 1
        self._history: List[UndoInfo] = []

    @classmethod
    def empty(cls) -> 'Board4D':
        """Empty board, white to move."""
        return cls()

    @classmethod
    def from_position_dict(cls, position: Dict[int, object],
                           *,
                           turn: bool = True,
                           ep_square: Optional[int] = None,
                           halfmove_clock: int = 0,
                           fullmove_number: int = 1) -> 'Board4D':
        """Construct from a {sq: piece_value} dict (the schema
        :func:`chess_spectral.fen_4d.parse` returns)."""
        b = cls()
        b._turn = turn
        b._ep_square = ep_square
        b._halfmove_clock = halfmove_clock
        b._fullmove_number = fullmove_number
        for sq, value in position.items():
            b.set_piece(sq, _normalize_piece_value(value))
        return b

    @classmethod
    def from_fen(cls, fen: str) -> 'Board4D':
        """Parse a FEN4 v1 placement literal. Game-state suffix is
        not yet defined in fen_4d v1; defaults are used (white to
        move, no en passant, halfmove=0, fullmove=1).

        FEN4 v1 piece values: bare 'P' / 'p' are deprecated; explicit
        ('P', 'w') / ('P', 'y') tuples are preferred."""
        position = _fen4.parse(fen)
        return cls.from_position_dict(position)

    # ---- Piece accessors ----------------------------------------

    def piece_at(self, sq: int) -> Optional[str]:
        """Return the piece char at sq, or None if empty.

        Pawns return 'P' / 'p' (the axis is queryable via
        :meth:`pawn_axis_at`).
        """
        if not 0 <= sq < N_SQUARES:
            raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
        for color in (True, False):
            for kind in _PIECE_KINDS:
                bb = self._get_bitboard(color, kind)
                if sq in bb:
                    return _piece_char(color, kind)
        return None

    def pawn_axis_at(self, sq: int) -> Optional[str]:
        """If a pawn is at sq, return 'w' or 'y'; else None."""
        if sq in self._white_pawn_w or sq in self._black_pawn_w:
            return 'w'
        if sq in self._white_pawn_y or sq in self._black_pawn_y:
            return 'y'
        return None

    def color_at(self, sq: int) -> Optional[bool]:
        """Return True (white), False (black), or None if empty."""
        if sq in self.white_occupancy():
            return True
        if sq in self.black_occupancy():
            return False
        return None

    def set_piece(self, sq: int,
                  piece_value: object) -> None:
        """Set the piece at sq. piece_value is either a single char
        (non-pawn) or a tuple ('P'/'p', axis) for axis-typed pawns.

        Raises ValueError if sq is occupied (no implicit overwrite;
        clear first via ``set_piece(sq, None)`` if you need to
        replace).
        """
        if not 0 <= sq < N_SQUARES:
            raise ValueError(f"sq {sq} out of range [0, {N_SQUARES})")
        if piece_value is None:
            # Clear the square across all piece slots.
            for color in (True, False):
                for kind in _PIECE_KINDS:
                    bb = self._get_bitboard(color, kind)
                    if sq in bb:
                        self._set_bitboard(color, kind, bb.clear_square(sq))
            return
        if self.piece_at(sq) is not None:
            raise ValueError(
                f"square {sq} already occupied by "
                f"{self.piece_at(sq)!r}; clear first"
            )
        color, kind = _decode_piece_value(piece_value)
        bb = self._get_bitboard(color, kind)
        self._set_bitboard(color, kind, bb.set_square(sq))

    def _get_bitboard(self, color: bool, kind: str) -> Bitboard4D:
        attr = f"_{'white' if color else 'black'}_{kind}"
        return getattr(self, attr)

    def _set_bitboard(self, color: bool, kind: str,
                      bb: Bitboard4D) -> None:
        attr = f"_{'white' if color else 'black'}_{kind}"
        setattr(self, attr, bb)

    # ---- Aggregate occupancies (computed) ---------------------

    def white_occupancy(self) -> Bitboard4D:
        return (self._white_pawn_w | self._white_pawn_y
                | self._white_knight | self._white_bishop
                | self._white_rook | self._white_queen
                | self._white_king)

    def black_occupancy(self) -> Bitboard4D:
        return (self._black_pawn_w | self._black_pawn_y
                | self._black_knight | self._black_bishop
                | self._black_rook | self._black_queen
                | self._black_king)

    def occupancy(self) -> Bitboard4D:
        return self.white_occupancy() | self.black_occupancy()

    def own_occupancy(self) -> Bitboard4D:
        """Squares occupied by the side to move."""
        return (self.white_occupancy() if self._turn
                else self.black_occupancy())

    def opponent_occupancy(self) -> Bitboard4D:
        return (self.black_occupancy() if self._turn
                else self.white_occupancy())

    # ---- Game state accessors --------------------------------

    @property
    def turn(self) -> bool:
        return self._turn

    @property
    def ep_square(self) -> Optional[int]:
        return self._ep_square

    @property
    def halfmove_clock(self) -> int:
        return self._halfmove_clock

    @property
    def fullmove_number(self) -> int:
        return self._fullmove_number

    @property
    def move_history(self) -> Tuple[Move4D, ...]:
        return tuple(u.move for u in self._history)

    # ---- Move generation -----------------------------------

    def legal_moves(self) -> Iterator[Move4D]:
        """Yield all legal moves for the side to move.

        Generates pseudo-legal moves and filters by check (pushes
        each onto the board, checks if our king is now attacked,
        pops). For long search loops this is the right interface
        (matches python-chess); for performance-critical inner
        loops, callers may prefer to call pseudo_legal_moves() and
        filter in batch.
        """
        for move in self.pseudo_legal_moves():
            self.push(move)
            try:
                # After push, turn is now opponent's; "is_check"
                # asks "is OUR king attacked", but our king is the
                # one that just moved. We need to check whether
                # the previously-moved side's king is in check.
                # Equivalent: is the opponent (now-to-move) king
                # NOT what we want; we want OUR (just-moved) king.
                if not self._is_attacked(self._our_king_sq_pre_flip(),
                                          attacker_color=self._turn):
                    yield move
            finally:
                self.pop()

    def _our_king_sq_pre_flip(self) -> int:
        """Return the square of the king that just moved (after
        a push, that's the !turn side's king). Helper for the
        check-filter in legal_moves()."""
        # After push, _turn is the now-to-move side. The king that
        # just moved is the OPPOSITE side's king.
        moved_side = not self._turn
        king_bb = (self._white_king if moved_side
                   else self._black_king)
        squares = king_bb.to_squares()
        if not squares:
            # No king on board (shouldn't happen in a real game).
            return -1
        return squares[0]

    def pseudo_legal_moves(self) -> Iterator[Move4D]:
        """Yield pseudo-legal moves -- correct piece-movement +
        capture rules but NOT filtered by self-check. Faster than
        legal_moves() when the caller already knows the position
        isn't in check (or doesn't care)."""
        own = self.own_occupancy()
        opp = self.opponent_occupancy()

        # Knights.
        knights = (self._white_knight if self._turn
                   else self._black_knight)
        for from_sq in knights.squares():
            attacks = KNIGHT_ATTACKS_4D[from_sq] - own
            for to_sq in attacks.squares():
                yield Move4D(from_sq, to_sq)

        # Kings.
        kings = (self._white_king if self._turn
                 else self._black_king)
        for from_sq in kings.squares():
            attacks = KING_ATTACKS_4D[from_sq] - own
            for to_sq in attacks.squares():
                yield Move4D(from_sq, to_sq)

        # Rooks, bishops, queens. occupancy needed for ray-cast.
        all_occ = own | opp
        for kind, gen in (
            ('rook', attacks_rook_4d),
            ('bishop', attacks_bishop_4d),
            ('queen', attacks_queen_4d),
        ):
            bb = self._get_bitboard(self._turn, kind)
            for from_sq in bb.squares():
                attacks = gen(from_sq, all_occ) - own
                for to_sq in attacks.squares():
                    yield Move4D(from_sq, to_sq)

        # Pawns: pushes + double-pushes + captures + EP + promotion.
        yield from self._pseudo_legal_pawn_moves(own, opp)

    def _pseudo_legal_pawn_moves(self,
                                  own: Bitboard4D,
                                  opp: Bitboard4D) -> Iterator[Move4D]:
        all_occ = own | opp
        for axis in ('w', 'y'):
            kind = f'pawn_{axis}'
            pawns = self._get_bitboard(self._turn, kind)
            push_table = (PAWN_PUSH_W_WHITE if (axis == 'w' and self._turn)
                          else PAWN_PUSH_W_BLACK if axis == 'w'
                          else PAWN_PUSH_Y_WHITE if self._turn
                          else PAWN_PUSH_Y_BLACK)
            attack_table = (PAWN_ATTACKS_W_WHITE if (axis == 'w' and self._turn)
                            else PAWN_ATTACKS_W_BLACK if axis == 'w'
                            else PAWN_ATTACKS_Y_WHITE if self._turn
                            else PAWN_ATTACKS_Y_BLACK)
            # Double-push: starting plane and target +2 plane.
            # White: w=1 (Pw) or y=1 (Py); pushes to w=3 / y=3.
            # Black: w=6 / y=6 -> w=4 / y=4.
            start_plane = (1 if self._turn else 6)
            mid_plane = (2 if self._turn else 5)
            end_plane = (3 if self._turn else 4)
            promo_plane = (7 if self._turn else 0)
            axis_idx = {'w': 3, 'y': 1}[axis]

            for from_sq in pawns.squares():
                from_coord = _t4.rc4(from_sq)
                # Single push.
                push_target = push_table[from_sq]
                push_target_blocked = (push_target & all_occ)
                if push_target.popcount() == 1 and push_target_blocked.is_empty():
                    to_sq = next(iter(push_target.squares()))
                    to_coord = _t4.rc4(to_sq)
                    if to_coord[axis_idx] == promo_plane:
                        # Promotion -- emit one move per target type.
                        for promo in ('Q', 'R', 'B', 'N'):
                            yield Move4D(from_sq, to_sq, promotion=promo)
                    else:
                        yield Move4D(from_sq, to_sq)
                    # Double push (only from starting plane, mid square empty).
                    if from_coord[axis_idx] == start_plane:
                        # The intermediate square (mid_plane) must
                        # equal push_target's square. For double
                        # push, we step further to end_plane.
                        end_coord = list(from_coord)
                        end_coord[axis_idx] = end_plane
                        end_sq = _t4.sq4(*end_coord)
                        if (end_sq not in all_occ
                                and to_sq not in all_occ):
                            # Both intermediate (single-push target)
                            # AND end_sq must be empty.
                            yield Move4D(from_sq, end_sq, is_double_push=True)

                # Diagonal captures (incl. promotions).
                cap_targets = attack_table[from_sq] & opp
                for to_sq in cap_targets.squares():
                    to_coord = _t4.rc4(to_sq)
                    if to_coord[axis_idx] == promo_plane:
                        for promo in ('Q', 'R', 'B', 'N'):
                            yield Move4D(from_sq, to_sq, promotion=promo)
                    else:
                        yield Move4D(from_sq, to_sq)

                # En passant.
                if self._ep_square is not None:
                    if self._ep_square in attack_table[from_sq]:
                        yield Move4D(from_sq, self._ep_square,
                                      is_ep_capture=True)

    # ---- Push / pop ---------------------------------------

    def push(self, move: Move4D) -> None:
        """Apply move; record undo info for pop()."""
        from_sq = move.from_sq
        to_sq = move.to_sq

        # Identify the moving piece.
        moving_kind = self._kind_at(self._turn, from_sq)
        if moving_kind is None:
            raise ValueError(
                f"no own piece at from_sq {from_sq}"
            )

        # Identify any captured piece.
        captured_kind: Optional[str] = None
        captured_color: Optional[bool] = None
        captured_sq: Optional[int] = None

        if move.is_ep_capture:
            # Captured pawn is at the en-passant capture-victim square,
            # which is from the side of the move source on the same
            # axis as the EP target. The pushed-pawn's axis is determined
            # by which axis its source was at the start_plane / end_plane
            # straddle. The simpler formulation: ep_square is the square
            # the pushed pawn skipped over; the actual pushed pawn is
            # one further forward (from the opponent's perspective).
            axis_idx = self._ep_axis_idx(to_sq)
            ep_coord = list(_t4.rc4(to_sq))
            # Direction of pushed pawn = opposite of our move direction.
            # If we're white (turn=True), opponent's pushed pawn went +axis,
            # so the captured pawn is at to_sq with axis += 1.
            # Wait, the captured pawn is at the square immediately past
            # to_sq in the OPPONENT's forward direction. Opponent forward
            # = -axis if we're white (because opp is black). So captured
            # pawn coord = to_sq with axis -= 1 if we're white.
            forward_sign = 1 if self._turn else -1
            ep_coord[axis_idx] -= forward_sign  # opp's pushed pawn at this
            captured_sq = _t4.sq4(*ep_coord)
            captured_kind = self._kind_at(not self._turn, captured_sq)
            captured_color = not self._turn
        else:
            # Normal capture: piece at to_sq, opponent color.
            opp_kind = self._kind_at(not self._turn, to_sq)
            if opp_kind is not None:
                captured_kind = opp_kind
                captured_color = not self._turn
                captured_sq = to_sq

        # Save undo info BEFORE mutating state.
        undo = UndoInfo(
            move=move,
            moving_kind=moving_kind,
            captured_kind=captured_kind,
            captured_color=captured_color,
            captured_sq=captured_sq,
            prev_ep_square=self._ep_square,
            prev_halfmove_clock=self._halfmove_clock,
            prev_fullmove_number=self._fullmove_number,
        )

        # Clear from_sq.
        bb = self._get_bitboard(self._turn, moving_kind)
        self._set_bitboard(self._turn, moving_kind, bb.clear_square(from_sq))

        # Clear captured piece (if any).
        if captured_kind is not None:
            cap_bb = self._get_bitboard(captured_color, captured_kind)
            self._set_bitboard(captured_color, captured_kind,
                                cap_bb.clear_square(captured_sq))

        # Set to_sq -- handle promotion.
        if move.promotion is not None:
            promo_kind = {
                'N': 'knight', 'B': 'bishop',
                'R': 'rook', 'Q': 'queen',
            }[move.promotion]
            promo_bb = self._get_bitboard(self._turn, promo_kind)
            self._set_bitboard(self._turn, promo_kind,
                                promo_bb.set_square(to_sq))
        else:
            new_bb = self._get_bitboard(self._turn, moving_kind)
            self._set_bitboard(self._turn, moving_kind,
                                new_bb.set_square(to_sq))

        # Update game state: ep_square, halfmove_clock, fullmove_number, turn.
        if move.is_double_push:
            # Set ep target = the square skipped over.
            axis_idx = self._pawn_axis_idx(moving_kind)
            from_coord = list(_t4.rc4(from_sq))
            mid_plane = 2 if self._turn else 5
            from_coord[axis_idx] = mid_plane
            self._ep_square = _t4.sq4(*from_coord)
        else:
            self._ep_square = None

        if (moving_kind in ('pawn_w', 'pawn_y')
                or captured_kind is not None):
            self._halfmove_clock = 0
        else:
            self._halfmove_clock += 1

        if not self._turn:
            self._fullmove_number += 1
        self._turn = not self._turn

        self._history.append(undo)

    def pop(self) -> Move4D:
        """Reverse the last push; return the move."""
        if not self._history:
            raise IndexError("no moves to pop")
        u = self._history.pop()
        move = u.move
        from_sq = move.from_sq
        to_sq = move.to_sq

        # Flip turn back.
        self._turn = not self._turn

        # Restore game state.
        self._ep_square = u.prev_ep_square
        self._halfmove_clock = u.prev_halfmove_clock
        self._fullmove_number = u.prev_fullmove_number

        # Unset to_sq -- if promotion, clear the promoted-piece slot;
        # else the moving slot.
        if move.promotion is not None:
            promo_kind = {
                'N': 'knight', 'B': 'bishop',
                'R': 'rook', 'Q': 'queen',
            }[move.promotion]
            promo_bb = self._get_bitboard(self._turn, promo_kind)
            self._set_bitboard(self._turn, promo_kind,
                                promo_bb.clear_square(to_sq))
        else:
            mb = self._get_bitboard(self._turn, u.moving_kind)
            self._set_bitboard(self._turn, u.moving_kind,
                                mb.clear_square(to_sq))

        # Restore from_sq.
        mb = self._get_bitboard(self._turn, u.moving_kind)
        self._set_bitboard(self._turn, u.moving_kind,
                            mb.set_square(from_sq))

        # Restore captured piece (if any).
        if u.captured_kind is not None:
            cb = self._get_bitboard(u.captured_color, u.captured_kind)
            self._set_bitboard(u.captured_color, u.captured_kind,
                                cb.set_square(u.captured_sq))

        return move

    # ---- Check detection -----------------------------------

    def is_check(self) -> bool:
        """True iff the side to move's king is attacked."""
        king_bb = (self._white_king if self._turn
                   else self._black_king)
        squares = king_bb.to_squares()
        if not squares:
            return False
        king_sq = squares[0]
        return self._is_attacked(king_sq, attacker_color=not self._turn)

    def _is_attacked(self, sq: int, attacker_color: bool) -> bool:
        """Is sq attacked by any piece of attacker_color?"""
        all_occ = self.occupancy()
        # Knight attacks.
        knight_bb = self._get_bitboard(attacker_color, 'knight')
        for atk_sq in knight_bb.squares():
            if sq in KNIGHT_ATTACKS_4D[atk_sq]:
                return True
        # King attacks.
        king_bb = self._get_bitboard(attacker_color, 'king')
        for atk_sq in king_bb.squares():
            if sq in KING_ATTACKS_4D[atk_sq]:
                return True
        # Rook / bishop / queen via ray-cast.
        for kind, gen in (
            ('rook', attacks_rook_4d),
            ('bishop', attacks_bishop_4d),
            ('queen', attacks_queen_4d),
        ):
            piece_bb = self._get_bitboard(attacker_color, kind)
            for atk_sq in piece_bb.squares():
                if sq in gen(atk_sq, all_occ):
                    return True
        # Pawn attacks (capture squares from opponent's perspective).
        for axis, attack_table_white, attack_table_black in (
            ('w', PAWN_ATTACKS_W_WHITE, PAWN_ATTACKS_W_BLACK),
            ('y', PAWN_ATTACKS_Y_WHITE, PAWN_ATTACKS_Y_BLACK),
        ):
            kind = f'pawn_{axis}'
            pawn_bb = self._get_bitboard(attacker_color, kind)
            attack_table = (attack_table_white if attacker_color
                            else attack_table_black)
            for atk_sq in pawn_bb.squares():
                if sq in attack_table[atk_sq]:
                    return True
        return False

    # ---- Helpers ------------------------------------------

    def _kind_at(self, color: bool, sq: int) -> Optional[str]:
        """Return the piece kind at sq for the given color, or None."""
        for kind in _PIECE_KINDS:
            bb = self._get_bitboard(color, kind)
            if sq in bb:
                return kind
        return None

    def _pawn_axis_idx(self, kind: str) -> int:
        """Return the coord index (0=x, 1=y, 2=z, 3=w) for a pawn kind."""
        if kind == 'pawn_w':
            return 3
        if kind == 'pawn_y':
            return 1
        raise ValueError(f"not a pawn kind: {kind!r}")

    def _ep_axis_idx(self, ep_sq: int) -> int:
        """Determine the axis (1 or 3) of the en-passant capture
        target square.

        Heuristic: the EP target square is the square the
        double-pushed pawn skipped over. It's at the mid_plane
        (w=2/5 or y=2/5). The axis is whichever coordinate equals
        mid_plane; when both could be (e.g., (4,2,4,2)), we look at
        the latest move in history to disambiguate."""
        # Look at the latest move to determine axis: the previous move
        # was a double push, so its from_sq's pawn kind tells us the axis.
        if not self._history:
            # Should not happen if ep_square is set.
            raise RuntimeError(
                "ep_square set but no move history to determine axis"
            )
        last = self._history[-1]
        if last.move.is_double_push:
            return self._pawn_axis_idx(last.moving_kind)
        # Also check from coords -- the EP square should be at the
        # mid-plane of one of the pawn axes.
        coord = _t4.rc4(ep_sq)
        if coord[3] in (2, 5):
            return 3  # w-axis
        if coord[1] in (2, 5):
            return 1  # y-axis
        raise RuntimeError(
            f"cannot determine EP axis for square {ep_sq}"
        )

    # ---- Hashing / FEN export ----------------------------

    def position_hash(self) -> int:
        """Stable hash of the position-relevant state.

        Includes: piece bitboards, side to move, ep square. Excludes:
        halfmove clock, fullmove number, history. This is the right
        scope for transposition-table keying and threefold-repetition
        detection.

        Implementation: deterministic Python hash of a tuple of the
        bitboard ints + scalars. Not Zobrist (no XOR magic) but
        functionally equivalent for TT and repetition checks.
        """
        return hash((
            self._white_pawn_w.bits, self._white_pawn_y.bits,
            self._white_knight.bits, self._white_bishop.bits,
            self._white_rook.bits, self._white_queen.bits,
            self._white_king.bits,
            self._black_pawn_w.bits, self._black_pawn_y.bits,
            self._black_knight.bits, self._black_bishop.bits,
            self._black_rook.bits, self._black_queen.bits,
            self._black_king.bits,
            self._turn, self._ep_square,
        ))

    def fen(self) -> str:
        """FEN4 v1 placement literal of the current position. Game-
        state suffix (turn, ep, halfmove, fullmove) is not yet
        round-tripped through fen_4d v1; only the placement is
        emitted. Round-tripping the full state requires fen_4d v2
        (deferred)."""
        position = self.to_position_dict()
        # fen_4d.serialize doesn't exist yet; emit a v1-compatible
        # literal by hand. Format: "4d-fen v1: <piece>@x,y,z,w; ..."
        parts = ["4d-fen v1:"]
        for sq in sorted(position):
            value = position[sq]
            if isinstance(value, tuple):
                char, axis = value
                tag = f"{char}{axis}"
            else:
                tag = str(value)
            x, y, z, w = _t4.rc4(sq)
            parts.append(f"{tag}@{x},{y},{z},{w};")
        return " ".join(parts)

    def to_position_dict(self) -> Dict[int, object]:
        """Inverse of from_position_dict: return {sq: piece_value}.
        Pawns are encoded as ('P'/'p', axis) tuples per fen_4d
        convention."""
        out: Dict[int, object] = {}
        for color in (True, False):
            for kind in _PIECE_KINDS:
                bb = self._get_bitboard(color, kind)
                for sq in bb.squares():
                    if kind == 'pawn_w':
                        out[sq] = ('P' if color else 'p', 'w')
                    elif kind == 'pawn_y':
                        out[sq] = ('P' if color else 'p', 'y')
                    else:
                        out[sq] = _piece_char(color, kind)
        return out

    # ---- Repr -------------------------------------------

    def __repr__(self) -> str:
        n_white = self.white_occupancy().popcount()
        n_black = self.black_occupancy().popcount()
        return (
            f"Board4D(turn={'w' if self._turn else 'b'}, "
            f"white_pieces={n_white}, black_pieces={n_black}, "
            f"halfmove={self._halfmove_clock}, "
            f"fullmove={self._fullmove_number})"
        )


# ---- Helpers --------------------------------------------------


def _normalize_piece_value(value: object) -> object:
    """Pass through a piece value (string or tuple) used by
    set_piece. Validates the type."""
    if isinstance(value, str):
        if len(value) != 1 or value not in 'PpNnBbRrQqKk':
            raise ValueError(f"invalid piece char {value!r}")
        return value
    if (isinstance(value, tuple) and len(value) == 2
            and value[0] in ('P', 'p') and value[1] in ('w', 'y')):
        return value
    raise ValueError(
        f"invalid piece value {value!r}; expected single char or "
        f"('P'/'p', 'w'/'y') tuple for axis-typed pawn"
    )


def _decode_piece_value(value: object) -> Tuple[bool, str]:
    """Convert a piece value to (color, kind). Pawns require the
    tuple form to specify the axis."""
    if isinstance(value, tuple):
        char, axis = value
        color = char.isupper()
        kind = f"pawn_{axis}"
        return color, kind
    # Single char -- non-pawn.
    if isinstance(value, str) and len(value) == 1:
        if value in 'Pp':
            raise ValueError(
                f"pawn piece char {value!r} requires axis tuple "
                f"('P'/'p', 'w'/'y')"
            )
        char = value
        color = char.isupper()
        kind_map = {
            'N': 'knight', 'B': 'bishop',
            'R': 'rook', 'Q': 'queen', 'K': 'king',
        }
        return color, kind_map[char.upper()]
    raise ValueError(f"unrecognized piece value {value!r}")


__all__ = ["Board4D", "UndoInfo"]
