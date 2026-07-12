"""Path A allpass — closed-form first-order / second-order allpass IIR filter.

Identity per the implementation plan §1: allpass IS a Class N (paired
numerator/denominator coefficient form: ``a[n]/(1 + a[n] z^{-1})`` for 1st
order, ``(a + b z^{-1} + z^{-2}) / (1 + b z^{-1} + a z^{-2})`` for 2nd order)
filter. The pairing IS the Class N rational identity that gives unity
magnitude response with non-trivial phase.

Path B dual in Phase 6 (Class N pairing in bound-vector substrate).

rc149 (B4b) classification: ``c_dispatched``.  An allpass section is an IIR
filter with mirrored numerator / denominator coefficients, so ``op`` builds the
``(b_coef, a_coef)`` pair then dispatches the recursive difference equation to
the c_dispatched ``srmech_iir_lfilter_f64`` (via ``_native.iir_lfilter_f64_c``)
when the native lib is present, falling back to the complete numpy-free pure
direct-form-I reference (``_lfilter_df1``) otherwise.  NUMERIC (within-tol, not
byte-identical): reldiff ≤ 1e-9.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Regalia,
Mitra & Vaidyanathan (1988) + Vaidyanathan (1993).
"""

from __future__ import annotations

OPERATION_NAME = "allpass"
CLASS_COMPOSITION = ("N",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Regalia, Mitra & Vaidyanathan (1988), 'The digital all-pass filter: a "
    "versatile signal processing building block', Proc. IEEE 76(1), 19-37. "
    "DOI 10.1109/5.3286 (Crossref). Vaidyanathan (1993), 'Multirate Systems "
    "and Filter Banks', Prentice Hall."
)


def _lfilter_df1(b_coef, a_coef, sig):
    """Pure numpy-free direct-form-I difference equation — the COMPLETE fallback
    (and the within-tol parity oracle) for the C ``srmech_iir_lfilter_f64``.

    ``y[i] = ( Σ_j b_coef[j]·sig[i-j] − Σ_{k>=1} a_coef[k]·out[i-k] ) / a_coef[0]``
    (Class N rational filter; the loop bound is the signal length). No numpy.
    """
    n = len(sig)
    out = [0.0] * n
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
    list[float]
        Allpass-filtered output (the framework-native numpy-free carrier;
        #564 carrier-flip) with unity magnitude at all frequencies.
    """
    # Carrier: a plain Python list of floats (numpy-free; float(x) over a
    # nested sequence raises, so a 1-D contract is still enforced).
    sig = [float(x) for x in signal]

    if order == 1:
        # First-order: H(z) = (a + z^-1) / (1 + a * z^-1)
        b_coef = [a, 1.0]
        a_coef = [1.0, a]
    elif order == 2:
        if b is None:
            raise ValueError("order=2 requires both 'a' and 'b' coefficients")
        # Second-order: H(z) = (a + b z^-1 + z^-2) / (1 + b z^-1 + a z^-2)
        b_coef = [a, b, 1.0]
        a_coef = [1.0, b, a]
    else:
        raise ValueError(f"order must be 1 or 2; got {order}")

    # c_dispatched (rc149 / B4b): the recursive difference equation dispatches to
    # srmech_iir_lfilter_f64; the pure direct-form-I reference is the complete
    # numpy-free fallback.
    from srmech.amsc import _native

    native = _native.iir_lfilter_f64_c(b_coef, a_coef, sig)
    if native is not None:
        return native
    return _lfilter_df1(b_coef, a_coef, sig)
