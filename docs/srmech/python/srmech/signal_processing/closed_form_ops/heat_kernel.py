"""Path A heat kernel denoising — closed-form ``g(lambda) = exp(-t*lambda)``.

Identity per the implementation plan §1: heat kernel denoising IS a Class L
(graph-Laplacian eigendecomposition) ∘ ``g(lambda) = exp(-t*lambda)``
elementwise transcendental on the eigenvalue spectrum. The denoised signal
is ``V @ diag(exp(-t*lambda)) @ V^H @ signal``.

This composes directly with ``srmech.amsc.laplacian.hermitian_eigendecompose``
which already provides the Class L primitive.

Path B dual in Phase 6 (Path B Laplacian g(lambda) bound-vector lookup).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Chung (1997)
*Spectral Graph Theory* §10 + Hammond, Vandergheynst & Gribonval (2011) on
spectral graph wavelets / heat kernel diffusion.
"""

from __future__ import annotations

import numpy as np

from srmech.amsc.laplacian import hermitian_eigendecompose

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


def op(signal, laplacian, *, t: float = 1.0, D: int = 8192):
    """Heat-kernel diffusion denoising on a graph substrate.

    Parameters
    ----------
    signal:
        ``(n,)`` real or complex node-domain state.
    laplacian:
        ``(n, n)`` Hermitian graph Laplacian.
    t:
        Diffusion time (larger ``t`` -> more smoothing). Default 1.0.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Denoised node-domain state, same length as ``signal``.
    """
    # Compose with the existing Class L primitive in srmech.amsc.laplacian.
    # The Laplacian is treated as complex-Hermitian; ``V`` is complex128 and
    # the downstream spectral-filter arithmetic (``V.conj().T``) keeps it so.
    L_arr = np.asarray(laplacian, dtype=np.complex128)
    eigvals, V = hermitian_eigendecompose(L_arr)

    sig_arr = np.asarray(signal, dtype=np.complex128)
    if sig_arr.ndim != 1:
        raise ValueError(f"heat_kernel expects 1-D signal; got {sig_arr.shape}")
    n = L_arr.shape[0]
    if sig_arr.shape[0] != n:
        raise ValueError(
            f"signal length {sig_arr.shape[0]} != laplacian size {n}"
        )
    # g(lambda) = exp(-t * lambda); applied elementwise on eigenvalue spectrum.
    g = np.exp(-t * eigvals)
    coeffs = V.conj().T @ sig_arr
    return V @ (g * coeffs)
