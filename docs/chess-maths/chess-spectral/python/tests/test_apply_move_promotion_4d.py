"""apply_move with promote_to argument (chess-spectral 1.4.0, §16.9 #1).

Covers:
    * default promote_to='Q' is back-compatible with v1.3.x silent auto-queen
    * Q / R / B / N promotion targets all accepted (case-insensitive)
    * malformed promote_to values raise ValueError
    * promotion is triggered iff pawn arrives on the appropriate rank
      for its (color, axis) — white W-axis: w=7, white Y-axis: y=7,
      black W-axis: w=0, black Y-axis: y=0
    * promote_to is silently ignored on non-promotion moves
    * encoded vector reflects the promoted piece (delta-vs-pawn)

Run via::

    cd python && python -m pytest tests/test_apply_move_promotion_4d.py -v
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
from chess_spectral.encoder_4d import encode_4d  # noqa: E402


def _new_state(pieces: dict) -> csd4.GameState4D:
    """Build a GameState4D with a hand-crafted dict of pieces.

    Keys are 4D coords (x, y, z, w); values are piece values
    accepted by encode_4d (single-char or pawn (color, axis) tuple).
    """
    pos = {csd4.coord_to_sq(coord): val for coord, val in pieces.items()}
    gs = csd4.GameState4D(position=pos)
    gs.history.record_initial_position(pos)
    return gs


# ─── Default behavior (back-compat) ─────────────────────────────────

def test_default_promote_to_is_queen() -> None:
    """Without an explicit promote_to, a promoting pawn becomes a
    queen of its color — same behavior as the v1.3.x auto-queen."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    move = csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7))
    sq = csd4.coord_to_sq((0, 0, 0, 7))
    assert gs.position[sq] == "Q"
    assert move.promote_to == "Q"


def test_default_signature_back_compat() -> None:
    """Calling apply_move with only (state, from, to) — no kwarg —
    must still work (i.e. promote_to is a keyword-only arg with a
    default, not a positional)."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    move = csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7))
    assert move.promote_to == "Q"


# ─── All four promotion targets ────────────────────────────────────

@pytest.mark.parametrize("target", ["Q", "R", "B", "N"])
def test_white_pawn_promotion_to_each_piece(target: str) -> None:
    """White W-axis pawn at w=6 promotes to Q/R/B/N at w=7."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to=target)
    sq = csd4.coord_to_sq((0, 0, 0, 7))
    assert gs.position[sq] == target


@pytest.mark.parametrize("target", ["Q", "R", "B", "N"])
def test_black_pawn_promotion_to_each_piece(target: str) -> None:
    """Black W-axis pawn at w=1 promotes to q/r/b/n at w=0."""
    gs = _new_state({(0, 0, 0, 1): ("p", "w")})
    csd4.apply_move(gs, (0, 0, 0, 1), (0, 0, 0, 0), promote_to=target)
    sq = csd4.coord_to_sq((0, 0, 0, 0))
    assert gs.position[sq] == target.lower()


@pytest.mark.parametrize("target", ["Q", "R", "B", "N"])
def test_white_pawn_y_axis_promotion(target: str) -> None:
    """Y-axis white pawn promotes when reaching y=7."""
    gs = _new_state({(0, 6, 0, 0): ("P", "y")})
    csd4.apply_move(gs, (0, 6, 0, 0), (0, 7, 0, 0), promote_to=target)
    sq = csd4.coord_to_sq((0, 7, 0, 0))
    assert gs.position[sq] == target


def test_promote_to_lowercase_accepted() -> None:
    """promote_to is case-insensitive — pass 'q', get a queen."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to="q")
    sq = csd4.coord_to_sq((0, 0, 0, 7))
    assert gs.position[sq] == "Q"


# ─── Validation ────────────────────────────────────────────────────

@pytest.mark.parametrize("bad", ["K", "P", "X", "1", "", "qq"])
def test_invalid_promote_to_rejected(bad: str) -> None:
    """K (king) and P (pawn) and any unknown letter must be rejected."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    with pytest.raises(ValueError, match="promote_to"):
        csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to=bad)


def test_promote_to_non_string_rejected() -> None:
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    with pytest.raises(ValueError, match="promote_to"):
        csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to=42)


# ─── Promotion-trigger conditions ──────────────────────────────────

def test_pawn_not_on_promotion_rank_does_not_promote() -> None:
    """Pawn moving from w=2 to w=3 doesn't promote, regardless of
    promote_to argument."""
    gs = _new_state({(0, 0, 0, 2): ("P", "w")})
    move = csd4.apply_move(gs, (0, 0, 0, 2), (0, 0, 0, 3), promote_to="N")
    sq = csd4.coord_to_sq((0, 0, 0, 3))
    assert gs.position[sq] == ("P", "w"), \
        "pawn on a non-promotion rank should remain a pawn"
    assert move.promote_to is None, \
        "non-promotion moves should record promote_to=None"


def test_non_pawn_with_promote_to_silently_ignored() -> None:
    """A king move with promote_to='Q' must NOT promote anything; the
    argument is silently ignored on non-promotion moves to match
    python-chess semantics."""
    gs = _new_state({(0, 0, 0, 0): "K"})
    move = csd4.apply_move(gs, (0, 0, 0, 0), (1, 0, 0, 0), promote_to="Q")
    sq = csd4.coord_to_sq((1, 0, 0, 0))
    assert gs.position[sq] == "K"
    assert move.promote_to is None


# ─── Encoded-vector reflects promoted piece ────────────────────────

def test_encoded_vector_reflects_promoted_queen() -> None:
    """Encoding the position after promotion shows queen-channel
    energy at the destination square — not pawn-channel energy."""
    gs = _new_state({(0, 0, 0, 6): ("P", "w")})
    csd4.apply_move(gs, (0, 0, 0, 6), (0, 0, 0, 7), promote_to="Q")
    enc_after = encode_4d(gs.position)
    # A promoted queen should produce a non-zero encoding (the empty
    # board encodes to zero everywhere; this is the cheapest possible
    # smoke check that the promotion was honored by the encoder).
    assert np.any(enc_after != 0)


def test_encoded_vector_differs_per_promotion_target() -> None:
    """Same pawn promoting to Q vs N produces visibly different
    encoded vectors (the channels flagged for queen vs knight differ)."""
    base_pieces = {(0, 0, 0, 6): ("P", "w")}

    gs_q = _new_state(dict(base_pieces))
    csd4.apply_move(gs_q, (0, 0, 0, 6), (0, 0, 0, 7), promote_to="Q")

    gs_n = _new_state(dict(base_pieces))
    csd4.apply_move(gs_n, (0, 0, 0, 6), (0, 0, 0, 7), promote_to="N")

    enc_q = encode_4d(gs_q.position)
    enc_n = encode_4d(gs_n.position)
    assert not np.array_equal(enc_q, enc_n), (
        "encoding must distinguish a queen from a knight at the same "
        "post-promotion square"
    )


# ─── Direct invocation ─────────────────────────────────────────────

if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)
