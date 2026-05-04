"""1.9.0 immolation: chess_spectral_4d.bridge sheet APIs.

The bridge module is the Pyodide / chess4D-OC consumer surface;
its return-path discipline is "plain dict, no numpy across WASM."
These tests verify the three new 1.9.0 functions:

    * get_sheet_state(state_or_board) -> dict
    * encode_sheet_aux(sheet_dict)    -> {"ok": True, "aux": list[float]}
    * decode_sheet_aux_from_vector(vec, offset) -> {"ok": True, "sheet": dict}

Coverage:
  - get_sheet_state on a 4D GameState4D returns castling/EP all-zero
    per ruleset; halfmove + side-to-move populated.
  - get_sheet_state on a python-chess Board lifts full state.
  - get_sheet_state on a bogus input returns {"ok": False, ...}.
  - encode_sheet_aux returns a plain Python list of 11 floats.
  - decode_sheet_aux_from_vector round-trips encode_sheet_aux.
  - decode_sheet_aux_from_vector handles short-vector / bad-input
    cases gracefully.
  - Round-trip via the bridge composes: state → get → encode →
    decode → matches.
"""
from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral_4d import bridge   # noqa: E402
from chess_spectral_4d import initial_position   # noqa: E402


# ─── get_sheet_state ─────────────────────────────────────────────────


def test_immolation_bridge_get_sheet_state_4d_canonical():
    """Canonical Oana-Chiru §3.3 startpos lifts to the expected
    sheet shape: castling/EP zero; white to move; halfmove 0;
    repetition 0."""
    gs = initial_position()
    res = bridge.get_sheet_state(gs)
    assert res == {
        "ok": True,
        "sheet": {
            "castling_wk": False,
            "castling_wq": False,
            "castling_bk": False,
            "castling_bq": False,
            "ep_file": None,
            "side_to_move_white": True,
            "halfmove_clock": 0,
            "repetition_count": 0,
        },
    }


def test_immolation_bridge_get_sheet_state_2d_chess_board():
    """python-chess Board at startpos lifts to all four castling
    rights alive + white to move + halfmove 0."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    res = bridge.get_sheet_state(board)
    assert res["ok"] is True
    s = res["sheet"]
    assert s["castling_wk"] is True
    assert s["castling_wq"] is True
    assert s["castling_bk"] is True
    assert s["castling_bq"] is True
    assert s["ep_file"] is None
    assert s["side_to_move_white"] is True
    assert s["halfmove_clock"] == 0
    assert s["repetition_count"] == 0


def test_immolation_bridge_get_sheet_state_2d_chess_board_after_e4():
    """1. e4 sets EP target file = 4 ('e' file)."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    board.push_uci("e2e4")
    res = bridge.get_sheet_state(board)
    assert res["ok"] is True
    s = res["sheet"]
    assert s["ep_file"] == 4
    assert s["side_to_move_white"] is False


def test_immolation_bridge_get_sheet_state_unrecognized_input():
    """A bogus input returns ok=False with a descriptive error."""
    res = bridge.get_sheet_state("not a board")
    assert res["ok"] is False
    assert "GameState4D" in res["error"] or "Board" in res["error"]


# ─── encode_sheet_aux ────────────────────────────────────────────────


def test_immolation_bridge_encode_sheet_aux_returns_plain_list():
    """encode_sheet_aux returns a plain Python list[float] of length 11
    — no numpy on the return path, per the WASM-boundary discipline."""
    sheet_dict = {
        "castling_wk": True,
        "castling_wq": False,
        "castling_bk": True,
        "castling_bq": True,
        "ep_file": 5,
        "side_to_move_white": False,
        "halfmove_clock": 37,
        "repetition_count": 1,
    }
    res = bridge.encode_sheet_aux(sheet_dict)
    assert res["ok"] is True
    aux = res["aux"]
    # Plain list, not numpy.
    assert isinstance(aux, list)
    assert len(aux) == 11
    for x in aux:
        assert isinstance(x, float)


def test_immolation_bridge_encode_sheet_aux_missing_field():
    """Missing required field returns ok=False."""
    incomplete = {
        "castling_wk": True,
        "castling_wq": True,
        # Missing castling_bk, castling_bq, etc.
    }
    res = bridge.encode_sheet_aux(incomplete)
    assert res["ok"] is False
    assert "KeyError" in res["error"]


def test_immolation_bridge_encode_sheet_aux_default_neutral():
    """Default neutral sheet (no rights, no EP, white to move,
    halfmove 0, rep 0) encodes to all-zero except the halfmove
    Fourier carrier slot 8 (cos(0) = 1)."""
    sheet_dict = {
        "castling_wk": False,
        "castling_wq": False,
        "castling_bk": False,
        "castling_bq": False,
        "ep_file": None,
        "side_to_move_white": True,
        "halfmove_clock": 0,
        "repetition_count": 0,
    }
    res = bridge.encode_sheet_aux(sheet_dict)
    assert res["ok"] is True
    aux = res["aux"]
    assert aux[0:8] == [0.0] * 8  # all zero through repetition slot
    assert aux[8] == pytest.approx(1.0)  # cos(0) = 1
    assert aux[9] == pytest.approx(0.0)  # sin(0) = 0
    assert aux[10] == 0.0  # reserved


# ─── decode_sheet_aux_from_vector ────────────────────────────────────


def test_immolation_bridge_decode_sheet_aux_from_vector_roundtrip():
    """Build an aux block via encode_sheet_aux, prepend zeros to
    simulate the encoder vector layout, then recover via
    decode_sheet_aux_from_vector. Must round-trip the original
    sheet dict exactly."""
    sheet_dict = {
        "castling_wk": True,
        "castling_wq": False,
        "castling_bk": True,
        "castling_bq": True,
        "ep_file": 5,
        "side_to_move_white": False,
        "halfmove_clock": 37,
        "repetition_count": 1,
    }
    enc_res = bridge.encode_sheet_aux(sheet_dict)
    assert enc_res["ok"] is True
    aux = enc_res["aux"]

    # Simulate a 2D-shaped encoded vector: 640 zeros + 11-dim aux.
    vec = [0.0] * 640 + aux
    dec_res = bridge.decode_sheet_aux_from_vector(vec, offset=640)
    assert dec_res["ok"] is True
    assert dec_res["sheet"] == sheet_dict


def test_immolation_bridge_decode_sheet_aux_short_vector():
    """A vector that's too short for the requested offset returns
    ok=False with a clear error."""
    too_short = [0.0] * 100
    res = bridge.decode_sheet_aux_from_vector(too_short, offset=640)
    assert res["ok"] is False
    assert "insufficient" in res["error"]


def test_immolation_bridge_decode_sheet_aux_at_4d_offset():
    """4D offset (45056) works the same shape as 2D offset (640)."""
    sheet_dict = {
        "castling_wk": False,
        "castling_wq": False,
        "castling_bk": False,
        "castling_bq": False,
        "ep_file": None,
        "side_to_move_white": True,
        "halfmove_clock": 50,
        "repetition_count": 2,
    }
    enc_res = bridge.encode_sheet_aux(sheet_dict)
    aux = enc_res["aux"]
    # Simulate a 4D-shaped vector.
    vec = [0.0] * 45056 + aux
    dec_res = bridge.decode_sheet_aux_from_vector(vec, offset=45056)
    assert dec_res["ok"] is True
    assert dec_res["sheet"] == sheet_dict


# ─── End-to-end round trip via the bridge ─────────────────────────────


def test_immolation_bridge_e2e_4d_roundtrip():
    """get_sheet_state → encode_sheet_aux → simulate vector →
    decode_sheet_aux_from_vector. Full bridge composition recovers
    the original sheet shape from a GameState4D."""
    gs = initial_position()
    state_res = bridge.get_sheet_state(gs)
    assert state_res["ok"] is True
    sheet_dict = state_res["sheet"]

    enc_res = bridge.encode_sheet_aux(sheet_dict)
    assert enc_res["ok"] is True
    aux = enc_res["aux"]

    vec = [0.0] * 45056 + aux
    dec_res = bridge.decode_sheet_aux_from_vector(vec, offset=45056)
    assert dec_res["ok"] is True
    assert dec_res["sheet"] == sheet_dict


def test_immolation_bridge_e2e_2d_roundtrip():
    """Same composition starting from a python-chess Board."""
    chess = pytest.importorskip("chess")
    board = chess.Board()
    state_res = bridge.get_sheet_state(board)
    assert state_res["ok"] is True
    sheet_dict = state_res["sheet"]

    enc_res = bridge.encode_sheet_aux(sheet_dict)
    aux = enc_res["aux"]

    vec = [0.0] * 640 + aux
    dec_res = bridge.decode_sheet_aux_from_vector(vec, offset=640)
    assert dec_res["ok"] is True
    assert dec_res["sheet"] == sheet_dict


# ─── encode_2d alias verification ────────────────────────────────────


def test_immolation_encode_2d_is_alias_of_encode_640():
    """1.9.0 — the future-proof alias `encode_2d` and the legacy name
    `encode_640` must be the same function object (true alias, not a
    wrapper). Decouples the public API from the dim-count-pinned name
    while preserving backward compatibility. See notebook §19.11."""
    from chess_spectral import encode_640, encode_2d
    assert encode_2d is encode_640
