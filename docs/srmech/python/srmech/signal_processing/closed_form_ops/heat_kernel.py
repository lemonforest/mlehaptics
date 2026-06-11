"""Path A heat kernel denoising — closed-form ``g(lambda) = exp(-t*lambda)``.

Identity per the implementation plan §1: heat kernel denoising IS a Class L
(graph-Laplacian eigendecomposition) ∘ ``g(lambda) = exp(-t*lambda)``
elementwise transcendental on the eigenvalue spectrum. The denoised signal
is ``V·diag(exp(-t*lambda))·V^H·signal``.

Carrier-removal #564 (rc100): numpy-FREE — the eigendecomposition routes through
the native :func:`~srmech.amsc.laplacian.mat_hermitian_eigendecompose`, the
spectral filter ``exp(-t*lambda)`` through the Class-N
:func:`srmech.amsc.rational.exp` cascade (real eigenvalues; dispatches to native
``srmech_exp``), and the project / reconstruct matvecs are pure-Python sums over
the eigenvector ``Mat``. No top-level ``import numpy``.

Path B dual in Phase 6 (Path B Laplacian g(lambda) bound-vector lookup).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Chung (1997)
*Spectral Graph Theory* §10 + Hammond, Vandergheynst & Gribonval (2011) on
spectral graph wavelets / heat kernel diffusion.
"""

from __future__ import annotations

from typing import List

from srmech.amsc.laplacian import mat_hermitian_eigendecompose
from srmech.amsc.mat import Mat
from srmech.amsc.rational import exp as _rexp  # Class-N exp cascade, not libm

OPERATION_NAME = "heat_kernel"
CLASS_COMPOSITION = ("L",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Chung (1997), 'Spectral Graph Theory', AMS CBMS Regional Conference "
    "Series Vol. 92, §10 (heat kernel on graphs). Hammond, Vandergheynst & "
    "Gribonval (2011), 'Wavelets on graphs via spectral graph theory', "
    "Appl. Comput. Harmon. Anal. 30, 129-150. DOI 10.1016/j.acha.2010.04.005 "
    "(Crossref)."
)


def op(signal, laplacian, *, t: float = 1.0, D: int = 8192) -> List[complex]:
    """Heat-kernel diffusion denoising on a graph substrate.

    Parameters
    ----------
    signal:
        ``(n,)`` real or complex node-domain state (a 1-D sequence / ndarray /
        anything with ``tolist()`` — coerced numpy-free).
    laplacian:
        ``(n, n)`` Hermitian graph Laplacian (a :class:`~srmech.amsc.mat.Mat`,
        nested sequence, or ``tolist()``-able).
    t:
        Diffusion time (larger ``t`` -> more smoothing). Default 1.0.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list[complex]
        Denoised node-domain state, same length as ``signal``.
    """
    # Coerce L → complex Mat; signal → a 1-D list of complex (numpy-free).
    l_rows = laplacian.tolist() if hasattr(laplacian, "tolist") else [list(r) for r in laplacian]
    n = len(l_rows)
    if n == 0 or any(len(r) != n for r in l_rows):
        cols = len(l_rows[0]) if l_rows else 0
        raise ValueError(f"laplacian must be square; got {n}x{cols}")
    sig_raw = signal.tolist() if hasattr(signal, "tolist") else list(signal)
    if sig_raw and isinstance(sig_raw[0], (list, tuple)):
        raise ValueError("heat_kernel expects 1-D signal")
    if len(sig_raw) != n:
        raise ValueError(f"signal length {len(sig_raw)} != laplacian size {n}")
    sig = [complex(v) for v in sig_raw]
    L_mat = Mat.from_rows([[complex(v) for v in r] for r in l_rows], is_complex=True)
    # Class L: Hermitian eigendecomposition via the native Mat-carrier solver.
    eigvals_mat, V = mat_hermitian_eigendecompose(L_mat)
    # g(λ) = exp(-t·λ) — eigenvalues are REAL, so a per-bin Class-N rational.exp
    # cascade (inlined, not the numpy-carrier elementwise_transcendental).
    g = [_rexp(-t * float(eigvals_mat[k, 0])) for k in range(n)]
    # coeffs = Vᴴ·signal (project onto the eigenbasis); pure-Python matvec.
    coeffs = [sum(V[i, k].conjugate() * sig[i] for i in range(n)) for k in range(n)]
    # out = V·(g ⊙ coeffs) (filter + reconstruct); pure-Python matvec.
    gc = [g[k] * coeffs[k] for k in range(n)]
    return [sum(V[i, k] * gc[k] for k in range(n)) for i in range(n)]
