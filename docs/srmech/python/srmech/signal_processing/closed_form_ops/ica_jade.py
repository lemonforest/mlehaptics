"""Path A ICA-JADE — joint approximate diagonalisation of eigen-matrices.

Identity per the implementation plan §1: ICA-JADE IS a Class L (joint
diagonalisation of fourth-order cumulant matrices) ∘ Class K (independence
threshold / projection onto the maximally-decorrelated basis) composition.

The closed-form reference ships a simplified JADE-style ICA via FastICA-
adjacent approach: whitening (PCA) + Givens-rotation-based joint diagonal-
isation of cumulant slices.

Path B dual in Phase 6 (Path B joint diagonalisation in B-native
eigendecomposition).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Cardoso &
Souloumiac (1993) original JADE + Hyvarinen & Oja (2000) ICA survey.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from srmech.amsc import rational as _srn
from srmech.amsc.laplacian import (
    dense_matmul_real,
    elementwise_sqrt,
    hermitian_eigendecompose,
)

OPERATION_NAME = "ica_jade"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-iterative"
SSOT_CITATION = (
    "Cardoso & Souloumiac (1993), 'Blind beamforming for non-Gaussian "
    "signals', IEE Proc. F 140(6), 362-370. DOI 10.1049/ip-f-2.1993.0054 "
    "(Crossref). Hyvarinen & Oja (2000), 'Independent component analysis: "
    "Algorithms and applications', Neural Networks 13(4-5), 411-430. DOI "
    "10.1016/S0893-6080(00)00026-5."
)


def op(
    X,
    *,
    n_components: Optional[int] = None,
    max_iter: int = 100,
    tol: float = 1e-6,
    D: int = 8192,
) -> Tuple[np.ndarray, np.ndarray]:
    """Independent-component-analysis via simplified JADE-style cumulant diagonalisation.

    Parameters
    ----------
    X:
        ``(n_samples, n_features)`` observation matrix.
    n_components:
        Number of independent components; default = n_features.
    max_iter:
        Maximum Givens-sweep iterations.
    tol:
        Convergence tolerance on off-diagonal cumulant magnitude.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(S, W)`` where ``S`` is the recovered sources ``(n_samples, k)``
        and ``W`` is the unmixing matrix ``(k, n_features)``.
    """
    X = np.asarray(X, dtype=np.float64)
    if X.ndim != 2:
        raise ValueError(f"ica_jade expects 2-D X; got {X.shape}")
    n, p = X.shape
    if n_components is None:
        n_components = p
    # Centring
    X = X - np.mean(X, axis=0, keepdims=True)
    # Whitening via PCA (Class L: covariance eigendecomposition) via srmech's
    # own cascade primitive. ``cov`` is a REAL symmetric covariance and the
    # whitening arithmetic below is real, so take the (mathematically exact)
    # real part of the always-complex128 eigenvectors (value-preserving .real).
    cov = dense_matmul_real(X.T, X) / n
    eigvals, eigvecs = hermitian_eigendecompose(cov)
    eigvecs = np.asarray(eigvecs).real
    # Sort by descending eigenvalue
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    # Keep top n_components and whiten
    eigvals = np.maximum(eigvals[:n_components], 1e-12)
    eigvecs = eigvecs[:, :n_components]
    W_whiten = dense_matmul_real(np.diag(1.0 / elementwise_sqrt(eigvals)), eigvecs.T)
    Z = dense_matmul_real(W_whiten, X.T).T  # whitened sources

    # Fourth-order cumulant approximation: M = E[Z (Z^T C Z) Z^T] - ...
    # For JADE simplified, use Givens-rotation joint diagonalisation
    # of the fourth-order cumulant tensor sliced along the leading dim.
    k = n_components
    cumulants = np.zeros((k, k, k, k), dtype=np.float64)
    for i in range(k):
        for j in range(k):
            for l in range(k):
                for m in range(k):
                    cumulants[i, j, l, m] = np.mean(Z[:, i] * Z[:, j] * Z[:, l] * Z[:, m])
                    if (i == j) and (l == m):
                        cumulants[i, j, l, m] -= 1.0
                    if (i == l) and (j == m):
                        cumulants[i, j, l, m] -= 1.0
                    if (i == m) and (j == l):
                        cumulants[i, j, l, m] -= 1.0

    # Joint diagonalisation via Givens sweeps.
    V = np.eye(k, dtype=np.float64)
    for it in range(max_iter):
        off = 0.0
        for i in range(k):
            for j in range(i + 1, k):
                # Compute the rotation angle that maximally diagonalises
                # the (i, j) slice. JADE canonical form:
                # G = [[a, b], [b, c]] with a + c = sum_{l,m} cumulants[i,j,l,m]^2.
                # Use simplified Givens via the M_ij = (cumulants[i,i,i,j] -
                # cumulants[j,j,j,i]) / (cumulants[i,i,i,i] + cumulants[j,j,j,j]).
                num = 2.0 * cumulants[i, j, i, j]
                den = cumulants[i, i, i, i] - cumulants[j, j, j, j]
                # Class-K sign-branch (no abs())
                if (num if num >= 0 else -num) + (den if den >= 0 else -den) < 1e-15:
                    continue
                theta = 0.25 * _srn.atan2(float(num), float(den) + 1e-15)
                # Class-K sign-branch (no abs())
                if (theta if theta >= 0 else -theta) < tol:
                    continue
                off += theta if theta >= 0 else -theta  # Class-K sign-branch (no abs())
                c, s = _srn.cos(float(theta)), _srn.sin(float(theta))
                # Apply rotation to V and to the cumulant slices.
                G = np.eye(k)
                G[i, i] = c
                G[j, j] = c
                G[i, j] = -s
                G[j, i] = s
                V = dense_matmul_real(V, G)
                # Rotate cumulant tensor along i, j axes.
                cumulants = np.einsum("ai,ijlm->ajlm", G.T, cumulants)
                cumulants = np.einsum("bj,ijlm->ibjm" if False else "ai,ijlm->ajlm", G.T, cumulants)
        if off < tol:
            break

    W = dense_matmul_real(V.T, W_whiten)
    S = dense_matmul_real(W, X.T).T
    return S, W
