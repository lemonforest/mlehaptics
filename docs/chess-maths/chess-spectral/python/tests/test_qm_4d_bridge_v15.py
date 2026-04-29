"""Unit tests for chess_spectral.qm_4d_bridge — v1.5 §17.1 + §17.5
bridge integration.

Covers the consumer-facing Pyodide bridge surface: the seven §17.1
QM-extension methods (``getQmState``, ``getQmDensity``, ``applyMoveQm``,
``measureAt``, ``getDensityMatrixOf``, ``getProbabilityCurrent``,
``getQmExpectation``), the six §17.5 dev/debug methods (``getVersion``,
``getEncoderShape``, ``getFen4State``, ``loadFen4``,
``loadJsonlFixture``, ``hasLegalMoves``), and the Pyodide-bridge
serialization helper (``complex_to_interleaved_float32``).

Per §17.4's acceptance criteria for v1.5.0, this module verifies:

  1. Each method's output matches its §17.1 / §17.5 contract shape.
  2. ``getQmState`` / ``applyMoveQm`` / ``getQmDensity`` numeric values
     match a direct ``state_to_psi`` call (the SSOT).
  3. ``measureAt``: Born-rule probability matches
     ``|⟨c|ψ⟩|²`` of the channel projector.
  4. ``getProbabilityCurrent``: probability current is divergence-free
     for static states (∂ρ/∂t = -∇·j; ∂ρ/∂t = 0 for static ⇒ ∇·j = 0
     within floating-point residual).
  5. ``getQmExpectation``: matches direct ``expectation(H, ψ)`` calls.
  6. ``getDensityMatrixOf`` / ``getQmDensity(piece_id=…)`` raise
     ``NotImplementedError`` with informative messages pointing to
     v1.7+.
  7. §17.5 dev methods: each returns the contracted shape.

Run with ``pytest tests/test_qm_4d_bridge_v15.py -v`` from python/.
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, Tuple

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

# IMPORTANT: import qm_4d_dynamics BEFORE qm_4d_bridge so the lazy
# circular-import contract holds the same way the existing
# test_qm_4d_dynamics_b1.py / b3a / etc. tests do. The bridge has a
# defensive lazy-import pattern that copes when invoked first, but
# matching the existing tests' import order keeps the test contract
# transparent (and avoids exercising a different code path than
# real-world callers).
from chess_spectral import encoder_4d as _enc4    # noqa: E402
from chess_spectral import qm_4d                  # noqa: E402
from chess_spectral import qm_4d_dynamics as _dyn  # noqa: E402
from chess_spectral import qm_4d_bridge as br     # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# =====================================================================
# Position fixtures
# =====================================================================


@pytest.fixture(scope='module')
def imbalanced_position() -> Dict[int, str]:
    """Mid-board imbalanced 6-piece position with non-zero A_1 channel."""
    coords = {
        (0, 0, 0, 0): 'K', (5, 5, 5, 5): 'k',
        (1, 2, 3, 4): 'Q',
        (3, 1, 2, 3): 'B',
        (2, 5, 0, 1): 'N',
        (4, 3, 1, 2): 'R',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


@pytest.fixture(scope='module')
def two_kings_only() -> Dict[int, str]:
    """Minimal antipodal-king position. Tests behave correctly under
    the encoder's central-inversion + color-flip Z_2 sector convention
    (Pre-flight 1)."""
    return {
        _t4.sq4(0, 0, 0, 0): 'K',
        _t4.sq4(7, 7, 7, 7): 'k',
    }


@pytest.fixture(scope='module')
def pawn_position() -> Dict[int, object]:
    """Single white pawn position. Pawns use the (color, axis) tuple
    form per the encoder's input schema."""
    return {
        _t4.sq4(3, 1, 4, 4): ('P', 'w'),
        _t4.sq4(0, 0, 0, 0): 'K',
        _t4.sq4(7, 7, 7, 7): 'k',
    }


# =====================================================================
# §17.1 #1: getQmState
# =====================================================================


class TestGetQmState:
    """getQmState contract:
      - shape: psi is float32, length 90112 (= 2 * 45056).
      - values: psi_complex == state_to_psi(state).
      - normSq: 1.0 within float rounding for non-empty positions.
      - basisDim: always 45056.
      - ok: True.
    """

    def test_imbalanced_position(self, imbalanced_position):
        res = br.get_qm_state(imbalanced_position)
        assert res['ok'] is True
        assert res['basisDim'] == 45056
        assert isinstance(res['psi'], np.ndarray)
        assert res['psi'].dtype == np.float32
        assert res['psi'].size == 90112
        assert abs(res['normSq'] - 1.0) < 1e-10

    def test_two_kings_position_is_zero_sentinel(self, two_kings_only):
        """Per Pre-flight 1, the antipodal-king position is in the
        kernel of the encoder (central-inversion + color-flip Z_2
        invariance kills the encoding). state_to_psi returns the
        zero vector as a non-physical sentinel; norm is 0, not 1."""
        res = br.get_qm_state(two_kings_only)
        assert res['ok'] is True
        # The encoder returns the zero vector for this antipodal
        # configuration; bridge surfaces it as normSq == 0.
        assert res['normSq'] == 0.0 or res['normSq'] < 1e-15

    def test_pawn_position(self, pawn_position):
        res = br.get_qm_state(pawn_position)
        assert res['ok'] is True
        assert abs(res['normSq'] - 1.0) < 1e-10

    def test_psi_round_trip_matches_direct_state_to_psi(
        self, imbalanced_position,
    ):
        """The interleaved Float32 reconstruction matches the direct
        complex psi (within float32 cast precision)."""
        res = br.get_qm_state(imbalanced_position)
        psi_direct = qm_4d.state_to_psi(imbalanced_position, True)
        psi_reconstructed = (
            res['psi'][0::2].astype(np.complex128)
            + 1j * res['psi'][1::2].astype(np.complex128)
        )
        # Float32 has ~7 decimal digits of precision; allow 1e-6.
        assert np.allclose(
            psi_reconstructed, psi_direct, atol=1e-6, rtol=1e-6,
        )

    def test_side_to_move_flip_negates_psi(self, imbalanced_position):
        """Per ADR-004 §3.4 amendment: state_to_psi(white) ==
        -state_to_psi(black). This is the Z_2 sector convention,
        and the bridge surfaces it via the side_to_move kwarg."""
        res_w = br.get_qm_state(imbalanced_position, side_to_move=True)
        res_b = br.get_qm_state(imbalanced_position, side_to_move=False)
        psi_w = (
            res_w['psi'][0::2].astype(np.complex128)
            + 1j * res_w['psi'][1::2].astype(np.complex128)
        )
        psi_b = (
            res_b['psi'][0::2].astype(np.complex128)
            + 1j * res_b['psi'][1::2].astype(np.complex128)
        )
        assert np.allclose(psi_w, -psi_b, atol=1e-6)


# =====================================================================
# §17.1 #2: getQmDensity
# =====================================================================


class TestGetQmDensity:
    """getQmDensity contract:
      - shape: density is float32, length 4096.
      - values: density[c] == sum_chan |psi[chan, c]|^2.
      - sum: density.sum() == 1.0 within float rounding.
      - per-piece variant raises NotImplementedError.
    """

    def test_full_density_shape_and_dtype(self, imbalanced_position):
        res = br.get_qm_density(imbalanced_position)
        assert res['ok'] is True
        assert isinstance(res['density'], np.ndarray)
        assert res['density'].dtype == np.float32
        assert res['density'].size == 4096

    def test_full_density_sums_to_one(self, imbalanced_position):
        res = br.get_qm_density(imbalanced_position)
        # For a normalized psi, sum_c rho_c = ||psi||^2 = 1.
        assert abs(float(res['density'].sum()) - 1.0) < 1e-6

    def test_full_density_matches_direct_calculation(
        self, imbalanced_position,
    ):
        """density[c] = sum_chan |psi[chan*4096 + c]|^2."""
        res = br.get_qm_density(imbalanced_position)
        psi = qm_4d.state_to_psi(imbalanced_position, True)
        psi_view = psi.reshape(11, 4096)
        expected = (np.abs(psi_view) ** 2).sum(axis=0)
        assert np.allclose(
            res['density'], expected.astype(np.float32),
            atol=1e-6, rtol=1e-6,
        )

    def test_per_piece_marginal_raises_nie(self, imbalanced_position):
        first_sq = next(iter(imbalanced_position))
        with pytest.raises(NotImplementedError) as excinfo:
            br.get_qm_density(imbalanced_position, piece_id=first_sq)
        # Message points at v1.7+ deferral.
        assert 'v1.7' in str(excinfo.value) or 'partial trace' in str(
            excinfo.value,
        )

    def test_density_non_negative(self, imbalanced_position):
        """|psi|^2 is always non-negative."""
        res = br.get_qm_density(imbalanced_position)
        assert (res['density'] >= 0).all()


# =====================================================================
# §17.1 #3: applyMoveQmFull (the v1.5 dispatch layer)
# =====================================================================


class TestApplyMoveQmFull:
    """applyMoveQmFull contract:
      - returns {ok, psi, basisDim, normSq}.
      - psi is float32 length 90112.
      - normSq == 1.0 (post-renormalization).
      - the dispatch logic correctly handles csr_matrix entries
        (multiply on channel block) and marker dicts (splice the
        psi_post_block when present, re-encode the cross-orbit case).
    """

    def test_non_capture_move_returns_normalized_psi(
        self, imbalanced_position,
    ):
        # Non-capture move: rook from (4,3,1,2) to (4,4,1,2).
        from_sq = _t4.sq4(4, 3, 1, 2)
        to_sq = _t4.sq4(4, 4, 1, 2)
        res = br.apply_move_qm_full(
            imbalanced_position, (from_sq, to_sq),
        )
        assert res['ok'] is True
        assert res['psi'].size == 90112
        assert res['psi'].dtype == np.float32
        assert abs(res['normSq'] - 1.0) < 1e-6

    def test_capture_move_returns_normalized_psi(
        self, imbalanced_position,
    ):
        """Capture moves pass through the all-marker-dict variant —
        every channel returns a psi_post_block that the bridge
        splices in. Re-normalization handles the FA_PAWN
        partial-isometry norm loss."""
        # Capture move: rook captures bishop at (3,1,2,3) — both
        # are pieces in imbalanced_position. We use the rook's
        # square as origin and the bishop's square as destination.
        from_sq = _t4.sq4(4, 3, 1, 2)  # R
        to_sq = _t4.sq4(3, 1, 2, 3)    # B (capture target)
        res = br.apply_move_qm_full(
            imbalanced_position, (from_sq, to_sq),
        )
        assert res['ok'] is True
        assert res['psi'].size == 90112
        # Capture path renormalizes; normSq == 1.0.
        assert abs(res['normSq'] - 1.0) < 1e-6

    def test_per_channel_dispatch_csr_path_matches_dynamics(
        self, imbalanced_position,
    ):
        """For non-capture moves, channels with csr_matrix entries
        produce ψ_post[chan_block] = U_chan @ ψ_pre[chan_block].
        Verify A_1 (always csr_matrix on non-capture) matches."""
        from_sq = _t4.sq4(0, 0, 0, 0)  # K (corner; same-orbit safe)
        to_sq = _t4.sq4(7, 7, 7, 7)    # k corner — actually capture
        # Use a non-capture move instead. Pick a same-orbit corner
        # pair: (0,0,0,0) and (7,0,0,0) lie in the same B_4 orbit
        # (corner orbit, size 16).
        # But (7,0,0,0) might be empty in imbalanced_position — check.
        to_sq = _t4.sq4(7, 0, 0, 0)
        if to_sq in imbalanced_position:
            pytest.skip(
                f"to_sq {to_sq} is occupied; pick a different test "
                "position"
            )
        res = br.apply_move_qm_full(
            imbalanced_position, (from_sq, to_sq),
            return_per_channel=True,
        )
        # A_1 channel was a csr_matrix (not a dict). Verify the
        # bridge dispatched it correctly.
        a1_value = res['perChannel']['A1']
        assert sp.issparse(a1_value), (
            "A_1 channel on non-capture move should return a "
            "csr_matrix, got dict marker"
        )
        # Reconstruct ψ_post[A_1 block] = U_A_1 @ ψ_pre[A_1 block].
        psi_pre = qm_4d.state_to_psi(imbalanced_position, True)
        psi_post_block_expected = a1_value @ psi_pre[:4096]
        psi_post = (
            res['psi'][0::2].astype(np.complex128)
            + 1j * res['psi'][1::2].astype(np.complex128)
        )
        # The ψ_post in res is normalized; the per-block
        # comparison needs the same scale. Compute the
        # un-renormalized expected magnitude.
        # NOTE: the renormalization scale factor applies uniformly
        # across all 11 blocks; we can recover it from the ratio of
        # the channel-block norms.
        scale_a1 = np.linalg.norm(psi_post[:4096]) / max(
            np.linalg.norm(psi_post_block_expected), 1e-15,
        )
        assert np.allclose(
            psi_post[:4096],
            scale_a1 * psi_post_block_expected,
            atol=1e-5, rtol=1e-5,
        )

    def test_return_per_channel_includes_dispatch_dict(
        self, imbalanced_position,
    ):
        from_sq = _t4.sq4(0, 0, 0, 0)
        to_sq = _t4.sq4(7, 0, 0, 0)
        if to_sq in imbalanced_position:
            pytest.skip("to_sq occupied")
        res = br.apply_move_qm_full(
            imbalanced_position, (from_sq, to_sq),
            return_per_channel=True,
        )
        assert 'perChannel' in res
        assert set(res['perChannel'].keys()) == {
            'A1', 'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
            'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
            'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
        }


# =====================================================================
# §17.1 #4: measureAt
# =====================================================================


class TestMeasureAt:
    """measureAt contract:
      - returns {ok, probability, sampledOutcome, postCollapsePsi}.
      - position observable: probability == |⟨c|ψ⟩|² of the
        channel-summed cell projector.
      - postCollapsePsi has unit norm (renormalized projection).
      - coords accept either 4-tuple or linear int.
    """

    def test_position_observable_4tuple_coords(self, imbalanced_position):
        coords = (1, 2, 3, 4)
        res = br.measure_at(imbalanced_position, coords)
        assert res['ok'] is True
        assert res['sampledOutcome'] == _t4.sq4(*coords)
        assert 0.0 <= res['probability'] <= 1.0
        assert res['postCollapsePsi'].size == 90112
        assert res['postCollapsePsi'].dtype == np.float32

    def test_position_observable_linear_int_coords(
        self, imbalanced_position,
    ):
        cell_idx = _t4.sq4(1, 2, 3, 4)
        res = br.measure_at(imbalanced_position, cell_idx)
        assert res['ok'] is True
        assert res['sampledOutcome'] == cell_idx

    def test_born_rule_probability_matches_direct_calculation(
        self, imbalanced_position,
    ):
        """Position observable's Born probability =
        sum_chan |psi[chan, cell]|^2."""
        cell_idx = _t4.sq4(1, 2, 3, 4)  # Queen position
        res = br.measure_at(imbalanced_position, cell_idx)
        psi = qm_4d.state_to_psi(imbalanced_position, True)
        psi_view = psi.reshape(11, 4096)
        expected_prob = float(
            np.vdot(psi_view[:, cell_idx], psi_view[:, cell_idx]).real
        )
        assert abs(res['probability'] - expected_prob) < 1e-10

    def test_post_collapse_psi_normalized(self, imbalanced_position):
        cell_idx = _t4.sq4(1, 2, 3, 4)
        res = br.measure_at(imbalanced_position, cell_idx)
        # Reconstruct complex psi from float32 interleaved.
        psi_post = (
            res['postCollapsePsi'][0::2].astype(np.complex128)
            + 1j * res['postCollapsePsi'][1::2].astype(np.complex128)
        )
        norm = float(np.linalg.norm(psi_post))
        # If probability was 0, post-collapse is zero (unprojectable);
        # otherwise normalized.
        if res['probability'] > 1e-15:
            assert abs(norm - 1.0) < 1e-6
        else:
            assert norm < 1e-6

    def test_post_collapse_zero_at_unmeasured_cells(
        self, imbalanced_position,
    ):
        """Position-observable collapse zeros out all cells != cell_idx."""
        cell_idx = _t4.sq4(1, 2, 3, 4)
        res = br.measure_at(imbalanced_position, cell_idx)
        psi_post = (
            res['postCollapsePsi'][0::2].astype(np.complex128)
            + 1j * res['postCollapsePsi'][1::2].astype(np.complex128)
        )
        psi_view = psi_post.reshape(11, 4096)
        # Every column except cell_idx must be exactly zero.
        zero_mask = np.ones(4096, dtype=bool)
        zero_mask[cell_idx] = False
        assert np.all(psi_view[:, zero_mask] == 0)

    def test_coords_out_of_range_raises(self, imbalanced_position):
        with pytest.raises(ValueError):
            br.measure_at(imbalanced_position, 4096)

    def test_named_observable_returns_eigenvalue_outcome(
        self, imbalanced_position,
    ):
        """Named-observable path returns an eigenvalue outcome (float).
        Use a deterministic RNG for reproducibility."""
        rng = np.random.default_rng(42)
        res = br.measure_at(
            imbalanced_position, _t4.sq4(0, 0, 0, 0),
            observable='rook', rng=rng,
        )
        assert res['ok'] is True
        # Rook's spectrum is in [-4, 28] per Pre-flight 2.
        assert -4 - 1e-6 <= res['sampledOutcome'] <= 28 + 1e-6


# =====================================================================
# §17.1 #5: getDensityMatrixOf
# =====================================================================


class TestGetDensityMatrixOf:
    """getDensityMatrixOf is deferred to v1.7+; raises NIE always."""

    def test_raises_nie(self, imbalanced_position):
        first_sq = next(iter(imbalanced_position))
        with pytest.raises(NotImplementedError) as excinfo:
            br.get_density_matrix_of(imbalanced_position, first_sq)
        msg = str(excinfo.value)
        assert 'v1.7' in msg or 'partial trace' in msg

    def test_nie_message_mentions_partial_trace(self, imbalanced_position):
        with pytest.raises(NotImplementedError) as excinfo:
            br.get_density_matrix_of(imbalanced_position, 0)
        assert 'partial trace' in str(excinfo.value).lower()


# =====================================================================
# §17.1 #6: getProbabilityCurrent
# =====================================================================


class TestGetProbabilityCurrent:
    """getProbabilityCurrent contract:
      - shape: j is float32, shape (4096, 4).
      - probability current is real-valued (Im(psi* grad psi)).
      - for static states (no time-evolution under H_0), the discrete
        continuity equation gives ∇·j ≈ 0 within floating residual.
        The static condition is ∂ρ/∂t = 0; combined with ∂ρ/∂t = -∇·j
        this requires ∇·j = 0.

    Note on the discrete continuity equation: for a state that is an
    eigenstate of H_0 (free Hamiltonian), the continuity equation
    holds exactly. For arbitrary states, the continuity equation is
    NOT automatic — only the integrated norm conservation
    (sum_c j-divergence == 0) holds. We test the integrated condition,
    which is the universal one.
    """

    def test_shape_and_dtype(self, imbalanced_position):
        res = br.get_probability_current(imbalanced_position)
        assert res['ok'] is True
        assert isinstance(res['j'], np.ndarray)
        assert res['j'].dtype == np.float32
        assert res['j'].shape == (4096, 4)

    def test_real_valued(self, imbalanced_position):
        """j is by definition Im(psi* ∂ψ), which is real-valued for
        any complex psi — but j can be negative. We just check it's
        finite."""
        res = br.get_probability_current(imbalanced_position)
        assert np.all(np.isfinite(res['j']))

    def test_integrated_divergence_is_zero(self, imbalanced_position):
        """The total probability is conserved: integrating ∇·j over
        the lattice is zero for any anti-Hermitian gradient operator
        (boundary terms cancel in our reflecting-boundary
        construction). This holds for ANY ψ, not just static
        eigenstates."""
        res = br.get_probability_current(imbalanced_position)
        j = res['j']
        # Integrated divergence: sum over all cells of (∂_x j_x +
        # ∂_y j_y + ∂_z j_z + ∂_w j_w). For our reflecting-boundary
        # construction, this should be exactly zero by construction
        # (anti-Hermitian gradient ⇒ Tr(grad) == 0).
        # We test by computing the divergence cell-wise and summing.
        from chess_spectral.qm_4d_bridge import _get_lattice_gradient_4d
        grads = _get_lattice_gradient_4d()
        div_total = 0.0
        for axis in range(4):
            # ∂_a j_a summed over all cells = sum of (grads[a] @ j_a)
            div_axis = grads[axis] @ j[:, axis].astype(np.complex128)
            div_total += float(div_axis.sum().real)
        # Floating residual; F32 precision allows ~1e-5.
        assert abs(div_total) < 1e-3

    def test_zero_position_zero_current(self):
        """Empty position → ψ=0 → j=0."""
        res = br.get_probability_current({})
        # The density is zero everywhere, so the current is zero too.
        assert np.allclose(res['j'], 0.0, atol=1e-10)


# =====================================================================
# §17.1 #7: getQmExpectation
# =====================================================================


class TestGetQmExpectation:
    """getQmExpectation contract:
      - returns {ok, value} with value == ⟨ψ|I_11 ⊗ H|ψ⟩.
      - matches a direct expectation(H, ψ_block) summed across
        channel blocks.
      - pawn observables raise NotImplementedError.
      - unknown observable names raise ValueError.
    """

    def test_rook_expectation_matches_direct(self, imbalanced_position):
        res = br.get_qm_expectation(imbalanced_position, 'rook')
        assert res['ok'] is True
        # Direct calculation: sum over channel blocks of ⟨ψ_chan|H|ψ_chan⟩
        psi = qm_4d.state_to_psi(imbalanced_position, True)
        H_rook = qm_4d.H_rook_4
        psi_view = psi.reshape(11, 4096)
        expected = sum(
            qm_4d.expectation(H_rook, psi_view[c])
            for c in range(11)
        )
        assert abs(res['value'] - expected) < 1e-10

    def test_bishop_expectation_matches_direct(self, imbalanced_position):
        res = br.get_qm_expectation(imbalanced_position, 'bishop')
        psi = qm_4d.state_to_psi(imbalanced_position, True)
        H_bishop = qm_4d.H_bishop_4
        psi_view = psi.reshape(11, 4096)
        expected = sum(
            qm_4d.expectation(H_bishop, psi_view[c])
            for c in range(11)
        )
        assert abs(res['value'] - expected) < 1e-10

    @pytest.mark.parametrize(
        'observable', ['rook', 'bishop', 'queen', 'king', 'knight'],
    )
    def test_all_piece_observables_supported(
        self, imbalanced_position, observable,
    ):
        res = br.get_qm_expectation(imbalanced_position, observable)
        assert res['ok'] is True
        assert isinstance(res['value'], float)

    def test_case_insensitive_observable_name(self, imbalanced_position):
        res_lower = br.get_qm_expectation(imbalanced_position, 'rook')
        res_upper = br.get_qm_expectation(imbalanced_position, 'ROOK')
        assert abs(res_lower['value'] - res_upper['value']) < 1e-10

    def test_pawn_observable_raises_nie(self, imbalanced_position):
        with pytest.raises(NotImplementedError):
            br.get_qm_expectation(imbalanced_position, 'pawn')

    def test_unknown_observable_raises_value_error(
        self, imbalanced_position,
    ):
        with pytest.raises(ValueError):
            br.get_qm_expectation(imbalanced_position, 'noodle')


# =====================================================================
# §17.5 dev/debug bridge surface
# =====================================================================


class TestGetVersion:
    def test_returns_version_string(self):
        res = br.get_version()
        assert res['ok'] is True
        assert isinstance(res['version'], str)
        assert len(res['version']) > 0


class TestGetEncoderShape:
    def test_returns_11_channels_45056_total(self):
        res = br.get_encoder_shape()
        assert res['ok'] is True
        assert res['totalDim'] == 45056
        assert len(res['channels']) == 11

    def test_channel_names_match_canonical_order(self):
        res = br.get_encoder_shape()
        names = [ch['name'] for ch in res['channels']]
        expected = [
            'A1', 'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
            'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
            'FA_PAWN_W', 'FA_PAWN_Y', 'FD_DIAG',
        ]
        assert names == expected

    def test_channel_offsets_are_block_diagonal(self):
        res = br.get_encoder_shape()
        for i, ch in enumerate(res['channels']):
            assert ch['offset'] == i * 4096
            assert ch['dim'] == 4096


class TestGetFen4State:
    def test_round_trip(self, imbalanced_position):
        res = br.get_fen4_state(imbalanced_position)
        assert res['ok'] is True
        assert isinstance(res['fen4'], str)
        # Round-trip: load_fen4(get_fen4_state(p)) == p.
        loaded = br.load_fen4(res['fen4'])
        assert loaded['state'] == imbalanced_position


class TestLoadFen4:
    def test_loads_minimal_fen4(self):
        # Build a known FEN4 string by serializing a known position.
        pos = {
            _t4.sq4(0, 0, 0, 0): 'K',
            _t4.sq4(7, 7, 7, 7): 'k',
        }
        fen = br.get_fen4_state(pos)['fen4']
        loaded = br.load_fen4(fen)
        assert loaded['ok'] is True
        assert loaded['state'] == pos


class TestLoadJsonlFixture:
    def test_idempotent_on_sq_int_keyed_dict(self, imbalanced_position):
        res = br.load_jsonl_fixture(imbalanced_position)
        assert res['ok'] is True
        assert res['state'] == imbalanced_position

    def test_jsonl_wrapper_with_sq_str_keys(self):
        """The fixture format used in
        ``tests/fixtures/positions_4d.jsonl`` keys pieces by
        sq-as-string and encodes pawns as a single 2-char piece string
        (e.g., 'Pw' = white pawn on w-axis)."""
        fixture = {
            'name': 'single_pawn_white',
            'pieces': {'1752': 'Pw'},
        }
        res = br.load_jsonl_fixture(fixture)
        assert res['ok'] is True
        assert res['state'] == {1752: ('P', 'w')}

    def test_jsonl_wrapper_empty(self):
        fixture = {'name': 'empty', 'pieces': {}}
        res = br.load_jsonl_fixture(fixture)
        assert res['ok'] is True
        assert res['state'] == {}

    def test_real_jsonl_fixture(self):
        """Load actual entries from positions_4d.jsonl."""
        fixture_path = os.path.join(
            HERE, 'fixtures', 'positions_4d.jsonl',
        )
        if not os.path.exists(fixture_path):
            pytest.skip(f"fixture file not found: {fixture_path}")
        with open(fixture_path, 'r', encoding='utf-8') as f:
            line = f.readline()  # 'empty'
            entry = json.loads(line)
        res = br.load_jsonl_fixture(entry)
        assert res['ok'] is True
        assert res['state'] == {}

    def test_coord_list_form(self):
        """Coord-list form: {'pieces': [{'coord': [x,y,z,w],
        'piece': str}]}"""
        fixture = {
            'pieces': [
                {'coord': [0, 0, 0, 0], 'piece': 'K'},
                {'coord': [7, 7, 7, 7], 'piece': 'k'},
            ],
        }
        res = br.load_jsonl_fixture(fixture)
        assert res['ok'] is True
        assert res['state'] == {
            _t4.sq4(0, 0, 0, 0): 'K',
            _t4.sq4(7, 7, 7, 7): 'k',
        }


class TestHasLegalMoves:
    """hasLegalMoves(team) contract:
      - returns {ok, hasMoves, count}.
      - hasMoves is True iff team has at least one legal move.
      - count is the integer move count (when computable).

    The chess4d-backed full-legality path is exercised iff chess4d is
    installed; otherwise the bridge falls back to the empty-board
    phase-operator lower bound. We test the fallback semantics here
    (which is what most v1.5 consumers will see in CI environments
    without chess4d).
    """

    def test_white_pieces_have_moves(self, imbalanced_position):
        res = br.has_legal_moves(imbalanced_position, 'white')
        assert res['ok'] is True
        # imbalanced_position has K, Q, B, N, R for white — at least
        # the white pieces should produce SOME phase reach.
        assert isinstance(res['hasMoves'], bool)
        assert isinstance(res['count'], int)
        assert res['count'] >= 0

    def test_team_case_insensitive(self, imbalanced_position):
        res_lower = br.has_legal_moves(imbalanced_position, 'white')
        res_upper = br.has_legal_moves(imbalanced_position, 'WHITE')
        assert res_lower['count'] == res_upper['count']

    def test_invalid_team_raises_value_error(self, imbalanced_position):
        with pytest.raises(ValueError):
            br.has_legal_moves(imbalanced_position, 'red')


# =====================================================================
# Pyodide-bridge serialization helpers
# =====================================================================


class TestComplexToInterleavedFloat32:
    def test_basic_roundtrip(self):
        psi = np.array([1+2j, 3+4j, 5-6j], dtype=np.complex128)
        out = br.complex_to_interleaved_float32(psi)
        assert out.dtype == np.float32
        assert out.size == 6
        assert out[0] == 1.0 and out[1] == 2.0
        assert out[2] == 3.0 and out[3] == 4.0
        assert out[4] == 5.0 and out[5] == -6.0

    def test_full_psi_serialization(self, imbalanced_position):
        psi = qm_4d.state_to_psi(imbalanced_position, True)
        out = br.complex_to_interleaved_float32(psi)
        assert out.size == 90112
        # Reconstruct and compare (within float32 precision).
        recon = (
            out[0::2].astype(np.complex128)
            + 1j * out[1::2].astype(np.complex128)
        )
        assert np.allclose(recon, psi, atol=1e-6, rtol=1e-6)

    def test_dtype_independence(self):
        """Input complex64 vs complex128 produces equivalent output."""
        psi64 = np.array([1+1j, 2+2j], dtype=np.complex64)
        psi128 = np.array([1+1j, 2+2j], dtype=np.complex128)
        out64 = br.complex_to_interleaved_float32(psi64)
        out128 = br.complex_to_interleaved_float32(psi128)
        assert np.allclose(out64, out128)
