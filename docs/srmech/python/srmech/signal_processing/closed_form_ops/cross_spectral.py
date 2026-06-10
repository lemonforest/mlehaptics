"""Path A cross-spectral — closed-form cross spectral density + coherence.

Identity per the implementation plan §1: cross-spectral density IS a Class M
(HDC bundle averaging across windowed frames) ∘ Class A (FFT cross-product
content addressing) composition. Coherence is the normalised CSD.

Closed-form reference: Welch's method (segment + FFT + cross-product +
average) for CSD; coherence is ``|S_xy|^2 / (S_xx * S_yy)``.

Path B dual in Phase 6 (bundle averaging in bound-vector substrate).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Welch
(1967) + Carter (1987) for cross-spectral / coherence.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from srmech.amsc import rational as _srn
from srmech.amsc.cascade import spectral_cascades as _sc

OPERATION_NAME = "cross_spectral"
CLASS_COMPOSITION = ("M", "A")
PERFORMANCE_HINT = "shallow-cascade-frame-wise"
SSOT_CITATION = (
    "Welch (1967), 'The use of fast Fourier transform for the estimation of "
    "power spectra', IEEE Trans. AU-15(2), 70-73. DOI 10.1109/TAU.1967."
    "1161901 (Crossref). Carter (1987), 'Coherence and time delay "
    "estimation', Proc. IEEE 75(2), 236-255. DOI 10.1109/PROC.1987.13723."
)


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade).

    Replaces ``np.cos`` on window/basis angle arrays — routes each angle
    through ``srmech.amsc.rational.cos`` (pi-free range reduction), no
    ``np.cos`` / ``math.cos`` in the call graph. numpy is used only as the
    array container.
    """
    a = np.asarray(a, dtype=float)
    return np.array(
        [_srn.cos(float(v)) for v in a.ravel()], dtype=float
    ).reshape(a.shape)


def op(
    x,
    y,
    *,
    frame_size: int = 256,
    hop_size: Optional[int] = None,
    coherence: bool = False,
    D: int = 8192,
) -> Tuple[np.ndarray, np.ndarray]:
    """Cross spectral density (CSD) of ``x`` and ``y`` via Welch's method.

    Parameters
    ----------
    x, y:
        Two real 1-D arrays of the same length.
    frame_size:
        FFT length per segment.
    hop_size:
        Samples between segment starts; default ``frame_size // 2``.
    coherence:
        If True, return coherence ``|S_xy|^2 / (S_xx * S_yy)`` instead of
        raw CSD.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        ``(freqs, S_xy_or_coherence)``.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.shape != y.shape:
        raise ValueError(
            f"cross_spectral expects matching shapes; got {x.shape} vs {y.shape}"
        )
    if x.ndim != 1:
        raise ValueError(f"cross_spectral expects 1-D inputs; got {x.shape}")
    if hop_size is None:
        hop_size = frame_size // 2
    n = x.shape[0]
    if n < frame_size:
        # Single zero-padded segment.
        xx = np.zeros(frame_size, dtype=np.float64)
        yy = np.zeros(frame_size, dtype=np.float64)
        xx[:n] = x
        yy[:n] = y
        X = np.asarray(_sc.fft(xx))
        Y = np.asarray(_sc.fft(yy))
        S_xy = X * np.conj(Y)
        if coherence:
            S_xx = X.real ** 2 + X.imag ** 2  # |z|² = real²+imag² (no abs())
            S_yy = Y.real ** 2 + Y.imag ** 2  # |z|² = real²+imag² (no abs())
            # |z|² = real²+imag² (no abs())
            S_out = (S_xy.real ** 2 + S_xy.imag ** 2) / np.maximum(S_xx * S_yy, 1e-30)
        else:
            S_out = S_xy
        freqs = np.fft.fftfreq(frame_size)
        return freqs, S_out

    n_frames = 1 + (n - frame_size) // hop_size
    S_xy_acc = np.zeros(frame_size, dtype=np.complex128)
    S_xx_acc = np.zeros(frame_size, dtype=np.float64)
    S_yy_acc = np.zeros(frame_size, dtype=np.float64)
    # Hann window per segment.
    nn = np.arange(frame_size)
    window = 0.5 * (1.0 - _ccos(2.0 * np.pi * nn / max(frame_size - 1, 1)))
    for i in range(n_frames):
        start = i * hop_size
        xf = x[start : start + frame_size] * window
        yf = y[start : start + frame_size] * window
        X = np.asarray(_sc.fft(xf))
        Y = np.asarray(_sc.fft(yf))
        S_xy_acc += X * np.conj(Y)
        S_xx_acc += X.real ** 2 + X.imag ** 2  # |z|² = real²+imag² (no abs())
        S_yy_acc += Y.real ** 2 + Y.imag ** 2  # |z|² = real²+imag² (no abs())
    S_xy = S_xy_acc / n_frames
    if coherence:
        S_xx = S_xx_acc / n_frames
        S_yy = S_yy_acc / n_frames
        # |z|² = real²+imag² (no abs())
        out = (S_xy.real ** 2 + S_xy.imag ** 2) / np.maximum(S_xx * S_yy, 1e-30)
    else:
        out = S_xy
    freqs = np.fft.fftfreq(frame_size)
    return freqs, out
