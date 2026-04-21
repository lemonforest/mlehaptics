"""§11.4 Solution B — occupation-aware phase operator tests.

Mirror of test_occupation_aware_c.py; both must produce identical results
on every fixture per §11.4.3 equivalence claim.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess  # noqa: E402

from occupation_field import WHITE_CHARGE, BLACK_CHARGE  # noqa: E402
from occupation_aware_b import occupation_aware_moves_b  # noqa: E402


def _board_with(pieces: dict[str, str]) -> chess.Board:
    """Empty board with given piece placements. Keys like 'e4', values 'P', 'n', etc."""
    board = chess.Board(None)
    for square_name, symbol in pieces.items():
        board.set_piece_at(chess.parse_square(square_name),
                           chess.Piece.from_symbol(symbol))
    return board


class TestSolutionB(unittest.TestCase):
    def test_starting_position_a1_rook_blocked(self):
        board = chess.Board()
        dests = occupation_aware_moves_b(board, "R", 0, 0, WHITE_CHARGE)
        self.assertEqual(dests, frozenset())

    def test_starting_position_b1_knight_two_dests(self):
        board = chess.Board()
        dests = occupation_aware_moves_b(board, "N", 0, 1, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(2, 0), (2, 2)}))

    def test_open_file_rook_six_moves_plus_capture(self):
        # b1 knight blocks the east ray so the test isolates the a-file;
        # expected 7 = six advances (a2..a7) + one capture (a8).
        board = _board_with({"a1": "R", "a8": "r", "b1": "N"})
        dests = occupation_aware_moves_b(board, "R", 0, 0, WHITE_CHARGE)
        expected = frozenset({(r, 0) for r in range(1, 8)})
        self.assertEqual(dests, expected)

    def test_bishop_mixed_blockers(self):
        # White bishop c1, own pawn e3 (NE blocker at k=2), black queen a3
        # (NW opposite-charge blocker at k=2, capture).
        board = _board_with({"c1": "B", "e3": "P", "a3": "q"})
        dests = occupation_aware_moves_b(board, "B", 0, 2, WHITE_CHARGE)
        # NE: d2 only (e3 blocks own). NW: b2 + a3 (capture). SE/SW off-board.
        self.assertEqual(dests, frozenset({(1, 3), (1, 1), (2, 0)}))

    def test_pawn_diagonal_captures_only_when_target_present(self):
        board = _board_with({"e4": "P", "d5": "p"})
        dests = occupation_aware_moves_b(board, "P", 3, 4, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(4, 4), (4, 3)}))

    def test_pawn_no_capture_without_target(self):
        board = _board_with({"e4": "P"})
        dests = occupation_aware_moves_b(board, "P", 3, 4, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(4, 4)}))

    def test_queen_empty_center_27_dests(self):
        board = _board_with({"d4": "Q"})
        dests = occupation_aware_moves_b(board, "Q", 3, 3, WHITE_CHARGE)
        self.assertEqual(len(dests), 27)


if __name__ == "__main__":
    unittest.main()
