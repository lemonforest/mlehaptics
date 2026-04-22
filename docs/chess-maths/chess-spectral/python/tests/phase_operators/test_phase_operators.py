"""Unit tests for the §11.2 phase operators and §11.3 inversion.

Run via pytest from the repo root or from the python/ package dir:

    pytest docs/chess-maths/chess-spectral/python/tests/phase_operators/

(unittest discovery still works because pytest collects unittest-style
TestCase subclasses).
"""
import math
import unittest

from chess_spectral.phase_operators import (
    MODULUS, ROW_GEN, COL_GEN,
    DIAG_NE_SW_GEN, DIAG_NW_SE_GEN,
    KNIGHT_SHIFTS, KING_SHIFTS,
    phi,
    P_rook, P_bishop, P_queen, P_king, P_knight,
    P_pawn_white, P_pawn_black,
    PHI_TO_RC, RC_TO_PHI,
    invert, phase_set_to_board,
)


class TestGeneratorCoprimality(unittest.TestCase):
    def test_gcd_67_640(self):
        self.assertEqual(math.gcd(ROW_GEN, MODULUS), 1)

    def test_gcd_7_640(self):
        self.assertEqual(math.gcd(COL_GEN, MODULUS), 1)

    def test_gcd_67_7(self):
        self.assertEqual(math.gcd(ROW_GEN, COL_GEN), 1)


class TestPhiInjectivity(unittest.TestCase):
    def test_phi_is_injective_on_board(self):
        phases = {phi(r, c) for r in range(8) for c in range(8)}
        self.assertEqual(len(phases), 64)


class TestSupplementWorkedExample(unittest.TestCase):
    """§11.3.3 worked example — boundary clip demonstration."""

    def test_rook_from_00_seven_rows_gives_469(self):
        self.assertEqual((phi(0, 0) + 7 * ROW_GEN) % MODULUS, 469)

    def test_rook_from_70_one_row_gives_536(self):
        self.assertEqual((phi(7, 0) + ROW_GEN) % MODULUS, 536)


class TestKnightShifts(unittest.TestCase):
    def test_knight_shifts_decode(self):
        self.assertEqual(set(KNIGHT_SHIFTS),
                         {141, 127, 81, 53, -141, -127, -81, -53})

    def test_knight_shifts_match_offset_derivation(self):
        # 141 = 2*67 + 7, 127 = 2*67 - 7, 81 = 67 + 2*7, 53 = 67 - 2*7
        derived = {
            2 * ROW_GEN + COL_GEN,
            2 * ROW_GEN - COL_GEN,
            ROW_GEN + 2 * COL_GEN,
            ROW_GEN - 2 * COL_GEN,
            -(2 * ROW_GEN + COL_GEN),
            -(2 * ROW_GEN - COL_GEN),
            -(ROW_GEN + 2 * COL_GEN),
            -(ROW_GEN - 2 * COL_GEN),
        }
        self.assertEqual(set(KNIGHT_SHIFTS), derived)


class TestKingShifts(unittest.TestCase):
    def test_king_shifts_decode(self):
        self.assertEqual(set(KING_SHIFTS),
                         {67, 7, 74, 60, -67, -7, -74, -60})

    def test_diagonal_generators(self):
        self.assertEqual(DIAG_NE_SW_GEN, ROW_GEN + COL_GEN)
        self.assertEqual(DIAG_NW_SE_GEN, ROW_GEN - COL_GEN)


class TestOperatorSizesInterior(unittest.TestCase):
    """Phase-level operator output sizes from interior square (4, 4).

    These are PRE-clip phase-value counts, per §11.2 formulas. The
    board-level (post-clip) counts the supplement quotes in prose
    (rook=14, bishop=13, queen=27 from (4,4)) are tested separately
    against phase_set_to_board once phase_to_coords lands.
    """

    def setUp(self):
        self.origin = phi(4, 4)

    def test_rook_size(self):
        # §11.2.2: k ∈ {±1,…,±7} × {ROW_GEN, COL_GEN} = 28 phase values,
        # all distinct because 67 and 7 are coprime to 640 and to each other.
        self.assertEqual(len(P_rook(self.origin)), 28)

    def test_bishop_size(self):
        # §11.2.3: k ∈ {±1,…,±7} × {DIAG_NE_SW, DIAG_NW_SE} = 28.
        self.assertEqual(len(P_bishop(self.origin)), 28)

    def test_queen_size(self):
        # §11.2.4: rook ∪ bishop. The four generator axes are pairwise
        # coprime-independent, so no collision at this range → 56.
        self.assertEqual(len(P_queen(self.origin)), 56)

    def test_king_size(self):
        self.assertEqual(len(P_king(self.origin)), 8)

    def test_knight_size(self):
        self.assertEqual(len(P_knight(self.origin)), 8)


class TestOperatorExcludesOrigin(unittest.TestCase):
    """Per §11.2, no operator includes the origin phase in its output."""

    def setUp(self):
        self.origin = phi(4, 4)

    def test_rook_excludes_origin(self):
        self.assertNotIn(self.origin, P_rook(self.origin))

    def test_bishop_excludes_origin(self):
        self.assertNotIn(self.origin, P_bishop(self.origin))

    def test_queen_excludes_origin(self):
        self.assertNotIn(self.origin, P_queen(self.origin))

    def test_king_excludes_origin(self):
        self.assertNotIn(self.origin, P_king(self.origin))

    def test_knight_excludes_origin(self):
        self.assertNotIn(self.origin, P_knight(self.origin))

    def test_pawn_white_excludes_origin(self):
        p = P_pawn_white(self.origin, on_starting_rank=True,
                         include_captures=True)
        self.assertNotIn(self.origin, p)

    def test_pawn_black_excludes_origin(self):
        p = P_pawn_black(self.origin, on_starting_rank=True,
                         include_captures=True)
        self.assertNotIn(self.origin, p)


class TestInversion(unittest.TestCase):
    """§11.3.2/§11.3.3 — PHI_TO_RC lookup + worked-example boundary clip."""

    def test_inversion_table_size(self):
        self.assertEqual(len(PHI_TO_RC), 64)
        self.assertEqual(len(RC_TO_PHI), 64)

    def test_inversion_round_trip(self):
        for r in range(8):
            for c in range(8):
                self.assertEqual(invert(phi(r, c)), (r, c))

    def test_invert_returns_none_off_image(self):
        # The 64 board phases are sparse in Z_640; most residues are holes.
        board_phases = {phi(r, c) for r in range(8) for c in range(8)}
        for p in range(MODULUS):
            if p not in board_phases:
                self.assertIsNone(invert(p))

    def test_rook_from_00_seven_rows_inverts_to_70(self):
        # §11.3.3: (phi(0,0) + 7*67) % 640 == 469 == phi(7,0).
        self.assertEqual(invert(469), (7, 0))

    def test_rook_from_70_one_row_inverts_to_none(self):
        # §11.3.3: (phi(7,0) + 67) % 640 == 536 is off the 64-image.
        self.assertIsNone(invert(536))


class TestBoardLevelOperatorSizes(unittest.TestCase):
    """Post-clip board-level destination counts from interior square (4, 4).

    These are the counts the supplement quotes in prose: rook reaches 14
    squares, bishop reaches 13, queen reaches 27 from (4, 4).
    """

    def setUp(self):
        self.origin = phi(4, 4)

    def test_rook_board_size(self):
        self.assertEqual(len(phase_set_to_board(P_rook(self.origin))), 14)

    def test_bishop_board_size(self):
        self.assertEqual(len(phase_set_to_board(P_bishop(self.origin))), 13)

    def test_queen_board_size(self):
        self.assertEqual(len(phase_set_to_board(P_queen(self.origin))), 27)


class TestPawnShapes(unittest.TestCase):
    """Pawn operator cardinality per §11.2 pawn rules."""

    def test_white_one_step_no_capture(self):
        p = P_pawn_white(phi(3, 4), on_starting_rank=False,
                         include_captures=False)
        self.assertEqual(len(p), 1)

    def test_white_starting_rank_no_capture(self):
        p = P_pawn_white(phi(1, 4), on_starting_rank=True,
                         include_captures=False)
        self.assertEqual(len(p), 2)

    def test_white_with_captures(self):
        p = P_pawn_white(phi(3, 4), on_starting_rank=False,
                         include_captures=True)
        self.assertEqual(len(p), 3)  # 1 advance + 2 captures

    def test_black_starting_rank_with_captures(self):
        p = P_pawn_black(phi(6, 4), on_starting_rank=True,
                         include_captures=True)
        self.assertEqual(len(p), 4)  # 2 advances + 2 captures


if __name__ == "__main__":
    unittest.main()
