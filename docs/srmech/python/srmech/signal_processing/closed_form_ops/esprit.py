"""Path A ESPRIT — closed-form rotational-invariance subspace DOA estimator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only.

Identity per the implementation plan §1: ESPRIT IS a Class L (generalised
eigendecomposition on shifted-subarray signal subspaces) ∘ Class K (rotation
extraction from the generalised eigenvalues onto the unit-circle / DOA
angles) composition.

Path B dual in Phase 6 (Path B generalised eigendecomposition).

Carrier-removal #564 (rc98): numpy-FREE — the three matrix steps route through
the native Mat-carrier foundation (:func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose`
+ :func:`~srmech.amsc.laplacian.mat_lstsq` + :func:`~srmech.amsc.laplacian.mat_eigvals`),
so esprit runs with numpy genuinely absent. No top-level ``import numpy``.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Roy &
Kailath (1989) ESPRIT original paper.
"""

from __future__ import annotations

from typing import List

from srmech.amsc.laplacian import (
    mat_hermitian_eigendecompose,
    mat_lstsq,
    mat_eigvals,
)
from srmech.amsc.mat import Mat

OPERATION_NAME = "esprit"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Roy & Kailath (1989), 'ESPRIT--Estimation of signal parameters via "
    "rotational invariance techniques', IEEE Trans. ASSP 37(7), 984-995. "
    "DOI 10.1109/29.32276 (Crossref)."
)


def op(R, *, n_sources: int, D: int = 8192) -> List[complex]:
    """ESPRIT generalised-eigenvalue DOA / frequency estimator.

    Parameters
    ----------
    R:
        ``(M, M)`` Hermitian covariance matrix from a uniform linear array
        (ULA) of M elements (a :class:`~srmech.amsc.mat.Mat`, a nested
        sequence, or anything with a ``tolist()`` — coerced numpy-free).
    n_sources:
        Number of sources (subspace dimension).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[complex]
        Length-``n_sources`` list of the generalised eigenvalues; their angles
        give the DOAs ``angle / (-pi * sin(theta))``.
    """
    # Coerce R to a numpy-free complex Mat (tolist() covers ndarray AND Mat).
    rows = R.tolist() if hasattr(R, "tolist") else [list(r) for r in R]
    M = len(rows)
    if M == 0 or any(len(r) != M for r in rows):
        cols = len(rows[0]) if rows else 0
        raise ValueError(f"R must be square; got {M}x{cols}")
    if n_sources >= M:
        raise ValueError(f"n_sources {n_sources} >= M {M}")
    R_mat = Mat.from_rows([[complex(v) for v in r] for r in rows], is_complex=True)
    # Eigendecomposition (Class L) via the native Mat-carrier Hermitian solver.
    # R is complex-Hermitian; ESPRIT uses signal-subspace projections
    # (phase/sign-invariant), so the complex eigenvectors are kept.
    eigvals_mat, eigvecs_mat = mat_hermitian_eigendecompose(R_mat)
    evals = [float(eigvals_mat[i, 0]) for i in range(M)]
    # Signal subspace: the n_sources LARGEST eigenvalues (descending argsort —
    # pure-Python, no np.argsort).
    order = sorted(range(M), key=lambda k: evals[k], reverse=True)[:n_sources]
    # Es = eigvecs[:, order] — column-select into a fresh (M, n_sources) Mat.
    es_rows = [[eigvecs_mat[i, order[s]] for s in range(n_sources)] for i in range(M)]
    # Shifted subarrays: Es1 = first M-1 rows, Es2 = last M-1 rows.
    Es1 = Mat.from_rows(es_rows[: M - 1], is_complex=True)
    Es2 = Mat.from_rows(es_rows[1:], is_complex=True)
    # Solve Es2 ≈ Es1·Phi via LS (Class L): Phi = (Es1ᴴ Es1)⁻¹ Es1ᴴ Es2.
    Phi = mat_lstsq(Es1, Es2)
    # Class K: extract the rotation as the eigenvalues of Phi.
    return mat_eigvals(Phi)
