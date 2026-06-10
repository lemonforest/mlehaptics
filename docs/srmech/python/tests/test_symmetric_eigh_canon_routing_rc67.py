"""rc67 — symmetric_eigendecompose → C-backed hermitian + eigenvector sign-canon.

Lane 1 of the post-floor numpy-removal: the real-symmetric `np.linalg.eigh` in
``laplacian.symmetric_eigendecompose`` routes onto the already-shipped, C-backed
``hermitian_eigendecompose`` (real-symmetric IS complex-Hermitian — native Jacobi
peer when present; NumPy ``eigh`` only as *that* op's own shared fallback). The
eigenvectors of a real-symmetric matrix are real (the Hermitian path returns them
with imaginary part ~0), so we take ``.real`` and ``_canonicalize_eigenvector_
signs`` pins each column's ±1 sign (Class-K: flip so its largest-magnitude entry
is positive, ``col²`` magnitude, never ``abs()`` and no float sqrt).

The eigenvector sign / degenerate-subspace basis is non-unique, so correctness is
pinned by the basis-INVARIANT properties — ascending eigenvalues, reconstruction
``L = V·diag(w)·Vᵀ``, orthonormality — verified here on non-degenerate AND
degenerate (repeated-eigenvalue) inputs, where the sign pin still yields a real
orthonormal V.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np

from srmech.amsc import laplacian
from srmech.amsc.laplacian import _canonicalize_eigenvector_signs


def _cases():
    rng = np.random.default_rng(42)
    A = rng.standard_normal((5, 5))
    yield "random-sym-5", A + A.T
    yield "diagonal", np.diag([3.0, 1.0, 5.0, 2.0])
    yield "4-cycle-Laplacian-degen", np.asarray(
        laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)]), dtype=np.float64
    )
    yield "identity-fully-degen", np.eye(5)
    yield "block-degen", np.diag([2.0, 2.0, 2.0, 5.0, 5.0])


def test_symmetric_eigendecompose_real_and_reconstructs_incl_degenerate():
    """Real float64 V, ascending eigvals == eigvalsh, exact reconstruction."""
    for label, L in _cases():
        L = np.asarray(L, dtype=np.float64)
        n = L.shape[0]
        w, V = laplacian.symmetric_eigendecompose(L)
        assert w.dtype == np.float64 and V.dtype == np.float64, label
        # ascending eigenvalues match numpy's eigvalsh
        np.testing.assert_allclose(w, np.linalg.eigvalsh(L), atol=1e-9,
                                   err_msg=f"{label}: eigvals")
        # reconstruction (basis-invariant — holds even on degenerate blocks)
        np.testing.assert_allclose(V @ np.diag(w) @ V.T, L, atol=1e-9,
                                   err_msg=f"{label}: reconstruction")
        # orthonormal
        np.testing.assert_allclose(V.T @ V, np.eye(n), atol=1e-9,
                                   err_msg=f"{label}: orthonormality")


def test_canonicalize_eigenvector_signs_pins_pivot_positive():
    """Each (real) column's largest-magnitude entry is flipped to positive — a
    pure ±1 Class-K sign pin (no abs / no sqrt)."""
    rng = np.random.default_rng(1)
    V = rng.standard_normal((6, 6))
    C = np.asarray(_canonicalize_eigenvector_signs(V))
    for j in range(6):
        col = C[:, j]
        k = int(np.argmax(col * col))   # largest-|·| via col² (matches the helper)
        assert col[k] > 0.0
    # a sign flip only multiplies a column by ±1: |C| == |V| columnwise, and
    # every column is ± the original
    np.testing.assert_allclose(np.abs(C), np.abs(V), atol=1e-12)
    for j in range(6):
        assert np.allclose(C[:, j], V[:, j]) or np.allclose(C[:, j], -V[:, j])


def test_canonicalize_is_deterministic():
    """Same input → same canonical output (a stable, settable convention)."""
    rng = np.random.default_rng(2)
    V = rng.standard_normal((4, 4))
    np.testing.assert_array_equal(
        np.asarray(_canonicalize_eigenvector_signs(V)),
        np.asarray(_canonicalize_eigenvector_signs(V)),
    )


def test_no_residual_np_linalg_eigh_in_symmetric_eigendecompose():
    """symmetric_eigendecompose no longer calls (or names) numpy eigh; it routes
    to hermitian_eigendecompose."""
    import srmech

    src = (pathlib.Path(srmech.__file__).parent / "amsc" / "laplacian.py").read_text(
        encoding="utf-8"
    )
    # isolate the symmetric_eigendecompose function body
    start = src.index("def symmetric_eigendecompose(")
    end = src.index("\ndef ", start + 1)
    body = src[start:end]
    assert not re.search(r"\b(?:np|numpy)\.linalg\.eigh\s*\(", body)
    assert "hermitian_eigendecompose(" in body
    assert "_canonicalize_eigenvector_signs(" in body
