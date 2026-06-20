"""Path A multirate — closed-form up/down/rational sample-rate conversion.

Identity per the implementation plan §1: multirate IS a Class N (rational
rate-conversion ratio ``p/q``) ∘ Class C (cyclic streaming of the resampled
signal) composition. Up-sampling by L inserts L-1 zeros between samples;
down-sampling by M keeps every M-th sample; rational rate L/M composes both.

Path B dual in Phase 6 (Path B up/down/rational rate).

numpy-free (carrier-removal #564, rc92): the windowed-sinc low-pass taps are
built with a substrate-native ``_sinc`` (sin(πx)/(πx), Class-N rational cascade
over the **Class-N π cascade** ``_PI``, Spike #32) and a numpy-free ``_ccos``
Hamming window; ``_dsp.convolve`` already returns a plain ``list``. numpy is no
longer imported — the carrier is a Python ``list`` throughout. The x=0 sinc
singularity is a Class-K removable branch (returns 1.0, no division), never an
``abs()``.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Vaidyanathan
(1993) *Multirate Systems and Filter Banks* §4.
"""

from __future__ import annotations

from typing import List, Optional

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

# Class-N π cascade (Archimedes hexagon-doubling, Spike #32) — the substrate-
# native π source for the windowed-sinc trig; NOT math.pi / np.pi.
_PI = float(_srn.pi_cascade_digits(30))


def _ccos(a):
    """Elementwise substrate-native cosine (Class-N rational cascade), numpy-free.

    Takes an iterable of angles, returns a plain ``list`` of ``float``
    (``rational.cos`` returns an exact ``Q``; the Hamming-window array is a real
    FPU coefficient bank that multiplies signal taps, so collapse to ``float``
    here — ``Q × complex`` has no interop by design). Replaces ``np.cos`` on the
    Hamming-window angle array; the rc33 trig-routing test references this
    helper directly.
    """
    return [float(_srn.cos(float(v))) for v in a]


def _sinc(x: float) -> float:
    """Normalised sinc ``sin(πx)/(πx)`` matching ``np.sinc``, numpy-free.

    Routes through ``rational.sin`` over the Class-N ``_PI`` source. The
    removable singularity at ``x == 0`` is a Class-K branch (returns ``1.0``,
    no division), so there is no ``abs()`` and no divide-by-zero.
    """
    if x == 0.0:
        return 1.0
    px = _PI * x
    return float(_srn.sin(px)) / px       # exact Q → float (FPU filter tap)


def op(
    signal,
    *,
    up: int = 1,
    down: int = 1,
    filter_taps: Optional[List[float]] = None,
    D: int = 8192,
) -> List[float]:
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
    list of float
        Resampled signal.
    """
    if up < 1 or down < 1:
        raise ValueError("up and down must be >= 1")
    seq = list(signal)
    if seq and hasattr(seq[0], "__len__") and not isinstance(seq[0], (str, bytes)):
        raise ValueError("multirate expects 1-D signal")
    sig = [float(v) for v in seq]
    n0 = len(sig)
    if up == 1 and down == 1:
        return list(sig)
    # Up-sample: insert ``up - 1`` zeros between samples (Class C streaming).
    if up > 1:
        upsampled = [0.0] * (n0 * up)
        for i in range(n0):
            upsampled[i * up] = sig[i]
    else:
        upsampled = list(sig)
    # Low-pass filter (Class N rational coefficients via windowed sinc).
    if filter_taps is None:
        n_taps = 41
        cutoff = 1.0 / max(up, down)
        centre = (n_taps - 1) / 2
        taps = [_sinc(cutoff * (k - centre)) * cutoff for k in range(n_taps)]
        # Hamming window (numpy-free _ccos).
        w = [
            0.54 - 0.46 * c
            for c in _ccos([2.0 * _PI * k / (n_taps - 1) for k in range(n_taps)])
        ]
        windowed = [taps[k] * w[k] for k in range(n_taps)]
        total = sum(windowed)
        filter_taps = [v / total for v in windowed]
    else:
        filter_taps = [float(v) for v in filter_taps]
    # _dsp.convolve is numpy-free (returns a list).
    filtered = _dsp.convolve(upsampled, filter_taps, mode="same")
    # Down-sample (Class N decimation), then apply the up-sampling gain.
    if down > 1:
        return [v * up for v in filtered[::down]]
    return [v * up for v in filtered]
