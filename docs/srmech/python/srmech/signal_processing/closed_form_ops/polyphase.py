"""Path A polyphase — closed-form polyphase filter decomposition.

Identity per the implementation plan §1: polyphase IS a Class L (subband
Laplacian per polyphase component) ∘ Class N (rational decomposition of the
FIR into ``L`` sub-filters indexed by ``n mod L``) composition.

The closed-form reference decomposes an FIR filter into ``L`` polyphase
components and either applies them parallel-then-mix (decimation) or
mix-then-parallel (interpolation).

Path B dual in Phase 6 (Path B subband bundle decomposition).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Vaidyanathan
(1993) *Multirate Systems and Filter Banks* §4.3 + Bellanger (1976).
"""

from __future__ import annotations

from typing import List

import numpy as np

from srmech.signal_processing import _dsp_cascades as _dsp

OPERATION_NAME = "polyphase"
CLASS_COMPOSITION = ("L", "N")
PERFORMANCE_HINT = "shallow-cascade-component-amortise"
SSOT_CITATION = (
    "Vaidyanathan (1993), 'Multirate Systems and Filter Banks', Prentice "
    "Hall, §4.3 (polyphase decomposition). Bellanger, Bonnerot & Coudreuse "
    "(1976), 'Digital filtering by polyphase network: Application to "
    "sample-rate alteration and filter banks', IEEE Trans. ASSP 24(2), "
    "109-114. DOI 10.1109/TASSP.1976.1162787 (Crossref)."
)


def decompose(filter_taps, L: int) -> List[np.ndarray]:
    """Decompose ``filter_taps`` into L polyphase components.

    ``E_k[n] = h[k + n*L]`` for k = 0..L-1.
    """
    taps = np.asarray(filter_taps, dtype=np.float64)
    # Pad to multiple of L
    pad = (-taps.shape[0]) % L
    if pad:
        taps = np.concatenate([taps, np.zeros(pad, dtype=np.float64)])
    M = taps.shape[0] // L
    components = []
    for k in range(L):
        e_k = taps[k::L]
        components.append(e_k)
    return components


def op(
    signal,
    filter_taps,
    *,
    L: int = 2,
    mode: str = "decimation",
    D: int = 8192,
):
    """Polyphase filter decomposition + apply.

    Parameters
    ----------
    signal:
        1-D real array.
    filter_taps:
        FIR filter taps.
    L:
        Polyphase order.
    mode:
        ``"decimation"`` (filter then decimate by L) or ``"interpolation"``
        (interpolate by L then filter).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    numpy.ndarray
        Polyphase-filtered output.
    """
    sig = np.asarray(signal, dtype=np.float64)
    components = decompose(filter_taps, L)
    if mode == "decimation":
        # Decimation: each polyphase component filters a decimated version
        # of the input then we sum.
        out_len = (sig.shape[0] + L - 1) // L
        out = np.zeros(out_len + components[0].shape[0] - 1, dtype=np.float64)
        for k, e_k in enumerate(components):
            # Take every L-th sample of signal starting at offset k
            x_k = sig[k::L] if k < sig.shape[0] else np.array([], dtype=np.float64)
            if x_k.shape[0] == 0:
                continue
            filtered = np.asarray(_dsp.convolve(x_k, e_k, mode="full"))
            out[: filtered.shape[0]] += filtered
        return out
    if mode == "interpolation":
        # Interpolation: filter each input through component then interleave.
        per_component = []
        for k, e_k in enumerate(components):
            filtered = np.asarray(_dsp.convolve(sig, e_k, mode="full"))
            per_component.append(filtered)
        # Interleave outputs.
        max_len = max(c.shape[0] for c in per_component)
        out = np.zeros(max_len * L, dtype=np.float64)
        for k, c in enumerate(per_component):
            out[k::L][: c.shape[0]] = c
        return out
    raise ValueError(f"mode must be 'decimation' or 'interpolation'; got {mode}")
