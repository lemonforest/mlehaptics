"""Path A fixed beamforming — closed-form delay-and-sum array processing.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only. Covers civilian acoustic
microphone-array beamforming (e.g., speech enhancement, hearing aids).
No targeting; no military framing.

Identity per the implementation plan §1: fixed beamforming IS a Class L
(microphone-array dense-matrix combiner) ∘ Class N (rational per-element
delay coefficients matching the array geometry) composition.

Path B dual in Phase 6 (Path B mic-array bound vectors).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Van Veen
& Buckley (1988) educational IEEE ASSP Mag. survey + Brandstein & Ward
(2001) *Microphone Arrays: Signal Processing Techniques*.
"""

from __future__ import annotations

import numpy as np

OPERATION_NAME = "beamforming_fixed"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Van Veen & Buckley (1988), 'Beamforming: A versatile approach to "
    "spatial filtering', IEEE ASSP Mag. 5(2), 4-24. DOI 10.1109/53.665 "
    "(Crossref). Brandstein & Ward (2001), 'Microphone Arrays: Signal "
    "Processing Techniques and Applications', Springer."
)


def op(array_signals, *, delays_samples, weights=None, D: int = 8192):
    """Delay-and-sum beamformer on a microphone-array signal matrix.

    Parameters
    ----------
    array_signals:
        ``(n_mics, n_samples)`` real or complex array of per-microphone
        recordings.
    delays_samples:
        Per-microphone integer delay in samples; sequence of length n_mics.
    weights:
        Optional per-mic complex weight vector (length n_mics); default 1/n_mics
        (uniform averaging).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Beamformer output of length ``n_samples`` minus delay padding.
    """
    sig = np.asarray(array_signals, dtype=np.complex128)
    if sig.ndim != 2:
        raise ValueError(f"beamforming expects 2-D array; got {sig.shape}")
    n_mics, n_samples = sig.shape
    d = np.asarray(delays_samples, dtype=np.int64)
    if d.shape[0] != n_mics:
        raise ValueError(
            f"delays_samples length {d.shape[0]} != n_mics {n_mics}"
        )
    if weights is None:
        w = np.full(n_mics, 1.0 / n_mics, dtype=np.complex128)
    else:
        w = np.asarray(weights, dtype=np.complex128)
        if w.shape[0] != n_mics:
            raise ValueError(
                f"weights length {w.shape[0]} != n_mics {n_mics}"
            )
    max_delay = int(np.max(d)) if d.shape[0] > 0 else 0
    out_len = n_samples - max_delay
    if out_len <= 0:
        return np.zeros(0, dtype=np.complex128)
    out = np.zeros(out_len, dtype=np.complex128)
    for m in range(n_mics):
        delay = int(d[m])
        # Take signal[m, delay : delay + out_len] aligned to t=0
        out += w[m] * sig[m, delay : delay + out_len]
    return out
