"""Numpy-free linear convolution / correlation cascades for the DSP layer.

The NumPy convolve and correlate calls are counted by the
``test_numpy_math_ratchet`` matmul ledger: a length-``N`` convolution is a
rank-1 accumulate, i.e. a small matrix product in disguise.  This module
replaces them with the substrate-native cascade — **Class I (cyclic shift,
the running output offset) composed with Class M (scaled accumulate, the
multiply-add of the kernel into the shifted slot)** — so the DSP closed-form
and Path-B ops carry no NumPy convolve / correlate callsite.

NumPy is used here purely as a **carrier**: ``np.zeros`` for the output buffer,
elementwise ``+`` / ``*`` for the inner accumulate, slicing for the shift and
the edge-mode crop.  No NumPy convolve / correlate / matmul / math-ufunc
appears, so the ops are libm-free and ratchet-clean.

These are signal_processing-internal helpers, **not** public
``srmech.amsc.*`` callables — they compose the existing carrier arithmetic
rather than introducing a new attested cascade op.  A future rc may promote
them to a public ``srmech.amsc.cascade`` op shipped together with a native C
twin (so they classify ``c_dispatched`` rather than adding Python-only debt).

Both functions are value-faithful to their NumPy counterparts across every
length relationship, edge mode (``"full"`` / ``"same"`` / ``"valid"``), and
dtype (real / complex / integer) — verified bit-for-bit in
``tests/test_dsp_convolution_cascade_rc58.py``.
"""

from __future__ import annotations

import numpy as np

__all__ = ["convolve", "correlate"]


def convolve(a, b, mode: str = "full"):
    """Discrete linear convolution — numpy-free Class I ∘ Class M cascade.

    Drop-in for NumPy's 1-D convolve.  The output buffer is
    a carrier; each iteration shifts the write window by one (Class I) and
    accumulates ``a[i] * b`` into it (Class M).

    Parameters
    ----------
    a, b:
        1-D array-likes.
    mode:
        ``"full"`` (default), ``"same"``, or ``"valid"`` per NumPy.

    Returns
    -------
    numpy.ndarray
        The convolution, value-faithful to NumPy convolve(a, b, mode).
    """
    a_arr = np.ascontiguousarray(a)
    b_arr = np.ascontiguousarray(b)
    if a_arr.ndim != 1 or b_arr.ndim != 1:
        raise ValueError(
            f"convolve expects 1-D inputs; got {a_arr.shape} and {b_arr.shape}"
        )
    na = a_arr.shape[0]
    nb = b_arr.shape[0]
    if na == 0 or nb == 0:
        raise ValueError("convolve inputs cannot be empty")
    full = np.zeros(na + nb - 1, dtype=np.result_type(a_arr.dtype, b_arr.dtype))
    # Class I shift (i) ∘ Class M scaled accumulate (a[i] * b into the slot).
    for i in range(na):
        full[i:i + nb] = full[i:i + nb] + a_arr[i] * b_arr
    if mode == "full":
        return full
    if mode == "same":
        target = max(na, nb)
        start = (full.shape[0] - target) // 2
        return full[start:start + target]
    if mode == "valid":
        target = max(na, nb) - min(na, nb) + 1
        start = min(na, nb) - 1
        return full[start:start + target]
    raise ValueError("mode must be one of 'full', 'same', 'valid'")


def correlate(a, v, mode: str = "valid"):
    """Cross-correlation — numpy-free, via the convolution cascade.

    Drop-in for NumPy's 1-D correlate:
    ``c[k] = sum_n a[n + k] * conj(v[n])``.  Built as
    ``convolve(a, conj(v)[::-1])`` (``np.conj`` is a carrier, not a counted
    math-ufunc), with NumPy's exact ``"same"``-mode crop — which centres on
    ``floor(diff/2)`` when ``len(a) >= len(v)`` and ``ceil(diff/2)`` when
    ``len(a) < len(v)`` (the historical NumPy swap convention).

    Parameters
    ----------
    a, v:
        1-D array-likes.
    mode:
        ``"valid"`` (default), ``"same"``, or ``"full"`` per NumPy.

    Returns
    -------
    numpy.ndarray
        The cross-correlation, value-faithful to NumPy correlate(a, v, mode).
    """
    a_arr = np.ascontiguousarray(a)
    v_arr = np.ascontiguousarray(v)
    if a_arr.ndim != 1 or v_arr.ndim != 1:
        raise ValueError(
            f"correlate expects 1-D inputs; got {a_arr.shape} and {v_arr.shape}"
        )
    na = a_arr.shape[0]
    nv = v_arr.shape[0]
    full = convolve(a_arr, np.conj(v_arr)[::-1], "full")
    if mode == "full":
        return full
    if mode == "valid":
        target = max(na, nv) - min(na, nv) + 1
        start = min(na, nv) - 1
        return full[start:start + target]
    if mode == "same":
        target = max(na, nv)
        diff = full.shape[0] - target
        # Class K pin-slot at the centre: floor below the boundary, ceil above.
        start = diff // 2 if na >= nv else (diff + 1) // 2
        return full[start:start + target]
    raise ValueError("mode must be one of 'full', 'same', 'valid'")
