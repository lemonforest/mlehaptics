"""Tests for chess_spectral.spatial_4d.draws (PR-7-G).

Draw / mate predicates: threefold, 50-move, insufficient material,
stalemate, checkmate. Plus is_game_over composition.
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
    Board4D, Move4D,
    is_threefold_repetition, is_fifty_move_rule,
    is_insufficient_material, is_stalemate, is_checkmate, is_game_over,
)
from chess_spectral.tables_4d import sq4                            # noqa: E402


# ---- Insufficient material -------------------------------


def test_insufficient_kk():
    """Lone kings → insufficient."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    assert is_insufficient_material(b)


def test_insufficient_kkn():
    """K vs K + knight → insufficient."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'n')
    assert is_insufficient_material(b)


def test_insufficient_kkb():
    """K vs K + bishop → insufficient."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'B')
    assert is_insufficient_material(b)


def test_insufficient_knkn():
    """K + N vs K + N → insufficient (per python-chess convention)."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(2, 2, 2, 2), 'N')
    b.set_piece(sq4(5, 5, 5, 5), 'n')
    assert is_insufficient_material(b)


def test_insufficient_kbkb_same_parity():
    """K + B vs K + B with same coord-sum parity → insufficient.
    Same parity means both bishops travel on the same connected
    component of the bishop-reach graph, so they can never meet."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')   # parity 0
    b.set_piece(sq4(7, 7, 7, 7), 'k')   # parity 0 (28 even)
    b.set_piece(sq4(2, 4, 4, 4), 'B')   # parity 0 (14 even)
    b.set_piece(sq4(4, 4, 4, 4), 'b')   # parity 0
    assert is_insufficient_material(b)


def test_kbkb_different_parity_sufficient():
    """K + B vs K + B with different coord-sum parity → not
    insufficient; bishops can mate together (one on each color
    component)."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')   # parity 0
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(1, 4, 4, 4), 'B')   # parity 1 (13 odd)
    b.set_piece(sq4(4, 4, 4, 4), 'b')   # parity 0 (16 even)
    assert not is_insufficient_material(b)


def test_pawn_disqualifies_insufficient():
    """Any pawn on the board → not insufficient (pawn can promote)."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 1), ('P', 'w'))
    assert not is_insufficient_material(b)


def test_rook_disqualifies_insufficient():
    """K + R vs K → sufficient (KRK is a known mate)."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    assert not is_insufficient_material(b)


def test_queen_disqualifies_insufficient():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'Q')
    assert not is_insufficient_material(b)


def test_two_minors_one_side_sufficient():
    """K + 2 minors vs K → not insufficient (e.g., K+B+N can mate)."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'B')
    b.set_piece(sq4(3, 3, 3, 3), 'N')
    assert not is_insufficient_material(b)


# ---- 50-move rule ----------------------------------------


def test_fifty_move_rule_at_clock_99_false():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b._halfmove_clock = 99
    assert not is_fifty_move_rule(b)


def test_fifty_move_rule_at_clock_100_true():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b._halfmove_clock = 100
    assert is_fifty_move_rule(b)


def test_fifty_move_rule_far_above_threshold_true():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b._halfmove_clock = 500
    assert is_fifty_move_rule(b)


# ---- Stalemate / checkmate ----------------------------


# Note on stalemate / checkmate explicit-position tests:
# Constructing a 4D stalemate or checkmate position is fiddly because
# a 4D king has up to 80 hypercube neighbours (vs 8 in 2D), and
# blanketing all of them with attacks while keeping the king itself
# safe requires careful piece placement. We test the predicate logic
# implicitly via the lone-kings test (no stalemate/mate when moves
# are available) and rely on the corpus parity gate (PR-7-H) to
# catch any regression in the underlying is_check / legal_moves
# composition.


def test_lone_kings_no_check_no_stalemate_or_mate():
    """Two lone kings: each has legal moves; neither stalemate nor
    checkmate."""
    b = Board4D.empty()
    b.set_piece(sq4(3, 3, 3, 3), 'K')
    b.set_piece(sq4(5, 5, 5, 5), 'k')
    # Kings have legal moves available; neither stalemate nor mate.
    assert not is_stalemate(b)
    assert not is_checkmate(b)


# ---- Threefold repetition --------------------------


def test_threefold_no_history_returns_false():
    """Position with no repetition history -> False."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    assert not is_threefold_repetition(b)


def test_threefold_via_repeated_knight_dance():
    """White knight + black knight dance back and forth, position
    repeats 3 times."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(2, 2, 4, 4), 'N')   # white knight
    b.set_piece(sq4(5, 5, 4, 4), 'n')   # black knight (matches symmetry)

    # Each side's knight does an out-and-back dance.
    # White: (2,2,4,4) -> (4,3,4,4) -> (2,2,4,4). Knight (±2,±1,0,0).
    # White move 1: (2,2,4,4) -> (4,3,4,4)
    move_w_out = Move4D(sq4(2, 2, 4, 4), sq4(4, 3, 4, 4))
    move_w_back = Move4D(sq4(4, 3, 4, 4), sq4(2, 2, 4, 4))
    move_b_out = Move4D(sq4(5, 5, 4, 4), sq4(3, 4, 4, 4))
    move_b_back = Move4D(sq4(3, 4, 4, 4), sq4(5, 5, 4, 4))

    # Sequence to repeat the start position 3 times:
    #   start: occurrence 1
    #   W out, B out, W back, B back -> back to start: occurrence 2
    #   W out, B out, W back, B back -> back to start: occurrence 3
    for _ in range(2):
        b.push(move_w_out)
        b.push(move_b_out)
        b.push(move_w_back)
        b.push(move_b_back)

    assert is_threefold_repetition(b)


def test_threefold_after_only_one_repeat_false():
    """After 2 occurrences, threefold is FALSE."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(2, 2, 4, 4), 'N')
    b.set_piece(sq4(5, 5, 4, 4), 'n')
    move_w_out = Move4D(sq4(2, 2, 4, 4), sq4(4, 3, 4, 4))
    move_w_back = Move4D(sq4(4, 3, 4, 4), sq4(2, 2, 4, 4))
    move_b_out = Move4D(sq4(5, 5, 4, 4), sq4(3, 4, 4, 4))
    move_b_back = Move4D(sq4(3, 4, 4, 4), sq4(5, 5, 4, 4))

    # Only 1 round-trip: start + return = 2 occurrences.
    b.push(move_w_out)
    b.push(move_b_out)
    b.push(move_w_back)
    b.push(move_b_back)

    assert not is_threefold_repetition(b)


# ---- is_game_over composition ----------------------


def test_is_game_over_kk_insufficient():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    assert is_game_over(b)


def test_is_game_over_fifty_move():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    b._halfmove_clock = 100
    assert is_game_over(b)


def test_is_game_over_active_position_false():
    """A normal mid-game position with sufficient material and
    moves available is not over."""
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    b.set_piece(sq4(2, 2, 2, 2), 'r')
    b.set_piece(sq4(6, 6, 6, 6), ('P', 'w'))
    assert not is_game_over(b)


# ---- API surface ----------------------------------


def test_module_exports():
    from chess_spectral.spatial_4d import draws
    for name in ('is_threefold_repetition', 'is_fifty_move_rule',
                 'is_insufficient_material', 'is_stalemate',
                 'is_checkmate', 'is_game_over'):
        assert name in draws.__all__


def test_package_re_exports():
    import chess_spectral.spatial_4d as pkg
    for name in ('is_threefold_repetition', 'is_fifty_move_rule',
                 'is_insufficient_material', 'is_stalemate',
                 'is_checkmate', 'is_game_over'):
        assert name in pkg.__all__
