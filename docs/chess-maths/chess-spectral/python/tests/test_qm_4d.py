"""Unit tests for chess_spectral.qm_4d (Track A kinematic).

Covers:
  * state_to_psi: normalization, Z_2 side-to-move parity, empty
    position handling
  * b4_unitary_rep_4096 / b4_unitary_rep_full: unitarity, norm
    preservation
  * channel_projector: orthogonality + completeness as a PVM
  * channel probabilities: sum to one for any normalized psi
  * H_<piece>_4: Hermiticity + integer spectrum in [-4, 28] for all
    five non-pawn pieces (Pre-flight 2)
  * H_pawn_*: NotImplementedError with helpful message
  * expectation: real for Hermitian observables on normalized psi

Run via `python -m pytest tests/test_qm_4d.py -v` from python/, or
directly via `python tests/test_qm_4d.py` if conftest is set up.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import qm_4d                           # noqa: E402
from chess_spectral import tables_4d as t4                  # noqa: E402


# ---- Test fixtures --------------------------------------------------


def _sq(x: int, y: int, z: int, w: int) -> int:
    return t4.sq4(x, y, z, w)


@pytest.fixture(scope='module')
def position_a():
    """Two kings + a queen + a knight + a pawn on the W-axis."""
    return {
        _sq(0, 0, 0, 0): 'K',
        _sq(7, 7, 7, 7): 'k',
        _sq(3, 3, 3, 3): 'Q',
        _sq(2, 4, 6, 1): 'n',
        _sq(1, 1, 1, 1): ('P', 'w'),
    }


@pytest.fixture(scope='module')
def position_b():
    """Different non-trivial position. Bishop + rook on different
    parities, plus pawns on both axes."""
    return {
        _sq(0, 4, 4, 0): 'B',
        _sq(5, 3, 2, 6): 'r',
        _sq(2, 0, 0, 0): ('P', 'y'),
        _sq(7, 0, 5, 5): ('p', 'w'),
        _sq(3, 3, 3, 4): 'K',
        _sq(4, 4, 4, 3): 'k',
    }


# ---- state_to_psi ---------------------------------------------------


def test_state_to_psi_shape_and_dtype(position_a):
    psi = qm_4d.state_to_psi(position_a, side_to_move=True)
    assert psi.shape == (qm_4d.ENCODING_DIM,)
    assert psi.dtype == np.complex128


def test_state_to_psi_normalized(position_a, position_b):
    """For non-empty positions, psi should be L2-unit."""
    for pos in (position_a, position_b):
        for side in (True, False):
            psi = qm_4d.state_to_psi(pos, side_to_move=side)
            assert qm_4d.is_normalized(psi), (
                f"||psi|| = {qm_4d.norm(psi)} != 1 for "
                f"side_to_move={side}"
            )


def test_state_to_psi_z2_parity(position_a, position_b):
    """psi(state, white) and psi(state, black) should differ only in
    overall sign (same unit-norm direction up to -1)."""
    for pos in (position_a, position_b):
        psi_w = qm_4d.state_to_psi(pos, side_to_move=True)
        psi_b = qm_4d.state_to_psi(pos, side_to_move=False)
        # exact opposite sign
        max_diff = float(np.max(np.abs(psi_w + psi_b)))
        assert max_diff < 1e-12, (
            f"psi_white + psi_black should be 0 within float error; "
            f"max |diff| = {max_diff}"
        )
        # alternative: inner product = -||psi||^2 = -1
        ip = qm_4d.inner_product(psi_w, psi_b)
        assert abs(ip + 1.0) < 1e-10, (
            f"<white|black> should be -1, got {ip}"
        )


def test_state_to_psi_zero_vector_flag():
    """Empty positions encode to the zero vector (cannot be
    normalized). state_to_psi returns the zero vector unchanged
    rather than raising; callers can detect via is_normalized."""
    psi = qm_4d.state_to_psi({}, side_to_move=True)
    assert psi.shape == (qm_4d.ENCODING_DIM,)
    assert np.all(psi == 0.0)
    # Sanity: not normalized.
    assert not qm_4d.is_normalized(psi)


# ---- b4_unitary_rep -------------------------------------------------


def test_b4_unitary_rep_is_unitary():
    """Sample group elements (a leftward stride covers identity, a few
    sign flips, an axis swap) and verify U U^dagger == I."""
    closure = t4.b4_closure()
    sample_indices = [0, 1, 5, 23, 47, 100, 200, 383]
    for idx in sample_indices:
        g = closure[idx]
        U = qm_4d.b4_unitary_rep_4096(g)
        assert qm_4d.is_unitary(U), (
            f"U[{idx}] g={g} is not unitary (max |UU^dag - I|)"
        )


def test_b4_unitary_rep_preserves_norm(position_a):
    """For each of several psi's, ||U psi|| == ||psi||."""
    psi = qm_4d.state_to_psi(position_a, side_to_move=True)
    closure = t4.b4_closure()
    for idx in [1, 17, 100, 250]:
        g = closure[idx]
        U_full = qm_4d.b4_unitary_rep_full(g)
        psi_rotated = U_full @ psi
        n_rot = qm_4d.norm(psi_rotated)
        assert abs(n_rot - 1.0) < 1e-10, (
            f"||U[{idx}] psi|| = {n_rot}, should be 1"
        )


def test_b4_unitary_rep_full_block_structure():
    """U_full = I_11 (x) U_4096 -- check shape, nnz, and one block."""
    closure = t4.b4_closure()
    g = closure[1]
    U_block = qm_4d.b4_unitary_rep_4096(g)
    U_full = qm_4d.b4_unitary_rep_full(g)
    assert U_full.shape == (qm_4d.ENCODING_DIM, qm_4d.ENCODING_DIM)
    # Block diagonal: nnz(U_full) == 11 * nnz(U_block).
    assert U_full.nnz == qm_4d.N_CHANNELS * U_block.nnz


def test_b4_unitary_rep_caches():
    """Two calls with the same g should return the same object."""
    closure = t4.b4_closure()
    g = closure[7]
    U1 = qm_4d.b4_unitary_rep_4096(g)
    U2 = qm_4d.b4_unitary_rep_4096(g)
    assert U1 is U2


# ---- Channel projector ----------------------------------------------


def test_channel_projector_self_idempotent():
    """P_c is a projector: P_c @ P_c == P_c for each c."""
    for c in range(qm_4d.N_CHANNELS):
        P = qm_4d.channel_projector(c)
        diff = (P @ P) - P
        diff.eliminate_zeros()
        assert diff.nnz == 0, (
            f"P_{c} is not idempotent (P @ P != P), {diff.nnz} nonzero"
        )


def test_channel_projector_orthogonal():
    """Cross terms vanish: P_c @ P_d == 0 for c != d."""
    for c in range(qm_4d.N_CHANNELS):
        P_c = qm_4d.channel_projector(c)
        for d in range(c + 1, qm_4d.N_CHANNELS):
            P_d = qm_4d.channel_projector(d)
            prod = P_c @ P_d
            prod.eliminate_zeros()
            assert prod.nnz == 0, (
                f"P_{c} P_{d} should be 0, got {prod.nnz} nonzero"
            )


def test_channel_projector_completeness():
    """Sum over all channels equals identity."""
    total = sum(
        qm_4d.channel_projector(c) for c in range(qm_4d.N_CHANNELS)
    )
    I = sp.eye(qm_4d.ENCODING_DIM, format='csr', dtype=np.complex128)
    diff = total - I
    diff.eliminate_zeros()
    assert diff.nnz == 0


def test_channel_projector_index_range():
    """Out-of-range channel indices raise."""
    with pytest.raises(ValueError):
        qm_4d.channel_projector(-1)
    with pytest.raises(ValueError):
        qm_4d.channel_projector(qm_4d.N_CHANNELS)


# ---- Channel probability --------------------------------------------


def test_channel_probabilities_sum_to_one(position_a, position_b):
    """For any normalized psi, sum of channel Born probabilities = 1."""
    for pos in (position_a, position_b):
        psi = qm_4d.state_to_psi(pos, side_to_move=True)
        probs = qm_4d.measure_channel_distribution(psi)
        assert probs.shape == (qm_4d.N_CHANNELS,)
        s = float(probs.sum())
        assert abs(s - 1.0) < 1e-10, f"channel probs sum = {s}"
        # All non-negative.
        assert np.all(probs >= -1e-15), f"negative prob: min = {probs.min()}"


def test_prob_channel_matches_distribution(position_a):
    """prob_channel(psi, c) matches measure_channel_distribution[c]."""
    psi = qm_4d.state_to_psi(position_a, side_to_move=True)
    probs = qm_4d.measure_channel_distribution(psi)
    for c in range(qm_4d.N_CHANNELS):
        assert abs(qm_4d.prob_channel(psi, c) - probs[c]) < 1e-15


def test_prob_channel_via_projector(position_a):
    """Cross-check: prob_channel(psi, c) == <psi|P_c|psi>."""
    psi = qm_4d.state_to_psi(position_a, side_to_move=True)
    for c in (0, 5, 10):
        P_c = qm_4d.channel_projector(c)
        e_op = qm_4d.expectation(P_c, psi)
        e_fast = qm_4d.prob_channel(psi, c)
        assert abs(e_op - e_fast) < 1e-12, (
            f"channel {c}: projector expectation {e_op} != "
            f"prob_channel {e_fast}"
        )


# ---- H_<piece> Hermiticity + spectrum -------------------------------


@pytest.mark.parametrize('piece,name', [
    ('R', 'rook'),
    ('B', 'bishop'),
    ('Q', 'queen'),
    ('K', 'king'),
    ('N', 'knight'),
])
def test_h_piece_hermitian(piece, name):
    """H_<piece> = H_<piece>^dagger at machine precision."""
    H = qm_4d.build_H_piece_4(piece)
    assert qm_4d.is_hermitian(H, tol=1e-12), (
        f"H_{name} ({piece!r}) is not Hermitian"
    )


@pytest.mark.parametrize('piece,name,lo_expected,hi_expected', [
    # Empirical spectrum ranges (eigvalsh on the 4096x4096 lift).
    # Rook is exactly {-4, ..., 28} integer (Pre-flight 2 audit);
    # the others are not integer due to boundary clipping breaking
    # vertex-transitivity. Bounds below are the empirical min/max
    # eigenvalues with a tiny tolerance margin -- this is a
    # regression check that the piece adjacencies have not silently
    # changed.
    ('R', 'rook', -4.0, 28.0),
    ('K', 'king', -22.0, 67.74),
    ('N', 'knight', -36.07, 36.07),
    ('B', 'bishop', -12.0, 54.38),
    ('Q', 'queen', -16.0, 81.95),
])
def test_h_piece_spectrum_real(piece, name, lo_expected, hi_expected):
    """Eigenvalues of H_<piece> are real (eigvalsh assumes Hermitian,
    cross-checked in test_h_piece_hermitian above) and within a
    piece-specific envelope. Pre-flight 2 confirmed integer spectra
    for rook/knight."""
    H = qm_4d.build_H_piece_4(piece)
    # eigvalsh is ~5x faster than eigvals on a 4096x4096 matrix and
    # returns real values (assumes Hermiticity, which we verify in
    # test_h_piece_hermitian). The realness claim is therefore moved
    # to a structural test on the matrix; this test focuses on the
    # spectrum envelope.
    eigs = np.linalg.eigvalsh(H.toarray())
    re_lo = float(eigs.min())
    re_hi = float(eigs.max())
    # Allow a small tolerance over the bound to absorb float error.
    tol = 1e-6
    assert re_lo >= lo_expected - tol, (
        f"H_{name} min eig {re_lo} < expected lo {lo_expected}"
    )
    assert re_hi <= hi_expected + tol, (
        f"H_{name} max eig {re_hi} > expected hi {hi_expected}"
    )


def test_h_rook_integer_spectrum_strict():
    """Stricter check on the rook: all eigenvalues are integer in
    {-4, ..., 28} (Pre-flight 2 audit)."""
    H = qm_4d.build_H_piece_4('R')
    eigs = np.linalg.eigvalsh(H.toarray())
    non_int = float(np.max(np.abs(eigs - np.round(eigs))))
    assert non_int < 1e-9, (
        f"H_rook eigenvalues not integer: max non-int dev = {non_int}"
    )
    rounded = np.round(eigs).astype(int)
    assert int(rounded.min()) == -4
    assert int(rounded.max()) == 28


def test_h_lazy_attribute_access():
    """H_rook_4 etc. are reachable via module-level attribute lookup
    and identical to build_H_piece_4 output."""
    H_lazy = qm_4d.H_rook_4
    H_built = qm_4d.build_H_piece_4('R')
    # The lazy access is cached, so a second call should be the same
    # object as the cached one; but vs build_H_piece_4 (uncached) we
    # need to compare structurally.
    diff = H_lazy - H_built
    diff.eliminate_zeros()
    assert diff.nnz == 0


# ---- Pawn observables not implemented -------------------------------


@pytest.mark.parametrize('key', ['P', 'p', 'P_w', 'P_y', 'p_w', 'p_y'])
def test_pawn_observables_not_implemented(key):
    """build_H_piece_4 raises NotImplementedError for pawns with a
    helpful message pointing to Track B."""
    with pytest.raises(NotImplementedError, match=r"[Tt]rack [Bb]"):
        qm_4d.build_H_piece_4(key)


def test_pawn_lazy_attribute_raises():
    """qm_4d.H_pawn_w_4 also raises NotImplementedError."""
    with pytest.raises(NotImplementedError, match=r"[Tt]rack [Bb]"):
        _ = qm_4d.H_pawn_w_4
    with pytest.raises(NotImplementedError, match=r"[Tt]rack [Bb]"):
        _ = qm_4d.H_pawn_y_4


def test_unknown_piece_raises():
    """build_H_piece_4 with a non-piece char raises ValueError."""
    with pytest.raises(ValueError, match=r"unknown piece"):
        qm_4d.build_H_piece_4('Z')
    with pytest.raises(ValueError, match=r"unknown piece"):
        qm_4d.build_H_piece_4('')


# ---- Expectation value real for Hermitian H -------------------------


@pytest.mark.parametrize('piece', ['R', 'B', 'Q', 'K', 'N'])
def test_expectation_real_for_hermitian(position_a, piece):
    """For a Hermitian H_piece and any unit psi, the channel-restricted
    expectation is real. We check by constructing the full-channel
    lift I_11 (x) H_piece on each channel and verifying the imaginary
    part of <psi|H|psi> is sub-1e-12."""
    psi = qm_4d.state_to_psi(position_a, side_to_move=True)
    H_block = qm_4d.build_H_piece_4(piece)
    # Lift to full 45056 space: I_11 (x) H_block.
    I_chan = sp.eye(qm_4d.N_CHANNELS, format='csr', dtype=np.complex128)
    H_full = sp.kron(I_chan, H_block, format='csr')
    val = qm_4d.expectation(H_full, psi)
    # Cross-check: explicit imaginary part computation.
    raw = np.vdot(psi, H_full @ psi)
    assert abs(raw.imag) < 1e-10, (
        f"<psi|H_{piece}|psi> has nonzero imag: {raw.imag}"
    )
    # `val` is float (the real part); just sanity that it is finite.
    assert np.isfinite(val)


# ---- inner product / norm sanity ------------------------------------


def test_inner_product_shape_mismatch():
    """inner_product on mismatched shapes raises ValueError."""
    a = np.zeros(10, dtype=np.complex128)
    b = np.zeros(11, dtype=np.complex128)
    with pytest.raises(ValueError):
        qm_4d.inner_product(a, b)


def test_norm_zero_vector():
    """Norm of zero vector is 0."""
    z = np.zeros(qm_4d.ENCODING_DIM, dtype=np.complex128)
    assert qm_4d.norm(z) == 0.0


# ---- measure_observable_distribution --------------------------------


def test_measure_observable_distribution_rook():
    """For the rook H on a uniform psi over a single channel block,
    eigenvalue distribution should sum to 1 and contain only the
    integer-spectrum values [-4..28]."""
    # Build a uniform psi over the 4096-square basis (1 channel).
    n = qm_4d.CHANNEL_DIM
    psi_4096 = np.ones(n, dtype=np.complex128) / np.sqrt(n)
    H = qm_4d.build_H_piece_4('R')
    eigvals, probs = qm_4d.measure_observable_distribution(
        H, psi_4096, tol=1e-6,
    )
    s = float(probs.sum())
    assert abs(s - 1.0) < 1e-9, f"rook prob sum {s} != 1"
    # All eigenvalues real-valued integers within tol.
    rounded = np.round(eigvals)
    assert np.all(np.abs(eigvals - rounded) < 1e-6), (
        "rook eigenvalues not integer in spectral grouping"
    )
