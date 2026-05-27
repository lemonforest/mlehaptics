"""Parity tests for the ADR-0002 Phase 2 Class L broadening (v0.4.1rc5).

Four new ops added per the Phase 1 spike finding (TDSE non-fitting case):

- ``hermitian_eigendecompose`` — complex Hermitian generalisation of
  ``jacobi_eigvals``.
- ``dense_matvec_complex`` — general complex ``M @ v``.
- ``elementwise_multiply_complex`` — pointwise ``a * b``.
- ``elementwise_transcendental`` — vectorised ``exp/cos/sin/log/exp_i``.

Parity is against numpy reference paths (``np.linalg.eigh``, ``M @ v``,
``a * b``, ``np.exp / cos / sin / log``).
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import _native, laplacian


# ---------------------------------------------------------------------
# hermitian_eigendecompose
# ---------------------------------------------------------------------


def _make_hermitian(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    H = (A + A.conj().T) / 2
    return H.astype(np.complex128)


def test_hermitian_eigendecompose_real_diagonal():
    H = np.diag(np.array([3.0, 1.0, 5.0, 2.0]) + 0j)
    eigvals, V = laplacian.hermitian_eigendecompose(H)
    np.testing.assert_allclose(eigvals, np.array([1.0, 2.0, 3.0, 5.0]),
                               atol=1e-12)
    # V should be a permutation of the identity (up to phases).
    assert V.shape == (4, 4)


def test_hermitian_eigendecompose_matches_numpy():
    H = _make_hermitian(4, seed=42)
    w, V = laplacian.hermitian_eigendecompose(H)
    w_ref = np.linalg.eigvalsh(H)
    np.testing.assert_allclose(w, w_ref, atol=1e-10)
    # H · V = V · diag(w): residual should be tiny.
    HV = H @ V
    Vdiag = V * w[np.newaxis, :]
    residual = np.linalg.norm(HV - Vdiag)
    assert residual < 1e-9, f"H V - V diag(w) = {residual}"


def test_hermitian_eigendecompose_unitary():
    H = _make_hermitian(5, seed=7)
    _, V = laplacian.hermitian_eigendecompose(H)
    VHV = V.conj().T @ V
    np.testing.assert_allclose(VHV, np.eye(5), atol=1e-9)


def test_hermitian_eigendecompose_zero_size():
    H = np.zeros((0, 0), dtype=np.complex128)
    w, V = laplacian.hermitian_eigendecompose(H)
    assert w.shape == (0,)
    assert V.shape == (0, 0)


def test_hermitian_eigendecompose_2x2_pauli():
    """Pauli-Y: H = [[0, -i], [i, 0]]; eigvals = ±1."""
    H = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
    w, V = laplacian.hermitian_eigendecompose(H)
    np.testing.assert_allclose(np.sort(w), np.array([-1.0, 1.0]), atol=1e-12)
    HV = H @ V
    Vdiag = V * w[np.newaxis, :]
    np.testing.assert_allclose(HV, Vdiag, atol=1e-12)


# ---------------------------------------------------------------------
# symmetric_eigendecompose  (v0.4.3rc4 — real-symmetric Class L
# specialisation of hermitian_eigendecompose; UPSTREAM_NOTES §2.1)
# ---------------------------------------------------------------------


def _make_symmetric(n: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    return ((A + A.T) / 2).astype(np.float64)


def test_symmetric_eigendecompose_returns_real_float64():
    """The whole point of the specialisation: real eigvals AND real
    eigvecs (no complex128 V → no ComplexWarning for real-symmetric L)."""
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    L = np.asarray(L, dtype=np.float64)
    eigvals, V = laplacian.symmetric_eigendecompose(L)
    assert eigvals.dtype == np.float64
    assert V.dtype == np.float64


def test_symmetric_eigendecompose_matches_numpy():
    L = _make_symmetric(5, seed=42)
    w, V = laplacian.symmetric_eigendecompose(L)
    w_ref = np.linalg.eigvalsh(L)
    np.testing.assert_allclose(w, w_ref, atol=1e-10)
    # Reconstruction L = V diag(w) Vᵀ.
    recon = V @ np.diag(w) @ V.T
    np.testing.assert_allclose(recon, L, atol=1e-9)


def test_symmetric_eigendecompose_orthonormal():
    L = _make_symmetric(6, seed=7)
    _, V = laplacian.symmetric_eigendecompose(L)
    np.testing.assert_allclose(V.T @ V, np.eye(6), atol=1e-9)


def test_symmetric_eigendecompose_diagonal():
    L = np.diag(np.array([3.0, 1.0, 5.0, 2.0]))
    eigvals, V = laplacian.symmetric_eigendecompose(L)
    np.testing.assert_allclose(eigvals, np.array([1.0, 2.0, 3.0, 5.0]),
                               atol=1e-12)
    assert V.shape == (4, 4)


def test_symmetric_eigendecompose_laplacian_nullspace():
    """A connected graph Laplacian has exactly one zero eigenvalue
    (the constant vector); smallest eigenvalue ≈ 0."""
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    L = np.asarray(L, dtype=np.float64)
    eigvals, _ = laplacian.symmetric_eigendecompose(L)
    assert abs(eigvals[0]) < 1e-10


def test_symmetric_eigendecompose_zero_size():
    L = np.zeros((0, 0), dtype=np.float64)
    w, V = laplacian.symmetric_eigendecompose(L)
    assert w.shape == (0,)
    assert V.shape == (0, 0)


def test_symmetric_eigendecompose_rejects_nonsquare():
    with pytest.raises(ValueError):
        laplacian.symmetric_eigendecompose(np.zeros((2, 3)))


def test_symmetric_eigendecompose_in_class_l_registry():
    assert "symmetric_eigendecompose" in laplacian.LAPLACIAN_OPS
    assert "symmetric_eigendecompose" in laplacian.__all__


# ---------------------------------------------------------------------
# dense_matvec_complex
# ---------------------------------------------------------------------


def test_dense_matvec_complex_matches_numpy():
    rng = np.random.default_rng(123)
    M = rng.standard_normal((5, 3)) + 1j * rng.standard_normal((5, 3))
    v = rng.standard_normal(3) + 1j * rng.standard_normal(3)
    out = laplacian.dense_matvec_complex(M, v)
    expected = M @ v
    np.testing.assert_allclose(out, expected, atol=1e-12)


def test_dense_matvec_complex_square():
    M = np.array([[1+0j, 2-1j], [0+1j, 3+0j]])
    v = np.array([1-1j, 2+0j])
    out = laplacian.dense_matvec_complex(M, v)
    np.testing.assert_allclose(out, M @ v, atol=1e-12)


def test_dense_matvec_complex_shape_mismatch():
    M = np.eye(3, dtype=np.complex128)
    v = np.zeros(2, dtype=np.complex128)
    with pytest.raises(ValueError):
        laplacian.dense_matvec_complex(M, v)


# ---------------------------------------------------------------------
# elementwise_multiply_complex
# ---------------------------------------------------------------------


def test_elementwise_multiply_complex_matches_numpy():
    a = np.array([1+1j, 2-1j, 3+0j, -1+2j])
    b = np.array([1-1j, 1+1j, -1j, 0+0j])
    out = laplacian.elementwise_multiply_complex(a, b)
    np.testing.assert_allclose(out, a * b, atol=1e-12)


def test_elementwise_multiply_complex_empty():
    a = np.zeros(0, dtype=np.complex128)
    b = np.zeros(0, dtype=np.complex128)
    out = laplacian.elementwise_multiply_complex(a, b)
    assert out.shape == (0,)


# ---------------------------------------------------------------------
# elementwise_transcendental
# ---------------------------------------------------------------------


def test_elementwise_transcendental_exp_matches_numpy():
    x = np.array([0.0, 0.5, 1.0, 2.0, -1.0])
    out = laplacian.elementwise_transcendental(x, "exp")
    np.testing.assert_allclose(out, np.exp(x), atol=1e-12)


def test_elementwise_transcendental_cos_sin_match_numpy():
    x = np.linspace(-3.0, 3.0, 7)
    np.testing.assert_allclose(
        laplacian.elementwise_transcendental(x, "cos"),
        np.cos(x), atol=1e-12,
    )
    np.testing.assert_allclose(
        laplacian.elementwise_transcendental(x, "sin"),
        np.sin(x), atol=1e-12,
    )


def test_elementwise_transcendental_log_matches_numpy():
    x = np.array([1.0, 2.0, 10.0, 0.5, 100.0])
    out = laplacian.elementwise_transcendental(x, "log")
    np.testing.assert_allclose(out, np.log(x), atol=1e-12)


def test_elementwise_transcendental_log_rejects_nonpositive():
    x = np.array([1.0, 0.0, 2.0])
    with pytest.raises((ValueError, FloatingPointError)):
        laplacian.elementwise_transcendental(x, "log")


def test_elementwise_transcendental_exp_i_complex():
    """exp_i(x) = exp(1j * x) — TDSE-relevant complex exponential."""
    x = np.array([0.0, np.pi / 4, np.pi / 2, np.pi, 2 * np.pi])
    out = laplacian.elementwise_transcendental(x, "exp_i")
    expected = np.exp(1j * x)
    np.testing.assert_allclose(out, expected, atol=1e-12)


def test_elementwise_transcendental_unknown_op_rejected():
    x = np.array([1.0, 2.0])
    with pytest.raises(ValueError):
        laplacian.elementwise_transcendental(x, "tanh")


# ---------------------------------------------------------------------
# LAPLACIAN_OPS registry
# ---------------------------------------------------------------------


def test_class_l_ops_registry_includes_new_ops():
    expected_new = {
        "hermitian_eigendecompose",
        "dense_matvec_complex",
        "elementwise_multiply_complex",
        "elementwise_transcendental",
    }
    expected_old = {
        "dense_adjacency",
        "dense_laplacian",
        "normalized_laplacian",
        "jacobi_eigvals",
    }
    ops = set(laplacian.LAPLACIAN_OPS)
    assert expected_new <= ops
    assert expected_old <= ops


def test_tdse_evolve_composition_end_to_end():
    """End-to-end TDSE compose test — the ADR-0002 Phase 1 spike scenario.

    psi(t) = V · diag(exp(-i*eigvals*t)) · V^H · psi(0). With H Hermitian
    and psi(0) arbitrary, verify |psi(t)| preservation (unitary
    evolution) plus numpy parity.
    """
    H = _make_hermitian(4, seed=99)
    psi0 = np.array([1.0, 0.5j, -0.5, 0.5+0.5j], dtype=np.complex128)
    psi0 = psi0 / np.linalg.norm(psi0)
    t = 1.5
    # Compose via the new Class L ops.
    w, V = laplacian.hermitian_eigendecompose(H)
    psi_eig = laplacian.dense_matvec_complex(V.conj().T, psi0)
    phase = laplacian.elementwise_transcendental(-w * t, "exp_i")
    psi_eig_t = laplacian.elementwise_multiply_complex(phase, psi_eig)
    psi_t = laplacian.dense_matvec_complex(V, psi_eig_t)
    # Reference: scipy-style direct expm-via-eigh.
    psi_t_ref = V @ (np.exp(-1j * w * t) * (V.conj().T @ psi0))
    np.testing.assert_allclose(psi_t, psi_t_ref, atol=1e-10)
    # Norm preserved by unitary evolution.
    np.testing.assert_allclose(
        np.linalg.norm(psi_t), 1.0, atol=1e-10,
    )
