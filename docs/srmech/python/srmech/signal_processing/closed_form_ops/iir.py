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

Carrier note (#564): numpy-free. The optional scipy accelerator is a lazy
import (scipy needs numpy, so a numpy-absent install falls through to the
pure-Python direct-form-II difference-equation reference, which runs on plain
``list``\\s — the Class-C recursive cascade of the Class-N ``b/a`` rational).
The op returns a ``list``.

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
    y = [0.0] * n
    nz = max(len(a), len(b)) - 1
    z = [0.0] * nz
    for i in range(n):
        y[i] = b[0] * x[i] + (z[0] if nz > 0 else 0.0)
        for j in range(1, len(b)):
            if j - 1 < nz:
                z[j - 1] = (
                    b[j] * x[i]
                    - (a[j] * y[i] if j < len(a) else 0.0)
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

    try:
        from scipy.signal import lfilter, sosfilt  # type: ignore[import-untyped]

        # scipy coerces the list inputs internally; wrap the ndarray result in a
        # list so the return type matches the numpy-free fallback path.
        if biquad_sections is not None:
            return list(sosfilt(biquad_sections, sig))
        return list(lfilter(b, a, sig))
    except ImportError:
        if biquad_sections is not None:
            out = list(sig)
            for section in biquad_sections:
                if len(section) != 6:
                    raise ValueError(
                        f"biquad section requires 6 coefficients; got "
                        f"{len(section)}"
                    )
                b_s = list(section[:3])
                a_s = list(section[3:])
                out = _lfilter_direct(b_s, a_s, out)
            return out
        return _lfilter_direct(list(b), list(a), sig)
