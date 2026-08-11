"""Path A MUSIC — multiple-signal-classification subspace DOA / frequency estimator.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only (acoustic source-finding,
civilian DOA estimation, frequency estimation).

⚠️ **"MUSIC" HERE IS AN ACRONYM, NOT THE ART FORM.** It expands to **MU**ltiple
**SI**gnal **C**lassification — an array-processing method for estimating the
direction of arrival of several sources at once. It has nothing whatever to do
with the ``srmech.music`` package next door, which is acoustics and pitch
relations. The two were a genuine homograph: this module was named ``music``
through rc423 and sat one dotted path away from ``srmech.music``. rc424 renamed
it ``music_doa`` so the collision cannot recur — the name now carries its own
disambiguation, rather than relying on a reader noticing the package it lives
in. See the reciprocal note in ``srmech/music/__init__.py``.

Identity per the implementation plan §1: MUSIC IS a Class L (correlation
eigendecomposition splitting signal and noise subspaces) ∘ Class K (subspace
threshold / projection that identifies the noise-orthogonal steering vectors)
composition.

Path B dual in Phase 6 (Path B correlation eigendecomposition).

Carrier-removal #564 (rc99): numpy-FREE — the eigendecomposition + noise-subspace
projection route through the native Mat-carrier foundation
(:func:`~srmech.math.laplacian.mat_hermitian_eigendecompose` +
:func:`~srmech.math.laplacian.mat_matmul`), so MUSIC runs with numpy genuinely
absent. No top-level ``import numpy``.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Schmidt's
original MUSIC paper, cited through its OPEN chain — see :data:`SSOT_CITATION`.
"""

from __future__ import annotations

from typing import List

from srmech.math.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.math.mat import Mat

OPERATION_NAME = "music_doa"
CLASS_COMPOSITION = ("L", "K")
PERFORMANCE_HINT = "shallow-cascade-eigendecomp-amortise"
#: OPEN attestation chain. Through rc423 this cited ONLY the paywalled IEEE
#: DOI 10.1109/TAP.1986.1143830, which ``[[feedback_paywalled_doi_cannot_be_attested]]``
#: rejects outright — and it was shipped text, so the project was breaking its
#: own rule in a published wheel. The primary anchor is now the openly
#: distributed DTIC proceedings volume in which Schmidt first presented the
#: method; the IEEE reprint is named as the later, paywalled venue rather than
#: used as the attestation. Same substitution shape as
#: ``srmech.chemistry.reactions`` (Feinberg lectures over the paywalled
#: Chem. Eng. Sci. origin paper).
SSOT_CITATION = (
    "Schmidt, R.O. (1979), 'Multiple emitter location and signal parameter "
    "estimation', in Proceedings of the RADC Spectrum Estimation Workshop "
    "(2nd), 3-5 October 1979, Griffiss AFB NY, 243-258; RADC-TR-79-63. "
    "OPEN: DTIC accession ADA081736 (public release, unlimited distribution). "
    "Reprinted as IEEE Trans. Antennas Propag. AP-34(3) (1986) 276-280, "
    "DOI 10.1109/TAP.1986.1143830 -- that venue is PAYWALLED and is named "
    "here for provenance only, NOT used as the attestation."
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
        ``(M, M)`` Hermitian covariance matrix (a :class:`~srmech.math.mat.Mat`,
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


# ──────────────────────────────────────────────────────────────────────
# Module-load registration with srmech.signal_processing.path_registry
# ──────────────────────────────────────────────────────────────────────


def _register() -> None:
    """Register Path A MUSIC DOA with the dispatcher's path_registry.

    rc424 (`#T1113`) — the FIRST registration of this op, not a re-pointing.
    Measured on rc423: 13 of the 38 declared Path-A modules were actually
    dispatchable, and this was not one of them, so the op was reachable only
    as ``closed_form_ops.music.op()``. It had no ToolEntry either, which is
    why it was ABSENT from ``search()`` rather than merely out-ranked by the
    ``srmech.music`` acoustics ops.

    Path-A-only (the Path B dual is Phase 6), so this follows the
    ``pi_cascade`` pattern: the registration lives in the ``closed_form_ops``
    module itself rather than in a ``path_b_ops`` sidecar.
    """
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=op,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register()
