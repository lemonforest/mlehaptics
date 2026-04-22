"""Unit tests for Derivation A (king-centered Laplacian eigenchannel)."""
import sys
import time
import unittest
from pathlib import Path

import chess
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from king_attack_encoder.derivation_a_laplacian import (  # noqa: E402
    derivation_a_channel, derivation_a_similarity, variance_explained,
    DEFAULT_K,
)


class TestDerivationA(unittest.TestCase):
    def test_starting_position_shape(self):
        board = chess.Board()
        v = derivation_a_channel(board)
        self.assertEqual(v.shape, (DEFAULT_K,))
        self.assertEqual(v.dtype, np.float64)

    def test_no_king_returns_zeros(self):
        board = chess.Board("8/8/8/8/8/8/8/8 w - - 0 1")
        v = derivation_a_channel(board)
        np.testing.assert_array_equal(v, np.zeros(DEFAULT_K))

    def test_determinism(self):
        board = chess.Board()
        a = derivation_a_channel(board, k=5)
        b = derivation_a_channel(board, k=5)
        np.testing.assert_array_equal(a, b)

    def test_k_bounds(self):
        board = chess.Board()
        with self.assertRaises(ValueError):
            derivation_a_channel(board, k=0)
        with self.assertRaises(ValueError):
            derivation_a_channel(board, k=65)
        # Boundary values allowed:
        self.assertEqual(derivation_a_channel(board, k=1).shape, (1,))
        self.assertEqual(derivation_a_channel(board, k=64).shape, (64,))

    def test_similarity_in_unit_interval(self):
        board = chess.Board()
        s = derivation_a_similarity(board, chess.Move.from_uci("e2e4"))
        self.assertGreaterEqual(s, -1.0 - 1e-9)
        self.assertLessEqual(s, 1.0 + 1e-9)

    def test_variance_explained_is_unit_norm_at_k64(self):
        """k=64 captures the full 64-dim basis, so variance-explained
        must equal 1.0 (modulo float drift)."""
        board = chess.Board()
        ve = variance_explained(board, k=64)
        self.assertAlmostEqual(ve, 1.0, places=10)

    def test_empty_attack_graph_variance_undefined_but_nonzero_k(self):
        """Only the mover's king on the board. The attack Laplacian is
        all zeros; any eigenbasis is valid. Variance-explained at k=5
        is still well-defined (captures the impulse in the first k
        directions of the degenerate eigenbasis) and must be in [0, 1].
        """
        board = chess.Board("8/8/8/8/8/8/8/4K3 w - - 0 1")
        ve = variance_explained(board, k=5)
        self.assertGreaterEqual(ve, 0.0)
        self.assertLessEqual(ve, 1.0 + 1e-9)

    def test_similarity_same_move_deterministic(self):
        board = chess.Board()
        s1 = derivation_a_similarity(board, chess.Move.from_uci("g1f3"))
        s2 = derivation_a_similarity(board, chess.Move.from_uci("g1f3"))
        self.assertEqual(s1, s2)

    def test_performance_budget(self):
        """Single-call cost must be well under 10 ms per §12.8."""
        board = chess.Board()
        # warmup
        derivation_a_channel(board)
        t0 = time.perf_counter()
        for _ in range(10):
            derivation_a_channel(board)
        elapsed_ms = (time.perf_counter() - t0) * 1000 / 10
        self.assertLess(elapsed_ms, 10.0,
                        f"per-call {elapsed_ms:.2f} ms exceeds budget")

    def test_similarity_uses_mover_king_after_move(self):
        """Regression test for the §12.7.1.1 turn-flip fix.

        Constructs a position where the mover's king IS attacked
        after the move (is_check_unsafe) but the opponent's king is
        NOT. The Derivation A channel computed on the post-move
        board must reflect the mover's king's neighborhood, not the
        opponent's.

        Before the fix, derivation_a_similarity consulted board.turn
        AFTER push without flipping, picking up the opponent's king.
        """
        board = chess.Board("k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d4")

        # Reference: compute what the wrapper SHOULD produce, by
        # doing the push + turn-flip explicitly.
        board_after = board.copy(stack=False)
        board_after.push(move)
        board_after.turn = not board_after.turn
        expected_after = derivation_a_channel(board_after, k=DEFAULT_K)
        expected_before = derivation_a_channel(board, k=DEFAULT_K)
        norm_b = float(np.linalg.norm(expected_before))
        norm_a = float(np.linalg.norm(expected_after))
        if norm_b > 0 and norm_a > 0:
            expected_sim = float(np.dot(expected_before, expected_after)
                                 / (norm_b * norm_a))
        else:
            expected_sim = 0.0

        actual_sim = derivation_a_similarity(board, move, k=DEFAULT_K)
        self.assertAlmostEqual(
            actual_sim, expected_sim, places=10,
            msg=("derivation_a_similarity must flip board.turn on "
                 "the post-move board; the mover's king is the "
                 "analysis target, not the opponent's."))


if __name__ == "__main__":
    unittest.main()
