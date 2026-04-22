"""Unit tests for occupation_field.py (§11.4 substrate)."""
import unittest

import chess

from chess_spectral.phase_operators import (
    phi,
    WHITE_CHARGE, BLACK_CHARGE,
    occupation_field_from_board,
    is_own_charge,
    ep_phase_from_board,
)


class TestOccupationField(unittest.TestCase):
    def test_starting_position_has_32_occupied_phases(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertEqual(len(occ), 32)

    def test_a1_rook_is_white(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertEqual(occ[phi(0, 0)], WHITE_CHARGE)

    def test_a8_rook_is_black(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertEqual(occ[phi(7, 0)], BLACK_CHARGE)

    def test_e4_after_e2e4(self):
        board = chess.Board()
        board.push_san("e4")
        occ = occupation_field_from_board(board)
        # e2 (r=1, c=4) now empty, e4 (r=3, c=4) now white.
        self.assertNotIn(phi(1, 4), occ)
        self.assertEqual(occ[phi(3, 4)], WHITE_CHARGE)

    def test_is_own_charge_same(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertIs(is_own_charge(occ, phi(0, 0), WHITE_CHARGE), True)

    def test_is_own_charge_opposite(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertIs(is_own_charge(occ, phi(7, 0), WHITE_CHARGE), False)

    def test_is_own_charge_empty(self):
        occ = occupation_field_from_board(chess.Board())
        self.assertIsNone(is_own_charge(occ, phi(4, 4), WHITE_CHARGE))

    def test_ep_phase_from_board_none_when_absent(self):
        """§11.4.3.2: no en passant target → helper returns None."""
        self.assertIsNone(ep_phase_from_board(chess.Board()))

    def test_ep_phase_from_board_matches_d6(self):
        """§11.4.3.2: after 1.e4 d5 2.e5, with black having just played
        d7-d5, FEN's ep_square is d6 (r=5, c=3). Helper returns
        phi(5, 3).
        """
        board = chess.Board(
            "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")
        self.assertEqual(ep_phase_from_board(board), phi(5, 3))


if __name__ == "__main__":
    unittest.main()
