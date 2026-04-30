"""Draw-rule predicates for 4D chess (PR-7-G).

Standard chess draw conditions, mapped to the 4D Oana-Chiru
ruleset:

  * **Threefold repetition** -- the same position has occurred at
    least three times across the game's move history.
  * **50-move rule** -- 100 plies (50 full moves) have passed
    without a pawn move or capture.
  * **Insufficient material** -- neither side has enough material
    to deliver checkmate. In 4D the canonical insufficient-material
    cases extend the 2D rule:
      - K vs K (lone kings)
      - K vs K + minor (knight or bishop)
      - K + minor vs K + minor (with same-color bishops; in 4D
        bishop-color is "coordinate-sum parity", per the
        graph-Laplacian eigenbasis 2-component result from
        Oana-Chiru §2)
    Pawns, rooks, queens disqualify by themselves.
  * **Stalemate** -- side to move has no legal moves AND is NOT
    in check.
  * **Checkmate** -- side to move has no legal moves AND IS in
    check.
  * **is_game_over** -- any of the above is true.

Each predicate is a stateless function of a Board4D + (for
threefold) the move history. Board4D exposes the data they need
(position_hash, halfmove_clock, move_history) -- this module
just composes them.

Public API
----------
- :func:`is_threefold_repetition(board) -> bool`
- :func:`is_fifty_move_rule(board) -> bool`
- :func:`is_insufficient_material(board) -> bool`
- :func:`is_stalemate(board) -> bool`
- :func:`is_checkmate(board) -> bool`
- :func:`is_game_over(board) -> bool`

Convention: each predicate returns a bool. ``is_game_over`` is
the OR of all the others; consumers needing the specific reason
call the individual predicates.
"""
from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .board import Board4D


def _count_positions_in_history(board: "Board4D") -> Counter:
    """Replay the move history from start, recording position_hash()
    at each ply. Returns a Counter of hash → occurrences.

    Implementation: pop all moves to the start, record the start
    hash, then push each move back (recording each intermediate
    hash + the final). Restores board state on completion.
    """
    # Save the moves, pop them all.
    moves = list(board.move_history)
    n = len(moves)
    for _ in range(n):
        board.pop()

    counter: Counter = Counter()
    counter[board.position_hash()] += 1
    for move in moves:
        board.push(move)
        counter[board.position_hash()] += 1
    return counter


def is_threefold_repetition(board: "Board4D") -> bool:
    """True iff the current position has occurred 3+ times in the
    game's history.

    Uses :meth:`Board4D.position_hash` (which excludes
    halfmove/fullmove counters) so that "same position with
    different move counts" registers as a repetition.

    Walks the move history each call (O(n_plies)). For hot loops
    that need repeated checks (e.g., search inner loops), the
    caller can maintain an external Counter incrementally.
    """
    history_counter = _count_positions_in_history(board)
    current = board.position_hash()
    return history_counter[current] >= 3


def is_fifty_move_rule(board: "Board4D") -> bool:
    """True iff 100 plies (50 full moves) have passed with no pawn
    move or capture. Uses ``board.halfmove_clock``."""
    return board.halfmove_clock >= 100


def is_insufficient_material(board: "Board4D") -> bool:
    """True iff neither side has enough material to checkmate.

    Cases recognized:
      - Both sides have only kings (KK).
      - One side has K + single minor (knight or bishop), other
        only K (KMK).
      - Both sides have K + bishop, with bishops on same
        coord-sum-parity (KBKB same-parity).
      - Both sides have K + knight (KNKN -- mathematically possible
        to mate but extremely rare and considered drawn at the
        rule level for the standard 2D "insufficient" set; we
        match python-chess's convention here).

    A pawn, rook, or queen on either side disqualifies (those
    pieces can mate alone with the friendly king).
    """
    # Pawns / rooks / queens are sufficient material.
    for color in (True, False):
        for kind in ('pawn_w', 'pawn_y', 'rook', 'queen'):
            if not board._get_bitboard(color, kind).is_empty():
                return False

    # Count knights, bishops per color.
    def _piece_squares(color: bool, kind: str):
        return board._get_bitboard(color, kind).to_squares()

    w_knights = _piece_squares(True, 'knight')
    w_bishops = _piece_squares(True, 'bishop')
    b_knights = _piece_squares(False, 'knight')
    b_bishops = _piece_squares(False, 'bishop')

    w_minors = len(w_knights) + len(w_bishops)
    b_minors = len(b_knights) + len(b_bishops)

    # KK
    if w_minors == 0 and b_minors == 0:
        return True

    # K + single minor vs K
    if (w_minors == 1 and b_minors == 0) or (
            w_minors == 0 and b_minors == 1):
        return True

    # K + bishop vs K + bishop (both single bishops, same parity)
    if (len(w_bishops) == 1 and len(b_bishops) == 1
            and len(w_knights) == 0 and len(b_knights) == 0):
        from .. import tables_4d as _t4
        wb_sq = w_bishops[0]
        bb_sq = b_bishops[0]
        wb_coord = _t4.rc4(wb_sq)
        bb_coord = _t4.rc4(bb_sq)
        wb_parity = sum(wb_coord) % 2
        bb_parity = sum(bb_coord) % 2
        if wb_parity == bb_parity:
            return True

    # K + N vs K + N -- python-chess treats this as insufficient.
    # In theory N vs N can mate; in practice it requires the
    # opponent to be cooperatively bad. Rule-of-thumb says drawn.
    if (len(w_knights) == 1 and len(b_knights) == 1
            and len(w_bishops) == 0 and len(b_bishops) == 0):
        return True

    return False


def is_stalemate(board: "Board4D") -> bool:
    """True iff side-to-move has no legal moves AND is NOT in check."""
    if board.is_check():
        return False
    for _ in board.legal_moves():
        return False
    return True


def is_checkmate(board: "Board4D") -> bool:
    """True iff side-to-move has no legal moves AND IS in check."""
    if not board.is_check():
        return False
    for _ in board.legal_moves():
        return False
    return True


def is_game_over(board: "Board4D") -> bool:
    """True iff any draw / mate condition triggers.

    Order of checks (any-true short-circuits):
      1. Checkmate
      2. Stalemate
      3. Threefold repetition
      4. Fifty-move rule
      5. Insufficient material
    """
    return (
        is_checkmate(board)
        or is_stalemate(board)
        or is_threefold_repetition(board)
        or is_fifty_move_rule(board)
        or is_insufficient_material(board)
    )


__all__ = [
    "is_threefold_repetition",
    "is_fifty_move_rule",
    "is_insufficient_material",
    "is_stalemate",
    "is_checkmate",
    "is_game_over",
]
