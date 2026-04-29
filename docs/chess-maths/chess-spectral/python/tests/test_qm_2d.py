"""Unit tests for chess_spectral.qm_2d (Track A kinematic, 2D).

Sibling of tests/test_qm_4d.py. Covers:
  * state_to_psi: normalization, Z_2 side-to-move parity, empty
    position handling
  * d4_unitary_rep_64 / d4_unitary_rep_full: unitarity, norm
    preservation, block structure, group closure caching
  * d4_closure: returns 8 elements with identity first
  * channel_projector: orthogonality + completeness as a 10-channel PVM
  * channel probabilities: sum to one for any normalized psi
  * H_<piece>_2: Hermiticity + real spectrum within audited envelope
    for all five non-pawn pieces. Rook spectrum is integer {-2..14}
    on the 8x8 P_8 x P_8 lattice (verified at construction time).
  * H_pawn_2: NotImplementedError with helpful message
  * expectation: real for Hermitian observables on normalized psi
  * measure_observable_distribution: sum equals ||psi||^2

Run via `python -m pytest tests/test_qm_2d.py -v` from python/, or
directly via `python tests/test_qm_2d.py`.
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

from chess_spectral import qm_2d                              # noqa: E402
from chess_spectral import fen_to_pos                          # noqa: E402


# ---- Test fixtures --------------------------------------------------


@pytest.fixture(scope='module')
def position_starting():
    """Standard chess starting position."""
    return fen_to_pos(
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    )


@pytest.fixture(scope='module')
def position_kasparov_topalov_mid():
    """A non-trivial mid-game position (Kasparov-Topalov 1999, ply ~30).
    Gives a different channel-energy profile than the starting
    position so per-channel tests aren't all degenerate."""
    return fen_to_pos(
        "r4rk1/ppq1bppp/2n2n2/3p4/3P4/2N1BN2/PPQ1BPPP/R4RK1 w - - 0 1"
    )


# ---- state_to_psi ---------------------------------------------------


def test_state_to_psi_shape_and_dtype(position_starting):
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    assert psi.shape == (qm_2d.ENCODING_DIM,)
    assert psi.dtype == np.complex128


def test_state_to_psi_normalized(position_starting,
                                 position_kasparov_topalov_mid):
    """For non-empty positions, psi should be L2-unit on both
    side-to-move parities."""
    for pos in (position_starting, position_kasparov_topalov_mid):
        for side in (True, False):
            psi = qm_2d.state_to_psi(pos, side_to_move=side)
            assert qm_2d.is_normalized(psi), (
                f"||psi|| = {qm_2d.norm(psi)} != 1 for "
                f"side_to_move={side}"
            )


def test_state_to_psi_z2_parity(position_starting,
                                position_kasparov_topalov_mid):
    """psi(state, white) and psi(state, black) should differ only in
    overall sign (same unit-norm direction up to -1)."""
    for pos in (position_starting, position_kasparov_topalov_mid):
        psi_w = qm_2d.state_to_psi(pos, side_to_move=True)
        psi_b = qm_2d.state_to_psi(pos, side_to_move=False)
        max_diff = float(np.max(np.abs(psi_w + psi_b)))
        assert max_diff < 1e-12, (
            f"psi_white + psi_black should be 0 within float error; "
            f"max |diff| = {max_diff}"
        )
        ip = qm_2d.inner_product(psi_w, psi_b)
        assert abs(ip + 1.0) < 1e-10, (
            f"<white|black> should be -1, got {ip}"
        )


def test_state_to_psi_zero_vector_flag():
    """Empty positions encode to the zero vector (cannot be
    normalized). state_to_psi returns the zero vector unchanged
    rather than raising; callers can detect via is_normalized."""
    psi = qm_2d.state_to_psi({}, side_to_move=True)
    assert psi.shape == (qm_2d.ENCODING_DIM,)
    assert np.all(psi == 0.0)
    assert not qm_2d.is_normalized(psi)


# ---- d4_closure -----------------------------------------------------


def test_d4_closure_has_eight_elements():
    """D_4 has order 8 by definition. Sanity that we enumerate all of
    them and identity is first."""
    closure = qm_2d.d4_closure()
    assert len(closure) == 8
    # Identity comes first; check it acts trivially.
    e = closure[0]
    for s in range(qm_2d.BOARD_DIM):
        assert e[s] == s, f"closure[0] should be identity; e[{s}] = {e[s]}"


def test_d4_closure_is_cached():
    """Two calls return the same list object."""
    closure1 = qm_2d.d4_closure()
    closure2 = qm_2d.d4_closure()
    assert closure1 is closure2


def test_d4_closure_elements_are_permutations():
    """Each closure element is a permutation of 0..63 (bijection)."""
    closure = qm_2d.d4_closure()
    for idx, g in enumerate(closure):
        name = qm_2d.d4_element_name(idx)
        assert sorted(g) == list(range(qm_2d.BOARD_DIM)), (
            f"closure[{idx}] ({name}) is not a permutation of 0..63"
        )


def test_d4_element_names():
    """Element-name accessor returns the documented label set."""
    expected = ['e', 'rot90', 'rot180', 'rot270',
                'flip_h', 'flip_v', 'flip_diag', 'flip_anti']
    for i, want in enumerate(expected):
        assert qm_2d.d4_element_name(i) == want


def test_d4_element_name_out_of_range():
    with pytest.raises(ValueError):
        qm_2d.d4_element_name(-1)
    with pytest.raises(ValueError):
        qm_2d.d4_element_name(8)


# ---- d4_unitary_rep -------------------------------------------------


def test_d4_unitary_rep_is_unitary():
    """All 8 D_4 elements lift to unitaries on C^64."""
    closure = qm_2d.d4_closure()
    for idx, g in enumerate(closure):
        U = qm_2d.d4_unitary_rep_64(g)
        assert qm_2d.is_unitary(U), (
            f"U[{idx}] ({qm_2d.d4_element_name(idx)}) is not unitary"
        )


def test_d4_unitary_rep_preserves_norm(position_starting):
    """For psi from a real position, ||U psi|| == ||psi|| for all g."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    closure = qm_2d.d4_closure()
    for idx, g in enumerate(closure):
        U_full = qm_2d.d4_unitary_rep_full(g)
        psi_rotated = U_full @ psi
        n_rot = qm_2d.norm(psi_rotated)
        assert abs(n_rot - 1.0) < 1e-10, (
            f"||U[{idx}] ({qm_2d.d4_element_name(idx)}) psi|| = {n_rot}, "
            "should be 1"
        )


def test_d4_unitary_rep_full_block_structure():
    """U_full = I_10 (x) U_64 -- check shape and nnz block structure."""
    closure = qm_2d.d4_closure()
    g = closure[1]   # rot90
    U_block = qm_2d.d4_unitary_rep_64(g)
    U_full = qm_2d.d4_unitary_rep_full(g)
    assert U_full.shape == (qm_2d.ENCODING_DIM, qm_2d.ENCODING_DIM)
    # Block diagonal: nnz(U_full) == 10 * nnz(U_block).
    assert U_full.nnz == qm_2d.N_CHANNELS * U_block.nnz


def test_d4_unitary_rep_caches():
    """Two calls with the same g should return the same object."""
    closure = qm_2d.d4_closure()
    g = closure[3]   # rot270
    U1 = qm_2d.d4_unitary_rep_64(g)
    U2 = qm_2d.d4_unitary_rep_64(g)
    assert U1 is U2


def test_d4_identity_is_identity_matrix():
    """e -> I_64."""
    closure = qm_2d.d4_closure()
    U = qm_2d.d4_unitary_rep_64(closure[0])
    I = sp.eye(qm_2d.BOARD_DIM, format='csr', dtype=np.complex128)
    diff = U - I
    diff.eliminate_zeros()
    assert diff.nnz == 0


# ---- Channel projector ----------------------------------------------


def test_channel_projector_self_idempotent():
    """P_c is a projector: P_c @ P_c == P_c for each c."""
    for c in range(qm_2d.N_CHANNELS):
        P = qm_2d.channel_projector(c)
        diff = (P @ P) - P
        diff.eliminate_zeros()
        assert diff.nnz == 0, (
            f"P_{c} is not idempotent (P @ P != P), {diff.nnz} nonzero"
        )


def test_channel_projector_orthogonal():
    """Cross terms vanish: P_c @ P_d == 0 for c != d."""
    for c in range(qm_2d.N_CHANNELS):
        P_c = qm_2d.channel_projector(c)
        for d in range(c + 1, qm_2d.N_CHANNELS):
            P_d = qm_2d.channel_projector(d)
            prod = P_c @ P_d
            prod.eliminate_zeros()
            assert prod.nnz == 0, (
                f"P_{c} P_{d} should be 0, got {prod.nnz} nonzero"
            )


def test_channel_projector_completeness():
    """Sum over all 10 channels equals I_640."""
    total = sum(
        qm_2d.channel_projector(c) for c in range(qm_2d.N_CHANNELS)
    )
    I = sp.eye(qm_2d.ENCODING_DIM, format='csr', dtype=np.complex128)
    diff = total - I
    diff.eliminate_zeros()
    assert diff.nnz == 0


def test_channel_projector_index_range():
    """Out-of-range channel indices raise."""
    with pytest.raises(ValueError):
        qm_2d.channel_projector(-1)
    with pytest.raises(ValueError):
        qm_2d.channel_projector(qm_2d.N_CHANNELS)


# ---- Channel probability --------------------------------------------


def test_channel_probabilities_sum_to_one(position_starting,
                                           position_kasparov_topalov_mid):
    """For any normalized psi, sum of channel Born probabilities = 1."""
    for pos in (position_starting, position_kasparov_topalov_mid):
        psi = qm_2d.state_to_psi(pos, side_to_move=True)
        probs = qm_2d.measure_channel_distribution(psi)
        assert probs.shape == (qm_2d.N_CHANNELS,)
        s = float(probs.sum())
        assert abs(s - 1.0) < 1e-10, f"channel probs sum = {s}"
        assert np.all(probs >= -1e-15), (
            f"negative prob: min = {probs.min()}"
        )


def test_prob_channel_matches_distribution(position_starting):
    """prob_channel(psi, c) matches measure_channel_distribution[c]."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    probs = qm_2d.measure_channel_distribution(psi)
    for c in range(qm_2d.N_CHANNELS):
        assert abs(qm_2d.prob_channel(psi, c) - probs[c]) < 1e-15


def test_prob_channel_via_projector(position_starting):
    """Cross-check: prob_channel(psi, c) == <psi|P_c|psi>."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    for c in (0, 4, 9):  # sample three channels: A1, E, FD
        P_c = qm_2d.channel_projector(c)
        e_op = qm_2d.expectation(P_c, psi)
        e_fast = qm_2d.prob_channel(psi, c)
        assert abs(e_op - e_fast) < 1e-12, (
            f"channel {c}: projector expectation {e_op} != "
            f"prob_channel {e_fast}"
        )


def test_prob_channel_index_range(position_starting):
    """Out-of-range channel indices raise on prob_channel too."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    with pytest.raises(ValueError):
        qm_2d.prob_channel(psi, -1)
    with pytest.raises(ValueError):
        qm_2d.prob_channel(psi, qm_2d.N_CHANNELS)


# ---- H_<piece> Hermiticity + spectrum -------------------------------


@pytest.mark.parametrize('piece,name', [
    ('R', 'rook'),
    ('B', 'bishop'),
    ('Q', 'queen'),
    ('K', 'king'),
    ('N', 'knight'),
])
def test_h_piece_hermitian(piece, name):
    """H_<piece>_2 = H_<piece>_2^dagger at machine precision."""
    H = qm_2d.build_H_piece_2(piece)
    assert qm_2d.is_hermitian(H, tol=1e-12), (
        f"H_{name}_2 ({piece!r}) is not Hermitian"
    )


@pytest.mark.parametrize('piece,name,lo_expected,hi_expected', [
    # Empirical spectrum ranges (eigvalsh on the 64x64 lift).
    # Rook is exactly {-2, ..., 14} integer (boundary clipping is
    # mild on the 8x8 lattice for rook). The others are non-integer
    # due to the boundary breaking vertex-transitivity. Bounds below
    # are the empirical min/max with a tiny tolerance margin -- this
    # is a regression check that the piece adjacencies have not
    # silently changed.
    ('R', 'rook',   -2.0,  14.0),
    ('K', 'king',   -3.5321,  7.2909),
    ('N', 'knight', -6.0107,  6.0107),
    ('B', 'bishop', -2.0,    9.1613),
    ('Q', 'queen',  -4.0,   22.9360),
])
def test_h_piece_spectrum_envelope(piece, name, lo_expected, hi_expected):
    """Eigenvalues of H_<piece>_2 lie within the audited envelope.
    Realness comes from Hermiticity (separately verified)."""
    H = qm_2d.build_H_piece_2(piece)
    eigs = np.linalg.eigvalsh(H.toarray())
    re_lo = float(eigs.min())
    re_hi = float(eigs.max())
    tol = 1e-3
    assert re_lo >= lo_expected - tol, (
        f"H_{name}_2 spectrum min {re_lo} below expected {lo_expected}"
    )
    assert re_hi <= hi_expected + tol, (
        f"H_{name}_2 spectrum max {re_hi} above expected {hi_expected}"
    )


def test_h_rook_2_integer_spectrum():
    """H_rook_2 has an integer spectrum on the 8x8 lattice. This is a
    structural property of the rook reach predicate (commutes with
    the 1D path-graph Laplacian on each axis); document + regression-
    test it explicitly."""
    H = qm_2d.build_H_piece_2('R')
    eigs = np.linalg.eigvalsh(H.toarray())
    rounded = np.round(eigs)
    assert np.allclose(eigs, rounded, atol=1e-9), (
        f"H_rook_2 spectrum is not integer: max |frac| = "
        f"{float(np.max(np.abs(eigs - rounded)))}"
    )


@pytest.mark.parametrize('pawn_key', ['P', 'p'])
def test_h_pawn_2_raises(pawn_key):
    """Pawn observables raise NotImplementedError with a deferral
    pointer."""
    with pytest.raises(NotImplementedError) as ei:
        qm_2d.build_H_piece_2(pawn_key)
    msg = str(ei.value)
    assert "kinematic" in msg.lower()
    assert "pseudo-hermitian" in msg.lower() or "eta" in msg.lower()


def test_h_pawn_2_via_attribute_raises():
    """Module attribute access also raises."""
    with pytest.raises(NotImplementedError):
        _ = qm_2d.H_pawn_2


def test_h_piece_unknown_raises():
    """Non-piece characters raise ValueError."""
    with pytest.raises(ValueError):
        qm_2d.build_H_piece_2('X')


# ---- expectation ----------------------------------------------------


def test_expectation_real_on_hermitian(position_starting):
    """For Hermitian H and any psi, <psi|H|psi> is real (returned
    as Python float; imaginary part vanishes within float error)."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    # Take H_rook_2 on the rook channel block (channel 4: E, arbitrary
    # 64-block; H is independent of channel placement). The point is
    # the expectation value is real-valued.
    H = qm_2d.H_rook_2
    block = psi[4 * 64:(4 + 1) * 64]
    val = qm_2d.expectation(H, block)
    assert isinstance(val, float)


def test_expectation_dense_and_sparse_agree(position_starting):
    """Same H delivered as csr or dense -> same expectation."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    H_sparse = qm_2d.H_knight_2
    H_dense = H_sparse.toarray()
    block = psi[5 * 64:(5 + 1) * 64]
    e_sparse = qm_2d.expectation(H_sparse, block)
    e_dense = qm_2d.expectation(H_dense, block)
    assert abs(e_sparse - e_dense) < 1e-12


# ---- measure_observable_distribution --------------------------------


def test_measure_observable_distribution_sums_to_norm(position_starting):
    """For a 64-dim psi-block and a Hermitian observable on C^64,
    the Born probabilities sum to ||psi_block||^2."""
    psi = qm_2d.state_to_psi(position_starting, side_to_move=True)
    block = psi[3 * 64:(3 + 1) * 64].copy()
    H = qm_2d.H_queen_2
    eigvals, probs = qm_2d.measure_observable_distribution(H, block)
    norm_sq = float(np.vdot(block, block).real)
    assert abs(probs.sum() - norm_sq) < 1e-10, (
        f"Born probs should sum to ||block||^2 = {norm_sq}, "
        f"got {probs.sum()}"
    )


def test_measure_observable_distribution_eigvals_distinct():
    """Returned eigenvalues are sorted ascending and distinct
    (within tol)."""
    H = qm_2d.H_rook_2
    psi = np.random.default_rng(42).standard_normal(64).astype(np.complex128)
    psi /= np.linalg.norm(psi)
    eigvals, probs = qm_2d.measure_observable_distribution(H, psi)
    # Strictly ascending after grouping.
    assert np.all(np.diff(eigvals) > 0), (
        f"eigvals not strictly ascending: {eigvals}"
    )
    # Probabilities sum to 1 for a unit-norm input.
    assert abs(probs.sum() - 1.0) < 1e-10


def test_measure_observable_shape_mismatch_raises():
    """Caller passing mismatched shapes raises ValueError."""
    H = qm_2d.H_rook_2
    bad_psi = np.zeros(640, dtype=np.complex128)  # wrong dim
    with pytest.raises(ValueError):
        qm_2d.measure_observable_distribution(H, bad_psi)


# ---- Public API surface ---------------------------------------------


def test_public_api_listed_in___all__():
    """Sanity: a `from chess_spectral.qm_2d import *` would not crash
    by trying to materialize H_pawn_2 (which raises). Verify
    H_pawn_2 is intentionally absent from __all__."""
    assert 'H_pawn_2' not in qm_2d.__all__
    # The five Hermitian pieces are in __all__:
    for name in ('H_rook_2', 'H_bishop_2', 'H_queen_2',
                 'H_king_2', 'H_knight_2'):
        assert name in qm_2d.__all__


def test_dimensions_match_encoder():
    """Constants match encoder.py source-of-truth."""
    from chess_spectral import encoder as _enc2
    assert qm_2d.ENCODING_DIM == _enc2.ENCODING_DIM
    assert qm_2d.N_CHANNELS == _enc2.N_CHANNELS
    assert qm_2d.CHANNEL_DIM == qm_2d.ENCODING_DIM // qm_2d.N_CHANNELS
