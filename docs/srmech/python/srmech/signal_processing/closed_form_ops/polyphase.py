"""Path A polyphase — closed-form polyphase filter decomposition.

Identity per the implementation plan §1: polyphase IS a Class L (subband
Laplacian per polyphase component) ∘ Class N (rational decomposition of the
FIR into ``L`` sub-filters indexed by ``n mod L``) composition.

The closed-form reference decomposes an FIR filter into ``L`` polyphase
components and either applies them parallel-then-mix (decimation) or
mix-then-parallel (interpolation).

Path B dual in Phase 6 (Path B subband bundle decomposition).

Carrier-free since v0.7.5rc85 (#564): plain Python ``list`` carriers; the only
delegate ``_dsp.convolve`` is already numpy-free (returns ``List[float]``). The
strided polyphase split/interleave and the per-component accumulate are explicit
index loops (Class-M elementwise adds); the ``[::L]`` strides are native list
slices.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Vaidyanathan
(1993) *Multirate Systems and Filter Banks* §4.3 + Bellanger (1976).
"""

from __future__ import annotations

from typing import List

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


def decompose(filter_taps, L: int) -> List[list]:
    """Decompose ``filter_taps`` into L polyphase components.

    ``E_k[n] = h[k + n*L]`` for k = 0..L-1. Returns a ``list`` of L ``list``s.
    """
    taps = [float(v) for v in filter_taps]
    # Pad to multiple of L
    pad = (-len(taps)) % L
    if pad:
        taps = taps + [0.0] * pad
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
        1-D real sequence.
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
    list
        Polyphase-filtered output (length-``N`` ``list`` of ``float``).
    """
    sig = [float(v) for v in signal]
    components = decompose(filter_taps, L)
    if mode == "decimation":
        # Decimation: each polyphase component filters a decimated version
        # of the input then we sum (Class-M accumulate into the shared buffer).
        out_len = (len(sig) + L - 1) // L
        out = [0.0] * (out_len + len(components[0]) - 1)
        for k, e_k in enumerate(components):
            # Take every L-th sample of signal starting at offset k
            x_k = sig[k::L] if k < len(sig) else []
            if len(x_k) == 0:
                continue
            filtered = _dsp.convolve(x_k, e_k, mode="full")
            for i in range(len(filtered)):
                out[i] += filtered[i]
        return out
    if mode == "interpolation":
        # Interpolation: filter each input through component then interleave.
        per_component = []
        for e_k in components:
            filtered = _dsp.convolve(sig, e_k, mode="full")
            per_component.append(filtered)
        # Interleave outputs (strided write, Class-C reorientation).
        max_len = max(len(c) for c in per_component)
        out = [0.0] * (max_len * L)
        for k, c in enumerate(per_component):
            for i in range(len(c)):
                out[k + i * L] = c[i]
        return out
    raise ValueError(f"mode must be 'decimation' or 'interpolation'; got {mode}")
