"""Adapter between python-chess Board and the chess_spectral encoder
position-dict format.

python-chess uses square indexing a1=0, a2=8, ..., h8=63 (rank-major
from a1). chess_spectral uses a8=0, b8=1, ..., h1=63 (row-major from
a8 -- visual top of the board). The conversion below collapses one
into the other in O(piece_count).
"""
from __future__ import annotations

from typing import Dict

import chess


def board_to_position(board: chess.Board) -> Dict[int, str]:
    """Convert a python-chess Board to the encoder's position dict.

    ``{spectral_sq: piece_char}`` where:
      * spectral_sq is row-major from a8=0 (matches encoder.py).
      * piece_char is ``'P'`` / ``'p'`` / ... (white upper, black lower).

    Output is byte-equal to ``fen_to_pos(board.fen())`` but ~10x
    faster (no FEN parse / regex).
    """
    out: Dict[int, str] = {}
    for s, piece in board.piece_map().items():
        rank = chess.square_rank(s)
        file = chess.square_file(s)
        spectral_sq = (7 - rank) * 8 + file
        out[spectral_sq] = piece.symbol()
    return out
