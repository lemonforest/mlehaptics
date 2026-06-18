"""Numpy-free linear convolution / correlation cascades for the DSP layer.

The NumPy convolve and correlate calls are counted by the
``test_numpy_math_ratchet`` matmul ledger: a length-``N`` convolution is a
rank-1 accumulate, i.e. a small matrix product in disguise.  This module
replaces them with the substrate-native cascade — **Class I (cyclic shift,
the running output offset) composed with Class M (scaled accumulate, the
multiply-add of the kernel into the shifted slot)** — so the DSP closed-form
and Path-B ops carry no NumPy convolve / correlate callsite.

Carrier note (#564): this module is now **numpy-free** at import and at run.
rc58 already removed numpy as the *math engine* (no convolve / correlate /
matmul / math-ufunc); rc79 removes the last numpy *carrier* — the output
buffer is a plain Python ``list`` (``[0] * N``, which promotes int → float →
complex exactly as the element arithmetic dictates), the shift is a list
slice, and the conjugate is the element's own ``.conjugate()`` (Python
``int`` / ``float`` / ``complex`` all provide it; so does any numpy scalar a
caller may still pass in).  No ``import numpy`` appears, so a length-``N``
convolution runs with no numpy present at all.

These are signal_processing-internal helpers, **not** public
``srmech.amsc.*`` callables — they compose the existing carrier arithmetic
rather than introducing a new attested cascade op.  A future rc may promote
them to a public ``srmech.amsc.cascade`` op shipped together with a native C
twin (so they classify ``c_dispatched`` rather than adding Python-only debt).

Both functions are value-faithful to their NumPy counterparts across every
length relationship, edge mode (``"full"`` / ``"same"`` / ``"valid"``), and
dtype (real / complex / integer) — verified bit-for-bit in
``tests/test_dsp_convolution_cascade_rc58.py``.  They return a Python
``list``; callers that need an ndarray wrap the result in ``np.asarray`` at
their own (numpy-importing) boundary.
"""

from __future__ import annotations

__all__ = ["convolve", "correlate"]


def _as_1d_list(x, name):
    """Coerce ``x`` to a flat Python list, rejecting nested (>1-D) sequences."""
    lst = list(x)
    # A 1-D numeric sequence has scalar elements; a nested sequence (2-D) has
    # elements that are themselves sized — reject those (mirrors ndim != 1).
    for e in lst:
        if hasattr(e, "__len__"):
            raise ValueError(f"{name} expects a 1-D input; got a nested sequence")
    return lst


def _conj(x):
    """Element conjugate — a carrier transform, not a counted math-ufunc.

    Python ``int`` / ``float`` / ``complex`` (and numpy scalars) all provide
    ``.conjugate()``; for reals it returns the value unchanged.
    """
    return x.conjugate()


def convolve(a, b, mode: str = "full"):
    """Discrete linear convolution — numpy-free Class I ∘ Class M cascade.

    Drop-in for NumPy's 1-D convolve.  The output buffer is a carrier; each
    iteration shifts the write window by one (Class I) and accumulates
    ``a[i] * b`` into it (Class M).

    Parameters
    ----------
    a, b:
        1-D array-likes.
    mode:
        ``"full"`` (default), ``"same"``, or ``"valid"`` per NumPy.

    Returns
    -------
    list
        The convolution, value-faithful to NumPy convolve(a, b, mode).
    """
    a_lst = _as_1d_list(a, "convolve")
    b_lst = _as_1d_list(b, "convolve")
    na = len(a_lst)
    nb = len(b_lst)
    if na == 0 or nb == 0:
        raise ValueError("convolve inputs cannot be empty")
    # Class I shift (i) ∘ Class M scaled accumulate (a[i] * b[j] into slot i+j).
    # Buffer seeded with int 0 so an all-integer convolution stays integer
    # (matching numpy's result_type), promoting to float / complex exactly when
    # the element arithmetic does. Accumulation order (i outer, j inner) matches
    # numpy's `full[i:i+nb] += a[i]*b` — so floats are bit-faithful.
    full = [0] * (na + nb - 1)
    for i in range(na):
        ai = a_lst[i]
        for j in range(nb):
            full[i + j] = full[i + j] + ai * b_lst[j]
    if mode == "full":
        return full
    if mode == "same":
        target = max(na, nb)
        start = (len(full) - target) // 2
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
    ``convolve(a, conj(v)[::-1])`` (the conjugate is a carrier, not a counted
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
    list
        The cross-correlation, value-faithful to NumPy correlate(a, v, mode).
    """
    a_lst = _as_1d_list(a, "correlate")
    v_lst = _as_1d_list(v, "correlate")
    na = len(a_lst)
    nv = len(v_lst)
    v_rev_conj = [_conj(x) for x in v_lst][::-1]
    full = convolve(a_lst, v_rev_conj, "full")
    if mode == "full":
        return full
    if mode == "valid":
        target = max(na, nv) - min(na, nv) + 1
        start = min(na, nv) - 1
        return full[start:start + target]
    if mode == "same":
        target = max(na, nv)
        diff = len(full) - target
        # Class K pin-slot at the centre: floor below the boundary, ceil above.
        start = diff // 2 if na >= nv else (diff + 1) // 2
        return full[start:start + target]
    raise ValueError("mode must be one of 'full', 'same', 'valid'")
