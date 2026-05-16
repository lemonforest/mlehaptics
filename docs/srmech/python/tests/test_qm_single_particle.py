"""Tests for srmech.qm.single_particle.

Verifies canonical QM identities for the single-particle operations layer.
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.qm import single_particle as sp


def _hermitian(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (A + A.conj().T) / 2.0


def _unit(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    psi = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    return psi / np.linalg.norm(psi)


# ----------------------------------------------------------------------
# tdse_evolve
# ----------------------------------------------------------------------


def test_tdse_zero_time_identity():
    n = 6
    H = _hermitian(n, 0)
    psi = _unit(n, 1)
    np.testing.assert_allclose(sp.tdse_evolve(H, psi, 0.0), psi, atol=1e-13)


def test_tdse_preserves_norm():
    n = 8
    H = _hermitian(n, 2)
    psi = _unit(n, 3)
    for t in (0.1, 0.5, 1.0, 5.0, 10.0):
        psi_t = sp.tdse_evolve(H, psi, t)
        assert abs(np.linalg.norm(psi_t) - 1.0) < 1e-12


def test_tdse_preserves_energy():
    """⟨H⟩ is conserved under TDSE evolution (H is time-independent)."""
    n = 7
    H = _hermitian(n, 4)
    psi = _unit(n, 5)
    E0 = np.real(psi.conj() @ H @ psi)
    for t in (0.3, 1.5, 4.7):
        psi_t = sp.tdse_evolve(H, psi, t)
        E_t = np.real(psi_t.conj() @ H @ psi_t)
        assert abs(E_t - E0) < 1e-12


def test_tdse_evolves_eigenstate_with_phase():
    """An eigenstate evolves as exp(-iE t) |E⟩ — only a global phase."""
    n = 5
    H = _hermitian(n, 6)
    eigvals, V = np.linalg.eigh(H)
    psi0 = V[:, 2]  # third eigenstate
    psi_t = sp.tdse_evolve(H, psi0, 1.3)
    expected = np.exp(-1j * eigvals[2] * 1.3) * psi0
    np.testing.assert_allclose(psi_t, expected, atol=1e-13)


# ----------------------------------------------------------------------
# tise_solve
# ----------------------------------------------------------------------


def test_tise_orthonormal_eigenvectors():
    n = 6
    H = _hermitian(n, 7)
    eigvals, V = sp.tise_solve(H)
    np.testing.assert_allclose(V.conj().T @ V, np.eye(n), atol=1e-12)


def test_tise_satisfies_eigen_relation():
    n = 8
    H = _hermitian(n, 8)
    eigvals, V = sp.tise_solve(H)
    for k in range(n):
        np.testing.assert_allclose(H @ V[:, k], eigvals[k] * V[:, k], atol=1e-12)


def test_tise_eigenvalues_ascending():
    H = _hermitian(10, 9)
    eigvals, _ = sp.tise_solve(H)
    assert np.all(np.diff(eigvals) >= -1e-13)


# ----------------------------------------------------------------------
# commutator
# ----------------------------------------------------------------------


def test_commutator_self_zero():
    A = _hermitian(5, 10)
    assert np.linalg.norm(sp.commutator(A, A)) < 1e-13


def test_commutator_antisymmetric():
    A = _hermitian(4, 11)
    B = _hermitian(4, 12)
    np.testing.assert_allclose(sp.commutator(A, B), -sp.commutator(B, A), atol=1e-13)


def test_commutator_with_identity_zero():
    A = _hermitian(6, 13)
    I = np.eye(6)
    assert np.linalg.norm(sp.commutator(A, I)) < 1e-13


# ----------------------------------------------------------------------
# heisenberg_evolve
# ----------------------------------------------------------------------


def test_heisenberg_zero_time_identity():
    n = 5
    A = _hermitian(n, 14)
    H = _hermitian(n, 15)
    np.testing.assert_allclose(sp.heisenberg_evolve(A, H, 0.0), A, atol=1e-13)


def test_heisenberg_commutes_with_self():
    """If A = H, A_H(t) = H always (H is conserved in Heisenberg picture)."""
    n = 6
    H = _hermitian(n, 16)
    for t in (0.1, 1.0, 5.0):
        H_t = sp.heisenberg_evolve(H, H, t)
        np.testing.assert_allclose(H_t, H, atol=1e-12)


# ----------------------------------------------------------------------
# lattice_momentum
# ----------------------------------------------------------------------


def test_lattice_momentum_hermitian():
    p = sp.lattice_momentum(16, dx=0.1)
    np.testing.assert_allclose(p, p.conj().T, atol=1e-14)


def test_lattice_momentum_zero_diagonal():
    p = sp.lattice_momentum(20)
    assert np.linalg.norm(np.diag(p)) < 1e-14


def test_lattice_momentum_invalid_n():
    with pytest.raises(ValueError):
        sp.lattice_momentum(1)


def test_lattice_momentum_invalid_dx():
    with pytest.raises(ValueError):
        sp.lattice_momentum(10, dx=0.0)


# ----------------------------------------------------------------------
# density_matrix
# ----------------------------------------------------------------------


def test_density_matrix_trace_normalized():
    psi = _unit(8, 17)
    rho = sp.density_matrix(psi)
    assert abs(np.trace(rho).real - 1.0) < 1e-13


def test_density_matrix_hermitian():
    psi = _unit(6, 18)
    rho = sp.density_matrix(psi)
    np.testing.assert_allclose(rho, rho.conj().T, atol=1e-14)


def test_density_matrix_pure_idempotent():
    """For a pure state, ρ² = ρ."""
    psi = _unit(5, 19)
    rho = sp.density_matrix(psi)
    np.testing.assert_allclose(rho @ rho, rho, atol=1e-12)


# ----------------------------------------------------------------------
# liouville_evolve
# ----------------------------------------------------------------------


def test_liouville_preserves_trace():
    n = 6
    H = _hermitian(n, 20)
    psi = _unit(n, 21)
    rho = sp.density_matrix(psi)
    for t in (0.0, 0.5, 2.0):
        rho_t = sp.liouville_evolve(rho, H, t)
        assert abs(np.trace(rho_t).real - 1.0) < 1e-12


def test_liouville_preserves_purity():
    """A pure state stays pure under unitary evolution."""
    n = 5
    H = _hermitian(n, 22)
    psi = _unit(n, 23)
    rho = sp.density_matrix(psi)
    rho_t = sp.liouville_evolve(rho, H, 1.7)
    np.testing.assert_allclose(rho_t @ rho_t, rho_t, atol=1e-11)


def test_liouville_zero_time_identity():
    n = 4
    H = _hermitian(n, 24)
    psi = _unit(n, 25)
    rho = sp.density_matrix(psi)
    np.testing.assert_allclose(sp.liouville_evolve(rho, H, 0.0), rho, atol=1e-13)
