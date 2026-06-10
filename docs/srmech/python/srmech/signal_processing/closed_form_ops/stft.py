"""Path A STFT — closed-form short-time Fourier transform (windowed FFT frames).

Identity: STFT IS a Class C (cyclic streaming over windowed frames) ∘ Class A
(content-addressing on (frame, freq) lattice) ∘ Class I (cyclic-group transform
per frame) ∘ Class K (rotation along the time-frequency plane) composition.

The closed-form reference applies a window function to each hop-overlapped
frame and computes a Class I DFT per frame; the result is the canonical
two-view (cyclic + windowed) STFT per the implementation plan §1 / Spike #178.

Path B dual in Phase 4 / Phase 6 (per-frame FFT with windowed bundle).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Allen (1977)
+ Oppenheim & Schafer (2010, 3rd ed.) §10.3.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from srmech.amsc import rational as _srn
from srmech.amsc.cascade import spectral_cascades as _sc

OPERATION_NAME = "stft"
CLASS_COMPOSITION = ("C", "A", "I", "K")
PERFORMANCE_HINT = "shallow-cascade-frame-wise"
SSOT_CITATION = (
    "Allen (1977), 'Short term spectral analysis, synthesis, and modification "
    "by discrete Fourier transform', IEEE Trans. ASSP 25(3), 235-238. "
    "Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time Signal Processing', "
    "Prentice Hall, §10.3."
)


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade).

    Replaces ``np.cos`` on the Hann-window angle array — routes each angle
    through ``srmech.amsc.rational.cos`` (pi-free range reduction); numpy is
    used only as the array container.
    """
    a = np.asarray(a, dtype=float)
    return np.array(
        [_srn.cos(float(v)) for v in a.ravel()], dtype=float
    ).reshape(a.shape)


def op(
    signal,
    *,
    frame_size: int = 256,
    hop_size: Optional[int] = None,
    window: Optional[np.ndarray] = None,
    D: int = 8192,
):
    """Short-time Fourier transform of ``signal`` via windowed frame FFTs.

    Parameters
    ----------
    signal:
        1-D real or complex array.
    frame_size:
        Number of samples per frame.
    hop_size:
        Samples between successive frame starts. Default ``frame_size // 2``.
    window:
        Optional window of length ``frame_size``. Default Hann window.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Complex ``(n_frames, frame_size)`` STFT matrix.
    """
    sig = np.asarray(signal, dtype=np.complex128)
    if sig.ndim != 1:
        raise ValueError(f"stft expects 1-D signal; got shape {sig.shape}")
    if hop_size is None:
        hop_size = frame_size // 2
    if hop_size <= 0:
        raise ValueError("hop_size must be positive")
    if window is None:
        # Closed-form Hann window: 0.5 (1 - cos(2 pi n / (N - 1)))
        n = np.arange(frame_size)
        window = 0.5 * (1.0 - _ccos(2.0 * np.pi * n / max(frame_size - 1, 1)))
    window = np.asarray(window, dtype=np.float64)
    if window.shape[0] != frame_size:
        raise ValueError(
            f"window length {window.shape[0]} != frame_size {frame_size}"
        )
    n_samples = sig.shape[0]
    if n_samples < frame_size:
        # Zero-pad so we still get one frame
        padded = np.zeros(frame_size, dtype=sig.dtype)
        padded[:n_samples] = sig
        return np.asarray(_sc.fft(padded * window))[np.newaxis, :]
    n_frames = 1 + (n_samples - frame_size) // hop_size
    out = np.zeros((n_frames, frame_size), dtype=np.complex128)
    for i in range(n_frames):
        start = i * hop_size
        frame = sig[start : start + frame_size] * window
        out[i] = np.asarray(_sc.fft(frame))
    return out
