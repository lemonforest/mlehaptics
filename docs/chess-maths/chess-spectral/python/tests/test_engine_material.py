"""Unit tests for the material evaluators (Phase 6 PR-2).

Covers both :mod:`chess_spectral.engine.eval.material` (2D) and
:mod:`chess_spectral_4d.engine.eval.material` (4D). Same test
patterns at both dimensions:

  * Empty position scores 0
  * Standard starting position scores 0 (perfectly balanced)
  * Material balance flips correctly under side_to_move
  * Lopsided positions score in the right direction and magnitude
  * Custom value-table dict accepted; unknown table string raises
  * 4D-specific: pawn axis is stripped (Pw and Py value the same)
  * 4D-specific: legacy single-char pawn 'P'/'p' accepted (no warning
    spam)
  * Spectral table differs from standard table on at least one piece
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import fen_to_pos                              # noqa: E402
from chess_spectral.engine.eval import material as material_2d     # noqa: E402
from chess_spectral_4d.engine.eval import material as material_4d  # noqa: E402
from chess_spectral.tables import SPECTRAL_VALS, VALS              # noqa: E402


# ---- 2D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def starting_position_2d():
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )


@pytest.fixture(scope="module")
def white_up_a_queen_2d():
    """White has all 16 pieces; black is missing a queen."""
    return fen_to_pos(
        "rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )


@pytest.fixture(scope="module")
def black_up_a_rook_2d():
    """Black has all 16 pieces; white is missing a rook."""
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBNR w Kkq - 0 1"
    )


# ---- 2D material tests ----------------------------------------------


def test_2d_empty_position_scores_zero():
    """Empty position has no material."""
    assert material_2d.evaluate({}, side_to_move=True) == 0.0
    assert material_2d.evaluate({}, side_to_move=False) == 0.0


def test_2d_starting_position_balanced(starting_position_2d):
    """Standard start: equal material on both sides -> score 0."""
    score = material_2d.evaluate(starting_position_2d, side_to_move=True)
    assert score == 0.0
    score = material_2d.evaluate(starting_position_2d, side_to_move=False)
    assert score == 0.0


def test_2d_white_up_queen_white_to_move(white_up_a_queen_2d):
    """Black is missing a queen; from white's perspective this is +Q."""
    score = material_2d.evaluate(white_up_a_queen_2d, side_to_move=True)
    # SPECTRAL_VALS['Q'] is positive (white queen weight). Float
    # accumulation across 31 pieces loses a few ulps -- use approx.
    assert score == pytest.approx(SPECTRAL_VALS['Q'])
    assert score > 0


def test_2d_white_up_queen_black_to_move(white_up_a_queen_2d):
    """Same lopsided position; from black's perspective material is -Q."""
    score = material_2d.evaluate(white_up_a_queen_2d, side_to_move=False)
    # Black to move; flipping perspective negates the score.
    assert score == pytest.approx(-SPECTRAL_VALS['Q'])
    assert score < 0


def test_2d_black_up_rook(black_up_a_rook_2d):
    """White is missing a rook; black gains."""
    white_pov = material_2d.evaluate(black_up_a_rook_2d,
                                      side_to_move=True)
    # White is missing R: from white's POV, score = -R (white loses).
    assert white_pov == pytest.approx(-SPECTRAL_VALS['R'])
    black_pov = material_2d.evaluate(black_up_a_rook_2d,
                                      side_to_move=False)
    # Black-to-move flips the sign: black sees +R.
    assert black_pov == pytest.approx(SPECTRAL_VALS['R'])


def test_2d_standard_value_table(white_up_a_queen_2d):
    """Switching to standard VALS gives the textbook +9 for the queen."""
    score = material_2d.evaluate(white_up_a_queen_2d,
                                  side_to_move=True,
                                  values='standard')
    assert score == pytest.approx(VALS['Q'])    # textbook 9


def test_2d_custom_value_table_dict(starting_position_2d):
    """Custom dict is taken verbatim; missing pieces score 0."""
    # Score only knights (every other piece -> 0). Both sides have 4
    # knights total (2 each); equal -> 0.
    table = {'N': 1.0, 'n': -1.0}
    score = material_2d.evaluate(starting_position_2d,
                                  side_to_move=True,
                                  values=table)
    assert score == 0.0   # 2 white knights - 2 black knights = 0
    # Lop-side: one black knight removed.
    pos = dict(starting_position_2d)
    # find a black knight (lowercase 'n') and drop it
    for sq, p in list(pos.items()):
        if p == 'n':
            del pos[sq]
            break
    score = material_2d.evaluate(pos, side_to_move=True, values=table)
    assert score == 1.0   # white still up by 1 knight


def test_2d_unknown_table_string_raises():
    """A string outside {'spectral', 'standard'} raises ValueError."""
    with pytest.raises(ValueError):
        material_2d.evaluate({}, side_to_move=True, values='qm')


def test_2d_unknown_piece_in_position_scores_zero():
    """A position containing an unknown piece char scores it as 0
    (rather than crashing). This makes the evaluator robust to
    malformed inputs from upstream pipelines."""
    pos = {0: 'X'}   # not a valid piece char
    score = material_2d.evaluate(pos, side_to_move=True)
    assert score == 0.0


def test_2d_evaluate_white_no_perspective_flip(white_up_a_queen_2d):
    """``evaluate_white`` always returns the score from white's POV."""
    score_white = material_2d.evaluate_white(white_up_a_queen_2d)
    score_default = material_2d.evaluate(white_up_a_queen_2d,
                                          side_to_move=True)
    assert score_white == score_default
    # And it ignores the (absent) side_to_move flag entirely.
    assert score_white == pytest.approx(SPECTRAL_VALS['Q'])


def test_2d_spectral_differs_from_standard():
    """Sanity: SPECTRAL_VALS and VALS aren't identical -- otherwise
    one of the table options would be redundant."""
    diffs = {p: (SPECTRAL_VALS[p], VALS[p])
             for p in 'PNBRQK' if SPECTRAL_VALS[p] != VALS[p]}
    assert len(diffs) > 0, (
        "SPECTRAL_VALS and VALS happen to coincide on all white "
        "pieces -- that would make the spectral evaluator trivially "
        "equivalent to standard. Worth a sanity check on tables.py."
    )


# ---- 4D fixtures ----------------------------------------------------


@pytest.fixture(scope="module")
def empty_4d():
    return {}


@pytest.fixture(scope="module")
def starting_4d():
    """A small 4D fixture: two kings + balanced bishops + one pair of
    pawns on each axis. Material-balanced (even though it's not a
    legal-game position)."""
    return {
        0: 'K',
        4095: 'k',
        100: 'B', 200: 'b',
        1000: ('P', 'w'), 2000: ('p', 'w'),
        1100: ('P', 'y'), 2100: ('p', 'y'),
    }


@pytest.fixture(scope="module")
def white_up_a_queen_4d():
    """White queen, no black queen. Lop-sided +Q for white."""
    return {
        0: 'K',
        4095: 'k',
        500: 'Q',   # white queen
        # no black queen
    }


# ---- 4D material tests ----------------------------------------------


def test_4d_empty_position_scores_zero(empty_4d):
    assert material_4d.evaluate(empty_4d, side_to_move=True) == 0.0


def test_4d_starting_4d_balanced(starting_4d):
    """The fixture is constructed material-symmetric."""
    score = material_4d.evaluate(starting_4d, side_to_move=True)
    assert score == 0.0
    score = material_4d.evaluate(starting_4d, side_to_move=False)
    assert score == 0.0


def test_4d_white_up_queen_white_to_move(white_up_a_queen_4d):
    score = material_4d.evaluate(white_up_a_queen_4d, side_to_move=True)
    assert score == SPECTRAL_VALS['Q']


def test_4d_white_up_queen_black_to_move(white_up_a_queen_4d):
    score = material_4d.evaluate(white_up_a_queen_4d, side_to_move=False)
    assert score == -SPECTRAL_VALS['Q']


def test_4d_pawn_axis_stripped():
    """W-axis pawn and Y-axis pawn have the same material value."""
    pos_w = {100: ('P', 'w')}
    pos_y = {100: ('P', 'y')}
    score_w = material_4d.evaluate(pos_w, side_to_move=True)
    score_y = material_4d.evaluate(pos_y, side_to_move=True)
    assert score_w == score_y == SPECTRAL_VALS['P']


def test_4d_legacy_single_char_pawn_accepted():
    """Legacy single-char 'P' / 'p' values still score correctly."""
    pos = {100: 'P', 200: 'p'}
    score = material_4d.evaluate(pos, side_to_move=True)
    # Equal pawns: balance.
    assert score == 0.0


def test_4d_standard_value_table(white_up_a_queen_4d):
    score = material_4d.evaluate(white_up_a_queen_4d,
                                  side_to_move=True,
                                  values='standard')
    assert score == VALS['Q']


def test_4d_custom_value_table_dict():
    """Custom dict accepted; pawn axis stripped before lookup."""
    table = {'P': 1.0, 'p': -1.0}
    pos = {100: ('P', 'w'), 200: ('P', 'y'), 300: ('p', 'w')}
    score = material_4d.evaluate(pos, side_to_move=True, values=table)
    # 2 white pawns - 1 black pawn = +1 from white's POV.
    assert score == 1.0


def test_4d_unknown_table_string_raises():
    with pytest.raises(ValueError):
        material_4d.evaluate({}, side_to_move=True, values='nonsense')


def test_4d_evaluate_white_no_perspective_flip(white_up_a_queen_4d):
    score_white = material_4d.evaluate_white(white_up_a_queen_4d)
    assert score_white == SPECTRAL_VALS['Q']


# ---- Cross-dim consistency ------------------------------------------


def test_2d_4d_value_table_identical():
    """Both evaluators use the same SPECTRAL_VALS / VALS source. A
    rook is worth the same in 2D and 4D."""
    pos_2d = {0: 'R'}
    pos_4d = {0: 'R'}
    score_2d = material_2d.evaluate(pos_2d, side_to_move=True)
    score_4d = material_4d.evaluate(pos_4d, side_to_move=True)
    assert score_2d == score_4d == SPECTRAL_VALS['R']


def test_2d_4d_side_to_move_flipping_consistent():
    """Flipping side_to_move negates the score in both dimensions."""
    pos_2d = {0: 'Q'}
    pos_4d = {0: 'Q'}
    s_2d_w = material_2d.evaluate(pos_2d, side_to_move=True)
    s_2d_b = material_2d.evaluate(pos_2d, side_to_move=False)
    s_4d_w = material_4d.evaluate(pos_4d, side_to_move=True)
    s_4d_b = material_4d.evaluate(pos_4d, side_to_move=False)
    assert s_2d_b == -s_2d_w
    assert s_4d_b == -s_4d_w
    assert s_2d_w == s_4d_w


# ---- API surface --------------------------------------------------


def test_2d_module_public_api():
    assert 'evaluate' in material_2d.__all__
    assert 'evaluate_white' in material_2d.__all__


def test_4d_module_public_api():
    assert 'evaluate' in material_4d.__all__
    assert 'evaluate_white' in material_4d.__all__


def test_2d_engine_namespace_re_exports():
    """``chess_spectral.engine`` imports succeed without circular
    issues."""
    from chess_spectral import engine
    assert hasattr(engine, 'material')


def test_4d_engine_namespace_re_exports():
    """``chess_spectral_4d.engine`` imports succeed."""
    from chess_spectral_4d import engine
    assert hasattr(engine, 'material')
