"""Path A spectrogram — closed-form ``|STFT|^2`` (squared magnitude).

Identity per the implementation plan §1: spectrogram IS STFT (Class C ∘ A ∘ I
∘ K composition) followed by elementwise modulus-squared. No new primitive
class; just a magnitude post-step on the STFT op.

Path B dual in Phase 6 (Path B STFT followed by elementwise mag-squared on
the bound-vector substrate).

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
