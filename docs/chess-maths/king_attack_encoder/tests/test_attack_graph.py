"""Unit tests for attack_graph.py (§12 shared substrate)."""
import sys
import unittest
from pathlib import Path

import chess
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from king_attack_encoder.attack_graph import (  # noqa: E402
    attack_adjacency, attack_laplacian, king_square,
)


class TestAttackAdjacency(unittest.TestCase):
    def test_starting_position_shape_and_type(self):
        board = chess.Board()
        A = attack_adjacency(board)
        self.assertEqual(A.shape, (64, 64))
        self.assertEqual(A.dtype, np.int8)

    def test_only_opponent_pieces_contribute(self):
        """In the starting position with white to move, black is the
        opponent. Every row corresponding to a white square must be
        all zeros (white pieces are not opponents of themselves)."""
        board = chess.Board()
        A = attack_adjacency(board)
        for sq in range(64):
            piece = board.piece_at(sq)
            if piece is not None and piece.color == chess.WHITE:
                self.assertTrue(np.all(A[sq] == 0),
                                f"white piece at {chess.square_name(sq)} "
                                f"contributed nonzero row")

    def test_rook_on_clear_file(self):
        """Black rook on e8, white king on e1 (to move), rest empty.
        Rook's attack row (from square 60 = e8) should mark e7..e1
        and nothing else. e-file squares: 52, 44, 36, 28, 20, 12, 4."""
        board = chess.Board("4r3/8/8/8/8/8/8/4K3 w - - 0 1")
        A = attack_adjacency(board)
        e8 = chess.parse_square("e8")
        expected = {chess.parse_square(s) for s in
                    ("e7", "e6", "e5", "e4", "e3", "e2", "e1")}
        actual = set(np.where(A[e8] == 1)[0].tolist())
        # Rook also attacks along 8th rank
        for s in ("a8", "b8", "c8", "d8", "f8", "g8", "h8"):
            expected.add(chess.parse_square(s))
        self.assertEqual(actual, expected)

    def test_no_opponent_pieces_yields_zero_matrix(self):
        # Only the mover's king on the board.
        board = chess.Board("8/8/8/8/8/8/8/4K3 w - - 0 1")
        A = attack_adjacency(board)
        self.assertEqual(A.sum(), 0)

    def test_determinism(self):
        board = chess.Board()
        A1 = attack_adjacency(board)
        A2 = attack_adjacency(board)
        np.testing.assert_array_equal(A1, A2)


class TestAttackLaplacian(unittest.TestCase):
    def test_laplacian_row_sums_zero(self):
        """Combinatorial Laplacian always has row-sums of 0."""
        board = chess.Board()
        L = attack_laplacian(board)
        np.testing.assert_allclose(L.sum(axis=1), np.zeros(64),
                                   atol=1e-12)

    def test_symmetric(self):
        board = chess.Board()
        L = attack_laplacian(board)
        np.testing.assert_allclose(L, L.T, atol=1e-12)

    def test_diagonal_matches_symmetrized_degree(self):
        board = chess.Board()
        A = attack_adjacency(board).astype(np.float64)
        A_sym = (A + A.T) / 2.0
        L = attack_laplacian(board)
        np.testing.assert_allclose(np.diag(L), A_sym.sum(axis=1),
                                   atol=1e-12)

    def test_empty_attack_graph_yields_zero_laplacian(self):
        board = chess.Board("8/8/8/8/8/8/8/4K3 w - - 0 1")
        L = attack_laplacian(board)
        np.testing.assert_allclose(L, np.zeros((64, 64)), atol=1e-12)


class TestKingSquare(unittest.TestCase):
    def test_starting_position_white_king_on_e1(self):
        board = chess.Board()
        self.assertEqual(king_square(board), chess.parse_square("e1"))

    def test_black_to_move_returns_black_king(self):
        board = chess.Board(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
        self.assertEqual(king_square(board), chess.parse_square("e8"))

    def test_no_king_returns_none(self):
        board = chess.Board("8/8/8/8/8/8/8/8 w - - 0 1")
        self.assertIsNone(king_square(board))


if __name__ == "__main__":
    unittest.main()
