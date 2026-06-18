"""Tests for srmech.qm.pseudo_hermitian (η-deformed inner product framework).

numpy-FREE (v0.7.5rc124, #564): matrices are the framework-native
:class:`srmech.amsc.mat.Mat`, vectors are plain ``complex`` lists, and the
oracle is direct ``Mat``-entry / list arithmetic + the numpy-free
``mat_hermitian_eigendecompose`` (NOT a numpy reference). Fixed small operators
replace the prior random fixtures.
"""

from __future__ import annotations

import pytest

from srmech.amsc.mat import Mat
from srmech.amsc.laplacian import mat_matmul, mat_hermitian_eigendecompose
from srmech.qm import pseudo_hermitian as ph


def _identity(n: int) -> "Mat":
    return Mat.from_rows(
        [[1.0 + 0j if i == j else 0j for j in range(n)] for i in range(n)],
        is_complex=True,
    )


# A fixed Hermitian operator (was a random Hermitian fixture).
_HERMITIAN = Mat.from_rows(
    [
        [2.0 + 0j, 1.0 + 1.0j, 0.5 - 0.5j],
        [1.0 - 1.0j, 3.0 + 0j, -0.5j],
        [0.5 + 0.5j, 0.5j, 1.0 + 0j],
    ],
    is_complex=True,
)

# A fixed Hermitian positive-definite η = A Aᴴ (was a random A·Aᴴ fixture).
_A = Mat.from_rows(
    [
        [1.0 + 0j, 0.3 + 0.2j, 0.0 + 0j],
        [0.1 - 0.4j, 1.2 + 0j, 0.2 + 0.1j],
        [0.0 + 0j, 0.5 - 0.3j, 1.5 + 0j],
    ],
    is_complex=True,
)
_POSITIVE_DEFINITE = mat_matmul(_A, _A.conj().T)


# ----------------------------------------------------------------------
# inner_product_eta
# ----------------------------------------------------------------------


def test_inner_product_eta_identity_reduces():
    """For η = I, ⟨a|b⟩_η = ⟨a|b⟩ (standard inner product)."""
    a = [1.0 + 2.0j, 3.0 - 1.0j, 0.0 + 1.0j, 2.0 + 0j, -1.0 + 0.5j]
    b = [2.0 + 0j, 1.0 + 1.0j, 4.0 - 2.0j, 0.0 + 3.0j, 1.0 - 1.0j]
    eta_inner = ph.inner_product_eta(a, b, _identity(5))
    std_inner = sum(a[i].conjugate() * b[i] for i in range(5))
    assert abs(eta_inner - std_inner) < 1e-13


def test_inner_product_eta_self_real():
    """For Hermitian (positive) η, ⟨a|a⟩_η is real."""
    a = [1.0 + 0.5j, -0.5 + 1.0j, 2.0 - 0.5j]
    val = ph.inner_product_eta(a, a, _POSITIVE_DEFINITE)
    assert abs(val.imag) < 1e-12


def test_inner_product_eta_shape_mismatch():
    with pytest.raises(ValueError):
        ph.inner_product_eta([1, 2], [1, 2, 3], _identity(2))


# ----------------------------------------------------------------------
# expectation_eta
# ----------------------------------------------------------------------


def test_expectation_eta_identity_reduces():
    """For η = I, ⟨O⟩_η = ⟨ψ|O|ψ⟩ / ⟨ψ|ψ⟩."""
    psi = [1.0 + 0.5j, -0.5 + 1.0j, 2.0 - 0.5j]
    O = _HERMITIAN
    val = ph.expectation_eta(O, psi, _identity(3))
    # manual ⟨ψ|O|ψ⟩ / ⟨ψ|ψ⟩
    n = 3
    Opsi = [sum(O[i, j] * psi[j] for j in range(n)) for i in range(n)]
    num = sum(psi[i].conjugate() * Opsi[i] for i in range(n))
    den = sum(psi[i].conjugate() * psi[i] for i in range(n))
    assert abs(val - num / den) < 1e-13


def test_expectation_eta_hermitian_eigenstate():
    """For Hermitian O and eigenstate |λ⟩ with η = I, ⟨O⟩ = λ."""
    evals, V = mat_hermitian_eigendecompose(_HERMITIAN)
    k = 1
    psi = [V[i, k] for i in range(3)]
    val = ph.expectation_eta(_HERMITIAN, psi, _identity(3))
    assert abs(val - evals[k, 0]) < 1e-12


# ----------------------------------------------------------------------
# is_pseudo_hermitian
# ----------------------------------------------------------------------


def test_is_pseudo_hermitian_for_hermitian_with_identity_eta():
    """Any Hermitian O is η-pseudo-Hermitian for η = I."""
    assert ph.is_pseudo_hermitian(_HERMITIAN, _identity(3))


def test_is_pseudo_hermitian_for_non_hermitian_with_identity_eta_fails():
    """Non-Hermitian O fails η-pseudo-Hermitian test for η = I."""
    O = Mat.from_rows(
        [[0.0 + 0j, 2.0 + 1.0j], [0.5 - 0.3j, 1.0 + 0j]], is_complex=True
    )
    assert not ph.is_pseudo_hermitian(O, _identity(2))


def test_is_pseudo_hermitian_constructed_eta():
    """η constructed from O's eigendecomposition makes O η-pseudo-Hermitian."""
    # Triangular matrix with distinct real eigenvalues (1, 2, 3).
    O = Mat.from_rows(
        [[1.0, 0.5, 0.0], [0.0, 2.0, 0.5], [0.0, 0.0, 3.0]], is_complex=True
    )
    eta = ph.construct_eta_from_eigendecomposition(O)
    assert ph.is_pseudo_hermitian(O, eta, atol=1e-8)


# ----------------------------------------------------------------------
# construct_eta_from_eigendecomposition
# ----------------------------------------------------------------------


def test_construct_eta_complex_spectrum_rejected():
    """Operator with complex spectrum (e.g. rotation) is rejected."""
    O = Mat.from_rows([[0.0, -1.0], [1.0, 0.0]], is_complex=True)  # eigvals ±i
    with pytest.raises(ValueError):
        ph.construct_eta_from_eigendecomposition(O)


def test_construct_eta_returns_hermitian():
    O = Mat.from_rows([[1.0, 0.5], [0.0, 2.0]], is_complex=True)
    eta = ph.construct_eta_from_eigendecomposition(O)
    n = eta.shape[0]
    herm_dev = max(
        abs(eta[i, j] - eta[j, i].conjugate()) for i in range(n) for j in range(n)
    )
    assert herm_dev < 1e-12


# ----------------------------------------------------------------------
# pseudo_hermitian_eigenvalues_real
# ----------------------------------------------------------------------


def test_eigenvalues_real_for_constructed_eta():
    """η-pseudo-Hermitian O with positive η has real spectrum
    (Mostafazadeh theorem)."""
    O = Mat.from_rows(
        [[1.0, 0.5, 0.0], [0.0, 2.0, 0.5], [0.0, 0.0, 3.0]], is_complex=True
    )
    eta = ph.construct_eta_from_eigendecomposition(O)
    assert ph.pseudo_hermitian_eigenvalues_real(O, eta, atol=1e-8)


def test_eigenvalues_real_returns_false_for_non_pseudo_hermitian():
    """A complex-spectrum operator with identity-η fails the test."""
    O = Mat.from_rows([[0.0, -1.0], [1.0, 0.0]], is_complex=True)  # eigvals ±i
    assert not ph.pseudo_hermitian_eigenvalues_real(O, _identity(2), atol=1e-10)
