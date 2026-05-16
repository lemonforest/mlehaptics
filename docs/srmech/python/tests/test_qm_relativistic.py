"""Tests for srmech.qm.relativistic (Dirac γ-matrices, Weyl, Majorana, KG)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from srmech.qm import relativistic as rel


# ----------------------------------------------------------------------
# γ-matrix Clifford algebra
# ----------------------------------------------------------------------


def test_clifford_residuals_machine_precision():
    """{γ^μ, γ^ν} = 2 η^{μν} I_4; γ_5² = I; {γ_5, γ^μ} = 0."""
    max_clifford, g5_sq, g5_anti = rel.clifford_residuals()
    assert max_clifford < 1e-13
    assert g5_sq < 1e-13
    assert g5_anti < 1e-13


def test_gamma_matrices_traceless():
    """tr(γ^μ) = 0 for all μ."""
    for g in rel.gamma_matrices():
        assert abs(np.trace(g)) < 1e-13


def test_gamma_5_squared_identity():
    """γ_5² = I_4."""
    g5 = rel.gamma_5()
    np.testing.assert_allclose(g5 @ g5, np.eye(4), atol=1e-13)


def test_gamma_5_hermitian():
    g5 = rel.gamma_5()
    np.testing.assert_allclose(g5, g5.conj().T, atol=1e-13)


# ----------------------------------------------------------------------
# Weyl chirality projectors
# ----------------------------------------------------------------------


def test_weyl_projectors_sum_to_identity():
    """P_L + P_R = I."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    np.testing.assert_allclose(PL + PR, np.eye(4), atol=1e-13)


def test_weyl_projectors_idempotent():
    """P_L² = P_L; P_R² = P_R."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    np.testing.assert_allclose(PL @ PL, PL, atol=1e-13)
    np.testing.assert_allclose(PR @ PR, PR, atol=1e-13)


def test_weyl_projectors_orthogonal():
    """P_L P_R = 0."""
    PL = rel.weyl_left_projector()
    PR = rel.weyl_right_projector()
    assert np.linalg.norm(PL @ PR) < 1e-13


# ----------------------------------------------------------------------
# Charge conjugation
# ----------------------------------------------------------------------


def test_charge_conjugation_matrix_shape():
    C = rel.charge_conjugation_matrix()
    assert C.shape == (4, 4)


def test_charge_conjugation_antisymmetric_property():
    """C γ^μ C^{-1} = -(γ^μ)^T (Peskin-Schroeder eq A.27 hallmark)."""
    C = rel.charge_conjugation_matrix()
    C_inv = np.linalg.inv(C)
    for g in rel.gamma_matrices():
        np.testing.assert_allclose(C @ g @ C_inv, -g.T, atol=1e-12)


# ----------------------------------------------------------------------
# Klein-Gordon dispersion
# ----------------------------------------------------------------------


def test_klein_gordon_dispersion_at_rest():
    """At |k| = 0: E = m."""
    E = rel.klein_gordon_dispersion(np.zeros(3), m=2.5)
    assert abs(E - 2.5) < 1e-14


def test_klein_gordon_dispersion_massless():
    """For m = 0: E = |k|."""
    k = np.array([3.0, 4.0, 0.0])  # |k| = 5
    E = rel.klein_gordon_dispersion(k, m=0.0)
    assert abs(E - 5.0) < 1e-14


def test_klein_gordon_dispersion_relativistic():
    """E² = |k|² + m²."""
    k = np.array([1.0, 1.0, 1.0])
    m = 2.0
    E = rel.klein_gordon_dispersion(k, m)
    assert abs(E * E - np.dot(k, k) - m * m) < 1e-13


def test_klein_gordon_dispersion_negative_mass_rejected():
    with pytest.raises(ValueError):
        rel.klein_gordon_dispersion(np.zeros(3), m=-1.0)


# ----------------------------------------------------------------------
# Dirac operator (momentum space)
# ----------------------------------------------------------------------


def test_dirac_operator_at_rest():
    """At k = (m, 0, 0, 0) (on-shell rest): γ^0 m - m I has 2 zero eigenvalues."""
    m = 1.5
    k = np.array([m, 0.0, 0.0, 0.0])
    D = rel.dirac_operator_momentum_space(k, m)
    eigvals = np.sort(np.linalg.eigvals(D).real)
    # Eigenvalues: 0 (doubly) and -2m (doubly): D = diag(m, m, -m, -m) - m·I = diag(0, 0, -2m, -2m)
    np.testing.assert_allclose(eigvals, [-2 * m, -2 * m, 0.0, 0.0], atol=1e-13)


def test_dirac_operator_on_shell_annihilates_positive_energy_spinor():
    """For on-shell positive-frequency u(p), (γ^μ p_μ - m) u = 0."""
    m = 1.0
    p = np.array([m, 0.0, 0.0, 0.0])  # rest frame
    D = rel.dirac_operator_momentum_space(p, m)
    # In rest frame Dirac basis, positive-energy spinors are (1, 0, 0, 0) and (0, 1, 0, 0).
    u1 = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
    u2 = np.array([0.0, 1.0, 0.0, 0.0], dtype=complex)
    assert np.linalg.norm(D @ u1) < 1e-13
    assert np.linalg.norm(D @ u2) < 1e-13


def test_four_momentum_squared_mostly_minus():
    """k² = E² - |k|² (mostly-minus)."""
    k = np.array([3.0, 1.0, 2.0, 0.0])
    k2 = rel.four_momentum_squared(k)
    assert abs(k2 - (9.0 - 1.0 - 4.0 - 0.0)) < 1e-14


def test_dirac_operator_wrong_shape():
    with pytest.raises(ValueError):
        rel.dirac_operator_momentum_space(np.array([1.0, 0.0, 0.0]), m=1.0)
