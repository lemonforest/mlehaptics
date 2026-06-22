"""Tests for srmech.qm.potentials (hydrogen radial, harmonic oscillator) — numpy-FREE.

potentials flipped numpy-free onto the ``Mat`` carrier at rc121 (#564): the
ladder/Hamiltonian are ``Mat``, ``hydrogen_radial`` returns ``(list, list, Mat)``.
Per ``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`` this
test file is itself numpy-free — no numpy oracle, no ``.to_numpy()``; equality is
direct ``Mat``-entry arithmetic, matrix products go through the native
``mat_matmul``, eigenvalues through ``mat_hermitian_eigendecompose``, and the
TDSE phase reference is the Class-N ``rational.cexp`` Euler cascade.
"""

from __future__ import annotations

import pytest

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat
from srmech.qm import potentials, single_particle


def _mat_sub(a: "Mat", b: "Mat") -> "Mat":
    """``A − B`` element-wise as a new complex ``Mat`` (numpy-free test helper)."""
    rows = [[a[i, j] - b[i, j] for j in range(a.n_cols)] for i in range(a.n_rows)]
    return Mat.from_rows(rows, is_complex=True)


# ----------------------------------------------------------------------
# Harmonic oscillator
# ----------------------------------------------------------------------


def test_harmonic_oscillator_ladder_commutator_diag():
    """[a, a†] = I in the bulk (truncation error appears only at the
    last index due to the truncated boundary)."""
    n = 30
    a, a_dagger = potentials.harmonic_oscillator_ladder(n_dim=n)
    # comm = a·a† − a†·a via the native mat_matmul (numpy-free).
    comm = _mat_sub(mat_matmul(a, a_dagger), mat_matmul(a_dagger, a))
    # Bulk identity: diagonal[:-1] ≈ 1.0 by direct entry access.
    for i in range(n - 1):
        assert abs(comm[i, i].real - 1.0) < 1e-13
        assert abs(comm[i, i].imag) < 1e-13


def test_harmonic_oscillator_ladder_action():
    """a|n⟩ = √n |n-1⟩ — the lowering operator has a[k-1,k] = √k and is zero
    elsewhere in column k (direct Mat-entry check; numpy-free)."""
    n = 20
    a, _ = potentials.harmonic_oscillator_ladder(n_dim=n)
    for k in range(1, n):
        expected = float(_srn.sqrt(float(k)))      # exact Q → float ladder element
        # Column k is √k on row k-1, zero on every other row.
        for i in range(n):
            want = expected if i == k - 1 else 0.0
            assert abs(a[i, k] - want) < 1e-14


def test_harmonic_oscillator_hamiltonian_spectrum():
    """E_n = ω (n + 1/2) for the truncated Hamiltonian, valid for low n."""
    n_dim = 30
    omega = 2.5
    H = potentials.harmonic_oscillator_hamiltonian(n_dim=n_dim, omega=omega)
    eigvals, _ = mat_hermitian_eigendecompose(H)
    # Lowest 20 levels should match analytic spectrum exactly:
    for n in range(20):
        expected = omega * (n + 0.5)
        assert abs(eigvals[n, 0] - expected) < 1e-12 * (1 + abs(expected))


def test_harmonic_oscillator_invalid_n_dim():
    with pytest.raises(ValueError):
        potentials.harmonic_oscillator_ladder(n_dim=1)


def test_harmonic_oscillator_invalid_omega():
    with pytest.raises(ValueError):
        potentials.harmonic_oscillator_ladder(n_dim=5, omega=0.0)


# ----------------------------------------------------------------------
# Hydrogen radial
#
# Grids sized for a fast native eig + in-band accuracy (rc121): the no-libm
# algebraic sqrt makes the native Jacobi ~O(seconds) per call, so the 3-point
# central-difference ground-state error (~dr²) is kept in-band with the SMALL
# grid n_grid=250, r_max=45 (dr≈0.18) — each eig is ~3-4s and lands well inside
# the unchanged accuracy bands. The orthonormal test uses the still-smaller
# n_grid=120 (dr≈0.33) since it checks Vᵀ V = I, not an energy band.
# ----------------------------------------------------------------------


def test_hydrogen_radial_ground_state_energy():
    """Lowest s-state eigenvalue approaches -1/2 (Rydberg ground)."""
    r, energies, _ = potentials.hydrogen_radial(n_grid=250, r_max=45.0, l_quantum=0)
    # Finite-grid: deviation O(dr²).
    assert -0.51 < energies[0] < -0.48


def test_hydrogen_radial_rydberg_series_2s():
    """Second s-state approaches -1/8 (n=2 Rydberg energy)."""
    r, energies, _ = potentials.hydrogen_radial(n_grid=250, r_max=45.0, l_quantum=0)
    # E_2 = -1/(2·4) = -0.125. Finite-grid error allowed.
    assert -0.14 < energies[1] < -0.115


def test_hydrogen_radial_l1_excludes_ground():
    """For l=1, lowest level is E_2 (the 2p state), not E_1."""
    r, energies, _ = potentials.hydrogen_radial(n_grid=250, r_max=45.0, l_quantum=1)
    # E_2 ≈ -0.125; the centrifugal barrier excludes a ground state at l=1.
    assert energies[0] > -0.14
    assert energies[0] < -0.115


def test_hydrogen_radial_eigenvectors_orthonormal():
    r, energies, V = potentials.hydrogen_radial(n_grid=120, r_max=40.0)
    assert V.is_complex is False  # real-symmetric H → real eigenvectors
    # Vᵀ·V = I via the native mat_matmul (V is a real Mat).
    gram = mat_matmul(V.T, V)
    n = gram.n_rows
    for i in range(n):
        for j in range(n):
            want = 1.0 if i == j else 0.0
            assert abs(gram[i, j] - want) < 1e-10


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

    ``potentials`` is numpy-free as of rc121 (#564): its Hamiltonian comes back
    as a ``Mat`` directly, so it feeds ``single_particle.tdse_evolve`` with no
    bridge; the TDSE exercise + assertion are numpy-FREE (the Class-N
    ``rational.cexp`` phase as the reference, direct list compare)."""
    n_dim = 20
    omega = 1.5
    H = potentials.harmonic_oscillator_hamiltonian(n_dim=n_dim, omega=omega)
    # Use the n=3 Fock state, as a plain complex vector.
    psi = [0j] * n_dim
    psi[3] = 1.0 + 0j
    E_expected = omega * (3 + 0.5)
    for t in (0.5, 1.0, 2.5):
        psi_t = single_particle.tdse_evolve(H, psi, t)
        phase = _srn.cexp(-(E_expected * t))            # e^{-iE t} (Class-N cascade)
        expected = [phase * psi[i] for i in range(n_dim)]
        assert max(abs(psi_t[i] - expected[i]) for i in range(n_dim)) < 1e-9
