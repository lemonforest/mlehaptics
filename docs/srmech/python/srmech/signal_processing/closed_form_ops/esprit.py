"""Path A ESPRIT — closed-form rotational-invariance subspace DOA estimator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only.

Identity per the implementation plan §1: ESPRIT IS a Class L (generalised
eigendecomposition on shifted-subarray signal subspaces) ∘ Class K (rotation
extraction from the generalised eigenvalues onto the unit-circle / DOA
angles) composition.

Path B dual in Phase 6 (Path B generalised eigendecomposition).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Roy &
Kailath (1989) ESPRIT original paper.
"""

from __future__ import annotations

import numpy as np

from srmech.amsc.laplacian import hermitian_eigendecompose

OPERATION_NAME = "esprit"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Roy & Kailath (1989), 'ESPRIT--Estimation of signal parameters via "
    "rotational invariance techniques', IEEE Trans. ASSP 37(7), 984-995. "
    "DOI 10.1109/29.32276 (Crossref)."
)


def op(R, *, n_sources: int, D: int = 8192) -> np.ndarray:
    """ESPRIT generalised-eigenvalue DOA / frequency estimator.

    Parameters
    ----------
    R:
        ``(M, M)`` Hermitian covariance matrix from a uniform linear array
        (ULA) of M elements.
    n_sources:
        Number of sources (subspace dimension).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Complex array of length ``n_sources`` containing the generalised
        eigenvalues; their angles give the DOAs ``angle / (-pi * sin(theta))``.
    """
    R_arr = np.asarray(R, dtype=np.complex128)
    if R_arr.ndim != 2 or R_arr.shape[0] != R_arr.shape[1]:
        raise ValueError(f"R must be square; got {R_arr.shape}")
    M = R_arr.shape[0]
    if n_sources >= M:
        raise ValueError(f"n_sources {n_sources} >= M {M}")
    # Eigendecomposition (Class L) via srmech's own cascade primitive.
    # R is complex-Hermitian; ESPRIT uses signal-subspace projections
    # (phase/sign-invariant), so the complex128 eigenvectors are kept.
    eigvals, eigvecs = hermitian_eigendecompose(R_arr)
    # Signal subspace: top n_sources.
    order = np.argsort(eigvals)[::-1]
    Es = eigvecs[:, order[:n_sources]]
    # Shifted subarrays: Es1 = first M-1 rows, Es2 = last M-1 rows.
    Es1 = Es[: M - 1, :]
    Es2 = Es[1:, :]
    # Solve Es2 = Es1 @ Phi via LS: Phi = (Es1^H Es1)^-1 Es1^H Es2
    Phi = np.linalg.lstsq(Es1, Es2, rcond=None)[0]
    # Class K: extract rotation as eigenvalues of Phi.
    phi_eigvals = np.linalg.eigvals(Phi)
    return phi_eigvals
