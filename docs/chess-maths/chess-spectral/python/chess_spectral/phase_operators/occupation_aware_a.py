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
     in castling.py.

python-chess dependency:
    ``chess`` is imported lazily inside functions that actually need it
    (see module header note in ``occupation_field.py``).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import chess

from .phase_operators import (
    phi,
    P_rook, P_bishop, P_queen, P_king, P_knight,
    P_pawn_white, P_pawn_black,
)
from .phase_to_coords import phase_set_to_board
from .occupation_field import WHITE_CHARGE
from .castling import castle_king_destinations


def _unobstructed_dests(piece_char: str, origin_r: int, origin_c: int,
                        mover_charge: int) -> frozenset[tuple[int, int]]:
    origin_phi = phi(origin_r, origin_c)
    pc = piece_char.upper()
    if pc == "R":
        return phase_set_to_board(P_rook(origin_phi))
    if pc == "B":
        return phase_set_to_board(P_bishop(origin_phi))
    if pc == "Q":
        return phase_set_to_board(P_queen(origin_phi))
    if pc == "K":
        return phase_set_to_board(P_king(origin_phi))  # castling unioned at top-level
    if pc == "N":
        return phase_set_to_board(P_knight(origin_phi))
    if pc == "P":
        if mover_charge == WHITE_CHARGE:
            phases = P_pawn_white(origin_phi,
                                  on_starting_rank=(origin_r == 1),
                                  include_captures=True)
        else:
            phases = P_pawn_black(origin_phi,
                                  on_starting_rank=(origin_r == 6),
                                  include_captures=True)
        return phase_set_to_board(phases)
    raise ValueError(f"unknown piece char: {piece_char}")


def _chess_legal_dests(board: "chess.Board", origin_r: int,
                       origin_c: int) -> frozenset[tuple[int, int]]:
    import chess
    origin_sq = chess.square(origin_c, origin_r)
    out: set[tuple[int, int]] = set()
    for move in board.legal_moves:
        if move.from_square == origin_sq:
            to_sq = move.to_square
            out.add((chess.square_rank(to_sq), chess.square_file(to_sq)))
    return frozenset(out)


def occupation_aware_moves_a(board: "chess.Board", piece_char: str,
                             origin_r: int, origin_c: int,
                             mover_charge: int) -> frozenset[tuple[int, int]]:
    """Hybrid: phase-space candidate generation, python-chess filter.

    En passant and promotion are NOT handled here (§11.2.8). Castling
    is handled via the §11.4.3.1 P_castle composite operator — king
    candidates are unioned with castle_king_destinations(board) before
    the legal-move intersection.
    """
    import chess
    candidates = _unobstructed_dests(piece_char, origin_r, origin_c,
                                     mover_charge)
    if piece_char.upper() == "K":
        mover_color = (chess.WHITE if mover_charge == WHITE_CHARGE
                       else chess.BLACK)
        candidates = candidates | castle_king_destinations(board, mover_color)
    legal = _chess_legal_dests(board, origin_r, origin_c)
    return frozenset(candidates & legal)
