"""Array-aware FFT carriers over the 1-D ``spectral_cascades`` cascade.

The signal_processing Path-A / Path-B reference ops (``fft`` / ``ifft`` /
``rfft``) accept ndarrays with NumPy's ``n=`` (zero-pad / truncate the
transformed axis) and ``axis=`` semantics. The substrate-native FFT cascade
``srmech.amsc.cascade.spectral_cascades.fft`` / ``.ifft`` is 1-D (Sequence ->
List, radix-2 Cooley-Tukey with a ``dft`` fallback for non-power-of-2 N;
exact-until-rotation).

**Carrier-removal (task #564):** the common **1-D / default-axis** case runs
**numpy-free** — a stdlib list flows straight through the substrate-native
cascade and comes back a list (the framework-native carrier when numpy is
absent; for API parity an ``ndarray`` when numpy is present). Only the
**n-D / non-default-axis** case still needs numpy as a carrier (``moveaxis`` /
``reshape`` / zero-pad), and it imports numpy **lazily** — so this module is
loadable AND 1-D-runnable with no numpy installed.

Bit-faithful to the NumPy FFT family (forward / inverse / real / freq-bins),
verified across real + complex, 1-D + n-D, every axis, and ``n``
pad/truncate (~1e-9). ``rfft`` mirrors NumPy by rejecting complex input
(NumPy raises ``TypeError``). The transform values are identical on both
paths — only the carrier shaping differs — because both ride the same
``spectral_cascades`` cascade.
"""

from __future__ import annotations

from typing import List, Optional

from srmech.amsc.cascade import spectral_cascades as _sc


def _is_nested(seq) -> bool:
    """True if the first element is itself a sequence (→ caller passed n-D)."""
    return bool(seq) and (
        isinstance(seq[0], (list, tuple)) or hasattr(seq[0], "__len__")
    )


def _apply_n(data: List[complex], n: Optional[int]) -> List[complex]:
    """NumPy ``n=`` semantics, numpy-free: truncate (Class K pin-slot) / zero-pad."""
    length = len(data)
    if n is None or n == length:
        return data
    if n < length:
        return data[:n]
    return data + [0j] * (n - length)


def _transform_1d(seq, n: Optional[int], cascade) -> List[complex]:
    """The numpy-free 1-D transform: Sequence → cascade → ``List[complex]``."""
    data = _apply_n([complex(x) for x in seq], n)
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
    to the non-redundant ``0 .. n//2`` bins (length ``n//2 + 1``)."""
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
