"""Move ordering for alpha-beta search.

MVV-LVA (Most Valuable Victim - Least Valuable Attacker): captures
ordered by victim_value descending, attacker_value ascending. Within
captures, ``QxP`` is sorted before ``PxQ`` -- both win material, but
``QxP`` wastes the queen's tempo and ``PxQ`` is the big-win move.
Standard heuristic; ~5-10x speedup on alpha-beta from cutting deep
material-imbalance branches early.

Non-captures fall back to source-square / destination-square ordering
for determinism (so two equal-material positions search in the same
deterministic order, useful for parity tests).
"""
from __future__ import annotations

from typing import Iterable, List, Optional

import chess

# Standard piece values for MVV-LVA ordering only (NOT for evaluation).
# Using textbook values keeps move ordering decoupled from the chosen
# evaluator's value table (which can be spectral / standard / custom).
_PIECE_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 300,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 100000,
}


def _move_priority(board: chess.Board, move: chess.Move,
                   tt_move: Optional[chess.Move]) -> int:
    """Smaller -> tried first.

    Order:
      0. TT-suggested move (the highest-priority move from a previous
         search iteration; almost always the best).
      1. Captures, sorted by MVV-LVA: smaller victim-attacker key
         means capture-of-bigger-piece-with-smaller-piece, which we
         want first.
      2. Non-captures, sorted by from_square + to_square (deterministic
         tie-breaker, no chess-specific signal).
    """
    if tt_move is not None and move == tt_move:
        return -1_000_000

    if board.is_capture(move):
        attacker_piece = board.piece_at(move.from_square)
        if move.promotion is not None:
            # Promotion + capture -- treat the promotion as the
            # attacker for ordering (the promoting pawn becomes a
            # queen, so high-value).
            attacker_value = _PIECE_VALUE.get(move.promotion, 100)
        else:
            attacker_value = (
                _PIECE_VALUE[attacker_piece.piece_type]
                if attacker_piece is not None else 100
            )
        # En passant: victim is a pawn, captured square != to_square.
        if board.is_en_passant(move):
            victim_value = _PIECE_VALUE[chess.PAWN]
        else:
            victim_piece = board.piece_at(move.to_square)
            victim_value = (
                _PIECE_VALUE[victim_piece.piece_type]
                if victim_piece is not None else 100
            )
        # MVV-LVA: high victim minus low attacker = big positive.
        # Negate so smaller -> tried first.
        return -1000 * victim_value + attacker_value

    # Non-capture: deterministic tie-breaker only. Add 10_000_000 to
    # ensure all non-captures come after captures.
    return 10_000_000 + 64 * move.from_square + move.to_square


def order_moves(board: chess.Board, moves: Iterable[chess.Move],
                tt_move: Optional[chess.Move] = None,
                ) -> List[chess.Move]:
    """Return moves sorted MVV-LVA, with tt_move first (if given).

    Stable sort -- two moves with the same priority retain the order
    of the input iterable. Callers passing ``board.legal_moves``
    inherit python-chess's enumeration order as the tiebreak (also
    deterministic, since python-chess iterates in a fixed
    piece-type/from-square/to-square order).
    """
    return sorted(moves, key=lambda m: _move_priority(board, m, tt_move))
