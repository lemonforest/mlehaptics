"""Path A fixed beamforming — closed-form delay-and-sum array processing.

Trauma-informed defensive scope per ``[[feedback_trauma_informed_defensive_scope]]``:
educational signal-processing reference only. Covers civilian acoustic
microphone-array beamforming (e.g., speech enhancement, hearing aids).
No targeting; no military framing.

Identity per the implementation plan §1: fixed beamforming IS a Class L
(microphone-array dense-matrix combiner) ∘ Class N (rational per-element
delay coefficients matching the array geometry) composition.

Path B dual in Phase 6 (Path B mic-array bound vectors).

Carrier-free since v0.7.5rc86 (#564): plain Python ``list`` / ``list``-of-
``list`` carriers; the ``max_delay`` is the builtin ``max`` (Class-L reduce, no
``abs()``), and the per-mic combine is an explicit scale-and-accumulate
(Class-M) index loop.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Van Veen
& Buckley (1988) educational IEEE ASSP Mag. survey + Brandstein & Ward
(2001) *Microphone Arrays: Signal Processing Techniques*.
"""

from __future__ import annotations

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
        ``(n_mics, n_samples)`` real or complex 2-D sequence of per-microphone
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
    list
        Beamformer output (``list`` of ``complex``) of length ``n_samples``
        minus delay padding.
    """
    rows = list(array_signals)
    n_mics = len(rows)
    # 2-D guard: each microphone row must itself be a sized sequence of samples.
    if n_mics > 0 and not hasattr(rows[0], "__len__"):
        raise ValueError(f"beamforming expects 2-D array; got 1-D length {n_mics}")
    sig = [[complex(v) for v in row] for row in rows]
    n_samples = len(sig[0]) if n_mics > 0 else 0
    if any(len(row) != n_samples for row in sig):
        raise ValueError("beamforming expects 2-D array; rows have unequal length")
    d = [int(x) for x in delays_samples]
    if len(d) != n_mics:
        raise ValueError(f"delays_samples length {len(d)} != n_mics {n_mics}")
    if weights is None:
        w = [complex(1.0 / n_mics)] * n_mics if n_mics > 0 else []
    else:
        w = [complex(v) for v in weights]
        if len(w) != n_mics:
            raise ValueError(f"weights length {len(w)} != n_mics {n_mics}")
    # Class-L reduce: the largest delay is a plain max over the integer delays.
    max_delay = max(d) if d else 0
    out_len = n_samples - max_delay
    if out_len <= 0:
        return []
    out = [complex(0)] * out_len
    for m in range(n_mics):
        delay = d[m]
        wm = w[m]
        row = sig[m]
        # Class-M scale-and-accumulate of the delay-aligned window onto t=0.
        for i in range(out_len):
            out[i] += wm * row[delay + i]
    return out
