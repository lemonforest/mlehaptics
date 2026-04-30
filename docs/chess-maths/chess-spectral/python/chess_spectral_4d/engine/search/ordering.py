"""MVV-LVA move ordering for the 4D search core.

Captures sorted by victim_value descending, attacker_value ascending.
TT-suggested move first overall.

Piece values are textbook (NOT the spectral values) so move
ordering is decoupled from the chosen evaluator's value table.
"""
from __future__ import annotations

from typing import Iterable, List, Optional

from chess_spectral.spatial_4d import Board4D, Move4D


# Standard piece values for ordering only.
_PIECE_VALUE = {
    'pawn_w': 100, 'pawn_y': 100,
    'knight': 300, 'bishop': 300,
    'rook': 500, 'queen': 900, 'king': 100000,
}


def _piece_kind_at(board: Board4D, sq: int) -> Optional[str]:
    """Return the piece kind at sq (any color), or None."""
    for kind in ('pawn_w', 'pawn_y', 'knight', 'bishop',
                 'rook', 'queen', 'king'):
        if sq in board._get_bitboard(True, kind):
            return kind
        if sq in board._get_bitboard(False, kind):
            return kind
    return None


def _move_priority(board: Board4D, move: Move4D,
                   tt_move: Optional[Move4D]) -> int:
    """Smaller -> tried first."""
    if tt_move is not None and move == tt_move:
        return -1_000_000

    # Identify whether the move is a capture: opponent piece at to_sq.
    own_color = board.turn
    opp_occ = board.opponent_occupancy()
    is_capture = move.to_sq in opp_occ or move.is_ep_capture

    if is_capture:
        attacker_kind = _piece_kind_at(board, move.from_sq)
        if move.promotion is not None:
            promo_kind = {'N': 'knight', 'B': 'bishop',
                          'R': 'rook', 'Q': 'queen'}[move.promotion]
            attacker_value = _PIECE_VALUE[promo_kind]
        else:
            attacker_value = _PIECE_VALUE.get(attacker_kind, 100)
        if move.is_ep_capture:
            victim_value = _PIECE_VALUE['pawn_w']  # any pawn type
        else:
            victim_kind = _piece_kind_at(board, move.to_sq)
            victim_value = _PIECE_VALUE.get(victim_kind, 100)
        return -1000 * victim_value + attacker_value

    # Non-capture: deterministic tie-break.
    return 10_000_000 + 4096 * move.from_sq + move.to_sq


def order_moves(board: Board4D, moves: Iterable[Move4D],
                tt_move: Optional[Move4D] = None,
                ) -> List[Move4D]:
    """Return moves sorted MVV-LVA, with tt_move first (if given)."""
    return sorted(moves, key=lambda m: _move_priority(board, m, tt_move))
