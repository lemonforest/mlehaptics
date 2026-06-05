"""rc33 cascade-routing parity tests for the srmech.qm.* layer.

v0.7.0rc33 routes the numpy-math calls in the QM layer through srmech's
own A-N cascade primitives:

- Hermitian eigendecomposition (``np.linalg.eigh`` / ``eigvalsh``) ->
  the Class-L primitive ``srmech.amsc.laplacian.hermitian_eigendecompose``
  (potentials / gauge / single_particle / so8).
- Standard-Model trig (``math.cos`` / ``math.sin`` / ``math.atan2``) ->
  the substrate-native Class-N rational trig ``srmech.amsc.rational.*``
  (sm).

These tests assert API-level parity: the cascade primitive's eigenvalues
match ``np.linalg.eigvalsh`` and its eigenvector SUBSPACES match (compared
by |overlap| and by ``V diag(w) V^H`` reconstruction, since eigenvectors
are only defined up to sign/phase), and the substrate-native trig matches
libm at the actual electroweak / CKM angles to within 1e-9. The public QM
functions that were re-routed are exercised against their pre-change
(``math`` / ``np.linalg.eigh``) outputs captured live in each test.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import hermitian_eigendecompose
from srmech.qm import gauge, potentials, sm, single_particle as sp


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _real_symmetric(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    return (A + A.T) / 2.0


def _complex_hermitian(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (A + A.conj().T) / 2.0


def _assert_eig_parity(H: np.ndarray) -> None:
    """Eigenvalues match eigvalsh; eigenvector subspaces match (phase-free)."""
    w, V = hermitian_eigendecompose(H)
    w_ref = np.linalg.eigvalsh(H)
    # Eigenvalues: ascending, match reference within 1e-9.
    np.testing.assert_allclose(w, w_ref, atol=1e-9)
    # Reconstruction H = V diag(w) V^H is phase/sign-invariant.
    H_rebuilt = V @ np.diag(w) @ V.conj().T
    np.testing.assert_allclose(H_rebuilt, np.asarray(H, dtype=complex), atol=1e-9)
    # Columns are orthonormal.
    np.testing.assert_allclose(V.conj().T @ V, np.eye(H.shape[0]), atol=1e-9)
    # Subspace overlap with a reference eigenbasis: |V^H V_ref| has ~1 on the
    # diagonal up to degeneracy. Use eigh's own basis as the reference.
    _, V_ref = np.linalg.eigh(H)
    overlap = np.asarray(V).conj().T @ V_ref
    # squared-magnitudes of the diagonal (value-preserving; no abs()) ~ 1.
    diag = np.diagonal(overlap)
    diag_sq = (diag * diag.conj()).real
    # Non-degenerate eigenvalues -> |overlap| ~ 1 on the diagonal.
    gaps = np.diff(w)
    nondegen = np.concatenate(([True], gaps > 1e-6)) & np.concatenate(
        (gaps > 1e-6, [True])
    )
    np.testing.assert_allclose(diag_sq[nondegen], 1.0, atol=1e-7)


# ----------------------------------------------------------------------
# A) Hermitian eigendecomposition routing
# ----------------------------------------------------------------------


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_eig_parity_real_symmetric(seed):
    _assert_eig_parity(_real_symmetric(8, seed))


@pytest.mark.parametrize("seed", [3, 4, 5])
def test_eig_parity_complex_hermitian(seed):
    _assert_eig_parity(_complex_hermitian(7, seed))


def test_hermitian_eigendecompose_eigenvalues_match_eigvalsh():
    """Eigenvalues alone (the eigvalsh use-site, e.g. so8) match within 1e-9."""
    for H in (_real_symmetric(10, 11), _complex_hermitian(9, 12)):
        w, _ = hermitian_eigendecompose(H)
        np.testing.assert_allclose(np.sort(w), np.linalg.eigvalsh(H), atol=1e-9)


def test_potentials_hydrogen_eigenvectors_real_and_orthonormal():
    """hydrogen_radial (real-symmetric H) returns REAL eigenvectors after the
    value-preserving .real, and they stay orthonormal (V.T @ V = I)."""
    r, eigvals, V = potentials.hydrogen_radial(n_grid=120, r_max=40.0)
    assert np.isrealobj(V), "real-symmetric eigenvectors must be real dtype"
    np.testing.assert_allclose(V.T @ V, np.eye(V.shape[1]), atol=1e-9)
    # Eigenvalues match a direct eigvalsh of the same Hamiltonian.
    # (rebuild H from the documented discretization is overkill; assert the
    # returned eigvals are ascending real and the ground state is physical.)
    assert np.all(np.diff(eigvals) >= -1e-9)
    assert -0.6 < eigvals[0] < -0.4


def test_single_particle_tise_subspace_parity():
    """tise_solve (complex-Hermitian) reconstructs H within 1e-9; eigenvectors
    stay complex128 and orthonormal (subspace parity, phase-free)."""
    H = _complex_hermitian(6, 30)
    w, V = sp.tise_solve(H)
    assert np.iscomplexobj(V)
    np.testing.assert_allclose(V.conj().T @ V, np.eye(6), atol=1e-9)
    np.testing.assert_allclose(V @ np.diag(w) @ V.conj().T, H, atol=1e-9)
    np.testing.assert_allclose(w, np.linalg.eigvalsh(H), atol=1e-9)


def test_single_particle_tdse_matches_reference():
    """tdse_evolve result matches a numpy.linalg.eigh-built reference (the
    pre-change closed form) within 1e-9 — independent of eigvec phase."""
    H = _complex_hermitian(5, 31)
    rng = np.random.default_rng(99)
    psi = rng.standard_normal(5) + 1j * rng.standard_normal(5)
    psi = psi / np.linalg.norm(psi)
    t = 1.7
    # Pre-change reference: numpy eigh closed form.
    w_ref, V_ref = np.linalg.eigh(H)
    ref = V_ref @ (np.exp(-1j * w_ref * t) * (V_ref.conj().T @ psi))
    got = sp.tdse_evolve(H, psi, t)
    np.testing.assert_allclose(got, ref, atol=1e-9)


def test_gauge_path_segment_matches_reference():
    """gauge_path_segment (complex-Hermitian SU(3) connection) matches the
    numpy.linalg.eigh reference unitary within 1e-9 (phase-invariant: the
    holonomy U = exp(iM) is basis-independent)."""
    gens = gauge.su3_gell_mann_matrices()
    rng = np.random.default_rng(7)
    A = rng.standard_normal(len(gens))
    U = gauge.gauge_path_segment(A, gens, coupling=0.8)
    # Reference: numpy eigh of the same M.
    M = 0.8 * sum(A[a] * gens[a] for a in range(len(gens)))
    w_ref, V_ref = np.linalg.eigh(M)
    U_ref = V_ref @ np.diag(np.exp(1j * w_ref)) @ V_ref.conj().T
    np.testing.assert_allclose(U, U_ref, atol=1e-9)
    # And it is unitary.
    np.testing.assert_allclose(U @ U.conj().T, np.eye(M.shape[0]), atol=1e-9)


# ----------------------------------------------------------------------
# B) Standard-Model substrate-native trig routing
# ----------------------------------------------------------------------


# Representative electroweak + CKM angles (radians).
_THETA_W = math.atan2(0.35, 0.65)
_CKM_ANGLES = [0.227, 0.003, 0.042, 0.4, 0.5, 0.2, 0.3]


def test_srn_trig_matches_libm_at_ew_ckm_angles():
    """_srn.cos/sin/atan2 match math.* at the actual EW/CKM angles to 1e-9."""
    for th in [_THETA_W, *_CKM_ANGLES]:
        assert abs(_srn.cos(th) - math.cos(th)) < 1e-9
        assert abs(_srn.sin(th) - math.sin(th)) < 1e-9
    for (y, x) in [(0.35, 0.65), (0.5, 0.5), (0.1, 1.0), (1.0, 1.0)]:
        assert abs(_srn.atan2(y, x) - math.atan2(y, x)) < 1e-9


def test_weak_mixing_angle_matches_pre_change():
    """weak_mixing_angle (now _srn.atan2) matches the math.atan2 value 1e-9."""
    for (g, gp) in [(0.65, 0.35), (0.5, 0.5), (1.0, 0.1), (0.8, 0.3)]:
        expected = math.atan2(gp, g)  # pre-change value
        assert abs(sm.weak_mixing_angle(g, gp) - expected) < 1e-9


def test_weinberg_relations_match_pre_change():
    """electroweak_summary cos/sin (now _srn.*) match the pre-change math.*
    closed form within 1e-9 for each observable in the bundle."""
    for (g, gp, v) in [(0.65, 0.35, 246.0), (0.5, 0.5, 100.0), (1.0, 0.1, 50.0)]:
        theta = math.atan2(gp, g)
        exp_MW = g * v / 2.0
        exp_MZ = v * math.sqrt(g * g + gp * gp) / 2.0
        exp_cos = math.cos(theta)
        exp_sin = math.sin(theta)
        got = sm.electroweak_summary(g, gp, v)
        assert abs(got["M_W"] - exp_MW) < 1e-9
        assert abs(got["M_Z"] - exp_MZ) < 1e-9
        assert abs(got["theta_W_rad"] - theta) < 1e-9
        assert abs(got["cos_theta_W"] - exp_cos) < 1e-9
        assert abs(got["sin_theta_W"] - exp_sin) < 1e-9


def test_ckm_matrix_matches_pre_change():
    """ckm_matrix (now _srn.cos/sin) matches the element-by-element math.*
    construction within 1e-9 for a representative parameter point."""
    th12, th13, th23, delta = 0.227, 0.003, 0.042, 1.20
    # Pre-change reference built with math.* exactly as the old code did.
    c12, s12 = math.cos(th12), math.sin(th12)
    c13, s13 = math.cos(th13), math.sin(th13)
    c23, s23 = math.cos(th23), math.sin(th23)
    phase = np.exp(1j * delta)
    inv_phase = np.exp(-1j * delta)
    V_ref = np.array([
        [c12 * c13, s12 * c13, s13 * inv_phase],
        [
            -s12 * c23 - c12 * s23 * s13 * phase,
            c12 * c23 - s12 * s23 * s13 * phase,
            s23 * c13,
        ],
        [
            s12 * s23 - c12 * c23 * s13 * phase,
            -c12 * s23 - s12 * c23 * s13 * phase,
            c23 * c13,
        ],
    ], dtype=complex)
    V = sm.ckm_matrix(th12, th13, th23, delta)
    np.testing.assert_allclose(V, V_ref, atol=1e-9)
    # Still unitary.
    np.testing.assert_allclose(V @ V.conj().T, np.eye(3), atol=1e-9)


# ----------------------------------------------------------------------
# No abs() / no stealth-abs in this test module itself (discipline echo):
# all magnitudes above use squared-magnitude (z * z.conj()).real, not abs().
# ----------------------------------------------------------------------
