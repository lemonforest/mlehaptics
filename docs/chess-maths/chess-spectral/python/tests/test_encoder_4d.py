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

def test_fiber_sym_channels_nonzero_with_nonrook_piece():
    """v1.1 wires the rank-3 cross-piece SVD fiber basis. A non-rook
    non-pawn piece with at least one occupied neighbor should produce
    nonzero energy in at least one FIB_SYM_* channel.

    The fiber aggregation uses `gradient = sig[neighbors].sum()` as a
    scalar multiplier. A single isolated piece has zero gradient, so
    the perturber (pawn at a knight-target square) is mandatory to get
    a nonzero fiber output.
    """
    s1_coord = (3, 3, 3, 3)
    s1 = _sq(*s1_coord)
    kn_target = next(iter(t4.knight4_targets(*s1_coord)))
    pos = {s1: 'N', _sq(*kn_target): 'P'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    total_fib = e["FIB_SYM_1"] + e["FIB_SYM_2"] + e["FIB_SYM_3"]
    assert total_fib > 0.0, (
        f'fiber-sym channels unexpectedly zero for knight+pawn-neighbor: '
        f'{e["FIB_SYM_1"]}, {e["FIB_SYM_2"]}, {e["FIB_SYM_3"]}'
    )


def test_fiber_sym_channels_zero_for_rook_only():
    """The 4D rook is diagonal in the tensor-DCT off-diagonal basis;
    it has zero projection onto the cross-piece SVD fiber directions.
    A rook-only position therefore has zero fiber-sym energy exactly
    (up to float32 round-off at zero)."""
    pos = {_sq(3, 3, 3, 3): 'R'}
    v = enc_mod.encode_4d(pos)
    e = enc_mod.channel_energies_4d(v)
    # FIBER_LOCAL[rook_idx, :, :] is exactly zero by construction (rook
    # row dropped from SVD, zero-filled on return), so the encoder
    # output in channels 5-7 is exactly zero for rook-only positions.
    assert e["FIB_SYM_1"] == 0.0
    assert e["FIB_SYM_2"] == 0.0
    assert e["FIB_SYM_3"] == 0.0


def test_fiber_sym_channels_distinguish_knight_bishop_king():
    """Knight, bishop, and king contribute to three different
    structural directions in the rank-3 fiber basis. Placing the same
    piece type at the same square should produce the same fiber
    channels; placing three different piece types should produce three
    distinguishable channel patterns.

    Each placement needs at least one occupied neighbor so the fiber
    gradient is nonzero. We pick a pawn perturber at a piece-specific
    target square (knight target for the knight run, bishop target for
    the bishop run, king target for the king run).
    """
    s_coord = (3, 3, 3, 3)
    s = _sq(*s_coord)
    fib_slice = slice(5 * 4096, 8 * 4096)

    kn_target = next(iter(t4.knight4_targets(*s_coord)))
    bp_target = next(iter(t4.bishop4_targets(*s_coord)))
    kg_target = next(iter(t4.king4_targets(*s_coord)))

    v_knight = enc_mod.encode_4d({s: 'N', _sq(*kn_target): 'P'})
    v_bishop = enc_mod.encode_4d({s: 'B', _sq(*bp_target): 'P'})
    v_king = enc_mod.encode_4d({s: 'K', _sq(*kg_target): 'P'})

    # Each piece type's fiber block must be nonzero (gradient enabled)
    assert np.any(v_knight[fib_slice] != 0)
    assert np.any(v_bishop[fib_slice] != 0)
    assert np.any(v_king[fib_slice] != 0)

    # All three must be distinguishable in the fiber-sym block
    assert not np.array_equal(v_knight[fib_slice], v_bishop[fib_slice])
    assert not np.array_equal(v_knight[fib_slice], v_king[fib_slice])
    assert not np.array_equal(v_bishop[fib_slice], v_king[fib_slice])


def test_fiber_local_queen_trace_equals_bishop_trace():
    """Queen = Bishop + Rook edge-wise. Rook's adjacency is diagonal in
    the tensor-DCT basis, so tr(K_d @ A_rook) = 0 for each fiber
    direction d. This gives the global identity:

        sum_s FIBER_LOCAL[queen_idx, s, d]
            = tr(K_d @ A_queen)
            = tr(K_d @ A_bishop) + tr(K_d @ A_rook)
            = tr(K_d @ A_bishop)
            = sum_s FIBER_LOCAL[bishop_idx, s, d]

    The per-square values differ (queen's sum includes rook targets),
    but the global sum across all source squares must match bishop's.
    This is the table-level analogue of the 2D LOCAL_FIBER_3D identity
    that queen = bishop + rook and rook contributes zero globally.
    """
    tables = enc_mod._load_tables()
    F = tables['FIBER_LOCAL']  # (5, 4096, 3)
    queen_idx = enc_mod._FIBER_IDX_4D['Q']
    bishop_idx = enc_mod._FIBER_IDX_4D['B']
    queen_totals = F[queen_idx].sum(axis=0)    # shape (3,)
    bishop_totals = F[bishop_idx].sum(axis=0)  # shape (3,)
    # Use a norm-relative tolerance: float32 K_d matmul accumulates
    # round-off over 4096 source squares per direction.
    scale = max(float(np.linalg.norm(bishop_totals)),
                float(np.linalg.norm(queen_totals)), 1.0)
    assert np.allclose(queen_totals, bishop_totals,
                       atol=1e-3 * scale), (
        f'queen global fiber totals {queen_totals} != bishop totals '
        f'{bishop_totals}; expected equality because '
        f'tr(K_d @ A_rook) = 0 (rook is diagonal in the tensor-DCT basis)'
    )


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


def test_pawn_antisym_factored_structure_is_w_axis_only():
    """Single pawn at (sx, sy, sz, sw) writes W_ANTI_DCT[sw] into the
    eight DCT modes at (sx, sy, sz, *) and exactly zero everywhere
    else. This is the algebraic invariant the factored form (and the
    C encoder port) must preserve. See encoder_4d.encode_4d channel 8
    comment and tables_4d.w_anti_dct_block."""
    sx, sy, sz, sw = 3, 3, 3, 3
    s = _sq(sx, sy, sz, sw)
    v = enc_mod.encode_4d({s: 'P'})
    fa = v[8 * 4096:9 * 4096]
    base = (sx << 9) | (sy << 6) | (sz << 3)
    W = t4.w_anti_dct_block()
    # Inside the (sx,sy,sz,*) ray: 8 modes match W_ANTI_DCT[sw]
    np.testing.assert_allclose(
        fa[base:base + 8].astype(np.float64), W[sw],
        atol=1e-6, err_msg='w-axis block mismatches W_ANTI_DCT[sw]'
    )
    # Outside: exactly zero, not just "small" — the factored form means
    # the encoder never even touches these modes.
    mask = np.ones(4096, dtype=bool)
    mask[base:base + 8] = False
    assert np.max(np.abs(fa[mask])) == 0.0, (
        f'factored form leaked off-w energy: '
        f'max |fa[off-w]| = {np.max(np.abs(fa[mask])):.3e}'
    )


def test_pawn_axis_factorization_structural():
    """P1 feasibility gate (v1.1.1): the Y- and W-axis pawn antisymmetric
    adjacencies lift the same 8x8 block into independent tensor factors
    of the 4D DCT basis, so they are Frobenius-orthogonal by construction.

    Computed via the factored Kronecker form (the same form the encoder
    uses to scatter 8 modes per pawn), not the dense 4096x4096 U^T A U
    that verify_phase4 uses — factored form avoids 128 MB of matmul
    round-off and makes the structural identities exact to ~1e-15.

    Checks:
    - C_anti_w has support only on the (x,y,z)-diagonal w-axis 8x8 block;
    - C_anti_y has support only on the (x,z,w)-diagonal y-axis 8x8 block;
    - on-axis Frobenius norms match (same 8x8 generator, different leg);
    - cross-channel Frobenius inner product ~ 0 (v1.1.1 feasibility
      signal — follows from tr(A_w_anti) = tr(A_y_anti) = 0 via the
      Kronecker trace identity tr(A (x) B (x) C (x) D) = tr A tr B tr C tr D).
    """
    from scipy.sparse import kron as skron, eye as seye, csr_matrix

    B = t4.BOARD_SIDE
    I8 = seye(B, format='csr')
    W = csr_matrix(t4.w_anti_dct_block())
    Y = csr_matrix(t4.y_anti_dct_block())

    # W-axis pawn antisym in DCT basis: I (x) I (x) I (x) W
    C_w = skron(skron(skron(I8, I8), I8), W, format='csr')
    # Y-axis pawn antisym in DCT basis: I (x) Y (x) I (x) I
    C_y = skron(skron(skron(I8, Y), I8), I8, format='csr')

    # Dense reshape for mask-based norms (4096x4096 float64 = 128 MB; fine
    # for a single structural test).
    T_w = C_w.toarray().reshape(B, B, B, B, B, B, B, B)
    T_y = C_y.toarray().reshape(B, B, B, B, B, B, B, B)

    # On-w mask: (i,j,k)==(i',j',k'); mix only on (l, l').
    mask_w = np.zeros_like(T_w, dtype=bool)
    for i in range(B):
        for j in range(B):
            for k in range(B):
                mask_w[i, j, k, :, i, j, k, :] = True
    # On-y mask: (i,k,l)==(i',k',l'); mix only on (j, j').
    mask_y = np.zeros_like(T_y, dtype=bool)
    for i in range(B):
        for k in range(B):
            for l in range(B):
                mask_y[i, :, k, l, i, :, k, l] = True

    on_w_norm = float(np.linalg.norm(T_w[mask_w]))
    off_w_norm = float(np.linalg.norm(T_w[~mask_w]))
    on_y_norm = float(np.linalg.norm(T_y[mask_y]))
    off_y_norm = float(np.linalg.norm(T_y[~mask_y]))

    # Factored form zeroes off-axis support exactly — tolerance tracks
    # the 8x8 eigendecomposition noise floor, not 128 MB matmul noise.
    assert off_w_norm < 1e-13, (
        f'W-axis pawn antisym leaked off-w energy: {off_w_norm:.3e}'
    )
    assert off_y_norm < 1e-13, (
        f'Y-axis pawn antisym leaked off-y energy: {off_y_norm:.3e}'
    )

    # Same 8x8 generator lifted to different legs => equal Frobenius norm
    # on the occupied block.
    assert abs(on_w_norm - on_y_norm) < 1e-10, (
        f'on-axis norms disagree: w={on_w_norm:.10f} y={on_y_norm:.10f}'
    )
    assert on_w_norm > 1.0, f'on-w norm unexpectedly small: {on_w_norm}'

    # *** v1.1.1 feasibility signal: cross-channel Frobenius inner
    # product ~ 0. Kronecker trace identity gives it exactly zero in
    # infinite precision; 8x8 eigendecomposition noise bounds the
    # numerical floor at ~ 1e-14.
    inner = float((C_w.multiply(C_y)).sum())
    assert abs(inner) < 1e-13, (
        f'cross-channel <C_anti_w, C_anti_y>_F = {inner:.3e} '
        f'(expected < 1e-13); independent-tensor-factor argument fails — '
        f'v1.1.1 feasibility premise does not hold'
    )


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
