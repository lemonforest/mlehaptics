"""Path A spectrogram — closed-form ``|STFT|^2`` (squared magnitude).

Identity per the implementation plan §1: spectrogram IS STFT (Class C ∘ A ∘ I
∘ K composition) followed by elementwise modulus-squared. No new primitive
class; just a magnitude post-step on the STFT op.

Path B dual in Phase 6 (Path B STFT followed by elementwise mag-squared on
the bound-vector substrate).

rc148 (B4a) classification: ``composition_of_c`` — composes the (now
composition_of_c) :func:`stft.op` (which dispatches each frame's FFT to the
c_dispatched ``srmech_fft_c128``) followed by a numpy-free ``|z|²=re²+im²``
elementwise glue (no ``abs()``). NUMERIC (within-tol, not byte-identical):
native == pure to reldiff ≤ 1e-9.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Oppenheim &
Schafer (2010, 3rd ed.) §10.4 (spectrogram as time-frequency energy density).
"""

from __future__ import annotations

from typing import Optional, Sequence

from .stft import op as stft_op

OPERATION_NAME = "spectrogram"
CLASS_COMPOSITION = ("C", "A", "I", "K")
PERFORMANCE_HINT = "shallow-cascade-frame-wise"
SSOT_CITATION = (
    "Oppenheim & Schafer (2010, 3rd ed.), 'Discrete-Time Signal Processing', "
    "Prentice Hall, §10.4. Spectrogram = |STFT|^2; classical time-frequency "
    "energy density."
)


def op(
    signal,
    *,
    frame_size: int = 256,
    hop_size: Optional[int] = None,
    window: Optional[Sequence[float]] = None,
    D: int = 8192,
):
    """Spectrogram of ``signal``: ``|STFT(signal)|^2``.

    Parameters
    ----------
    signal:
        1-D real or complex array.
    frame_size, hop_size, window:
        Forwarded to :func:`stft.op`.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list
        Real energy density as a ``list`` of ``n_frames`` per-frame ``list``s
        (carrier-free since v0.7.5rc89, #564 — ``stft.op`` now returns lists).

    **Accuracy (rc466, `#T1188`).** The energy density is ``|X|²`` of the
    STFT's single **terminal float lift** — a float64 quantity **accurate to
    round-off** (~1 ULP) per bin, never exact. For an integer signal under an
    integer window the underlying STFT bins are exact-until-rotation (see
    :func:`stft.op`), but the squared magnitude is taken AFTER the lift, so a
    bin whose exact value is not float-representable is rounded before it is
    squared: ``op([2**53+1, 0, 0, 0], frame_size=4, window=[1]*4)`` and the
    same call at ``2**53`` return the same density. The exact object — the
    ring norm ``X_k·conj(X_k)`` of an exact ``ℤ[ζ_N]`` bin, an element of the
    real subring ``ℤ[ζ_N]⁺`` — IS representable (:func:`srmech.cascade.exact_dft`
    returns the bin), but no shipped op computes that norm and no STFT returns
    exact frames; that is the drain path, recorded in the CHANGELOG. This is a
    declaration of the shipped surface, not a float-by-nature claim.
    """
    stft_matrix = stft_op(
        signal,
        frame_size=frame_size,
        hop_size=hop_size,
        window=window,
        D=D,
    )
    # |z|² = real²+imag² (no abs()), elementwise over the list-of-lists STFT.
    return [
        [v.real * v.real + v.imag * v.imag for v in row]
        for row in stft_matrix
    ]
