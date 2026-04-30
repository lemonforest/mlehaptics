"""Quiescence search for the 4D search core.

Capture-only extension at leaves. Stand-pat: if static eval already
exceeds beta, side-to-move can decline to capture and lock in the
score. Same shape as the 2D quiescence module.
"""
from __future__ import annotations

from typing import Callable

from chess_spectral.spatial_4d import Board4D, Move4D
from .ordering import order_moves


def quiescence(board: Board4D,
               alpha: float,
               beta: float,
               evaluator: Callable[[dict, bool], float],
               max_depth: int = 8) -> float:
    """Quiescence search: extend on captures until quiet."""
    pos_dict = board.to_position_dict()
    stand_pat = evaluator(pos_dict, board.turn)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if max_depth <= 0:
        return alpha

    # Generate only capture moves + promotions.
    own = board.own_occupancy()
    opp = board.opponent_occupancy()
    capture_moves = []
    for m in board.legal_moves():
        if m.to_sq in opp or m.is_ep_capture or m.promotion is not None:
            capture_moves.append(m)
    capture_moves = order_moves(board, capture_moves)

    for move in capture_moves:
        board.push(move)
        score = -quiescence(board, -beta, -alpha,
                            evaluator,
                            max_depth=max_depth - 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha
