"""Path A multirate — closed-form up/down/rational sample-rate conversion.

Identity per the implementation plan §1: multirate IS a Class N (rational
rate-conversion ratio ``p/q``) ∘ Class C (cyclic streaming of the resampled
signal) composition. Up-sampling by L inserts L-1 zeros between samples;
down-sampling by M keeps every M-th sample; rational rate L/M composes both.

Path B dual in Phase 6 (Path B up/down/rational rate).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Vaidyanathan
(1993) *Multirate Systems and Filter Banks* §4.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from srmech.amsc import rational as _srn
from srmech.signal_processing import _dsp_cascades as _dsp

OPERATION_NAME = "multirate"
CLASS_COMPOSITION = ("N", "C")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Vaidyanathan (1993), 'Multirate Systems and Filter Banks', Prentice "
    "Hall, §4 (decimation, interpolation, rational rate conversion). "
    "Crochiere & Rabiner (1983), 'Multirate Digital Signal Processing', "
    "Prentice Hall."
)


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade).

    Replaces ``np.cos`` on the Hamming-window angle array — routes each angle
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
    up: int = 1,
    down: int = 1,
    filter_taps: Optional[np.ndarray] = None,
    D: int = 8192,
):
    """Rational sample-rate conversion by ratio ``up/down``.

    Up-samples by inserting ``up - 1`` zeros, low-pass filters with
    ``filter_taps`` (default sinc-truncated), then decimates by ``down``.

    Parameters
    ----------
    signal:
        1-D real array.
    up:
        Up-sampling factor (>= 1).
    down:
        Down-sampling factor (>= 1).
    filter_taps:
        Optional low-pass FIR taps. Default: 41-tap windowed-sinc at
        cutoff ``1 / max(up, down)``.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Resampled signal.
    """
    if up < 1 or down < 1:
        raise ValueError("up and down must be >= 1")
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"multirate expects 1-D signal; got {sig.shape}")
    if up == 1 and down == 1:
        return sig.copy()
    # Up-sample: insert zeros
    if up > 1:
        upsampled = np.zeros(sig.shape[0] * up, dtype=np.float64)
        upsampled[::up] = sig
    else:
        upsampled = sig
    # Low-pass filter (Class N rational coefficients via sinc)
    if filter_taps is None:
        N_taps = 41
        cutoff = 1.0 / max(up, down)
        n = np.arange(N_taps) - (N_taps - 1) / 2
        taps = np.sinc(cutoff * n) * cutoff
        # Hamming window
        w = 0.54 - 0.46 * _ccos(2.0 * np.pi * np.arange(N_taps) / (N_taps - 1))
        filter_taps = taps * w
        filter_taps = filter_taps / np.sum(filter_taps)
    filtered = _dsp.convolve(upsampled, filter_taps, mode="same")
    # Down-sample
    if down > 1:
        return filtered[::down] * up
    return filtered * up
