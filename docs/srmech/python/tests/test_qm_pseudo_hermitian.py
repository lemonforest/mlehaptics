"""Tests for srmech.qm.pseudo_hermitian (η-deformed inner product framework)."""

from __future__ import annotations

import numpy as np
import pytest

from srmech.qm import pseudo_hermitian as ph


def _hermitian(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    return (A + A.conj().T) / 2.0


def _positive_definite(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    # η = A A† is Hermitian positive definite.
    return A @ A.conj().T


# ----------------------------------------------------------------------
# inner_product_eta
# ----------------------------------------------------------------------


def test_inner_product_eta_identity_reduces():
    """For η = I, ⟨a|b⟩_η = ⟨a|b⟩ (standard inner product)."""
    rng = np.random.default_rng(0)
    n = 5
    a = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    b = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    I = np.eye(n, dtype=complex)
    eta_inner = ph.inner_product_eta(a, b, I)
    std_inner = a.conj() @ b
    assert abs(eta_inner - std_inner) < 1e-13


def test_inner_product_eta_self_real():
    """For Hermitian (positive) η, ⟨a|a⟩_η is real."""
    eta = _positive_definite(6, 1)
    rng = np.random.default_rng(2)
    a = rng.standard_normal(6) + 1j * rng.standard_normal(6)
    val = ph.inner_product_eta(a, a, eta)
    assert abs(val.imag) < 1e-12


def test_inner_product_eta_shape_mismatch():
    with pytest.raises(ValueError):
        ph.inner_product_eta(np.array([1, 2]), np.array([1, 2, 3]), np.eye(2))


# ----------------------------------------------------------------------
# expectation_eta
# ----------------------------------------------------------------------


def test_expectation_eta_identity_reduces():
    """For η = I, ⟨O⟩_η = ⟨ψ|O|ψ⟩ / ⟨ψ|ψ⟩."""
    rng = np.random.default_rng(3)
    n = 4
    psi = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    O = _hermitian(n, 4)
    val = ph.expectation_eta(O, psi, np.eye(n, dtype=complex))
    std_val = (psi.conj() @ O @ psi) / (psi.conj() @ psi)
    assert abs(val - std_val) < 1e-13


def test_expectation_eta_hermitian_eigenstate():
    """For Hermitian O and eigenstate |λ⟩ with η = I, ⟨O⟩ = λ."""
    O = _hermitian(5, 5)
    eigvals, V = np.linalg.eigh(O)
    psi = V[:, 2]
    val = ph.expectation_eta(O, psi, np.eye(5, dtype=complex))
    assert abs(val - eigvals[2]) < 1e-12


# ----------------------------------------------------------------------
# is_pseudo_hermitian
# ----------------------------------------------------------------------


def test_is_pseudo_hermitian_for_hermitian_with_identity_eta():
    """Any Hermitian O is η-pseudo-Hermitian for η = I."""
    O = _hermitian(4, 6)
    assert ph.is_pseudo_hermitian(O, np.eye(4, dtype=complex))


def test_is_pseudo_hermitian_for_non_hermitian_with_identity_eta_fails():
    """Non-Hermitian O fails η-pseudo-Hermitian test for η = I."""
    rng = np.random.default_rng(7)
    O = rng.standard_normal((4, 4)) + 1j * rng.standard_normal((4, 4))
    # Make sure O is not Hermitian by accident.
    if np.linalg.norm(O - O.conj().T) < 1e-10:
        O[0, 1] += 1.0
    assert not ph.is_pseudo_hermitian(O, np.eye(4, dtype=complex))


def test_is_pseudo_hermitian_constructed_eta():
    """η constructed from O's eigendecomposition makes O η-pseudo-Hermitian."""
    # Use a small real-spectrum non-Hermitian operator.
    # Triangular matrix with distinct real eigenvalues.
    O = np.array([
        [1.0, 0.5, 0.0],
        [0.0, 2.0, 0.5],
        [0.0, 0.0, 3.0],
    ], dtype=complex)
    eta = ph.construct_eta_from_eigendecomposition(O)
    assert ph.is_pseudo_hermitian(O, eta, atol=1e-8)


# ----------------------------------------------------------------------
# construct_eta_from_eigendecomposition
# ----------------------------------------------------------------------


def test_construct_eta_complex_spectrum_rejected():
    """Operator with complex spectrum (e.g. rotation) is rejected."""
    O = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=complex)  # eigvals ±i
    with pytest.raises(ValueError):
        ph.construct_eta_from_eigendecomposition(O)


def test_construct_eta_returns_hermitian():
    O = np.array([[1.0, 0.5], [0.0, 2.0]], dtype=complex)
    eta = ph.construct_eta_from_eigendecomposition(O)
    np.testing.assert_allclose(eta, eta.conj().T, atol=1e-12)


# ----------------------------------------------------------------------
# pseudo_hermitian_eigenvalues_real
# ----------------------------------------------------------------------


def test_eigenvalues_real_for_constructed_eta():
    """η-pseudo-Hermitian O with positive η has real spectrum
    (Mostafazadeh theorem)."""
    O = np.array([
        [1.0, 0.5, 0.0],
        [0.0, 2.0, 0.5],
        [0.0, 0.0, 3.0],
    ], dtype=complex)
    eta = ph.construct_eta_from_eigendecomposition(O)
    assert ph.pseudo_hermitian_eigenvalues_real(O, eta, atol=1e-8)


def test_eigenvalues_real_returns_false_for_non_pseudo_hermitian():
    """A complex-spectrum operator with identity-η fails the test."""
    O = np.array([[0.0, -1.0], [1.0, 0.0]], dtype=complex)  # eigvals ±i
    assert not ph.pseudo_hermitian_eigenvalues_real(
        O, np.eye(2, dtype=complex), atol=1e-10
    )
