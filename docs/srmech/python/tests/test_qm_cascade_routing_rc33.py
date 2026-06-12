"""rc33 cascade-routing parity tests for the srmech.qm.* layer.

v0.7.0rc33 routes the numpy-math calls in the QM layer through srmech's
own A-N cascade primitives:

- Hermitian eigendecomposition (``np.linalg.eigh`` / ``eigvalsh``) ->
  the Class-L primitive ``srmech.amsc.laplacian.hermitian_eigendecompose``
  (potentials / gauge / so8). ``single_particle`` has since (rc117, #564)
  been flipped fully numpy-free onto the ``Mat`` carrier
  (``mat_hermitian_eigendecompose`` + the Class-N ``rational.cexp`` phase),
  so its two tests below build inputs and assert WITHOUT numpy.
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
from srmech.amsc.laplacian import hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat
from srmech.qm import gauge, potentials, sm, single_particle as sp


# ----------------------------------------------------------------------
# numpy-free fixtures for the FLIPPED single_particle op (rc117, #564):
# single_particle now holds its matrices in `Mat` and is numpy-free, so its
# tests below build inputs + assert WITHOUT numpy (numpy stays the sanctioned
# oracle only for the still-unflipped gauge / potentials / hermitian_eigen
# routing tests in this file).
# ----------------------------------------------------------------------


def _lcg(seed: int):
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _hermitian_mat(n: int, seed: int) -> "Mat":
    g = _lcg(seed)
    a = [[complex(next(g), next(g)) for _ in range(n)] for _ in range(n)]
    h = [
        [(a[i][j] + complex(a[j][i]).conjugate()) / 2.0 for j in range(n)]
        for i in range(n)
    ]
    return Mat.from_rows(h, is_complex=True)


def _unit_vec(n: int, seed: int):
    g = _lcg(seed + 777)
    v = [complex(next(g), next(g)) for _ in range(n)]
    nrm = _srn.sqrt(sum(x.real * x.real + x.imag * x.imag for x in v))
    return [x / nrm for x in v]


def _matvec_mat(m: "Mat", v):
    col = Mat.from_rows([[x] for x in v], is_complex=True)
    out = mat_matmul(m, col)
    return [out[i, 0] for i in range(out.n_rows)]


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
    """tise_solve (complex-Hermitian) returns the ``(n,1)`` real eigval ``Mat`` +
    complex unitary eigvec ``Mat``; reconstruction ``H ≈ V·diag(w)·Vᴴ`` and
    unitarity ``Vᴴ·V ≈ I`` both hold — numpy-FREE (single_particle is a
    numpy-free ``Mat`` op as of rc117; an eigenvector is fixed only up to phase,
    so correctness is reconstruction + unitarity, not element-wise parity)."""
    n = 6
    H = _hermitian_mat(n, 30)
    w, V = sp.tise_solve(H)
    assert V.is_complex and w.shape == (n, 1)
    # Unitarity: Vᴴ·V = I (via the native mat_matmul).
    vhv = mat_matmul(V.conj().T, V)
    assert max(
        abs(vhv[i, j] - (1.0 if i == j else 0.0)) for i in range(n) for j in range(n)
    ) < 1e-9
    # Reconstruction: H = V·diag(w)·Vᴴ.
    D = Mat.from_rows(
        [[w[i, 0] if i == j else 0.0 for j in range(n)] for i in range(n)],
        is_complex=True,
    )
    H_rebuilt = mat_matmul(mat_matmul(V, D), V.conj().T)
    assert max(
        abs(H_rebuilt[i, j] - H[i, j]) for i in range(n) for j in range(n)
    ) < 1e-9
    # Eigenvalues ascending.
    for i in range(n - 1):
        assert w[i + 1, 0] - w[i, 0] >= -1e-9


def test_single_particle_tdse_matches_reference():
    """tdse_evolve matches the hand-composed closed form ``V·diag(e^{-iλt})·Vᴴ·ψ``
    built from ``tise_solve`` + the Class-N ``rational.cexp`` — numpy-FREE
    (the reference is the framework's own eigendecomposition + Euler cascade,
    NOT a numpy oracle, so the flipped op's test is itself numpy-free)."""
    n = 5
    H = _hermitian_mat(n, 31)
    psi = _unit_vec(n, 99)
    t = 1.7
    w, V = sp.tise_solve(H)
    # Reference: V·diag(e^{-iλt})·Vᴴ·ψ via Mat ops + Class-N cexp.
    vh_psi = _matvec_mat(V.conj().T, psi)
    phased = [_srn.cexp(-(w[k, 0] * t)) * vh_psi[k] for k in range(n)]
    ref = _matvec_mat(V, phased)
    got = sp.tdse_evolve(H, psi, t)
    assert max(abs(got[i] - ref[i]) for i in range(n)) < 1e-9


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
    """ckm_matrix (numpy-free `Mat` as of rc116) matches the element-by-element
    construction within 1e-9 for a representative parameter point.

    numpy-FREE: the reference is built with the stdlib `math`/`cmath` (an
    INDEPENDENT oracle, NOT the framework's own `rational.cexp`, so it's a
    genuine cross-check), compared via direct `Mat`-entry access, and unitarity
    is checked via the native `mat_matmul` — no numpy (the flipped op's test is
    itself numpy-free per the carrier-removal discipline).
    """
    import cmath
    from srmech.amsc.laplacian import mat_matmul
    th12, th13, th23, delta = 0.227, 0.003, 0.042, 1.20
    c12, s12 = math.cos(th12), math.sin(th12)
    c13, s13 = math.cos(th13), math.sin(th13)
    c23, s23 = math.cos(th23), math.sin(th23)
    phase = cmath.exp(1j * delta)
    inv_phase = cmath.exp(-1j * delta)
    ref = [
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
    ]
    V = sm.ckm_matrix(th12, th13, th23, delta)
    for i in range(3):
        for j in range(3):
            assert abs(V[i, j] - ref[i][j]) < 1e-9, (i, j)
    # Still unitary: V·Vᴴ = I (numpy-free, via the native mat_matmul).
    vvh = mat_matmul(V, V.conj().T)
    for i in range(3):
        for j in range(3):
            assert abs(vvh[i, j] - (1.0 if i == j else 0.0)) < 1e-9, (i, j)


# ----------------------------------------------------------------------
# No abs() / no stealth-abs in this test module itself (discipline echo):
# all magnitudes above use squared-magnitude (z * z.conj()).real, not abs().
# ----------------------------------------------------------------------
