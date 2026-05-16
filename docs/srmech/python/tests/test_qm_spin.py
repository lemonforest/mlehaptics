"""Tests for srmech.qm.spin (Pauli matrices, Clifford algebra)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from srmech.qm import spin


def test_pauli_matrices_hermitian():
    """All Pauli matrices are Hermitian."""
    sx, sy, sz = spin.pauli_matrices()
    for label, s in (("σ_x", sx), ("σ_y", sy), ("σ_z", sz)):
        np.testing.assert_allclose(s, s.conj().T, atol=1e-14, err_msg=label)


def test_pauli_matrices_traceless():
    """tr(σ_i) = 0."""
    sx, sy, sz = spin.pauli_matrices()
    for s in (sx, sy, sz):
        assert abs(np.trace(s)) < 1e-14


def test_pauli_matrices_square_identity():
    """σ_i² = I."""
    sx, sy, sz = spin.pauli_matrices()
    I = spin.pauli_identity()
    np.testing.assert_allclose(sx @ sx, I, atol=1e-14)
    np.testing.assert_allclose(sy @ sy, I, atol=1e-14)
    np.testing.assert_allclose(sz @ sz, I, atol=1e-14)


def test_pauli_eigenvalues():
    """Each σ_i has eigenvalues ±1."""
    sx, sy, sz = spin.pauli_matrices()
    for s in (sx, sy, sz):
        eigvals = np.linalg.eigvalsh(s)
        np.testing.assert_allclose(sorted(eigvals.real), [-1.0, 1.0], atol=1e-14)


def test_pauli_clifford_residuals():
    """{σ_i, σ_j} = 2 δ_{ij} I and [σ_i, σ_j] = 2i ε_{ijk} σ_k at machine precision."""
    max_anti, max_comm = spin.pauli_clifford_residuals()
    assert max_anti < 1e-13
    assert max_comm < 1e-13


def test_pauli_spin_operator_eigenvalues_half():
    """S_n = (1/2) σ·n̂ has eigenvalues ±½ for any direction."""
    for direction in [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]),
        np.array([0.3, -0.7, 1.5]),
    ]:
        S = spin.pauli_spin_operator(direction)
        eigvals = sorted(np.linalg.eigvalsh(S).real)
        np.testing.assert_allclose(eigvals, [-0.5, 0.5], atol=1e-14)


def test_pauli_spin_operator_zero_direction_raises():
    with pytest.raises(ValueError):
        spin.pauli_spin_operator(np.zeros(3))


def test_pauli_spin_operator_wrong_shape_raises():
    with pytest.raises(ValueError):
        spin.pauli_spin_operator(np.array([1.0, 0.0]))


def test_pauli_anti_commute_cross_pairs():
    """σ_i σ_j = -σ_j σ_i for i ≠ j."""
    sx, sy, sz = spin.pauli_matrices()
    pairs = [(sx, sy), (sy, sz), (sx, sz)]
    for a, b in pairs:
        np.testing.assert_allclose(a @ b, -b @ a, atol=1e-14)
