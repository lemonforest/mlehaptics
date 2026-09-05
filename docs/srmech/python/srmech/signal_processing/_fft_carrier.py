"""Array-aware FFT carriers over the 1-D ``spectral_cascades`` cascade.

The signal_processing Path-A / Path-B reference ops (``fft`` / ``ifft`` /
``rfft``) accept ndarrays with NumPy's ``n=`` (zero-pad / truncate the
transformed axis) and ``axis=`` semantics. The substrate-native FFT cascade
``srmech.cascade.spectral_cascades.fft`` / ``.ifft`` is 1-D (Sequence ->
List, radix-2 Cooley-Tukey with a ``dft`` fallback for non-power-of-2 N;
exact-until-rotation).

**Carrier-removal (task #564):** the common **1-D / default-axis** case runs
**numpy-free** — a stdlib list flows straight through the substrate-native
cascade and comes back a ``List[complex]`` — the framework-native carrier,
unconditionally. The **n-D / non-default-axis** case is not supported: it
raises a clean ``ValueError`` (#564). This module is loadable and fully
runnable with no numpy installed.

Bit-faithful to the NumPy FFT family (forward / inverse / real / freq-bins),
verified across real + complex 1-D input on the default axis, with ``n``
pad/truncate (~1e-9). ``rfft`` mirrors NumPy by rejecting complex input
(NumPy raises ``TypeError``). The transform values are identical on both
paths — only the carrier shaping differs — because both ride the same
``spectral_cascades`` cascade.
"""

from __future__ import annotations

from typing import List, Optional

from srmech.cascade import spectral_cascades as _sc


def _is_nested(seq) -> bool:
    """True if the first element is itself a sequence (→ caller passed n-D)."""
    return bool(seq) and (
        isinstance(seq[0], (list, tuple)) or hasattr(seq[0], "__len__")
    )


def _apply_n(data: list, n: Optional[int]) -> list:
    """NumPy ``n=`` semantics, numpy-free: truncate (Class K pin-slot) / zero-pad.

    rc466 (`#T1188`): the pad is the exact integer ``0`` — on the exact route
    it keeps an integer signal integer, and on the float route the cascade's
    own ``complex(v)`` makes it ``0j``, byte-identical to the old ``[0j]`` pad."""
    length = len(data)
    if n is None or n == length:
        return data
    if n < length:
        return data[:n]
    return data + [0] * (n - length)


def _transform_1d(seq, n: Optional[int], cascade) -> List[complex]:
    """The numpy-free 1-D transform: Sequence → cascade → ``List[complex]``.

    ⚠️ rc466 (`#T1188`): the operand is handed to the cascade AS GIVEN. Through
    rc465 this read ``[complex(x) for x in seq]`` — and the cascade it hands the
    frame to (:func:`srmech.cascade.spectral_cascades.fft`) already routes an
    integer / Gaussian-integer signal through the exact-until-rotation
    cyclotomic engine, so the one line here rounded the operand BEFORE the
    exact engine saw it: ``rfft([2**53+1, 0, -1, 0, 1, 0, -1, 0])[0]`` came
    back ``9007199254740991+0j`` while the cascade on the same list gives the
    exact ``9007199254740992+0j`` (Σx = 2**53). The exact engine transformed
    the wrong signal faithfully. A float signal takes the cascade's float route
    exactly as before."""
    data = _apply_n(list(seq), n)
    if not data:
        return []
    return [complex(z) for z in cascade(data)]


def _try_1d_sequence(arr):
    """Return ``list(arr)`` if ``arr`` is a plain 1-D sequence, else ``None``.

    A numpy ndarray reports ``.ndim``; a plain list/tuple is 1-D iff its first
    element is a scalar (not itself a sequence)."""
    ndim = getattr(arr, "ndim", None)
    if ndim == 1:
        return list(arr)
    if ndim is not None:  # 0-D or n-D ndarray → not the 1-D fast path
        return None
    try:
        seq = list(arr)
    except TypeError:
        return None
    return None if _is_nested(seq) else seq


def _transform_nd(arr, n: Optional[int], axis: int, inverse: bool):
    """Apply the 1-D cascade ``fft``/``ifft`` along the default axis with ``n``
    semantics — numpy-free (#564), returns a ``List[complex]``.

    Only the **1-D / default-axis** case is supported: numpy is gone, so the n-D
    ``moveaxis`` / ``reshape`` / zero-pad carrier (and any non-default ``axis``)
    raises a clean ``ValueError``."""
    cascade = _sc.ifft if inverse else _sc.fft
    if axis in (-1, 0):
        seq = _try_1d_sequence(arr)
        if seq is not None:
            return _transform_1d(seq, n, cascade)
    raise ValueError(
        "numpy-free FFT supports a 1-D sequence with the default axis only "
        "(#564: numpy removed); got an n-D input or a non-default axis "
        f"(axis={axis}). Transform each 1-D slice with the default axis."
    )


def fft(arr, n: Optional[int] = None, axis: int = -1):
    """``NumPy fft``-faithful forward DFT via the cascade (numpy-free for 1-D)."""
    return _transform_nd(arr, n, axis, inverse=False)


def ifft(arr, n: Optional[int] = None, axis: int = -1):
    """``NumPy ifft``-faithful inverse DFT via the cascade (numpy-free for 1-D)."""
    return _transform_nd(arr, n, axis, inverse=True)


def rfft(arr, n: Optional[int] = None, axis: int = -1):
    """``NumPy rfft``-faithful real-input half-spectrum (numpy-free for 1-D).

    Mirrors NumPy by rejecting complex input (NumPy raises ``TypeError``).
    For real input the Hermitian half-spectrum is the full transform sliced
    to the non-redundant ``0 .. n//2`` bins (length ``n//2 + 1``).

    **Accuracy (rc466, `#T1188`).** An integer signal rides the cascade's
    exact-until-rotation route (:func:`srmech.cascade.spectral_cascades.fft`
    routes 1-2: every coefficient an exact ``ℤ[ζ_N]`` integer) and the returned
    ``complex`` is its single **terminal float lift** — exact wherever the bin
    value is float-representable (the DC bin of any integer signal is the exact
    sum ``Σx`` up to 2**53), **accurate to round-off** (~1 ULP) otherwise. A
    float signal is transformed on the float64 carrier, **accurate to
    round-off**. A non-integral rational leaf takes the float route (the
    exact engine admits ``ℤ`` / ``ℤ[i]`` only)."""
    if axis in (-1, 0):
        seq = _try_1d_sequence(arr)
        if seq is not None:
            if any(isinstance(x, complex) for x in seq):  # numpy-complex too (subclass)
                raise TypeError(
                    "rfft does not accept complex input (use fft); "
                    "matches NumPy rfft which raises on complex dtype"
                )
            effective = n if n is not None else len(seq)
            full = _transform_1d(seq, n, _sc.fft)
            return full[: effective // 2 + 1]
    raise ValueError(
        "numpy-free rfft supports a 1-D sequence with the default axis only "
        f"(#564: numpy removed); got an n-D input or a non-default axis (axis={axis})."
    )


def fftfreq(n: int, d: float = 1.0):
    """``NumPy fftfreq``-faithful DFT sample frequencies (numpy-free, #564).

    Returns ``[0, 1, ..., n//2-1, -(n//2), ..., -1] / (n*d)`` — integer bin
    indices (Class I cyclic-group positions on the transformed axis) scaled by
    the carrier ``1/(n*d)``. No transcendentals; a plain ``List[float]``."""
    val = 1.0 / (n * d)
    half = (n - 1) // 2 + 1
    idx = list(range(0, half)) + list(range(-(n // 2), 0))
    return [i * val for i in idx]
