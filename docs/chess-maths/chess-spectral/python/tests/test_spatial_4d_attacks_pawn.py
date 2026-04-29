"""Tests for chess_spectral.spatial_4d.attacks_pawn.

4D pawn move tables. Pawns are axis-typed (w/y per Oana-Chiru Def 11);
forward direction depends on (color, axis).

Coverage:
  * Pushes: single forward step on the pawn's axis; empty at the
    forward boundary.
  * Captures: 6 diagonal targets (forward step + ±1 on one of the
    other 3 axes); fewer near boundary.
  * Color symmetry: black pushes are the mirror of white (by sign
    flip on the forward axis).
  * Axis symmetry: 'y' tables are 'w' tables under the y↔w
    coordinate swap (per O&C §3.11 ruleset-preserving symmetry).
  * Push tables match tables_4d.{white_pawn4_targets,
    white_pawn4_y_targets} on every from-square (white side).
  * Edge cases: input validation, source square never in own
    push/attack set, axis must be 'w' or 'y'.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral.spatial_4d import (                            # noqa: E402
    Bitboard4D,
    pawn_pushes_4d, attacks_pawn_4d,
    PAWN_PUSH_W_WHITE, PAWN_PUSH_W_BLACK,
    PAWN_PUSH_Y_WHITE, PAWN_PUSH_Y_BLACK,
    PAWN_ATTACKS_W_WHITE, PAWN_ATTACKS_W_BLACK,
    PAWN_ATTACKS_Y_WHITE, PAWN_ATTACKS_Y_BLACK,
)
from chess_spectral.spatial_4d.bitboard import N_SQUARES           # noqa: E402
from chess_spectral.tables_4d import (                              # noqa: E402
    sq4, white_pawn4_targets, white_pawn4_y_targets,
)


# ---- Push tables: shape -----------------------------------------


@pytest.mark.parametrize('table', [
    PAWN_PUSH_W_WHITE, PAWN_PUSH_W_BLACK,
    PAWN_PUSH_Y_WHITE, PAWN_PUSH_Y_BLACK,
])
def test_push_tables_shape(table):
    """Each push table is 4096 Bitboard4D entries."""
    assert isinstance(table, tuple)
    assert len(table) == N_SQUARES
    for sq in (0, 100, 4095):
        assert isinstance(table[sq], Bitboard4D)


@pytest.mark.parametrize('table', [
    PAWN_ATTACKS_W_WHITE, PAWN_ATTACKS_W_BLACK,
    PAWN_ATTACKS_Y_WHITE, PAWN_ATTACKS_Y_BLACK,
])
def test_attack_tables_shape(table):
    assert isinstance(table, tuple)
    assert len(table) == N_SQUARES


# ---- Push semantics --------------------------------------------


def test_white_w_push_advances_w_axis_by_one():
    """White Pw at (4,4,4,4) pushes to (4,4,4,5)."""
    sq = sq4(4, 4, 4, 4)
    targets = pawn_pushes_4d(sq, 'w', True).to_squares()
    assert targets == [sq4(4, 4, 4, 5)]


def test_white_y_push_advances_y_axis_by_one():
    sq = sq4(4, 4, 4, 4)
    targets = pawn_pushes_4d(sq, 'y', True).to_squares()
    assert targets == [sq4(4, 5, 4, 4)]


def test_black_w_push_decrements_w_axis():
    sq = sq4(4, 4, 4, 4)
    targets = pawn_pushes_4d(sq, 'w', False).to_squares()
    assert targets == [sq4(4, 4, 4, 3)]


def test_black_y_push_decrements_y_axis():
    sq = sq4(4, 4, 4, 4)
    targets = pawn_pushes_4d(sq, 'y', False).to_squares()
    assert targets == [sq4(4, 3, 4, 4)]


def test_white_w_push_at_forward_boundary_empty():
    """White Pw at w=7 (already at far end) cannot push."""
    sq = sq4(4, 4, 4, 7)
    assert pawn_pushes_4d(sq, 'w', True).is_empty()


def test_black_w_push_at_backward_boundary_empty():
    """Black pw at w=0 cannot push (forward = -w)."""
    sq = sq4(4, 4, 4, 0)
    assert pawn_pushes_4d(sq, 'w', False).is_empty()


def test_white_y_push_at_y_boundary_empty():
    sq = sq4(4, 7, 4, 4)
    assert pawn_pushes_4d(sq, 'y', True).is_empty()


# ---- Push parity vs tables_4d ----------------------------------


def test_white_w_push_table_matches_tables_4d():
    """White Pw push table matches tables_4d.white_pawn4_targets on
    every from-square."""
    for s in range(N_SQUARES):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        expected = frozenset(sq4(*t) for t in white_pawn4_targets(x, y, z, w))
        actual = frozenset(PAWN_PUSH_W_WHITE[s].to_squares())
        assert expected == actual, (
            f"white-Pw push @ s={s}: expected {expected} vs actual {actual}"
        )


def test_white_y_push_table_matches_tables_4d():
    for s in range(N_SQUARES):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        expected = frozenset(sq4(*t) for t in white_pawn4_y_targets(x, y, z, w))
        actual = frozenset(PAWN_PUSH_Y_WHITE[s].to_squares())
        assert expected == actual, (
            f"white-Py push @ s={s}: mismatch"
        )


# ---- Color symmetry --------------------------------------------


def test_black_w_push_is_white_w_push_with_inverted_w():
    """Black Pw push at (x,y,z,w) = white Pw push at (x,y,z,7-w)
    after re-inverting w."""
    for s in range(0, N_SQUARES, 17):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        s_inv = sq4(x, y, z, 7 - w)
        white_targets = PAWN_PUSH_W_WHITE[s_inv].to_squares()
        black_targets = PAWN_PUSH_W_BLACK[s].to_squares()
        # Each white target (x,y,z,7-w + 1) should map to
        # (x,y,z,7-(7-w+1)) = (x,y,z,w-1) which is the black push.
        white_inverted = []
        for t in white_targets:
            tx, ty, tz, tw = t // 512, (t // 64) % 8, (t // 8) % 8, t % 8
            white_inverted.append(sq4(tx, ty, tz, 7 - tw))
        assert sorted(white_inverted) == sorted(black_targets)


# ---- Capture semantics -----------------------------------------


def test_white_w_captures_count_at_interior():
    """White Pw at deep interior reaches 6 capture targets:
    forward step on +w + ±1 on one of {x, y, z} = 3 axes × 2 signs."""
    sq = sq4(4, 4, 4, 4)
    bb = attacks_pawn_4d(sq, 'w', True)
    assert bb.popcount() == 6


def test_white_w_captures_at_corner():
    """White Pw at (0,0,0,0): forward = +w, so target w-coord = 1.
    Other axes ±1: only +1 in each of x,y,z is in-bounds (-1 not).
    Expect 3 targets: (1,0,0,1), (0,1,0,1), (0,0,1,1)."""
    sq = sq4(0, 0, 0, 0)
    bb = attacks_pawn_4d(sq, 'w', True)
    assert bb.popcount() == 3
    assert sq4(1, 0, 0, 1) in bb
    assert sq4(0, 1, 0, 1) in bb
    assert sq4(0, 0, 1, 1) in bb


def test_white_w_captures_at_forward_edge_empty():
    """White Pw at w=7: no forward squares exist, captures empty."""
    sq = sq4(4, 4, 4, 7)
    assert attacks_pawn_4d(sq, 'w', True).is_empty()


def test_black_w_captures_at_w7_has_3_targets():
    """Black pw at (0,0,0,7): forward = -w, target w=6.
    Other axes ±1: only +1 valid. Targets: (1,0,0,6), (0,1,0,6),
    (0,0,1,6). Expect 3."""
    sq = sq4(0, 0, 0, 7)
    bb = attacks_pawn_4d(sq, 'w', False)
    assert bb.popcount() == 3
    assert sq4(1, 0, 0, 6) in bb


def test_white_y_captures_count_at_interior():
    """White Py at deep interior: 6 captures (forward = +y, plus ±1
    on one of {x, z, w})."""
    sq = sq4(4, 4, 4, 4)
    bb = attacks_pawn_4d(sq, 'y', True)
    assert bb.popcount() == 6


def test_pawn_capture_does_not_include_self():
    for axis in ('w', 'y'):
        for color in (True, False):
            for coord in [(4, 4, 4, 4), (0, 0, 0, 0), (1, 2, 3, 4)]:
                sq = sq4(*coord)
                bb = attacks_pawn_4d(sq, axis, color)
                assert sq not in bb


def test_pawn_push_does_not_include_self():
    for axis in ('w', 'y'):
        for color in (True, False):
            for coord in [(4, 4, 4, 4), (0, 0, 0, 0), (1, 2, 3, 4)]:
                sq = sq4(*coord)
                bb = pawn_pushes_4d(sq, axis, color)
                assert sq not in bb


# ---- Capture rule structure ------------------------------------


def test_capture_targets_advance_forward_axis():
    """Every white-Pw capture target has w-coord = source_w + 1."""
    for s in range(0, N_SQUARES, 17):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        bb = attacks_pawn_4d(s, 'w', True)
        for t in bb.to_squares():
            tw = t % 8
            assert tw == w + 1, (
                f"white-Pw capture target {t} from {s}: "
                f"expected w+1={w+1}, got {tw}"
            )


def test_capture_targets_change_exactly_two_coords():
    """White Pw capture target differs from source in exactly 2
    coords: w (always +1) and one of x/y/z (±1)."""
    for s in range(0, N_SQUARES, 31):
        x, y, z, w = s // 512, (s // 64) % 8, (s // 8) % 8, s % 8
        bb = attacks_pawn_4d(s, 'w', True)
        for t in bb.to_squares():
            tx, ty, tz, tw = t // 512, (t // 64) % 8, (t // 8) % 8, t % 8
            n_changed = sum(int(a != b) for a, b in
                            ((tx, x), (ty, y), (tz, z), (tw, w)))
            assert n_changed == 2, (
                f"white-Pw capture from {s} to {t}: changed "
                f"{n_changed} coords, expected 2"
            )


# ---- API edge cases --------------------------------------------


def test_invalid_square_raises():
    with pytest.raises(ValueError):
        pawn_pushes_4d(-1, 'w', True)
    with pytest.raises(ValueError):
        pawn_pushes_4d(N_SQUARES, 'w', True)
    with pytest.raises(ValueError):
        attacks_pawn_4d(-1, 'y', False)


def test_invalid_axis_raises():
    with pytest.raises(ValueError):
        pawn_pushes_4d(0, 'x', True)
    with pytest.raises(ValueError):
        pawn_pushes_4d(0, 'z', True)
    with pytest.raises(ValueError):
        attacks_pawn_4d(0, 'q', True)


def test_color_must_be_bool():
    """Non-bool color is a type error (e.g. accidentally passing
    1 or 'white' instead of True)."""
    with pytest.raises(TypeError):
        pawn_pushes_4d(0, 'w', 1)
    with pytest.raises(TypeError):
        attacks_pawn_4d(0, 'w', 'white')


# ---- API surface ----------------------------------------------


def test_module_exports():
    from chess_spectral.spatial_4d import attacks_pawn
    for name in ('pawn_pushes_4d', 'attacks_pawn_4d',
                 'PAWN_PUSH_W_WHITE', 'PAWN_PUSH_W_BLACK',
                 'PAWN_PUSH_Y_WHITE', 'PAWN_PUSH_Y_BLACK',
                 'PAWN_ATTACKS_W_WHITE', 'PAWN_ATTACKS_W_BLACK',
                 'PAWN_ATTACKS_Y_WHITE', 'PAWN_ATTACKS_Y_BLACK'):
        assert name in attacks_pawn.__all__


def test_package_re_exports():
    """Top-level chess_spectral.spatial_4d re-exports the pawn API."""
    import chess_spectral.spatial_4d as pkg
    for name in ('pawn_pushes_4d', 'attacks_pawn_4d'):
        assert name in pkg.__all__
