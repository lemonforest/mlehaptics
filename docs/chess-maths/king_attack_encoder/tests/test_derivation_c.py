"""Unit tests for Derivation C (attack operator from king's phase)."""
import sys
import time
import unittest
from pathlib import Path

import chess
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from king_attack_encoder.derivation_c_operator import (  # noqa: E402
    FEATURE_DIM, derivation_c_channel, derivation_c_similarity,
)


class TestDerivationC(unittest.TestCase):
    def test_shape_and_dtype(self):
        board = chess.Board()
        v = derivation_c_channel(board)
        self.assertEqual(v.shape, (FEATURE_DIM,))
        self.assertEqual(v.dtype, np.float64)

    def test_non_negative_components(self):
        """Every component is a density or count — must be >= 0."""
        board = chess.Board()
        v = derivation_c_channel(board)
        self.assertTrue(np.all(v >= 0.0))

    def test_no_king_returns_zeros(self):
        board = chess.Board("8/8/8/8/8/8/8/8 w - - 0 1")
        v = derivation_c_channel(board)
        np.testing.assert_array_equal(v, np.zeros(FEATURE_DIM))

    def test_reserved_components_always_zero_in_phase_a(self):
        """Components 12..15 are reserved for Phase B extensions."""
        board = chess.Board()
        v = derivation_c_channel(board)
        np.testing.assert_array_equal(v[12:16], np.zeros(4))

    def test_rook_on_clear_file_produces_rook_ray_signal(self):
        """Black rook on e8, white king on e1. The +row ray from e1
        (towards e8) hits the rook at k=7. Density = 1/7."""
        board = chess.Board("4r3/8/8/8/8/8/8/4K3 w - - 0 1")
        v = derivation_c_channel(board)
        # +row direction is index 0
        self.assertAlmostEqual(v[0], 1.0 / 7.0, places=10)
        # Knight count (8), king adj (9), pawns (10, 11) must be 0
        self.assertEqual(v[8], 0.0)
        self.assertEqual(v[9], 0.0)
        self.assertEqual(v[10], 0.0)
        self.assertEqual(v[11], 0.0)

    def test_knight_attacks_king(self):
        """Black knight on d3, white king on e1. Knight attacks e1
        from d3 via (2, -1) jump. Knight count component == 1."""
        board = chess.Board("4k3/8/8/8/8/3n4/8/4K3 w - - 0 1")
        v = derivation_c_channel(board)
        self.assertEqual(v[8], 1.0)

    def test_blocker_prevents_rook_ray(self):
        """White pawn on e2 blocks the black e8-rook's attack on e1.
        The +row ray finds the pawn first, density stays 0."""
        board = chess.Board("4r3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        v = derivation_c_channel(board)
        self.assertEqual(v[0], 0.0)

    def test_determinism(self):
        board = chess.Board()
        a = derivation_c_channel(board)
        b = derivation_c_channel(board)
        np.testing.assert_array_equal(a, b)

    def test_similarity_in_unit_interval(self):
        board = chess.Board()
        s = derivation_c_similarity(board, chess.Move.from_uci("e2e4"))
        self.assertGreaterEqual(s, -1.0 - 1e-9)
        self.assertLessEqual(s, 1.0 + 1e-9)

    def test_similarity_zero_on_quiet_opening_moves(self):
        """In the starting position neither king has any attack
        density; both pre- and post-move vectors are all zeros;
        the similarity function returns 0.0 for zero-norm cases."""
        board = chess.Board()
        s = derivation_c_similarity(
            board, chess.Move.from_uci("g1f3"))
        self.assertEqual(s, 0.0)

    def test_performance_budget(self):
        board = chess.Board()
        derivation_c_channel(board)  # warmup
        t0 = time.perf_counter()
        for _ in range(10):
            derivation_c_channel(board)
        elapsed_ms = (time.perf_counter() - t0) * 1000 / 10
        self.assertLess(elapsed_ms, 10.0,
                        f"per-call {elapsed_ms:.2f} ms exceeds budget")


if __name__ == "__main__":
    unittest.main()
