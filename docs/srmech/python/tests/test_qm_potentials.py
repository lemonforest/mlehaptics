"""Tests for srmech.qm.potentials (hydrogen radial, harmonic oscillator)."""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import rational as _srn
from srmech.amsc.mat import Mat
from srmech.qm import potentials, single_particle


# ----------------------------------------------------------------------
# Harmonic oscillator
# ----------------------------------------------------------------------


def test_harmonic_oscillator_ladder_commutator_diag():
    """[a, a†] = I in the bulk (truncation error appears only at the
    last index due to the truncated boundary)."""
    n = 30
    a, a_dagger = potentials.harmonic_oscillator_ladder(n_dim=n)
    comm = a @ a_dagger - a_dagger @ a
    # Bulk identity:
    np.testing.assert_allclose(np.diag(comm)[:-1].real, 1.0, atol=1e-13)


def test_harmonic_oscillator_ladder_action():
    """a|n⟩ = √n |n-1⟩ (column-by-column verification on basis vectors)."""
    n = 20
    a, _ = potentials.harmonic_oscillator_ladder(n_dim=n)
    for k in range(1, n):
        basis_k = np.zeros(n, dtype=complex)
        basis_k[k] = 1.0
        result = a @ basis_k
        expected = np.zeros(n, dtype=complex)
        expected[k - 1] = np.sqrt(k)
        np.testing.assert_allclose(result, expected, atol=1e-14)


def test_harmonic_oscillator_hamiltonian_spectrum():
    """E_n = ω (n + 1/2) for the truncated Hamiltonian, valid for low n."""
    n_dim = 30
    omega = 2.5
    H = potentials.harmonic_oscillator_hamiltonian(n_dim=n_dim, omega=omega)
    eigvals = np.linalg.eigvalsh(H)
    # Lowest 20 levels should match analytic spectrum exactly:
    for n in range(20):
        expected = omega * (n + 0.5)
        assert abs(eigvals[n] - expected) < 1e-12 * (1 + abs(expected))


def test_harmonic_oscillator_invalid_n_dim():
    with pytest.raises(ValueError):
        potentials.harmonic_oscillator_ladder(n_dim=1)


def test_harmonic_oscillator_invalid_omega():
    with pytest.raises(ValueError):
        potentials.harmonic_oscillator_ladder(n_dim=5, omega=0.0)


# ----------------------------------------------------------------------
# Hydrogen radial
# ----------------------------------------------------------------------


def test_hydrogen_radial_ground_state_energy():
    """Lowest s-state eigenvalue approaches -1/2 (Rydberg ground)."""
    r, eigvals, _ = potentials.hydrogen_radial(n_grid=600, r_max=80.0, l_quantum=0)
    # Finite-grid: deviation O(dr²). For n_grid=600, dr ≈ 0.13, error ~1%.
    assert -0.51 < eigvals[0] < -0.48


def test_hydrogen_radial_rydberg_series_2s():
    """Second s-state approaches -1/8 (n=2 Rydberg energy)."""
    r, eigvals, _ = potentials.hydrogen_radial(n_grid=600, r_max=80.0, l_quantum=0)
    # E_2 = -1/(2·4) = -0.125. Finite-grid error allowed.
    assert -0.14 < eigvals[1] < -0.115


def test_hydrogen_radial_l1_excludes_ground():
    """For l=1, lowest level is E_2 (the 2p state), not E_1."""
    r, eigvals, _ = potentials.hydrogen_radial(n_grid=600, r_max=80.0, l_quantum=1)
    # E_2 ≈ -0.125; the centrifugal barrier excludes a ground state at l=1.
    assert eigvals[0] > -0.14
    assert eigvals[0] < -0.115


def test_hydrogen_radial_eigenvectors_orthonormal():
    r, eigvals, V = potentials.hydrogen_radial(n_grid=200, r_max=40.0)
    np.testing.assert_allclose(V.T @ V, np.eye(V.shape[1]), atol=1e-10)


def test_hydrogen_radial_invalid_l():
    with pytest.raises(ValueError):
        potentials.hydrogen_radial(l_quantum=-1)


def test_hydrogen_radial_invalid_n_grid():
    with pytest.raises(ValueError):
        potentials.hydrogen_radial(n_grid=2)


# ----------------------------------------------------------------------
# Cross-check: harmonic oscillator vs TDSE
# ----------------------------------------------------------------------


def test_harmonic_oscillator_tdse_consistency():
    """Eigenstate evolves with phase exp(-iE_n t) under TDSE on H.

    ``potentials`` is still a numpy carrier (unflipped), so its Hamiltonian
    comes back as numpy and is bridged to a ``Mat`` at the flipped
    ``single_particle.tdse_evolve`` boundary (numpy → Mat once); the TDSE
    exercise + assertion are then numpy-FREE (the Class-N ``rational.cexp``
    phase as the reference, direct list compare) per the carrier-removal
    discipline (single_particle is numpy-free as of rc117, #564)."""
    n_dim = 20
    omega = 1.5
    H_np = potentials.harmonic_oscillator_hamiltonian(n_dim=n_dim, omega=omega)
    H = Mat.from_rows(H_np.tolist(), is_complex=True)   # numpy→Mat at the flipped-op boundary
    # Use the n=3 Fock state, as a plain complex vector.
    psi = [0j] * n_dim
    psi[3] = 1.0 + 0j
    E_expected = omega * (3 + 0.5)
    for t in (0.5, 1.0, 2.5):
        psi_t = single_particle.tdse_evolve(H, psi, t)
        phase = _srn.cexp(-(E_expected * t))            # e^{-iE t} (Class-N cascade)
        expected = [phase * psi[i] for i in range(n_dim)]
        assert max(abs(psi_t[i] - expected[i]) for i in range(n_dim)) < 1e-9
