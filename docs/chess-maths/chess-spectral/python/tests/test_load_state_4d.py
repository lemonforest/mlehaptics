"""bridge.load_state — re-import a FEN4 string into a GameState4D
(chess-spectral 1.4.0, §16.9 #5 / §17.4).

Covers:
    * load_state returns a fresh GameState4D with no history
    * load → encode == encode of the original parsed position
    * load → to_fen4 round-trips back to the input
    * malformed input returns {"ok": False, "error": ...}
      rather than raising
    * side_to_move is honored in the returned state

Run via::

    cd python && python -m pytest tests/test_load_state_4d.py -v
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

import chess_spectral_4d as csd4  # noqa: E402
from chess_spectral import fen_4d  # noqa: E402
from chess_spectral.encoder_4d import encode_4d  # noqa: E402


# ─── Fixture FEN4 strings for repeated use ─────────────────────────

SIMPLE_KK = "4d-fen v1: K@0,0,0,0; k@7,7,7,7"
SINGLE_KNIGHT = "4d-fen v1: N@4,3,2,1"
PAWN_PAIR = "4d-fen v1: Pw@1,2,3,4; py@5,6,7,0"
EMPTY = "4d-fen v1:"


# ─── Happy path ────────────────────────────────────────────────────

def test_load_state_returns_ok_dict() -> None:
    out = csd4.bridge.load_state(SIMPLE_KK)
    assert out["ok"] is True
    assert isinstance(out["state"], csd4.GameState4D)


def test_load_state_yields_empty_history() -> None:
    """Freshly loaded state has no recorded moves; only the starting
    position is in the repetition table."""
    out = csd4.bridge.load_state(SIMPLE_KK)
    state = out["state"]
    assert len(state.history.moves) == 0
    assert len(state.history.position_counts) == 1
    assert state.history.half_move_clock == 0


def test_load_state_default_side_is_white() -> None:
    out = csd4.bridge.load_state(SIMPLE_KK)
    assert out["state"].history.side_to_move == csd4.SIDE_WHITE


def test_load_state_explicit_side_black() -> None:
    out = csd4.bridge.load_state(SIMPLE_KK, side_to_move=csd4.SIDE_BLACK)
    assert out["state"].history.side_to_move == csd4.SIDE_BLACK


# ─── Encoding parity vs direct parse() ─────────────────────────────

@pytest.mark.parametrize("fen", [SIMPLE_KK, SINGLE_KNIGHT, PAWN_PAIR, EMPTY])
def test_load_state_encoding_matches_direct_parse(fen: str) -> None:
    """The encoder output for the loaded state must equal the encoder
    output for the position dict produced by fen_4d.parse — i.e.
    load_state introduces no rounding or transformation."""
    direct = fen_4d.parse(fen)
    loaded = csd4.bridge.load_state(fen)["state"]
    assert loaded.position == direct
    enc_direct = encode_4d(direct)
    enc_loaded = encode_4d(loaded.position)
    assert np.array_equal(enc_direct, enc_loaded)


# ─── Round-trip via to_fen4 ───────────────────────────────────────

@pytest.mark.parametrize("fen", [SIMPLE_KK, SINGLE_KNIGHT, PAWN_PAIR, EMPTY])
def test_load_state_to_fen4_round_trip(fen: str) -> None:
    """load_state(fen).to_fen4() should be a fixed point under
    further parse→serialize cycles. Equivalence to the *exact* input
    string isn't required (whitespace can vary), but the canonical
    serialization must be stable."""
    state = csd4.bridge.load_state(fen)["state"]
    s1 = state.to_fen4()
    state2 = csd4.bridge.load_state(s1)["state"]
    s2 = state2.to_fen4()
    assert s1 == s2
    assert state.position == state2.position


# ─── Error handling ────────────────────────────────────────────────

def test_load_state_rejects_missing_prefix() -> None:
    out = csd4.bridge.load_state("K@0,0,0,0")
    assert out["ok"] is False
    assert "error" in out
    assert "prefix" in out["error"].lower()


def test_load_state_rejects_bad_piece() -> None:
    out = csd4.bridge.load_state("4d-fen v1: X@0,0,0,0")
    assert out["ok"] is False
    assert "error" in out


def test_load_state_rejects_bad_coord() -> None:
    out = csd4.bridge.load_state("4d-fen v1: K@8,0,0,0")  # 8 out of range
    assert out["ok"] is False


def test_load_state_rejects_none() -> None:
    out = csd4.bridge.load_state(None)  # type: ignore[arg-type]
    assert out["ok"] is False


# ─── Direct invocation ─────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)
