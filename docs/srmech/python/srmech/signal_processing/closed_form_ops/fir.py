"""Path A FIR filter — closed-form linear convolution with rational coefficients.

Identity per the implementation plan §1: FIR IS a Class N (rational
coefficient table) ∘ Class C (cyclic streaming over the signal-tap product
cascade) composition. Class N is the closed-form home for the impulse
response, and Class C is the cyclic streaming that produces the output.

The closed-form reference uses NumPy linear convolution.

Path B dual in Phase 6 (FIR via Class N rational + bundle convolution).

rc149 (B4b) classification: ``composition_of_c``.  The FIR filter is a
(feed-forward-only) linear convolution, so it re-expresses the convolution as a
**Toeplitz matvec** ``M·b`` routed through ``_dsp.convolve_matmul`` →
``laplacian.mat_matvec`` ∘ ``mat_matmul`` → the c_dispatched
``srmech_dense_matmul_complex`` when the native lib is present, and falls back
to the complete numpy-free pure ``_dsp.convolve`` cascade otherwise.  NUMERIC
(within-tol, not byte-identical): the matmul float accumulation may FMA-fuse
~1 ULP on some platforms, so the parity contract is differential (reldiff
≤ 1e-9), NOT byte-equality.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim
& Schafer (2010, 3rd ed.) §5.2 + Proakis & Manolakis (2007, 4th ed.) §10.
"""

from __future__ import annotations

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
    list
        Filtered output (length per ``mode``); numpy-free (#564).
    """
    # composition_of_c (rc149 / B4b): when the native dense-matmul is present the
    # convolution is a Toeplitz matvec through the c_dispatched
    # srmech_dense_matmul_complex; otherwise the complete numpy-free pure
    # cascade. Both coerce to 1-D lists (ValueError on nested/2-D / empty input)
    # and return a list; the matmul path is within-tol (not byte-identical).
    from srmech.amsc import _native

    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_dense_matmul_complex")
    ):
        return _dsp.convolve_matmul(signal, coefficients, mode=mode)
    return _dsp.convolve(signal, coefficients, mode=mode)
