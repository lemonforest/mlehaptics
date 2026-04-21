"""§11.4.3.1 P_castle composite operator tests."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess  # noqa: E402

from phase_operators import phi, COL_GEN  # noqa: E402
from castling import (  # noqa: E402
    CASTLES, CastleMove, available_castles, castle_king_destinations,
)
from occupation_field import WHITE_CHARGE, BLACK_CHARGE  # noqa: E402
from occupation_aware_a import occupation_aware_moves_a  # noqa: E402
from occupation_aware_b import occupation_aware_moves_b  # noqa: E402
from occupation_aware_c import occupation_aware_moves_c  # noqa: E402


class TestCastles(unittest.TestCase):
    def test_castles_dict_derived_from_phi(self):
        """Each entry's phi fields match phi(r, c) — not hard-coded."""
        self.assertEqual(len(CASTLES), 4)
        for cm in CASTLES.values():
            self.assertIsInstance(cm, CastleMove)
            self.assertEqual(cm.king_from_phi, phi(*cm.king_from_rc))
            self.assertEqual(cm.king_to_phi, phi(*cm.king_to_rc))
            self.assertEqual(cm.rook_from_phi, phi(*cm.rook_from_rc))
            self.assertEqual(cm.rook_to_phi, phi(*cm.rook_to_rc))

    def test_king_phase_shift_is_two_col_gens(self):
        ks_w = CASTLES[(chess.WHITE, "kingside")]
        qs_w = CASTLES[(chess.WHITE, "queenside")]
        self.assertEqual(
            (ks_w.king_to_phi - ks_w.king_from_phi) % 640, 2 * COL_GEN)
        self.assertEqual(
            (qs_w.king_to_phi - qs_w.king_from_phi) % 640, (-2 * COL_GEN) % 640)

    def test_starting_position_no_castles(self):
        board = chess.Board()
        self.assertEqual(available_castles(board), [])
        self.assertEqual(
            castle_king_destinations(board, chess.WHITE), frozenset())

    def test_open_position_yields_both_white_castles(self):
        # Clear path for both white castles, black king out of interference.
        board = chess.Board(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        dests = castle_king_destinations(board, chess.WHITE)
        self.assertEqual(dests, frozenset({(0, 6), (0, 2)}))

    def test_blocker_prevents_kingside(self):
        # White kingside blocked by f1 bishop; queenside still open.
        board = chess.Board(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3KB1R w KQkq - 0 1")
        dests = castle_king_destinations(board, chess.WHITE)
        self.assertEqual(dests, frozenset({(0, 2)}))

    def test_abc_agree_on_king_castling(self):
        """Solutions A, B, C must produce identical king sets including
        castles in an open position."""
        board = chess.Board(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1")
        a = occupation_aware_moves_a(board, "K", 0, 4, WHITE_CHARGE)
        b = occupation_aware_moves_b(board, "K", 0, 4, WHITE_CHARGE)
        c = occupation_aware_moves_c(board, "K", 0, 4, WHITE_CHARGE)
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        # Must include both castle squares (g1, c1).
        self.assertIn((0, 6), a)
        self.assertIn((0, 2), a)

    def test_black_side_to_move(self):
        board = chess.Board(
            "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R b KQkq - 0 1")
        self.assertEqual(
            castle_king_destinations(board, chess.WHITE), frozenset())
        self.assertEqual(
            castle_king_destinations(board, chess.BLACK),
            frozenset({(7, 6), (7, 2)}))


if __name__ == "__main__":
    unittest.main()
