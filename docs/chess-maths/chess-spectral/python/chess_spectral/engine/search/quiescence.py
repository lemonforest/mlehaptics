"""Quiescence search.

At the leaves of the alpha-beta tree, we don't want to evaluate
positions where the side to move is in the middle of an exchange --
that produces the "horizon effect" where the search stops just
before a capture, missing the obvious tactical answer.

Quiescence search extends only on captures (and optionally checks)
until the position is "quiet" (no forcing moves). It's a small
secondary search rooted at each leaf node.

The standard "stand pat" pattern: if the static evaluation already
beats beta, we don't need to capture -- the side to move can
"stand pat" and lock in the score.
"""
from __future__ import annotations

from typing import Callable, Optional

import chess

from .ordering import order_moves


def quiescence(board: chess.Board,
               alpha: float,
               beta: float,
               evaluator: Callable[[dict, bool], float],
               position_of: Callable[[chess.Board], dict],
               max_depth: int = 8) -> float:
    """Quiescence search: extend on captures until quiet.

    Parameters
    ----------
    board : chess.Board
        Current position (mutated in place during recursion via
        push/pop; restored to original on return).
    alpha, beta : float
        Standard alpha-beta window.
    evaluator : callable
        ``evaluator(position_dict, side_to_move) -> float``. Called
        for the static evaluation at quiescent positions and for the
        stand-pat baseline.
    position_of : callable
        Adapter ``(board) -> position_dict``.
    max_depth : int, default 8
        Quiescence-only recursion depth limit. Cuts off pathological
        capture chains (long sequences of trade-down captures).

    Returns
    -------
    score : float
        Best achievable score from current side-to-move's perspective.
    """
    # Stand-pat: if the static eval already exceeds beta, the side
    # to move can decline to capture and still get >= beta.
    stand_pat = evaluator(position_of(board), board.turn)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    if max_depth <= 0:
        return alpha

    # Generate only capture moves (and promotions, which are
    # similarly forcing). Skip checks for now -- including them
    # explodes the quiescence tree without commensurate Elo gain
    # at our scale.
    capture_moves = [m for m in board.legal_moves
                     if board.is_capture(m) or m.promotion is not None]
    capture_moves = order_moves(board, capture_moves)

    for move in capture_moves:
        board.push(move)
        score = -quiescence(board, -beta, -alpha,
                            evaluator, position_of,
                            max_depth=max_depth - 1)
        board.pop()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha
