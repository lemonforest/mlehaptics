"""Tests for chess_spectral.qm_2d_bridge — §17.2 dispatch surface (v1.6.x PR-C).

Mirrors :mod:`tests.test_qm_4d_bridge_v15` at 2D scale. Each method is
verified for return-type contract + observed values on the standard
starting position (the most stable fixture across runs).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
PY_DIR = HERE.parent
sys.path.insert(0, str(PY_DIR))

from chess_spectral.qm_2d_bridge import (  # noqa: E402
    get_version, get_encoder_shape,
    get_fen_state, load_fen, has_legal_moves,
    complex_to_interleaved_float32,
    get_qm_state, get_qm_density, get_qm_expectation,
)


_STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


# ─── §17.5 dev/debug methods ────────────────────────────────────────


def test_get_version_returns_required_keys():
    r = get_version()
    assert r["ok"] is True
    assert isinstance(r["version"], str)
    assert r["bridge"] == "qm_2d_bridge"
    assert "17.2" in r["surface"]


def test_get_encoder_shape_returns_640_dim_2d_layout():
    r = get_encoder_shape()
    assert r["ok"] is True
    assert r["encodingDim"] == 640
    assert r["nChannels"] == 10
    assert r["channelDim"] == 64
    assert r["boardSide"] == 8
    assert r["channelNames"] == [
        "A1", "A2", "B1", "B2", "E", "F1", "F2", "F3", "FA", "FD"
    ]


def test_get_fen_state_from_chess_board_round_trips():
    import chess
    b = chess.Board()
    r = get_fen_state(b)
    assert r["ok"] is True
    assert r["fen"] == _STARTING_FEN


def test_get_fen_state_from_position_dict_uses_correct_convention():
    """Round-trip a starting-position dict through get_fen_state and
    verify the placement matches the canonical FEN. Catches the
    chess_spectral-vs-python-chess square-indexing convention bug
    that affected an earlier draft."""
    loaded = load_fen(_STARTING_FEN)
    r = get_fen_state(loaded["position"])
    # Just compare the placement portion (we don't track castling /
    # ep / clocks in the dict).
    placement = r["fen"].split()[0]
    expected = _STARTING_FEN.split()[0]
    assert placement == expected, (
        f"placement round-trip mismatch:\n  got {placement!r}\n"
        f"  exp {expected!r}"
    )


def test_load_fen_returns_dict_with_32_pieces_for_starting_position():
    r = load_fen(_STARTING_FEN)
    assert r["ok"] is True
    assert r["sideToMove"] is True
    assert len(r["position"]) == 32   # standard 16+16 starting layout


def test_has_legal_moves_starting_position_chess_board():
    """Starting position has 20 legal moves (8 pawn × 2 each = 16,
    plus 4 knight moves). The §16 search test_engine_search.py and
    classical chess theory both confirm this."""
    import chess
    r = has_legal_moves(chess.Board())
    assert r["ok"] is True
    assert r["hasLegalMoves"] is True
    assert r["count"] == 20
    assert r["inCheck"] is False


def test_has_legal_moves_starting_position_position_dict():
    """Same count via the dict round-trip path. Regression guard for
    the convention bug fixed in the v1.6.x PR-C draft."""
    loaded = load_fen(_STARTING_FEN)
    r = has_legal_moves(loaded["position"])
    assert r["ok"] is True
    assert r["count"] == 20


# ─── ComplexArray serialization ─────────────────────────────────────


def test_complex_to_interleaved_float32_roundtrip():
    psi = np.array([1 + 2j, 3 + 4j, 5 + 6j], dtype=np.complex128)
    out = complex_to_interleaved_float32(psi)
    assert out.dtype == np.float32
    assert out.shape == (6,)
    assert np.allclose(out, [1, 2, 3, 4, 5, 6], atol=1e-7)


def test_complex_to_interleaved_handles_complex64_input():
    psi = np.array([1 + 2j], dtype=np.complex64)
    out = complex_to_interleaved_float32(psi)
    assert out.shape == (2,)
    assert np.allclose(out, [1.0, 2.0], atol=1e-6)


# ─── §17.2 #1: get_qm_state ────────────────────────────────────────


def test_get_qm_state_starting_position_normalized():
    loaded = load_fen(_STARTING_FEN)
    r = get_qm_state(loaded["position"])
    assert r["ok"] is True
    assert r["basisDim"] == 640
    assert abs(r["normSq"] - 1.0) < 1e-6
    assert r["psi"].dtype == np.float32
    assert r["psi"].shape == (1280,)   # 2 * 640 (interleaved real+imag)


def test_get_qm_state_accepts_chess_board():
    import chess
    r = get_qm_state(chess.Board())
    assert r["ok"] is True
    assert r["basisDim"] == 640


def test_get_qm_state_side_to_move_changes_psi():
    """The Z_2 superselection sign in state_to_psi should differentiate
    white-to-move from black-to-move. The two ψ are not identical."""
    loaded = load_fen(_STARTING_FEN)
    r_white = get_qm_state(loaded["position"], side_to_move=True)
    r_black = get_qm_state(loaded["position"], side_to_move=False)
    # The two interleaved arrays should differ somewhere.
    assert not np.array_equal(r_white["psi"], r_black["psi"])


# ─── §17.2 #2: get_qm_density ──────────────────────────────────────


def test_get_qm_density_returns_64_cell_array():
    loaded = load_fen(_STARTING_FEN)
    r = get_qm_density(loaded["position"])
    assert r["ok"] is True
    assert r["density"].shape == (64,)
    assert r["density"].dtype == np.float32


def test_get_qm_density_sums_to_unity():
    """For a normalized ψ, the sum of per-cell |ψ|² across all 10
    channels equals ⟨ψ|ψ⟩ = 1.0."""
    loaded = load_fen(_STARTING_FEN)
    r = get_qm_density(loaded["position"])
    total = float(r["density"].sum())
    assert abs(total - 1.0) < 1e-5


def test_get_qm_density_nonnegative():
    """|ψ|² is by construction non-negative."""
    loaded = load_fen(_STARTING_FEN)
    r = get_qm_density(loaded["position"])
    assert (r["density"] >= 0).all()


# ─── §17.2 #3: get_qm_expectation ──────────────────────────────────


@pytest.mark.parametrize("piece", ["rook", "bishop", "queen", "king", "knight"])
def test_get_qm_expectation_real_valued_for_each_piece(piece):
    loaded = load_fen(_STARTING_FEN)
    r = get_qm_expectation(loaded["position"], piece)
    assert r["ok"] is True
    assert r["observable"] == piece
    assert isinstance(r["expectation"], float)
    # Expectation values should be real and finite. No specific
    # numerical claim — those would need pinning against the kinematic
    # reference values from qm_2d.
    assert np.isfinite(r["expectation"])


def test_get_qm_expectation_pawn_raises():
    loaded = load_fen(_STARTING_FEN)
    with pytest.raises(ValueError, match="pawn observable"):
        get_qm_expectation(loaded["position"], "pawn")


def test_get_qm_expectation_unknown_observable_raises():
    loaded = load_fen(_STARTING_FEN)
    with pytest.raises(ValueError, match="unknown observable"):
        get_qm_expectation(loaded["position"], "elephant")


def test_get_qm_expectation_observable_name_case_insensitive():
    """ROOK, Rook, rook all resolve to the same observable."""
    loaded = load_fen(_STARTING_FEN)
    r1 = get_qm_expectation(loaded["position"], "rook")
    r2 = get_qm_expectation(loaded["position"], "ROOK")
    r3 = get_qm_expectation(loaded["position"], "  Rook  ")
    assert r1["expectation"] == r2["expectation"] == r3["expectation"]
