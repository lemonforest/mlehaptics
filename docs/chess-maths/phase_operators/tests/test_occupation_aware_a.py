"""§11.4 Solution A — post-hoc geometric pruning tests.

Mirror of test_occupation_aware_{b,c}.py; A must produce identical sets
on every fixture per §11.4 four-way convergence.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import chess  # noqa: E402

from occupation_field import WHITE_CHARGE, BLACK_CHARGE  # noqa: E402
from occupation_aware_a import occupation_aware_moves_a  # noqa: E402


def _board_with(pieces: dict[str, str], turn: chess.Color = chess.WHITE) -> chess.Board:
    board = chess.Board(None)
    for square_name, symbol in pieces.items():
        board.set_piece_at(chess.parse_square(square_name),
                           chess.Piece.from_symbol(symbol))
    board.turn = turn
    # Place kings if absent so python-chess will emit legal moves; if the
    # test setup explicitly placed kings, this is a no-op.
    if board.king(chess.WHITE) is None:
        board.set_piece_at(chess.H1, chess.Piece.from_symbol("K"))
    if board.king(chess.BLACK) is None:
        board.set_piece_at(chess.H8, chess.Piece.from_symbol("k"))
    return board


class TestSolutionA(unittest.TestCase):
    def test_starting_position_a1_rook_blocked(self):
        board = chess.Board()
        dests = occupation_aware_moves_a(board, "R", 0, 0, WHITE_CHARGE)
        self.assertEqual(dests, frozenset())

    def test_starting_position_b1_knight_two_dests(self):
        board = chess.Board()
        dests = occupation_aware_moves_a(board, "N", 0, 1, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(2, 0), (2, 2)}))

    def test_open_file_rook_six_moves_plus_capture(self):
        # Mirror the B/C test: block rank 1 east ray with a white knight
        # so the test isolates a-file destinations (7 = a2..a7 + a8).
        board = _board_with({"a1": "R", "a8": "r", "b1": "N"})
        dests = occupation_aware_moves_a(board, "R", 0, 0, WHITE_CHARGE)
        expected = frozenset({(r, 0) for r in range(1, 8)})
        self.assertEqual(dests, expected)

    def test_bishop_mixed_blockers(self):
        board = _board_with({"c1": "B", "e3": "P", "a3": "q"})
        dests = occupation_aware_moves_a(board, "B", 0, 2, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(1, 3), (1, 1), (2, 0)}))

    def test_pawn_diagonal_captures_only_when_target_present(self):
        board = _board_with({"e4": "P", "d5": "p"})
        dests = occupation_aware_moves_a(board, "P", 3, 4, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(4, 4), (4, 3)}))

    def test_pawn_no_capture_without_target(self):
        board = _board_with({"e4": "P"})
        dests = occupation_aware_moves_a(board, "P", 3, 4, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(4, 4)}))

    def test_queen_empty_center_27_dests(self):
        board = _board_with({"d4": "Q"})
        dests = occupation_aware_moves_a(board, "Q", 3, 3, WHITE_CHARGE)
        self.assertEqual(len(dests), 27)

    def test_pawn_en_passant_white_captures_d6(self):
        """§11.4.3.2: A's hybrid pipeline (unobstructed pawn candidates
        ∩ python-chess legal_moves) includes ep destinations because the
        unobstructed diagonal is in P_pawn_white(include_captures=True)
        and python-chess's legal_moves include the ep move.
        """
        board = chess.Board(
            "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")
        dests = occupation_aware_moves_a(board, "P", 4, 4, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(5, 4), (5, 3)}))

    def test_pawn_promotion_destination_single_square(self):
        """§11.4.3.3: A's set-collapsed comparison makes the four
        promotion Moves on the same to_square indistinguishable from a
        single phase destination. Returned set is {(7, 0)}.
        """
        board = chess.Board("4k3/P7/8/8/8/8/8/4K3 w - - 0 1")
        dests = occupation_aware_moves_a(board, "P", 6, 0, WHITE_CHARGE)
        self.assertEqual(dests, frozenset({(7, 0)}))


if __name__ == "__main__":
    unittest.main()
