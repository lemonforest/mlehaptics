"""Path A multitaper — closed-form DPSS / Slepian multitaper spectral estimator.

Identity per the implementation plan §1: multitaper IS a Class L (band-limit
Laplacian eigendecomposition producing DPSS / discrete prolate spheroidal
sequences) ∘ Class M (bundle averaging across tapered eigenspectrum-windowed
periodograms) composition.

The closed-form reference uses scipy.signal.windows.dpss when available, else
falls back to a sinc-based Slepian approximation. The averaging is the
canonical multitaper estimator.

Path B dual in Phase 6 (DPSS bound-vector bank).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Slepian
(1978) + Thomson (1982) + Percival & Walden (1993).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

OPERATION_NAME = "multitaper"
CLASS_COMPOSITION = ("L", "M")
PERFORMANCE_HINT = "shallow-cascade-bundle-amortise"
SSOT_CITATION = (
    "Slepian (1978), 'Prolate spheroidal wave functions, Fourier analysis, "
    "and uncertainty - V: The discrete case', Bell Sys. Tech. J. 57(5), "
    "1371-1430. Thomson (1982), 'Spectrum estimation and harmonic analysis', "
    "Proc. IEEE 70(9), 1055-1096. DOI 10.1109/PROC.1982.12433. Percival & "
    "Walden (1993), 'Spectral Analysis for Physical Applications', "
    "Cambridge."
)


def op(
    signal,
    *,
    n_tapers: int = 4,
    nw: float = 4.0,
    D: int = 8192,
):
    """Multitaper power spectral density estimate of ``signal``.

    Parameters
    ----------
    signal:
        1-D real array.
    n_tapers:
        Number of DPSS tapers (must satisfy ``n_tapers <= 2*nw - 1``).
    nw:
        Time-bandwidth product (Slepian concentration parameter).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Real PSD estimate of length ``len(signal)``.
    """
    arr = np.asarray(signal, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(f"multitaper expects 1-D signal; got {arr.shape}")
    n = arr.shape[0]
    try:
        from scipy.signal.windows import dpss  # type: ignore[import-untyped]

        tapers = dpss(n, NW=nw, Kmax=n_tapers)
    except (ImportError, ValueError):
        # Fallback: cosine tapers (sinusoidal multitaper approximation;
        # less concentrated but identity-preserving for the dispatch surface)
        tapers = np.zeros((n_tapers, n))
        for k in range(n_tapers):
            tapers[k] = np.sin(np.pi * (k + 1) * (np.arange(n) + 1) / (n + 1))
            tapers[k] /= np.linalg.norm(tapers[k])
    acc = np.zeros(n, dtype=np.float64)
    for k in range(n_tapers):
        tapered = arr * tapers[k]
        _F = np.fft.fft(tapered)
        spectrum = _F.real ** 2 + _F.imag ** 2  # |z|² = real²+imag² (no abs())
        acc += spectrum
    return acc / n_tapers
