"""Path A allpass — closed-form first-order / second-order allpass IIR filter.

Identity per the implementation plan §1: allpass IS a Class N (paired
numerator/denominator coefficient form: ``a[n]/(1 + a[n] z^{-1})`` for 1st
order, ``(a + b z^{-1} + z^{-2}) / (1 + b z^{-1} + a z^{-2})`` for 2nd order)
filter. The pairing IS the Class N rational identity that gives unity
magnitude response with non-trivial phase.

Path B dual in Phase 6 (Class N pairing in bound-vector substrate).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Regalia,
Mitra & Vaidyanathan (1988) + Vaidyanathan (1993).
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "allpass"
CLASS_COMPOSITION = ("N",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Regalia, Mitra & Vaidyanathan (1988), 'The digital all-pass filter: a "
    "versatile signal processing building block', Proc. IEEE 76(1), 19-37. "
    "DOI 10.1109/5.3286 (Crossref). Vaidyanathan (1993), 'Multirate Systems "
    "and Filter Banks', Prentice Hall."
)


def op(signal, a, *, b=None, order: int = 1, D: int = 8192):
    """First-order or second-order allpass IIR filter.

    Parameters
    ----------
    signal:
        1-D real input.
    a:
        First coefficient (pole/zero pair location).
    b:
        Second coefficient (only used for second-order; None for first-order).
    order:
        1 (first-order) or 2 (second-order). Default 1.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Allpass-filtered output with unity magnitude at all frequencies.
    """
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"allpass expects 1-D signal; got {sig.shape}")

    if order == 1:
        # First-order: H(z) = (a + z^-1) / (1 + a * z^-1)
        b_coef = np.array([a, 1.0], dtype=np.float64)
        a_coef = np.array([1.0, a], dtype=np.float64)
    elif order == 2:
        if b is None:
            raise ValueError("order=2 requires both 'a' and 'b' coefficients")
        # Second-order: H(z) = (a + b z^-1 + z^-2) / (1 + b z^-1 + a z^-2)
        b_coef = np.array([a, b, 1.0], dtype=np.float64)
        a_coef = np.array([1.0, b, a], dtype=np.float64)
    else:
        raise ValueError(f"order must be 1 or 2; got {order}")

    try:
        from scipy.signal import lfilter  # type: ignore[import-untyped]

        return lfilter(b_coef, a_coef, sig)
    except ImportError:
        n = sig.shape[0]
        out = np.zeros(n, dtype=np.float64)
        # Direct-form-I difference equation; loop bound = sig length.
        for i in range(n):
            acc = 0.0
            for j, bj in enumerate(b_coef):
                if i - j >= 0:
                    acc += bj * sig[i - j]
            for k in range(1, len(a_coef)):
                if i - k >= 0:
                    acc -= a_coef[k] * out[i - k]
            out[i] = acc / a_coef[0]
        return out
