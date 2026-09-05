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

rc150 (B4c) classification:
  • :func:`op` — ``composition_of_c``.  The heavy numeric kernel is the
    per-component convolution; when the native lib is present each
    ``E_k * x_k`` re-expresses the (feed-forward-only) linear filter as a
    **Toeplitz matvec** routed through ``_dsp.convolve_matmul`` →
    ``laplacian.mat_matvec`` ∘ ``mat_matmul`` → the c_dispatched
    ``srmech_dense_matmul_complex``; otherwise the complete numpy-free pure
    ``_dsp.convolve`` cascade.  The strided split / accumulate / interleave are
    exact integer-indexed glue.  NUMERIC (within-tol, not byte-identical):
    reldiff ≤ 1e-9 (the matmul float accumulation may FMA-fuse ~1 ULP).
  • :func:`decompose` — ``non_compute``.  Splitting a tap table into ``L``
    phase branches ``E_k[n] = h[k + n·L]`` is a pure integer **reindex**
    (``taps[k::L]`` list-slices + a zero-pad to a multiple of ``L``); there is
    NO floating-point kernel — nothing to mirror in C — so it honestly carries
    no owed-C debt (``h[k + n·L]`` is trivial pointer arithmetic on a C host,
    not a numeric kernel).

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

    rc466 (`#T1188`): a pure REINDEX — the taps are kept as given when every
    tap is exact (``int`` / ``Q`` / ``(num, den)``), so an exact prototype
    decomposes into exact components; a float tap keeps the float carrier.
    """
    taps = list(filter_taps)
    if _dsp.exact_operands(taps):
        pad_v = 0
    else:
        taps = [float(v) for v in taps]
        pad_v = 0.0
    # Pad to multiple of L
    pad = (-len(taps)) % L
    if pad:
        taps = taps + [pad_v] * pad
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
        Polyphase-filtered output (length-``N`` ``list`` of ``float``, or of
        ``int`` / ``Q`` on the exact route — see below).

    Accuracy (rc466, `#T1188`)
    --------------------------
    **The carrier is the operand's.** An exact ``signal`` AND exact
    ``filter_taps`` (every leaf ``int`` / ``Q`` / ``(num, den)``) take the
    type-preserving pure convolution cascade on BOTH projections
    (:func:`srmech.signal_processing._dsp_cascades.convolve`, seeded with the
    integer ``0``) and the output is the EXACT filter response — integers for
    integers, ``Q`` for rationals — the rc463 ``fir`` routing, verbatim. A
    float leaf anywhere keeps the c_dispatched Toeplitz matvec
    (``srmech_dense_matmul_complex``), **accurate to round-off** (~1 ULP;
    the accumulation may FMA-fuse). Through rc465 ``[float(v) for v in
    signal]`` ran at the entry and EVERY call took the float matvec whenever
    the library was loaded, so ``polyphase([2**53+1, 2, 3], [1, 2, 3, 4])``
    returned ``9007199254740992.0`` where the exact cascade gives
    ``9007199254740993``.
    """
    sig = list(signal)
    exact = _dsp.exact_operands(sig, filter_taps)
    if not exact:
        sig = [float(v) for v in sig]
    components = decompose(filter_taps, L)
    # composition_of_c (rc150 / B4c): route each per-component convolution through
    # the c_dispatched srmech_dense_matmul_complex (Toeplitz matvec) when the
    # native lib is present; else the complete numpy-free pure cascade. Within-tol
    # (not byte-identical): the matmul float accumulation may FMA-fuse ~1 ULP.
    # rc466: EXACT operands take the pure cascade on BOTH projections (the
    # rc463 fir precedent — see _dsp.exact_operands).
    from srmech import _native

    _convolve = (
        _dsp.convolve_matmul
        if (
            _native.HAS_NATIVE
            and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_dense_matmul_complex")
            and not exact
        )
        else _dsp.convolve
    )
    zero = 0 if exact else 0.0
    if mode == "decimation":
        # Decimation: each polyphase component filters a decimated version
        # of the input then we sum (Class-M accumulate into the shared buffer).
        out_len = (len(sig) + L - 1) // L
        out = [zero] * (out_len + len(components[0]) - 1)
        for k, e_k in enumerate(components):
            # Take every L-th sample of signal starting at offset k
            x_k = sig[k::L] if k < len(sig) else []
            if len(x_k) == 0:
                continue
            filtered = _convolve(x_k, e_k, mode="full")
            for i in range(len(filtered)):
                out[i] += filtered[i]
        return out
    if mode == "interpolation":
        # Interpolation: filter each input through component then interleave.
        per_component = []
        for e_k in components:
            filtered = _convolve(sig, e_k, mode="full")
            per_component.append(filtered)
        # Interleave outputs (strided write, Class-C reorientation).
        max_len = max(len(c) for c in per_component)
        out = [zero] * (max_len * L)
        for k, c in enumerate(per_component):
            for i in range(len(c)):
                out[k + i * L] = c[i]
        return out
    raise ValueError(f"mode must be 'decimation' or 'interpolation'; got {mode}")
