"""Path A MUSIC — multiple-signal-classification subspace DOA / frequency estimator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only (acoustic source-finding,
civilian DOA estimation, frequency estimation).

Identity per the implementation plan §1: MUSIC IS a Class L (correlation
eigendecomposition splitting signal and noise subspaces) ∘ Class K (subspace
threshold / projection projection that identifies the noise-orthogonal
steering vectors) composition.

Path B dual in Phase 6 (Path B correlation eigendecomposition).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Schmidt
(1986) original MUSIC paper.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from srmech.amsc.laplacian import dense_matmul_complex, hermitian_eigendecompose

OPERATION_NAME = "music"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-eigendecomp-amortise"
SSOT_CITATION = (
    "Schmidt (1986), 'Multiple emitter location and signal parameter "
    "estimation', IEEE Trans. AP-34(3), 276-280. DOI 10.1109/TAP.1986."
    "1143830 (Crossref)."
)


def op(
    R,
    steering_vectors,
    *,
    n_sources: int,
    D: int = 8192,
) -> np.ndarray:
    """MUSIC pseudo-spectrum for ``steering_vectors`` given covariance ``R``.

    Parameters
    ----------
    R:
        ``(M, M)`` Hermitian covariance matrix.
    steering_vectors:
        ``(M, K)`` candidate array-manifold vectors (one per angle bin).
    n_sources:
        Number of sources (Class K: subspace partition threshold).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Real-valued MUSIC pseudo-spectrum of length K (one per steering
        vector); peaks correspond to source directions.
    """
    R_arr = np.asarray(R, dtype=np.complex128)
    if R_arr.ndim != 2 or R_arr.shape[0] != R_arr.shape[1]:
        raise ValueError(f"R must be square; got {R_arr.shape}")
    A = np.asarray(steering_vectors, dtype=np.complex128)
    if A.ndim != 2:
        raise ValueError(f"steering_vectors must be 2-D; got {A.shape}")
    M = R_arr.shape[0]
    if A.shape[0] != M:
        raise ValueError(
            f"steering_vectors first dim {A.shape[0]} != M {M}"
        )
    # Class L: Hermitian eigendecomposition via srmech's own cascade primitive.
    # R is complex-Hermitian; MUSIC uses the noise-subspace projection
    # (phase/sign-invariant), so the complex128 eigenvectors are kept.
    eigvals, eigvecs = hermitian_eigendecompose(R_arr)
    # Sort by ascending eigenvalue; noise subspace = smallest M - n_sources.
    order = np.argsort(eigvals)
    eigvecs = eigvecs[:, order]
    # Class K: subspace partition threshold.
    n_noise = M - n_sources
    En = eigvecs[:, :n_noise]
    # MUSIC pseudo-spectrum: P(theta) = 1 / (a^H En En^H a)
    # Vectorise across all steering vectors.
    # Enᴴ·A — Class-L dense complex matmul (noise-subspace projection).
    proj = dense_matmul_complex(En.conj().T, A)  # shape (n_noise, K)
    # |z|² = real²+imag² (no abs())
    denom = np.sum(proj.real ** 2 + proj.imag ** 2, axis=0)
    return 1.0 / np.maximum(denom, 1e-30)
