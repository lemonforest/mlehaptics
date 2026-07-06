"""Path A cross-spectral — closed-form cross spectral density + coherence.

Identity per the implementation plan §1: cross-spectral density IS a Class M
(HDC bundle averaging across windowed frames) ∘ Class A (FFT cross-product
content addressing) composition. Coherence is the normalised CSD.

Closed-form reference: Welch's method (segment + FFT + cross-product +
average) for CSD; coherence is ``|S_xy|^2 / (S_xx * S_yy)``.

Path B dual in Phase 6 (bundle averaging in bound-vector substrate).

Carrier-free since v0.7.5rc88 (#564): plain Python ``list`` carriers; the Hann
window uses the **Class-N π cascade** (``float(pi_cascade_digits(30))``,
Archimedes hexagon-doubling — the first sigproc carrier-flip to need π) fed to
``rational.cos``; the cross-product ``X·conj(Y)``, the per-bin power
``|z|²=real²+imag²`` (no ``abs()``) and the ``np.maximum(..., eps)`` coherence
floor are explicit elementwise list comprehensions. ``_sc.fft`` returns
``List[complex]``; ``_fc.fftfreq`` returns a plain list numpy-absent.

rc148 (B4a) classification: ``composition_of_c`` — each Welch segment's
``_sc.fft`` dispatches to the c_dispatched numeric FFT foundation
``srmech_fft_c128`` (rc139); the Hann window is the byte-exact Class-N
``rational.cos`` cascade (C-backed) and the cross-product ``X·conj(Y)`` / power
``|z|²=re²+im²`` / bundle average are numpy-free elementwise glue (no ``abs()``).
NUMERIC (within-tol, not byte-identical): native == pure to reldiff ≤ 1e-9.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Welch
(1967) + Carter (1987) for cross-spectral / coherence.
"""

from __future__ import annotations

from typing import Optional, Tuple

from srmech.amsc import rational as _srn
from srmech.amsc.cascade import spectral_cascades as _sc
from srmech.signal_processing import _fft_carrier as _fc

OPERATION_NAME = "cross_spectral"
CLASS_COMPOSITION = ("M", "A")
PERFORMANCE_HINT = "shallow-cascade-frame-wise"
SSOT_CITATION = (
    "Welch (1967), 'The use of fast Fourier transform for the estimation of "
    "power spectra', IEEE Trans. AU-15(2), 70-73. DOI 10.1109/TAU.1967."
    "1161901 (Crossref). Carter (1987), 'Coherence and time delay "
    "estimation', Proc. IEEE 75(2), 236-255. DOI 10.1109/PROC.1987.13723."
)

# Class-N π geometric cascade (Archimedes hexagon-doubling; Spike #32), numpy-free.
_PI = float(_srn.pi_cascade_digits(30))


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade), numpy-free.

    Replaces ``np.cos`` on the window-angle array — routes each angle through
    ``srmech.amsc.rational.cos`` (pi-free range reduction); no ``np.cos`` /
    ``math.cos`` in the call graph. ``rational.cos`` returns an exact ``Q``; the
    window is a real FPU array that multiplies the complex signal segments, so
    collapse to ``float`` here (``Q × complex`` has no interop by design).
    Returns a plain ``list`` of ``float``.
    """
    return [float(_srn.cos(float(v))) for v in a]


def _coherence(s_xy, s_xx, s_yy):
    """``|S_xy|² / max(S_xx·S_yy, eps)`` per bin (no ``abs()``; eps-floor is the
    builtin ``max``)."""
    return [
        (s_xy[k].real * s_xy[k].real + s_xy[k].imag * s_xy[k].imag)
        / max(s_xx[k] * s_yy[k], 1e-30)
        for k in range(len(s_xy))
    ]


def op(
    x,
    y,
    *,
    frame_size: int = 256,
    hop_size: Optional[int] = None,
    coherence: bool = False,
    D: int = 8192,
) -> Tuple[list, list]:
    """Cross spectral density (CSD) of ``x`` and ``y`` via Welch's method.

    Parameters
    ----------
    x, y:
        Two real 1-D sequences of the same length.
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
        ``(freqs, S_xy_or_coherence)`` as two ``list``s of length
        ``frame_size``.
    """
    xs = [float(v) for v in x]
    ys = [float(v) for v in y]
    if len(xs) != len(ys):
        raise ValueError(
            f"cross_spectral expects matching shapes; got {len(xs)} vs {len(ys)}"
        )
    if hop_size is None:
        hop_size = frame_size // 2
    n = len(xs)
    if n < frame_size:
        # Single zero-padded segment.
        xx = [0.0] * frame_size
        yy = [0.0] * frame_size
        for k in range(n):
            xx[k] = xs[k]
            yy[k] = ys[k]
        X = list(_sc.fft(xx))
        Y = list(_sc.fft(yy))
        s_xy = [X[k] * Y[k].conjugate() for k in range(frame_size)]
        if coherence:
            s_xx = [v.real * v.real + v.imag * v.imag for v in X]
            s_yy = [v.real * v.real + v.imag * v.imag for v in Y]
            s_out = _coherence(s_xy, s_xx, s_yy)
        else:
            s_out = s_xy
        return _fc.fftfreq(frame_size), s_out

    n_frames = 1 + (n - frame_size) // hop_size
    s_xy_acc = [complex(0)] * frame_size
    s_xx_acc = [0.0] * frame_size
    s_yy_acc = [0.0] * frame_size
    # Hann window per segment: 0.5·(1 − cos(2π·nn/(N−1))) via the Class-N cascade.
    denom = max(frame_size - 1, 1)
    window = [
        0.5 * (1.0 - c)
        for c in _ccos([2.0 * _PI * nn / denom for nn in range(frame_size)])
    ]
    for i in range(n_frames):
        start = i * hop_size
        xf = [xs[start + k] * window[k] for k in range(frame_size)]
        yf = [ys[start + k] * window[k] for k in range(frame_size)]
        X = list(_sc.fft(xf))
        Y = list(_sc.fft(yf))
        for k in range(frame_size):
            s_xy_acc[k] += X[k] * Y[k].conjugate()
            s_xx_acc[k] += X[k].real * X[k].real + X[k].imag * X[k].imag
            s_yy_acc[k] += Y[k].real * Y[k].real + Y[k].imag * Y[k].imag
    s_xy = [v / n_frames for v in s_xy_acc]
    if coherence:
        s_xx = [v / n_frames for v in s_xx_acc]
        s_yy = [v / n_frames for v in s_yy_acc]
        out = _coherence(s_xy, s_xx, s_yy)
    else:
        out = s_xy
    return _fc.fftfreq(frame_size), out
