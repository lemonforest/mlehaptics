"""Path A IIR filter — closed-form recursive filter with biquad cascade option.

Identity per the implementation plan §1: IIR IS a Class N (rational
``b(z)/a(z)`` coefficient pair) ∘ Class C (cyclic-cascade composition of
biquad sections) composition. Each biquad section is itself a Class N rational
of order 2.

The closed-form reference uses scipy.signal.lfilter when available, else a
hand-rolled direct-form-II implementation. Biquad cascade is supported via the
``biquad_sections`` argument.

Path B dual in Phase 6 (IIR via Class N rational + Class C cascade in bound-
vector substrate).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim
& Schafer (2010, 3rd ed.) §6 + Proakis & Manolakis (2007, 4th ed.) §10.
RBJ EQ Cookbook for biquad-design forms.
"""

from __future__ import annotations

from typing import Iterable, Optional, Sequence

import numpy as np

OPERATION_NAME = "iir"
CLASS_COMPOSITION = ("N", "C")
PERFORMANCE_HINT = "shallow-cascade-biquad-amortise"
SSOT_CITATION = (
    "Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time Signal Processing', "
    "Prentice Hall, §6 (IIR filters). Proakis & Manolakis (2007, 4th ed.), "
    "'Digital Signal Processing', Pearson, §10. Bristow-Johnson, 'Cookbook "
    "formulae for audio EQ biquad filter coefficients' (RBJ EQ Cookbook, "
    "2005), https://www.w3.org/TR/audio-eq-cookbook/."
)


def _lfilter_direct(b: np.ndarray, a: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Direct-form-II transposed IIR filter (closed-form reference)."""
    b = b / a[0]
    a = a / a[0]
    n = x.shape[0]
    y = np.zeros(n, dtype=np.float64)
    z = np.zeros(max(len(a), len(b)) - 1, dtype=np.float64)
    for i in range(n):
        y[i] = b[0] * x[i] + (z[0] if z.shape[0] > 0 else 0.0)
        for j in range(1, len(b)):
            if j - 1 < z.shape[0]:
                z[j - 1] = (
                    b[j] * x[i]
                    - (a[j] * y[i] if j < len(a) else 0.0)
                    + (z[j] if j < z.shape[0] else 0.0)
                )
    return y


def op(
    signal,
    b,
    a,
    *,
    biquad_sections: Optional[Sequence[Sequence[float]]] = None,
    D: int = 8192,
):
    """Recursive IIR filter applied to ``signal``.

    Parameters
    ----------
    signal:
        1-D real input.
    b:
        Numerator (feed-forward) coefficient sequence.
    a:
        Denominator (feed-back) coefficient sequence; ``a[0]`` typically 1.
    biquad_sections:
        Optional list of 6-tuples ``[b0, b1, b2, a0, a1, a2]`` for cascade
        application. When provided, ``b`` / ``a`` are ignored.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Filtered output.
    """
    sig = np.asarray(signal, dtype=np.float64)
    if sig.ndim != 1:
        raise ValueError(f"iir expects 1-D signal; got {sig.shape}")

    try:
        from scipy.signal import lfilter, sosfilt  # type: ignore[import-untyped]

        if biquad_sections is not None:
            sos = np.asarray(biquad_sections, dtype=np.float64)
            return sosfilt(sos, sig)
        return lfilter(
            np.asarray(b, dtype=np.float64),
            np.asarray(a, dtype=np.float64),
            sig,
        )
    except ImportError:
        if biquad_sections is not None:
            out = sig.copy()
            for section in biquad_sections:
                section_arr = np.asarray(section, dtype=np.float64)
                if section_arr.shape[0] != 6:
                    raise ValueError(
                        f"biquad section requires 6 coefficients; got "
                        f"{section_arr.shape}"
                    )
                b_s = section_arr[:3]
                a_s = section_arr[3:]
                out = _lfilter_direct(b_s, a_s, out)
            return out
        return _lfilter_direct(
            np.asarray(b, dtype=np.float64),
            np.asarray(a, dtype=np.float64),
            sig,
        )
