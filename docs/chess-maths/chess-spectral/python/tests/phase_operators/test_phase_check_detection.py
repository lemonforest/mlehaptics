"""§11.5 path-1 phase-native is_check tests."""
import random
import unittest

import chess

from chess_spectral.phase_operators import phasecast_is_check


class TestPhaseCheckDetection(unittest.TestCase):
    def test_lone_king_not_in_check(self):
        board = chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
        self.assertFalse(phasecast_is_check(board))

    def test_knight_check(self):
        # White K on e1, Black N on d3 -> knight attacks e1 (two-one jump).
        board = chess.Board("4k3/8/8/8/8/3n4/8/4K3 w - - 0 1")
        self.assertTrue(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_rook_check_clear_file(self):
        board = chess.Board("4k3/8/8/8/8/8/8/r3K3 w - - 0 1")
        self.assertTrue(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_rook_blocked_by_own_pawn(self):
        # White K on e1, White P on e2, Black R on e8 — pawn blocks.
        board = chess.Board("4r3/8/8/8/8/8/4P3/4K3 w - - 0 1")
        self.assertFalse(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_rook_blocked_by_enemy_non_attacker(self):
        # White K on e1, Black N on e4 (blocks), Black R on e8.
        # Knight blocks the rook but does not itself attack e1 from e4.
        board = chess.Board("4r3/8/8/8/4n3/8/8/4K3 w - - 0 1")
        self.assertFalse(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_bishop_diagonal_check(self):
        # White K on e1, Black B on h4 — attacks via e1-h4 diagonal.
        board = chess.Board("4k3/8/8/8/7b/8/8/4K3 w - - 0 1")
        self.assertTrue(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_pawn_check_white_king(self):
        # White K on e4, Black P on d5 — attacks e4 diagonally.
        board = chess.Board("4k3/8/8/3p4/4K3/8/8/8 w - - 0 1")
        self.assertTrue(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_pawn_check_black_king(self):
        # Black K on e5, White P on d4 — attacks e5 diagonally.
        board = chess.Board("8/8/8/4k3/3P4/8/8/4K3 b - - 0 1")
        self.assertTrue(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_starting_position_no_check(self):
        board = chess.Board()
        self.assertFalse(phasecast_is_check(board))
        self.assertEqual(phasecast_is_check(board), board.is_check())

    def test_matches_chess_random_play_500(self):
        """500-position cross-check: random-play rollouts, assert
        phasecast_is_check == board.is_check() on every ply."""
        rng = random.Random(42)
        positions_checked = 0
        games = 0
        while positions_checked < 500:
            board = chess.Board()
            games += 1
            while not board.is_game_over(claim_draw=False):
                self.assertEqual(
                    phasecast_is_check(board), board.is_check(),
                    msg=f"mismatch on {board.fen()}")
                positions_checked += 1
                if positions_checked >= 500:
                    break
                legal = list(board.legal_moves)
                if not legal:
                    break
                board.push(rng.choice(legal))
        self.assertGreaterEqual(positions_checked, 500)


if __name__ == "__main__":
    unittest.main()
