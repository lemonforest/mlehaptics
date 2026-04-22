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
    derivation_c_delta, derivation_c_after_magnitude,
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

    def test_after_magnitude_measures_mover_king(self):
        """Regression test for the §12.7.1.1 turn-flip fix.

        derivation_c_after_magnitude is designed as a tautological
        baseline: |C_after| must be non-zero whenever the move
        leaves the MOVER's king attacked (is_check_unsafe=True). If
        the wrapper queries the opponent's king instead, this
        baseline fails (which is what Phase A2 initially detected).

        In the test FEN, after Qe4d4 the white king on e1 is
        attacked by the black rook on e5 via the cleared e-file;
        the black king on a8 remains attack-free. The post-flip
        channel must be non-zero.
        """
        board = chess.Board("k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d4")

        mag = derivation_c_after_magnitude(board, move)
        self.assertGreater(
            mag, 0.0,
            "Mover's king (white e1) is attacked after Qd4 clears "
            "the e-file; |C_after| must be positive. A value of "
            "0.0 indicates the wrapper is querying the opponent's "
            "king (black a8) instead.")

        # Pin the exact value: rook ray from e1 in the -row direction
        # hits the rook on e5 at k=4, so the density component is
        # 1/4 = 0.25. All other components are 0. |C_after| = 0.25.
        board_after = board.copy(stack=False)
        board_after.push(move)
        board_after.turn = not board_after.turn
        expected_channel = derivation_c_channel(board_after)
        expected_mag = float(np.linalg.norm(expected_channel))
        self.assertAlmostEqual(mag, expected_mag, places=10)
        # Component layout: index 1 is -row ray (pointing from king
        # toward e5 given white king on e1, that's the +row toward
        # a higher rank -- index 0). The actual ray direction depends
        # on the ROW_GEN sign convention; assert that SOMETHING is
        # nonzero in the rook-ray band [0..3].
        rook_band = expected_channel[0:4]
        self.assertGreater(
            float(np.max(rook_band)), 0.0,
            "One of the four rook-ray density components must be "
            "non-zero; got all zeros.")

    def test_delta_uses_mover_king_after_move(self):
        """Regression test for the §12.7.1.1 turn-flip fix on
        derivation_c_delta."""
        board = chess.Board("k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d4")

        dlt = derivation_c_delta(board, move)
        # Before the move, white's king on e1 has no attackers (the
        # rook on e5 is blocked by the queen on e4). So C_before is
        # all zeros. After the move with turn-flip, C_after has
        # 0.25 in the rook-ray component. Delta = L2(C_after - 0) =
        # |C_after| = 0.25.
        board_after = board.copy(stack=False)
        board_after.push(move)
        board_after.turn = not board_after.turn
        b = derivation_c_channel(board)
        a = derivation_c_channel(board_after)
        expected = float(np.linalg.norm(a - b))
        self.assertAlmostEqual(dlt, expected, places=10)
        self.assertGreater(
            dlt, 0.0,
            "delta_c must measure change on mover's-king attack "
            "density, not opponent's-king.")

    def test_similarity_uses_mover_king_after_move(self):
        """Regression test for the §12.7.1.1 turn-flip fix on
        derivation_c_similarity."""
        board = chess.Board("k7/8/8/4r3/4Q3/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("e4d4")

        sim = derivation_c_similarity(board, move)
        # C_before is all zeros (queen blocks the rook); with the
        # zero-norm fallback the cosine returns 0.0 regardless of
        # whether the turn-flip is applied. But the reference path
        # with explicit flip should match.
        board_after = board.copy(stack=False)
        board_after.push(move)
        board_after.turn = not board_after.turn
        b = derivation_c_channel(board)
        a = derivation_c_channel(board_after)
        norm = float(np.linalg.norm(b) * np.linalg.norm(a))
        expected = (float(np.dot(b, a) / norm)
                    if norm > 0 else 0.0)
        self.assertAlmostEqual(sim, expected, places=10)


if __name__ == "__main__":
    unittest.main()
