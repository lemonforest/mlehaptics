"""Shared substrate: opponent-attack graph structures for a position.

Builds two numpy objects per position:
  - A_ka: 64x64 directed binary adjacency. A[i, j] = 1 iff opponent
    piece on square i attacks square j.
  - L_ka: 64x64 symmetric Laplacian L = D - (A + A.T)/2.

The attack relation is directed (attack is not symmetric in general:
a bishop on c1 attacks h6; a bishop on h6 attacks c1 only if there's
a bishop there). Derivation A (Laplacian eigenchannel) symmetrizes
for a well-defined spectrum; Derivation B (D4 decomposition) consumes
the directed A_ka directly and reduces to a 64-dim signal via row-sum.

The graph construction is POSITION-DEPENDENT and consumes python-chess
to enumerate per-piece attack sets. This is a geometric input, not a
phase-arithmetic computation. §12 operates on the resulting algebraic
objects (Laplacian spectrum, adjacency irrep decomposition); the input
graph itself is not phase-native.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.3 and §12.4.
"""
import chess
import numpy as np


def attack_adjacency(board: chess.Board) -> np.ndarray:
    """64x64 directed binary attack adjacency.

    A[i, j] = 1 iff an opponent piece on square i attacks square j.
    The "opponent" is the side NOT to move — the side whose attacks
    threaten the mover's king in the is_check_unsafe framing used by
    §11.5 / §12.
    """
    A = np.zeros((64, 64), dtype=np.int8)
    opp_color = not board.turn
    for square, piece in board.piece_map().items():
        if piece.color != opp_color:
            continue
        for target in board.attacks(square):
            A[square, target] = 1
    return A


def attack_laplacian(board: chess.Board) -> np.ndarray:
    """64x64 combinatorial Laplacian L = D - (A + A.T)/2 of the
    symmetrized opponent-attack graph.

    Symmetrization is intentional: the eigendecomposition is more
    interpretable on a symmetric matrix, and the directional content
    is recoverable separately from the unsymmetrized A_ka consumed by
    Derivation B. This parallels the convention in chess_spectral.tables
    where graph_laplacian operates on symmetric board adjacency.
    """
    A = attack_adjacency(board).astype(np.float64)
    A_sym = (A + A.T) / 2.0
    deg = A_sym.sum(axis=1)
    L = np.diag(deg) - A_sym
    return L


def king_square(board: chess.Board):
    """Return the 0..63 square index of the side-to-move's king, or
    None if there is no such king (degenerate FEN — the attack
    derivations return a zero vector in that case)."""
    return board.king(board.turn)
