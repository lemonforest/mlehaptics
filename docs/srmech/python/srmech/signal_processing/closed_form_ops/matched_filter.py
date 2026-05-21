"""Path A matched filter — closed-form correlation against a template.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ Spike #173 + Spike #176: matched filter IS a Class A (content-addressing
on template canonical form) ∘ Class C (cyclic streaming over the signal)
∘ Class M (HDC bind/similarity for the cross-correlation peak) composition.

The closed-form reference computes the cross-correlation via the FFT
convolution theorem (``X * conj(H)``); the matched filter output peaks at
the time-shift where the template best aligns with the signal.

Path B dual in Phase 4 (B-native A ∘ C ∘ M cross-correlation per Spike
#176 anchor).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: North
(1943) + Turin (1960) + Proakis & Salehi (2008, 5th ed.).
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "matched_filter"
CLASS_COMPOSITION = ("A", "C", "M")
PERFORMANCE_HINT = "shallow-cascade-cross-correlation"
SSOT_CITATION = (
    "North (1943), 'An analysis of the factors which determine signal/noise "
    "discrimination in pulsed-carrier systems', RCA Lab Report PTR-6C "
    "(reprinted Proc. IEEE 51, 1016-1027, 1963). Turin (1960), 'An "
    "introduction to matched filters', IRE Trans. Info. Theory 6(3), "
    "311-329. DOI 10.1109/TIT.1960.1057571 (Crossref). Proakis & Salehi "
    "(2008, 5th ed.), 'Digital Communications', McGraw-Hill."
)


def op(signal, template, *, mode: str = "full", D: int = 8192):
    """Matched-filter output of ``signal`` against ``template``.

    Parameters
    ----------
    signal:
        1-D real or complex array.
    template:
        1-D real or complex template (the matched filter impulse).
    mode:
        Correlation mode passed to ``numpy.correlate``: ``"full"`` (default;
        length = ``n + m - 1``), ``"same"``, or ``"valid"``.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Cross-correlation array; the index of the maximum-magnitude entry
        is the most-likely template alignment.
    """
    sig = np.asarray(signal)
    tmpl = np.asarray(template)
    if sig.ndim != 1 or tmpl.ndim != 1:
        raise ValueError(
            f"matched_filter expects 1-D inputs; got {sig.shape} and {tmpl.shape}"
        )
    # numpy.correlate(a, v) computes sum_n a[n+k] * conj(v[n]) — exactly
    # the matched-filter output. Mode controls boundary handling.
    return np.correlate(sig, tmpl, mode=mode)
