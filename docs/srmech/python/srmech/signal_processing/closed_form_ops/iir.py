"""Path A IIR filter — closed-form recursive filter with biquad cascade option.

Identity per the implementation plan §1: IIR IS a Class N (rational
``b(z)/a(z)`` coefficient pair) ∘ Class C (cyclic-cascade composition of
biquad sections) composition. Each biquad section is itself a Class N rational
of order 2.

rc149 (B4b) classification: ``c_dispatched``.  The recursive difference
equation ``y[n] = Σ b·x[n-k] − Σ a·y[n-k]`` reads the output the loop is still
producing, so it is inherently SEQUENTIAL and does NOT decompose into a
matmul / FFT — it is the ONE genuinely-new numeric kernel the filter family
needs.  ``op`` dispatches to the c_dispatched ``srmech_iir_lfilter_f64`` (via
``_native.iir_lfilter_f64_c``) when the native lib is present, and falls back to
the complete numpy-free pure-Python direct-form-II-transposed reference
(``_lfilter_direct``) otherwise (a biquad cascade dispatches per second-order
section).  NUMERIC (within-tol, not byte-identical): the accumulation may
FMA-fuse ~1 ULP on some platforms, so the parity contract is differential
(reldiff ≤ 1e-9), NOT byte-equality.

Path B dual in Phase 6 (IIR via Class N rational + Class C cascade in bound-
vector substrate).

Carrier note (#564): numpy-free. The C dispatch + the pure direct-form-II-
transposed reference both run on plain ``list``\\s (the Class-C recursive
cascade of the Class-N ``b/a`` rational); the op returns a ``list``. No scipy /
numpy is imported.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim
& Schafer (2010, 3rd ed.) §6 + Proakis & Manolakis (2007, 4th ed.) §10.
RBJ EQ Cookbook for biquad-design forms.
"""

from __future__ import annotations

from typing import Optional, Sequence

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


def _lfilter_direct(b: Sequence[float], a: Sequence[float], x: Sequence[float]):
    """Direct-form-II transposed IIR filter (closed-form reference), numpy-free.

    The Class-C recursive cascade of the Class-N ``b/a`` rational over a plain
    ``list`` carrier; ``y[i]`` and the state ``z`` are accumulated by explicit
    multiply-adds (no numpy).
    """
    a0 = a[0]
    b = [bi / a0 for bi in b]
    a = [ai / a0 for ai in a]
    n = len(x)
    # DF2T needs b and a to share the filter length: pad the shorter with zeros
    # (a shorter b would otherwise drop the trailing feedback taps, since the
    # a[j]·y[i] correction lives inside the b-indexed state loop). This matches
    # scipy.lfilter's b/a padding to max(len(a), len(b)).
    nfilt = max(len(a), len(b))
    b = b + [0.0] * (nfilt - len(b))
    a = a + [0.0] * (nfilt - len(a))
    y = [0.0] * n
    nz = nfilt - 1
    z = [0.0] * nz
    for i in range(n):
        y[i] = b[0] * x[i] + (z[0] if nz > 0 else 0.0)
        for j in range(1, nfilt):
            if j - 1 < nz:
                z[j - 1] = (
                    b[j] * x[i]
                    - a[j] * y[i]
                    + (z[j] if j < nz else 0.0)
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
    list
        Filtered output; numpy-free (#564).
    """
    try:
        sig = [float(x) for x in signal]
    except TypeError as exc:  # nested sequence -> not 1-D
        raise ValueError("iir expects a 1-D real signal") from exc

    from srmech.amsc import _native

    if biquad_sections is not None:
        # Cascade of second-order sections (sosfilt): apply each in turn, each
        # dispatched to the c_dispatched srmech_iir_lfilter_f64 (else pure).
        out = list(sig)
        for section in biquad_sections:
            if len(section) != 6:
                raise ValueError(
                    f"biquad section requires 6 coefficients; got "
                    f"{len(section)}"
                )
            b_s = list(section[:3])
            a_s = list(section[3:])
            native = _native.iir_lfilter_f64_c(b_s, a_s, out)
            out = native if native is not None else _lfilter_direct(b_s, a_s, out)
        return out

    # Direct (b, a) form: prefer the c_dispatched srmech_iir_lfilter_f64; the
    # pure direct-form-II-transposed reference is the complete fallback.
    native = _native.iir_lfilter_f64_c(b, a, sig)
    if native is not None:
        return native
    return _lfilter_direct(list(b), list(a), sig)
