"""Unit tests for occupation_field.py (§11.4 substrate)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess  # noqa: E402

from phase_operators import phi  # noqa: E402
from occupation_field import (  # noqa: E402
    WHITE_CHARGE, BLACK_CHARGE,
    occupation_field_from_board,
    is_own_charge,
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


if __name__ == "__main__":
    unittest.main()
