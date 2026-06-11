"""Path A FIR filter — closed-form linear convolution with rational coefficients.

Identity per the implementation plan §1: FIR IS a Class N (rational
coefficient table) ∘ Class C (cyclic streaming over the signal-tap product
cascade) composition. Class N is the closed-form home for the impulse
response, and Class C is the cyclic streaming that produces the output.

The closed-form reference uses NumPy linear convolution.

Path B dual in Phase 6 (FIR via Class N rational + bundle convolution).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim
& Schafer (2010, 3rd ed.) §5.2 + Proakis & Manolakis (2007, 4th ed.) §10.
"""

from __future__ import annotations

import numpy as np

from srmech.signal_processing import _dsp_cascades as _dsp

OPERATION_NAME = "fir"
CLASS_COMPOSITION = ("N", "C")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time Signal Processing', "
    "Prentice Hall, §5.2 (FIR filters). Proakis & Manolakis (2007, 4th ed.), "
    "'Digital Signal Processing', Pearson, §10 (FIR filter design + "
    "structures)."
)


def op(signal, coefficients, *, mode: str = "full", D: int = 8192):
    """Linear FIR filter ``y[n] = sum_k b_k * x[n-k]``.

    Parameters
    ----------
    signal:
        1-D real or complex input.
    coefficients:
        FIR filter taps ``[b_0, b_1, ..., b_{M-1}]`` (Class N rational table).
    mode:
        ``"full"`` (default), ``"same"``, or ``"valid"`` per NumPy convolution.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Filtered output.
    """
    sig = np.asarray(signal)
    b = np.asarray(coefficients)
    if sig.ndim != 1 or b.ndim != 1:
        raise ValueError(
            f"fir expects 1-D inputs; got {sig.shape} and {b.shape}"
        )
    # _dsp.convolve is numpy-free (returns a list); wrap to preserve the
    # ndarray return contract (this op still imports numpy as a carrier).
    return np.asarray(_dsp.convolve(sig, b, mode=mode))
