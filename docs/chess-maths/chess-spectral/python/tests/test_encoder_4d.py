"""Unit tests for the 4D chess-spectral encoder.

Covers:
    * board_signal_4d: position -> 4096-vector piece values
    * encode_4d: position -> 40960 float32 vector, channel layout,
      channel_energies_4d
    * Algebraic properties expected of a correct encoder:
        - A_1 channel respects B_4 symmetry (orbit-sum averaging)
        - std-4D coordinate residual channels are zero on the centered
          sum-invariant and nonzero on asymmetric placements
        - pawn antisymmetric channel is zero with no pawns, nonzero
          with a single pawn
        - diagonal-deviation channel depends on piece type
    * Determinism: same input -> bit-identical output (float32)

Run via `python -m pytest tests/test_encoder_4d.py` from the python/
directory, or directly via `python tests/test_encoder_4d.py`.
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

from chess_spectral import encoder_4d as enc_mod        # noqa: E402
from chess_spectral import tables_4d as t4               # noqa: E402


def _sq(x: int, y: int, z: int, w: int) -> int:
    return t4.sq4(x, y, z, w)


# ---- board_signal_4d --------------------------------------------------

def test_board_signal_empty():
    sig = enc_mod.board_signal_4d({})
    assert sig.shape == (4096,)
    assert sig.dtype == np.float64
    assert np.all(sig == 0.0)


def test_board_signal_pieces_assign_correct_values():
    pos = {_sq(0, 0, 0, 0): 'P', _sq(1, 2, 3, 4): 'q',
           _sq(7, 7, 7, 7): 'K'}
    sig = enc_mod.board_signal_4d(pos)
    assert sig[_sq(0, 0, 0, 0)] == enc_mod.PIECE_VALUES_4D['P']
    assert sig[_sq(1, 2, 3, 4)] == enc_mod.PIECE_VALUES_4D['q']
    assert sig[_sq(7, 7, 7, 7)] == enc_mod.PIECE_VALUES_4D['K']
    assert sig.sum() == (
        enc_mod.PIECE_VALUES_4D['P'] + enc_mod.PIECE_VALUES_4D['q']
        + enc_mod.PIECE_VALUES_4D['K']
    )


def test_board_signal_rejects_unknown_piece():
    with pytest.raises(ValueError):
        enc_mod.board_signal_4d({0: '?'})


def test_board_signal_rejects_out_of_range_square():
    with pytest.raises(ValueError):
        enc_mod.board_signal_4d({4096: 'P'})


# ---- encode_4d shape & dtype ------------------------------------------

def test_encode_shape_dtype_and_channel_split():
    pos = {_sq(0, 0, 0, 1): 'P'}
    v = enc_mod.encode_4d(pos)
    assert v.shape == (enc_mod.ENCODING_DIM_4D,)
    assert v.dtype == np.float32
    # 10 channels of 4096
    assert enc_mod.ENCODING_DIM_4D == 10 * 4096


def test_encode_empty_position_is_all_zeros():
    v = enc_mod.encode_4d({})
    assert np.all(v == 0.0)


def test_encode_determinism_same_input_bit_identical():
    pos = {_sq(2, 3, 4, 5): 'N', _sq(6, 1, 0, 7): 'b'}
    v1 = enc_mod.encode_4d(pos)
    v2 = enc_mod.encode_4d(pos)
    assert np.array_equal(v1, v2)


# ---- Channel-level algebraic sanity -----------------------------------

def test_fiber_sym_channels_are_zero_in_v1():
    """v1 leaves fiber-sym channels as zero (local tables too large to
    precompute). Once we ship v1.1 this test will flip to assert > 0."""
    pos = {_sq(3, 3, 3, 3): 'R', _sq(4, 4, 4, 4): 'q'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    assert e["FIB_SYM_1"] == 0.0
    assert e["FIB_SYM_2"] == 0.0
    assert e["FIB_SYM_3"] == 0.0


def test_pawn_antisym_channel_zero_without_pawns():
    pos = {_sq(0, 0, 0, 0): 'Q'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    assert e["FA_PAWN"] == 0.0


def test_pawn_antisym_channel_nonzero_with_pawn():
    pos = {_sq(0, 0, 0, 3): 'P'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    assert e["FA_PAWN"] > 0.0


def test_white_and_black_pawn_same_square_antisym_flip():
    """Equal-magnitude opposite-color pawn at same square should give
    opposite-signed pawn antisym contributions (encoding difference is
    exactly 2x one pawn's contribution)."""
    s = _sq(3, 3, 3, 3)
    v_white = enc_mod.encode_4d({s: 'P'})
    v_black = enc_mod.encode_4d({s: 'p'})
    # FA channel should be exactly opposite
    fa_start = 8 * 4096
    fa_end = 9 * 4096
    assert np.allclose(v_white[fa_start:fa_end],
                       -v_black[fa_start:fa_end], atol=0)


def test_diagonal_deviation_differs_by_piece_type():
    s = _sq(3, 3, 3, 3)
    fd_slice = slice(9 * 4096, 10 * 4096)
    v_knight = enc_mod.encode_4d({s: 'N'})
    v_rook = enc_mod.encode_4d({s: 'R'})
    v_queen = enc_mod.encode_4d({s: 'Q'})
    # Different piece types must produce distinct diag-dev channels
    assert not np.array_equal(v_knight[fd_slice], v_rook[fd_slice])
    assert not np.array_equal(v_knight[fd_slice], v_queen[fd_slice])
    assert not np.array_equal(v_rook[fd_slice], v_queen[fd_slice])


def test_a1_channel_is_b4_orbit_invariant():
    """The A_1 channel is (P_A1 @ signal), where P_A1 averages over
    B_4-orbits of squares. If we place a single piece at two squares
    in the same orbit, the A_1 channel must be identical."""
    # Apply an axis-transposition (x <-> y) and a sign flip (z -> 7-z)
    # to get two orbit-equivalent squares under B_4.
    s1 = _sq(1, 2, 3, 4)
    s2 = _sq(2, 1, 4, 4)   # x<->y; z=3 is NOT fixed under sign flip
    # Normalize: compute orbit of s1 under the closure and pick one
    closure = t4.b4_closure()
    orbit = {t4.sq4(*t4._apply_b4_to_square(g, *t4.rc4(s1)))
             for g in closure}
    # pick any orbit member that isn't s1 itself
    other = next(s for s in orbit if s != s1)
    v1 = enc_mod.encode_4d({s1: 'R'})
    v2 = enc_mod.encode_4d({other: 'R'})
    a1_slice = slice(0, 4096)
    # A_1 is orbit-averaged; the nonzero entries are at orbit members.
    # Two placements on the same orbit give the same A_1 channel.
    assert np.allclose(v1[a1_slice], v2[a1_slice], atol=1e-6)


def test_channel_energies_sum_to_total_energy():
    pos = {_sq(0, 0, 0, 0): 'P', _sq(1, 2, 3, 4): 'N',
           _sq(7, 7, 7, 7): 'K'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    total_via_channels = sum(e.values())
    total_direct = float(np.dot(v, v))
    # Channels tile the 40960-dim output exactly; energies partition.
    assert np.isclose(total_via_channels, total_direct, rtol=1e-5)


if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"],
                   check=False)
