"""1.9.0 immolation: non-Markovian sheet aux block.

Tests cover:
  - Default-state aux block has the documented shape + values
  - All four castling rights round-trip independently
  - EP target round-trips for every file 0..7 plus None
  - Halfmove clock round-trips for all integer values [0, 100]
  - Side-to-move flag round-trips both ways
  - Repetition count round-trips for {0, 1, 2}
  - encode_640(pos, sheets=...) returns a 651-dim float64 vector
    with bit-identical first 640 dims to encode_640(pos)
  - encode_4d(pos4, sheets=...) returns a 45067-dim float32 vector
    with bit-identical first 45056 dims to encode_4d(pos4)
  - Halfmove clamping at 100 (50-move-rule has fired)
  - Repetition clamping to [0, 2]
  - SheetState.from_chess_board lifts python-chess Board state
  - SheetState.from_game_state_4d lifts GameState4D state
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import (   # noqa: E402
    encode_640, fen_to_pos,
    SheetState,
    SHEET_AUX_DIM, SHEET_OFFSET_2D, SHEET_OFFSET_4D,
    FIFTY_MOVE_THRESHOLD,
    encode_aux_block,
    decode_castling_rights, decode_ep_file,
    decode_side_to_move_white, decode_repetition_count,
    decode_halfmove_clock, decode_sheet_state,
)


# ─── Default state ──────────────────────────────────────────────────


def test_immolation_default_aux_block_shape_and_dtype():
    aux = encode_aux_block(SheetState())
    assert aux.shape == (SHEET_AUX_DIM,) == (11,)
    assert aux.dtype == np.float64


def test_immolation_default_aux_block_all_zero_except_halfmove_carrier():
    """Default SheetState: no rights, no EP, white to move (slot=0),
    halfmove=0, rep=0. The halfmove carrier at clock=0 is (cos(0),
    sin(0)) = (1, 0). All other slots zero."""
    aux = encode_aux_block(SheetState())
    assert aux[0] == 0.0   # castling_wk
    assert aux[1] == 0.0   # castling_wq
    assert aux[2] == 0.0   # castling_bk
    assert aux[3] == 0.0   # castling_bq
    assert aux[4] == 0.0   # ep_active
    assert aux[5] == 0.0   # ep_file
    assert aux[6] == 0.0   # side_to_move (white = 0)
    assert aux[7] == 0.0   # repetition_count
    assert aux[8] == pytest.approx(1.0)  # cos(0) = 1
    assert aux[9] == pytest.approx(0.0)  # sin(0) = 0
    assert aux[10] == 0.0  # reserved


# ─── Castling rights round-trip ─────────────────────────────────────


@pytest.mark.parametrize("wk,wq,bk,bq", [
    (False, False, False, False),
    (True, False, False, False),
    (False, True, False, False),
    (False, False, True, False),
    (False, False, False, True),
    (True, True, True, True),
    (True, False, True, False),
    (False, True, False, True),
])
def test_immolation_castling_rights_round_trip(wk, wq, bk, bq):
    state = SheetState(
        castling_wk=wk, castling_wq=wq,
        castling_bk=bk, castling_bq=bq,
    )
    aux = encode_aux_block(state)
    # Stuff into a fake-base zero vector to exercise offset machinery.
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    out = decode_castling_rights(vec, SHEET_OFFSET_2D)
    assert out == (wk, wq, bk, bq)


# ─── EP target round-trip ────────────────────────────────────────────


@pytest.mark.parametrize("ep_file", [None, 0, 1, 2, 3, 4, 5, 6, 7])
def test_immolation_ep_file_round_trip(ep_file):
    state = SheetState(ep_file=ep_file)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_ep_file(vec, SHEET_OFFSET_2D) == ep_file


# ─── Halfmove clock round-trip ───────────────────────────────────────


@pytest.mark.parametrize("h", list(range(0, 101)))
def test_immolation_halfmove_round_trip_all_legal_values(h):
    state = SheetState(halfmove_clock=h)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_halfmove_clock(vec, SHEET_OFFSET_2D) == h


def test_immolation_halfmove_clamp_above_threshold():
    """Halfmove > 100 clamps to 100 (the 50-move rule has triggered)."""
    state = SheetState(halfmove_clock=150)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_halfmove_clock(vec, SHEET_OFFSET_2D) == FIFTY_MOVE_THRESHOLD


def test_immolation_halfmove_carrier_is_unit_modulus():
    """For any halfmove clock h in [0, 100], the (cos, sin) pair
    sits on the unit circle to float64 precision."""
    for h in range(0, 101):
        aux = encode_aux_block(SheetState(halfmove_clock=h))
        c, s = aux[8], aux[9]
        assert c * c + s * s == pytest.approx(1.0, rel=1e-12)


# ─── Side-to-move round-trip ─────────────────────────────────────────


@pytest.mark.parametrize("white", [True, False])
def test_immolation_side_to_move_round_trip(white):
    state = SheetState(side_to_move_white=white)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_side_to_move_white(vec, SHEET_OFFSET_2D) == white


# ─── Repetition count round-trip ─────────────────────────────────────


@pytest.mark.parametrize("rep", [0, 1, 2])
def test_immolation_repetition_round_trip(rep):
    state = SheetState(repetition_count=rep)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_repetition_count(vec, SHEET_OFFSET_2D) == rep


def test_immolation_repetition_clamp_above_two():
    """Repetition counts above 2 clamp to 2 (claim is already
    available — saturating at the threshold)."""
    state = SheetState(repetition_count=99)
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    assert decode_repetition_count(vec, SHEET_OFFSET_2D) == 2


# ─── Aggregate decode ───────────────────────────────────────────────


def test_immolation_decode_sheet_state_full_round_trip():
    """All fields populated non-trivially; ``decode_sheet_state``
    recovers a SheetState equal to the source."""
    state = SheetState(
        castling_wk=True,
        castling_wq=False,
        castling_bk=True,
        castling_bq=True,
        ep_file=5,
        side_to_move_white=False,
        halfmove_clock=37,
        repetition_count=1,
    )
    aux = encode_aux_block(state)
    vec = np.zeros(SHEET_OFFSET_2D + SHEET_AUX_DIM)
    vec[SHEET_OFFSET_2D:] = aux
    recovered = decode_sheet_state(vec, SHEET_OFFSET_2D)
    assert recovered == state


# ─── 2D encoder integration ─────────────────────────────────────────


def _starting_pos_2d():
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")


def test_immolation_encode_640_default_unchanged_dims():
    """encode_640 without sheets returns 640-dim float64."""
    pos = _starting_pos_2d()
    enc = encode_640(pos)
    assert enc.shape == (640,)
    assert enc.dtype == np.float64


def test_immolation_encode_640_with_sheets_extends_to_651():
    """encode_640(pos, sheets=...) returns 651-dim float64."""
    pos = _starting_pos_2d()
    enc = encode_640(pos, sheets=SheetState())
    assert enc.shape == (651,)
    assert enc.dtype == np.float64


def test_immolation_encode_640_with_sheets_preserves_base():
    """First 640 dims of sheet-aware encoding must be bit-identical
    to legacy 640-dim encoding (the 1.9.0 backward-compat contract)."""
    pos = _starting_pos_2d()
    base = encode_640(pos)
    full = encode_640(pos, sheets=SheetState(
        castling_wk=True, castling_wq=True,
        castling_bk=True, castling_bq=True,
        halfmove_clock=42,
    ))
    np.testing.assert_array_equal(full[:640], base)


def test_immolation_encode_640_aux_at_correct_offset():
    """The aux block is written at offset 640 (SHEET_OFFSET_2D)."""
    pos = _starting_pos_2d()
    state = SheetState(
        castling_wk=True, castling_wq=True,
        castling_bk=True, castling_bq=True,
        side_to_move_white=True,
    )
    enc = encode_640(pos, sheets=state)
    aux_independently = encode_aux_block(state)
    np.testing.assert_array_equal(
        enc[SHEET_OFFSET_2D:SHEET_OFFSET_2D + SHEET_AUX_DIM],
        aux_independently,
    )


# ─── 4D encoder integration ─────────────────────────────────────────


def test_immolation_encode_4d_default_unchanged_dims():
    """encode_4d without sheets returns 45056-dim float32."""
    from chess_spectral import encoder_4d
    from chess_spectral_4d import initial_position
    pos4 = dict(initial_position().position.items())
    enc = encoder_4d.encode_4d(pos4)
    assert enc.shape == (45056,)
    assert enc.dtype == np.float32


def test_immolation_encode_4d_with_sheets_extends_to_45067():
    from chess_spectral import encoder_4d
    from chess_spectral_4d import initial_position
    pos4 = dict(initial_position().position.items())
    enc = encoder_4d.encode_4d(pos4, sheets=SheetState())
    assert enc.shape == (45067,)
    assert enc.dtype == np.float32


def test_immolation_encode_4d_with_sheets_preserves_base():
    from chess_spectral import encoder_4d
    from chess_spectral_4d import initial_position
    pos4 = dict(initial_position().position.items())
    base = encoder_4d.encode_4d(pos4)
    full = encoder_4d.encode_4d(pos4, sheets=SheetState(
        halfmove_clock=42, repetition_count=1,
    ))
    np.testing.assert_array_equal(full[:45056], base)


def test_immolation_encode_4d_aux_at_correct_offset():
    from chess_spectral import encoder_4d
    from chess_spectral_4d import initial_position
    pos4 = dict(initial_position().position.items())
    state = SheetState(
        side_to_move_white=False,
        halfmove_clock=99,
        repetition_count=2,
    )
    enc = encoder_4d.encode_4d(pos4, sheets=state)
    # 4D output is float32; aux is cast at concat. Decode via
    # SHEET_OFFSET_4D and verify field-by-field.
    cwk, cwq, cbk, cbq = decode_castling_rights(enc, SHEET_OFFSET_4D)
    assert (cwk, cwq, cbk, cbq) == (False, False, False, False)
    assert decode_ep_file(enc, SHEET_OFFSET_4D) is None
    assert decode_side_to_move_white(enc, SHEET_OFFSET_4D) is False
    assert decode_repetition_count(enc, SHEET_OFFSET_4D) == 2
    assert decode_halfmove_clock(enc, SHEET_OFFSET_4D) == 99


# ─── from_chess_board factory ───────────────────────────────────────


def test_immolation_from_chess_board_starting_position():
    """python-chess startpos lifts to a SheetState with all four
    castling rights and white to move."""
    chess = pytest.importorskip("chess")
    board = chess.Board()  # standard starting position
    state = SheetState.from_chess_board(board)
    assert state.castling_wk is True
    assert state.castling_wq is True
    assert state.castling_bk is True
    assert state.castling_bq is True
    assert state.ep_file is None
    assert state.side_to_move_white is True
    assert state.halfmove_clock == 0
    assert state.repetition_count == 0


def test_immolation_from_chess_board_after_double_push():
    """e2e4 sets EP target to e3 (file 4)."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("e2e4")
    state = SheetState.from_chess_board(board)
    assert state.ep_file == 4  # 'e' file
    assert state.side_to_move_white is False
    assert state.halfmove_clock == 0  # double-push resets clock


def test_immolation_from_chess_board_after_quiet_move():
    """1. Nf3 — knight move, halfmove clock advances to 1."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("g1f3")
    state = SheetState.from_chess_board(board)
    assert state.halfmove_clock == 1
    assert state.ep_file is None


# ─── from_game_state_4d factory ─────────────────────────────────────


def test_immolation_from_game_state_4d_canonical_start():
    """4D OC §3.3 starting position lifts to neutral SheetState
    (no castling, no EP, white to move, halfmove=0, rep=0)."""
    from chess_spectral_4d import initial_position
    state = SheetState.from_game_state_4d(initial_position())
    assert state.castling_wk is False
    assert state.castling_wq is False
    assert state.castling_bk is False
    assert state.castling_bq is False
    assert state.ep_file is None
    assert state.side_to_move_white is True
    assert state.halfmove_clock == 0
    assert state.repetition_count == 0
