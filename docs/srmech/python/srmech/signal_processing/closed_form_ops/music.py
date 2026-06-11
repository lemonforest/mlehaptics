"""Path A MUSIC — multiple-signal-classification subspace DOA / frequency estimator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only (acoustic source-finding,
civilian DOA estimation, frequency estimation).

Identity per the implementation plan §1: MUSIC IS a Class L (correlation
eigendecomposition splitting signal and noise subspaces) ∘ Class K (subspace
threshold / projection projection that identifies the noise-orthogonal
steering vectors) composition.

Path B dual in Phase 6 (Path B correlation eigendecomposition).

Carrier-removal #564 (rc99): numpy-FREE — the eigendecomposition + noise-subspace
projection route through the native Mat-carrier foundation
(:func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose` +
:func:`~srmech.amsc.laplacian.mat_matmul`), so MUSIC runs with numpy genuinely
absent. No top-level ``import numpy``.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Schmidt
(1986) original MUSIC paper.
"""

from __future__ import annotations

from typing import List

from srmech.amsc.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.amsc.mat import Mat

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
) -> List[float]:
    """MUSIC pseudo-spectrum for ``steering_vectors`` given covariance ``R``.

    Parameters
    ----------
    R:
        ``(M, M)`` Hermitian covariance matrix (a :class:`~srmech.amsc.mat.Mat`,
        a nested sequence, or anything with ``tolist()`` — coerced numpy-free).
    steering_vectors:
        ``(M, K)`` candidate array-manifold vectors (one per angle bin).
    n_sources:
        Number of sources (Class K: subspace partition threshold).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[float]
        Real-valued MUSIC pseudo-spectrum of length K (one per steering
        vector); peaks correspond to source directions.
    """
    # Coerce R + steering vectors to numpy-free complex Mats (tolist() covers
    # ndarray AND Mat).
    r_rows = R.tolist() if hasattr(R, "tolist") else [list(r) for r in R]
    M = len(r_rows)
    if M == 0 or any(len(r) != M for r in r_rows):
        cols = len(r_rows[0]) if r_rows else 0
        raise ValueError(f"R must be square; got {M}x{cols}")
    a_rows = (
        steering_vectors.tolist()
        if hasattr(steering_vectors, "tolist")
        else [list(r) for r in steering_vectors]
    )
    if len(a_rows) != M:
        raise ValueError(f"steering_vectors first dim {len(a_rows)} != M {M}")
    K = len(a_rows[0]) if a_rows else 0
    # Class L: Hermitian eigendecomposition via the native Mat-carrier solver.
    # R is complex-Hermitian; MUSIC uses the noise-subspace projection
    # (phase/sign-invariant), so the complex eigenvectors are kept.
    R_mat = Mat.from_rows([[complex(v) for v in r] for r in r_rows], is_complex=True)
    eigvals_mat, eigvecs_mat = mat_hermitian_eigendecompose(R_mat)
    evals = [float(eigvals_mat[i, 0]) for i in range(M)]
    # Class K: subspace partition threshold. Noise subspace = the smallest
    # M - n_sources eigenvectors (ascending argsort — pure-Python, no np.argsort).
    order = sorted(range(M), key=lambda k: evals[k])
    n_noise = M - n_sources
    if n_noise <= 0:
        # Degenerate (no noise subspace): denom ≡ 0 → 1/eps everywhere.
        return [1.0 / 1e-30] * K
    noise_cols = order[:n_noise]
    # Enᴴ = conj-transpose of the noise eigenvectors → (n_noise, M); built numpy-
    # free as a fresh Mat over conj(eigvecs[i, noise_col]).
    enh_rows = [
        [eigvecs_mat[i, noise_cols[s]].conjugate() for i in range(M)]
        for s in range(n_noise)
    ]
    EnH = Mat.from_rows(enh_rows, is_complex=True)
    A_mat = Mat.from_rows([[complex(v) for v in r] for r in a_rows], is_complex=True)
    # Enᴴ·A — Class-L dense complex matmul via the native Mat kernel, (n_noise, K).
    proj = mat_matmul(EnH, A_mat)
    # P(theta) = 1 / Σ_s |proj[s, k]|²  (|z|² = re²+im², no abs()).
    out: List[float] = []
    for k in range(K):
        denom = 0.0
        for s in range(n_noise):
            z = complex(proj[s, k])
            denom += z.real * z.real + z.imag * z.imag
        out.append(1.0 / (denom if denom > 1e-30 else 1e-30))
    return out
