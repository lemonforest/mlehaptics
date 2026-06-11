"""Path A STFT — closed-form short-time Fourier transform (windowed FFT frames).

Identity: STFT IS a Class C (cyclic streaming over windowed frames) ∘ Class A
(content-addressing on (frame, freq) lattice) ∘ Class I (cyclic-group transform
per frame) ∘ Class K (rotation along the time-frequency plane) composition.

The closed-form reference applies a window function to each hop-overlapped
frame and computes a Class I DFT per frame; the result is the canonical
two-view (cyclic + windowed) STFT per the implementation plan §1 / Spike #178.

Path B dual in Phase 4 / Phase 6 (per-frame FFT with windowed bundle).

Carrier-free since v0.7.5rc89 (#564): plain Python ``list`` carriers (the STFT
matrix is a ``list`` of per-frame ``list``s). The default Hann window uses the
**Class-N π cascade** (``float(pi_cascade_digits(30))``, Archimedes
hexagon-doubling — same π source the rc88 cross_spectral flip validated
bit-faithful) fed to ``rational.cos`` via ``_ccos``. ``_sc.fft`` already returns
``List[complex]`` numpy-absent; per-frame ``signal·window`` is an explicit list
comprehension.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Allen (1977)
+ Oppenheim & Schafer (2010, 3rd ed.) §10.3.
"""

from __future__ import annotations

from typing import List, Optional

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

# Class-N π geometric cascade (Archimedes hexagon-doubling; Spike #32), numpy-free.
_PI = float(_srn.pi_cascade_digits(30))


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade), numpy-free.

    Replaces ``np.cos`` on the Hann-window angle array — routes each angle
    through ``srmech.amsc.rational.cos`` (pi-free range reduction); no ``np.cos``
    / ``math.cos`` in the call graph. Returns a plain ``list`` of ``float``.
    """
    return [_srn.cos(float(v)) for v in a]


def op(
    signal,
    *,
    frame_size: int = 256,
    hop_size: Optional[int] = None,
    window=None,
    D: int = 8192,
) -> List[list]:
    """Short-time Fourier transform of ``signal`` via windowed frame FFTs.

    Parameters
    ----------
    signal:
        1-D real or complex sequence.
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
    list
        Complex STFT matrix as a ``list`` of ``n_frames`` per-frame ``list``s,
        each of length ``frame_size``.
    """
    seq = list(signal)
    if seq and hasattr(seq[0], "__len__") and not isinstance(seq[0], (str, bytes)):
        raise ValueError("stft expects 1-D signal")
    sig = [complex(v) for v in seq]
    if hop_size is None:
        hop_size = frame_size // 2
    if hop_size <= 0:
        raise ValueError("hop_size must be positive")
    if window is None:
        # Closed-form Hann window: 0.5 (1 - cos(2 pi n / (N - 1))) via Class-N cascade.
        denom = max(frame_size - 1, 1)
        window = [
            0.5 * (1.0 - c)
            for c in _ccos([2.0 * _PI * nn / denom for nn in range(frame_size)])
        ]
    else:
        window = [float(v) for v in window]
    if len(window) != frame_size:
        raise ValueError(
            f"window length {len(window)} != frame_size {frame_size}"
        )
    n_samples = len(sig)
    if n_samples < frame_size:
        # Zero-pad so we still get one frame.
        padded = [complex(0)] * frame_size
        for k in range(n_samples):
            padded[k] = sig[k]
        framed = [padded[k] * window[k] for k in range(frame_size)]
        return [list(_sc.fft(framed))]
    n_frames = 1 + (n_samples - frame_size) // hop_size
    out = []
    for i in range(n_frames):
        start = i * hop_size
        framed = [sig[start + k] * window[k] for k in range(frame_size)]
        out.append(list(_sc.fft(framed)))
    return out
