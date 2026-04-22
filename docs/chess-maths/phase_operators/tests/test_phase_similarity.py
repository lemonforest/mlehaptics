"""§11.5 path-2 phase_similarity tests."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess  # noqa: E402

from phase_similarity import phase_similarity  # noqa: E402


class TestPhaseSimilarity(unittest.TestCase):
    def test_trivial_move_high_but_below_one(self):
        # e2-e4 from starting position: single pawn moves two squares.
        # Cosine should be high but strictly less than 1.0.
        board = chess.Board()
        move = chess.Move.from_uci("e2e4")
        sim = phase_similarity(board, move)
        self.assertLess(sim, 1.0)
        self.assertGreater(sim, 0.5)

    def test_determinism(self):
        board = chess.Board()
        move = chess.Move.from_uci("g1f3")
        a = phase_similarity(board, move)
        b = phase_similarity(board, move)
        self.assertEqual(a, b)

    def test_bounded_in_unit_interval(self):
        """Across 20 random positions, cosine stays in [-1, 1]."""
        rng = random.Random(7)
        positions_checked = 0
        while positions_checked < 20:
            board = chess.Board()
            while not board.is_game_over(claim_draw=False):
                legal = list(board.legal_moves)
                if not legal:
                    break
                mv = rng.choice(legal)
                sim = phase_similarity(board, mv)
                self.assertGreaterEqual(sim, -1.0 - 1e-9)
                self.assertLessEqual(sim, 1.0 + 1e-9)
                board.push(mv)
                positions_checked += 1
                if positions_checked >= 20:
                    break

    def test_capture_vs_quiet_population(self):
        """Captures change the field more than quiet moves on average.

        Probabilistic — not a correctness guarantee. Runs a random walk
        and compares mean similarity for capture vs quiet moves.
        """
        rng = random.Random(123)
        capture_sims = []
        quiet_sims = []
        trials = 0
        while trials < 20 and (
            len(capture_sims) < 10 or len(quiet_sims) < 10
        ):
            board = chess.Board()
            while not board.is_game_over(claim_draw=False):
                legal = list(board.legal_moves)
                if not legal:
                    break
                mv = rng.choice(legal)
                is_cap = board.is_capture(mv)
                sim = phase_similarity(board, mv)
                if is_cap:
                    capture_sims.append(sim)
                else:
                    quiet_sims.append(sim)
                board.push(mv)
            trials += 1
        if capture_sims and quiet_sims:
            mean_cap = sum(capture_sims) / len(capture_sims)
            mean_quiet = sum(quiet_sims) / len(quiet_sims)
            self.assertLess(
                mean_cap, mean_quiet + 1e-6,
                msg=f"mean_capture={mean_cap:.4f}, "
                    f"mean_quiet={mean_quiet:.4f}")

    def test_different_moves_differ(self):
        """Two different opening moves should produce different similarities."""
        board = chess.Board()
        s_e4 = phase_similarity(board, chess.Move.from_uci("e2e4"))
        s_nf3 = phase_similarity(board, chess.Move.from_uci("g1f3"))
        self.assertNotEqual(s_e4, s_nf3)


if __name__ == "__main__":
    unittest.main()
