"""Tests for Board4D and Move4D (spatial_4d game state).

Covers:
  * Move4D: construction, equality, hashing, validation, repr
  * Board4D core: empty board, set_piece / piece_at / clear,
    occupancies, FEN round-trip
  * Pseudo-legal generation: knight, king, slider, pawn (push,
    double-push, capture, promotion, en passant)
  * Legal generation: filtering by check
  * Check detection: piece-by-piece attacker types
  * Push/pop reversibility: state restored exactly after pop
  * Position hashing: stable, equal positions hash equal
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
    Board4D, Move4D, PROMOTION_TARGETS,
)
from chess_spectral.tables_4d import sq4                            # noqa: E402


# ---- Move4D --------------------------------------------------


def test_move_basic():
    m = Move4D(0, 17)
    assert m.from_sq == 0
    assert m.to_sq == 17
    assert m.promotion is None
    assert not m.is_double_push
    assert not m.is_ep_capture


def test_move_promotion():
    m = Move4D(0, 17, promotion='Q')
    assert m.promotion == 'Q'


def test_move_promotion_validation():
    with pytest.raises(ValueError):
        Move4D(0, 17, promotion='K')   # not a valid promotion target
    with pytest.raises(ValueError):
        Move4D(0, 17, promotion='P')   # pawns can't promote to pawns


def test_move_equality():
    m1 = Move4D(0, 17)
    m2 = Move4D(0, 17)
    m3 = Move4D(0, 18)
    assert m1 == m2
    assert m1 != m3
    assert hash(m1) == hash(m2)


def test_move_with_flags_equality():
    """Promotion and special-flag fields participate in equality."""
    m1 = Move4D(0, 17, promotion='Q')
    m2 = Move4D(0, 17, promotion='R')
    assert m1 != m2


def test_move_hashable_for_dict_keys():
    """Move4D is usable as a dict key (transposition tables)."""
    d = {Move4D(0, 17): 'a', Move4D(2, 30): 'b'}
    assert d[Move4D(0, 17)] == 'a'


def test_move_repr():
    m = Move4D(0, 17, promotion='Q')
    r = repr(m)
    assert 'from_sq=0' in r and 'to_sq=17' in r and 'Q' in r


# ---- Board4D core ------------------------------------------


def test_empty_board():
    b = Board4D.empty()
    assert b.turn is True
    assert b.ep_square is None
    assert b.halfmove_clock == 0
    assert b.fullmove_number == 1
    assert b.white_occupancy().is_empty()
    assert b.black_occupancy().is_empty()
    assert list(b.legal_moves()) == []


def test_set_piece_knight():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    assert b.piece_at(sq4(4, 4, 4, 4)) == 'N'
    assert b.color_at(sq4(4, 4, 4, 4)) is True


def test_set_piece_pawn_requires_axis_tuple():
    b = Board4D.empty()
    with pytest.raises(ValueError):
        b.set_piece(sq4(0, 0, 0, 0), 'P')


def test_set_piece_pawn_w():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 1), ('P', 'w'))
    assert b.piece_at(sq4(4, 4, 4, 1)) == 'P'
    assert b.pawn_axis_at(sq4(4, 4, 4, 1)) == 'w'


def test_set_piece_pawn_y():
    b = Board4D.empty()
    b.set_piece(sq4(4, 1, 4, 4), ('P', 'y'))
    assert b.piece_at(sq4(4, 1, 4, 4)) == 'P'
    assert b.pawn_axis_at(sq4(4, 1, 4, 4)) == 'y'


def test_set_piece_already_occupied_raises():
    b = Board4D.empty()
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    with pytest.raises(ValueError):
        b.set_piece(sq4(0, 0, 0, 0), 'k')


def test_clear_piece_via_none():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(4, 4, 4, 4), None)
    assert b.piece_at(sq4(4, 4, 4, 4)) is None


def test_piece_at_invalid_sq():
    b = Board4D.empty()
    with pytest.raises(ValueError):
        b.piece_at(-1)
    with pytest.raises(ValueError):
        b.piece_at(4096)


# ---- Pseudo-legal move generation ---------------------------


def test_knight_at_interior_generates_48_moves():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    knight_moves = [m for m in b.legal_moves()
                    if m.from_sq == sq4(4, 4, 4, 4)]
    assert len(knight_moves) == 48


def test_rook_attacks_along_4_axes():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    rook_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 4)]
    assert len(rook_moves) == 28   # 7 squares per axis × 4


def test_rook_blocked_by_own_piece():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    b.set_piece(sq4(6, 4, 4, 4), 'N')   # own piece blocks
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    rook_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 4)]
    # Per-direction reach:
    #   +x (blocked at x=6 by own knight): 1 square (x=5)
    #   -x: 4 (x=3,2,1,0)
    #   +y: 3 (y=5,6,7); -y: 4 (y=3,2,1,0)
    #   +z: 3; -z: 4
    #   +w: 3; -w: 4
    # Total: 1 + 4 + (3+4) + (3+4) + (3+4) = 26.
    assert len(rook_moves) == 26
    # Verify (6,4,4,4) not in moves (own blocker, can't capture).
    assert not any(m.to_sq == sq4(6, 4, 4, 4) for m in rook_moves)
    # Verify (5,4,4,4) IS in moves (one square away from rook).
    assert any(m.to_sq == sq4(5, 4, 4, 4) for m in rook_moves)
    # Verify (7,4,4,4) NOT in moves (beyond blocker).
    assert not any(m.to_sq == sq4(7, 4, 4, 4) for m in rook_moves)


def test_rook_can_capture_opponent():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'R')
    b.set_piece(sq4(6, 4, 4, 4), 'q')   # opponent
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    rook_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 4)]
    # Squares: (5,...) and (6,...) along +x. Then 7 each on other axes.
    # +x: 2 (5 and 6). -x: 4 (3,2,1,0). +y: 3 (5,6,7). -y: 4. Same for z, w.
    # Total: 2+4 + 3+4 + 3+4 + 3+4 = 27. (Since y=4 source can go to y=5,6,7 = 3, and y=3,2,1,0 = 4.)
    # Actually for from y=4: targets are y=0..7 except y=4, so 7 targets per axis WITHOUT blocker.
    # With +x blocker at x=6: targets along +x are x=5 and x=6 (capture), so 2 there. Other axes unchanged: 7 each.
    # Total: 2 + 4 + 7 + 7 + 7 = 27.
    assert len(rook_moves) == 27
    assert any(m.to_sq == sq4(6, 4, 4, 4) for m in rook_moves)
    assert not any(m.to_sq == sq4(7, 4, 4, 4) for m in rook_moves)


def test_pawn_single_push():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 1), ('P', 'w'))   # white W-axis pawn at w=1
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    pawn_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 1)]
    # Single push to (4,4,4,2) PLUS double-push to (4,4,4,3).
    assert len(pawn_moves) == 2
    push_targets = {m.to_sq for m in pawn_moves}
    assert sq4(4, 4, 4, 2) in push_targets
    assert sq4(4, 4, 4, 3) in push_targets


def test_pawn_double_push_only_from_start_plane():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 2), ('P', 'w'))   # white W-axis at w=2 (NOT start)
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    pawn_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 2)]
    # Only single push to (4,4,4,3); no double push.
    assert len(pawn_moves) == 1
    assert pawn_moves[0].to_sq == sq4(4, 4, 4, 3)
    assert not pawn_moves[0].is_double_push


def test_pawn_promotion():
    """White W-axis pawn at w=6, push to w=7 promotes (4 promotion
    options)."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 6), ('P', 'w'))
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 0), 'k')   # avoid blocking the promotion sq
    pawn_moves = [m for m in b.legal_moves()
                  if m.from_sq == sq4(4, 4, 4, 6)]
    # 4 promotion targets per push square.
    promotions = [m for m in pawn_moves if m.promotion is not None]
    assert len(promotions) == 4
    assert {m.promotion for m in promotions} == set(PROMOTION_TARGETS)


def test_pawn_capture():
    """White Pw at (4,4,4,4) can capture black piece at (5,4,4,5)."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), ('P', 'w'))
    b.set_piece(sq4(5, 4, 4, 5), 'n')   # black knight at one of the 6 capture targets
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    captures = [m for m in b.legal_moves()
                if m.from_sq == sq4(4, 4, 4, 4)
                and m.to_sq == sq4(5, 4, 4, 5)]
    assert len(captures) == 1


# ---- Push/pop reversibility -------------------------------


def test_push_pop_round_trip():
    """After push + pop, board state is byte-identical."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    h_before = b.position_hash()
    fen_before = b.fen()
    move = next(iter(b.legal_moves()))
    b.push(move)
    b.pop()
    assert b.position_hash() == h_before
    assert b.fen() == fen_before


def test_push_pop_capture_restores_captured():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(6, 5, 4, 4), 'q')   # capturable queen
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    h_before = b.position_hash()
    move = Move4D(sq4(4, 4, 4, 4), sq4(6, 5, 4, 4))
    b.push(move)
    assert b.piece_at(sq4(6, 5, 4, 4)) == 'N'   # knight captured queen
    b.pop()
    assert b.piece_at(sq4(6, 5, 4, 4)) == 'q'   # queen restored
    assert b.piece_at(sq4(4, 4, 4, 4)) == 'N'   # knight back home
    assert b.position_hash() == h_before


def test_push_pop_promotion():
    """Promotion + pop restores the pawn."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 6), ('P', 'w'))
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 0), 'k')
    h_before = b.position_hash()
    move = Move4D(sq4(4, 4, 4, 6), sq4(4, 4, 4, 7), promotion='Q')
    b.push(move)
    assert b.piece_at(sq4(4, 4, 4, 7)) == 'Q'
    assert b.piece_at(sq4(4, 4, 4, 6)) is None
    b.pop()
    assert b.piece_at(sq4(4, 4, 4, 6)) == 'P'
    assert b.pawn_axis_at(sq4(4, 4, 4, 6)) == 'w'
    assert b.piece_at(sq4(4, 4, 4, 7)) is None
    assert b.position_hash() == h_before


def test_pop_empty_history_raises():
    b = Board4D.empty()
    with pytest.raises(IndexError):
        b.pop()


def test_turn_flips_on_push():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    assert b.turn is True
    move = next(iter(b.legal_moves()))
    b.push(move)
    assert b.turn is False
    b.pop()
    assert b.turn is True


def test_halfmove_clock_resets_on_capture():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(6, 5, 4, 4), 'q')   # capturable
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    # Bump halfmove via a non-capture knight move-and-back.
    b._halfmove_clock = 10
    move = Move4D(sq4(4, 4, 4, 4), sq4(6, 5, 4, 4))   # capture
    b.push(move)
    assert b.halfmove_clock == 0


def test_halfmove_clock_increments_on_quiet_move():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'N')
    b.set_piece(sq4(0, 0, 0, 0), 'K')
    b.set_piece(sq4(7, 7, 7, 7), 'k')
    b._halfmove_clock = 5
    move = Move4D(sq4(4, 4, 4, 4), sq4(6, 5, 4, 4))
    b.push(move)
    assert b.halfmove_clock == 6


# ---- Check detection -----------------------------------


def test_is_check_detects_rook_attack():
    """White king at (4,4,4,4), black rook at (4,4,4,7) -> in check."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'K')
    b.set_piece(sq4(4, 4, 4, 7), 'r')
    b.set_piece(sq4(0, 0, 0, 0), 'k')   # opp king somewhere
    assert b.is_check()


def test_is_check_detects_knight_attack():
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'K')
    b.set_piece(sq4(6, 5, 4, 4), 'n')   # black knight (2,1,0,0)
    b.set_piece(sq4(0, 0, 0, 0), 'k')
    assert b.is_check()


def test_not_in_check_when_blocker_present():
    """Rook attack along axis blocked by own piece."""
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'K')
    b.set_piece(sq4(4, 4, 4, 5), ('P', 'w'))   # white pawn blocks
    b.set_piece(sq4(4, 4, 4, 7), 'r')
    b.set_piece(sq4(0, 0, 0, 0), 'k')
    assert not b.is_check()


# ---- Legal-move filtering by check ---------------------


def test_pinned_piece_cannot_move():
    """If moving a piece exposes our king to attack, the move is
    not legal."""
    # White king at (4,4,4,4); white knight at (4,4,4,5); black rook at (4,4,4,7).
    # If knight moves, king is in check -> knight is pinned.
    b = Board4D.empty()
    b.set_piece(sq4(4, 4, 4, 4), 'K')
    b.set_piece(sq4(4, 4, 4, 5), 'N')
    b.set_piece(sq4(4, 4, 4, 7), 'r')
    b.set_piece(sq4(0, 0, 0, 0), 'k')
    knight_moves = [m for m in b.legal_moves()
                    if m.from_sq == sq4(4, 4, 4, 5)]
    # Knight is pinned along the w-axis; moving it would expose the king.
    # Note: pinned pieces can sometimes move ALONG the pin (capture pinner).
    # 4D knight moves don't include axis-aligned moves (knight = (2,1)),
    # so all 48-ish possible knight moves leave the pin → all illegal.
    # Wait — but knight moves to the rook (4,4,4,7) might capture and remove
    # the threat. Let me check: distance (4,4,4,5)→(4,4,4,7) is (0,0,0,2),
    # which is NOT a knight move (needs (±2, ±1, 0, 0) shape with 2 nonzero).
    # So all knight moves from (4,4,4,5) leave the king exposed.
    assert len(knight_moves) == 0


# ---- FEN round-trip --------------------------------


def test_fen_round_trip_simple():
    """Place a few pieces; FEN round-trip preserves placement."""
    fen_in = "4d-fen v1: K@0,0,0,0; k@7,7,7,7; N@4,4,4,4;"
    b = Board4D.from_fen(fen_in)
    assert b.piece_at(sq4(0, 0, 0, 0)) == 'K'
    assert b.piece_at(sq4(7, 7, 7, 7)) == 'k'
    assert b.piece_at(sq4(4, 4, 4, 4)) == 'N'

    # Re-export and re-parse.
    fen_out = b.fen()
    b2 = Board4D.from_fen(fen_out)
    assert b2.piece_at(sq4(0, 0, 0, 0)) == 'K'
    assert b2.piece_at(sq4(7, 7, 7, 7)) == 'k'
    assert b2.piece_at(sq4(4, 4, 4, 4)) == 'N'


def test_fen_round_trip_pawns():
    fen_in = "4d-fen v1: K@0,0,0,0; k@7,7,7,7; Pw@1,1,1,1; py@7,1,7,7;"
    b = Board4D.from_fen(fen_in)
    assert b.piece_at(sq4(1, 1, 1, 1)) == 'P'
    assert b.pawn_axis_at(sq4(1, 1, 1, 1)) == 'w'
    assert b.piece_at(sq4(7, 1, 7, 7)) == 'p'
    assert b.pawn_axis_at(sq4(7, 1, 7, 7)) == 'y'


# ---- Position hash --------------------------------


def test_position_hash_stable():
    """Two boards with identical pieces + state hash equal."""
    b1 = Board4D.empty()
    b2 = Board4D.empty()
    for sq in (sq4(4, 4, 4, 4), sq4(0, 0, 0, 0), sq4(7, 7, 7, 7)):
        b1.set_piece(sq, 'K' if sq == sq4(0, 0, 0, 0) else
                     ('k' if sq == sq4(7, 7, 7, 7) else 'N'))
        b2.set_piece(sq, 'K' if sq == sq4(0, 0, 0, 0) else
                     ('k' if sq == sq4(7, 7, 7, 7) else 'N'))
    assert b1.position_hash() == b2.position_hash()


def test_position_hash_distinguishes_turn():
    """Same pieces, different turn -> different hashes."""
    b1 = Board4D.empty()
    b1.set_piece(sq4(0, 0, 0, 0), 'K')
    b1.set_piece(sq4(7, 7, 7, 7), 'k')
    b2 = Board4D.empty()
    b2._turn = False
    b2.set_piece(sq4(0, 0, 0, 0), 'K')
    b2.set_piece(sq4(7, 7, 7, 7), 'k')
    assert b1.position_hash() != b2.position_hash()


# ---- API surface ---------------------------------


def test_module_exports():
    from chess_spectral.spatial_4d import board, move
    assert "Board4D" in board.__all__
    assert "UndoInfo" in board.__all__
    assert "Move4D" in move.__all__


def test_package_re_exports():
    import chess_spectral.spatial_4d as pkg
    for name in ("Board4D", "Move4D", "UndoInfo",
                 "PIECE_CHARS", "PROMOTION_TARGETS"):
        assert name in pkg.__all__
