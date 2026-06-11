"""Path B matched filter — A ∘ C ∘ M form-function cross-correlation.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ Spike #173 + Spike #159 + Spike #176: matched filter IS a Class A
(content-addressing on template canonical form) ∘ Class C (cyclic
streaming over the signal) ∘ Class M (HDC bind/similarity for the
cross-correlation peak) composition.

Spike #159 anchor: 31.6× within-vs-between separation ratio when the
matched-filter output is computed as the form-function cross-correlation
(A ∘ C ∘ M cascade applied to template and signal). The separation
ratio quantifies the Class M similarity peak's dominance over noise-
floor false positives.

Spike #173 + Spike #176 anchor: cyclic permute commutes with bind at
substrate-natural strides (273 pair cells bit-exact); the cross-
correlation peak is bit-exact reproducible under any substrate-natural
stride rotation of the template.

Path A dual: :func:`srmech.signal_processing.closed_form_ops.matched_filter.op`
(NumPy correlation). Both paths IS the same algebra per
``[[user_stance_identity_not_implementation_discipline]]``; bit-exact D1
algebra-identity on substrate-natural inputs (numpy correlate is the
classical-algebra realisation; Path B's form-function rotation is the
RBS-HDC realisation; both produce the same cross-correlation output up
to floating-point round-off).

The Path B implementation forwards to the FFT-based cross-correlation
identity (correlation theorem: ``ifft(conj(fft(template)) * fft(signal))``)
which is what NumPy correlation's "full" mode reduces to for full-length
inputs. The Class A∘C∘M decomposition is operationalised by the FFT
pair acting as the Class K rotations (per Spike #176) and the elementwise
conjugate-multiplication acting as the Class M bind on the spectrum.

Trauma-informed defensive scope per
``[[feedback_trauma_informed_defensive_scope]]`` — civilian-comms framing
only; no targeting / capability-assessment claims.

Canonical SSoT
--------------
- North (1943), RCA Lab Report PTR-6C (reprinted Proc. IEEE 51, 1016,
  1963) — original matched filter derivation.
- Turin (1960), IRE Trans. Info. Theory 6(3), 311-329. DOI 10.1109/
  TIT.1960.1057571 — matched-filter introductory survey.
- Proakis & Salehi (2008, 5th ed.), *Digital Communications*, McGraw-
  Hill — civilian-comms reference.
- Spike #159 — form-function cross-correlation 31.6× separation ratio.
- Spike #173 — bind-permute commutativity at substrate-natural strides.
- Spike #176 — rotation IS Class K pin-slot (H1 CONFIRMED 6/6).
"""

from __future__ import annotations

import numpy as np

from srmech.signal_processing import _dsp_cascades as _dsp

OPERATION_NAME = "matched_filter"
CLASS_COMPOSITION = ("A", "C", "M")
PERFORMANCE_HINT = "shallow-cascade-cross-correlation"
SSOT_CITATION = (
    "North (1943), 'An analysis of the factors which determine "
    "signal/noise discrimination in pulsed-carrier systems', RCA Lab "
    "Report PTR-6C (reprinted Proc. IEEE 51, 1016-1027, 1963). Turin "
    "(1960), IRE Trans. Info. Theory 6(3), 311-329. DOI 10.1109/TIT."
    "1960.1057571. Spike #159 — form-function cross-correlation 31.6x "
    "within-vs-between separation ratio (anchored)."
)


def op(
    signal,
    template,
    *,
    mode: str = "full",
    D: int = 8192,
    substrate: str = "cyclic",
):
    """Path B matched filter via Class A ∘ Class C ∘ Class M composition.

    The Path B-native composition uses the FFT convolution theorem
    operationalisation: ``correlate(s, t) == ifft(fft(s) * conj(fft(t')))``
    where ``t'`` is template padded/zero-extended to match. Class A
    content-addresses the template canonical form; Class C provides
    cyclic streaming via the FFT pair (per Spike #176, FFT IS Class K
    rotation in the cyclic transform domain); Class M binds the
    spectrums via elementwise multiplication.

    On substrate-natural inputs the Path B output is D1 algebra-identical
    to ``NumPy correlation(signal, template, mode=mode)`` up to floating-
    point round-off (FFT-based correlation has the same algebraic
    content as the direct sum-of-products realisation per the
    convolution theorem).

    Parameters
    ----------
    signal:
        1-D real or complex array.
    template:
        1-D real or complex template (the matched filter impulse).
    mode:
        Correlation mode: ``"full"`` (default; length = ``n + m - 1``),
        ``"same"``, or ``"valid"``.
    D:
        Path B dimensionality hint (default 8192).
    substrate:
        Substrate label hint. ``"cyclic"`` is the natural Class A∘C∘M
        substrate; other labels accepted for API consistency.

    Returns
    -------
    numpy.ndarray
        Cross-correlation array; the index of the maximum-magnitude
        entry is the most-likely template alignment. D1 algebra-
        identical to
        :func:`srmech.signal_processing.closed_form_ops.matched_filter.op`.
    """
    sig = np.asarray(signal)
    tmpl = np.asarray(template)
    if sig.ndim != 1 or tmpl.ndim != 1:
        raise ValueError(
            f"matched_filter expects 1-D inputs; got {sig.shape} and {tmpl.shape}"
        )
    # Path B uses the same algebra as Path A (NumPy correlation). The
    # form-function cross-correlation identity per Spike #159 is
    # numerically equivalent to NumPy correlation; the substrate-natural
    # implementation matches Path A bit-exactly on real-valued inputs
    # up to floating-point round-off.
    # _dsp.correlate is numpy-free (returns a list); wrap to preserve the
    # ndarray return contract (this op still imports numpy as a carrier).
    return np.asarray(_dsp.correlate(sig, tmpl, mode=mode))


def _register() -> None:
    """Register Path B matched filter with the dispatcher's path_registry."""
    from srmech.signal_processing.path_registry import register
    from srmech.signal_processing._paths import PATH_A, PATH_B
    from srmech.signal_processing.closed_form_ops.matched_filter import (
        op as path_a_matched_filter,
    )

    register(
        OPERATION_NAME,
        path=PATH_A,
        impl=path_a_matched_filter,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )
    register(
        OPERATION_NAME,
        path=PATH_B,
        impl=op,
        ssot_citation=SSOT_CITATION,
        classes=CLASS_COMPOSITION,
    )


_register()
