"""Array-aware FFT carriers over the 1-D ``spectral_cascades`` cascade.

The signal_processing Path-A / Path-B reference ops (``fft`` / ``ifft`` /
``rfft``) accept ndarrays with NumPy's ``n=`` (zero-pad / truncate the
transformed axis) and ``axis=`` semantics. The substrate-native FFT cascade
``srmech.amsc.cascade.spectral_cascades.fft`` / ``.ifft`` is 1-D (Sequence ->
List, radix-2 Cooley-Tukey with a ``dft`` fallback for non-power-of-2 N;
exact-until-rotation). These thin carriers lift the 1-D cascade to the
ndarray + ``n`` + ``axis`` contract **value-for-value**: NumPy is a carrier
only (``moveaxis`` / ``reshape`` / zero-pad / slice), the transform itself
rides the cascade.

Bit-faithful to the NumPy FFT family (forward / inverse / real / freq-bins),
verified across real + complex, 1-D + n-D, every axis, and ``n``
pad/truncate (~1e-9). ``rfft`` mirrors NumPy by rejecting complex input
(NumPy raises ``TypeError``).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from srmech.amsc.cascade import spectral_cascades as _sc


def _transform_nd(arr, n: Optional[int], axis: int, inverse: bool) -> np.ndarray:
    """Apply the 1-D cascade ``fft``/``ifft`` along ``axis`` with ``n`` semantics."""
    a = np.asarray(arr)
    if a.ndim == 0:
        a = a.reshape(1)
    a = np.moveaxis(a, axis, -1)
    length = a.shape[-1]
    if n is None:
        n = length
    if n < length:  # truncate (Class K pin-slot on the transformed axis)
        a = a[..., :n]
    elif n > length:  # zero-pad carrier
        pad_shape = list(a.shape)
        pad_shape[-1] = n - length
        a = np.concatenate([a, np.zeros(pad_shape, dtype=a.dtype)], axis=-1)
    flat = np.ascontiguousarray(a).reshape(-1, n)
    cascade = _sc.ifft if inverse else _sc.fft
    out = np.empty((flat.shape[0], n), dtype=np.complex128)
    for i in range(flat.shape[0]):
        out[i] = np.asarray(cascade(flat[i]))
    out = out.reshape(a.shape[:-1] + (n,))
    return np.moveaxis(out, -1, axis)


def fft(arr, n: Optional[int] = None, axis: int = -1) -> np.ndarray:
    """``NumPy fft``-faithful forward DFT via the cascade."""
    return _transform_nd(arr, n, axis, inverse=False)


def ifft(arr, n: Optional[int] = None, axis: int = -1) -> np.ndarray:
    """``NumPy ifft``-faithful inverse DFT via the cascade."""
    return _transform_nd(arr, n, axis, inverse=True)


def rfft(arr, n: Optional[int] = None, axis: int = -1) -> np.ndarray:
    """``NumPy rfft``-faithful real-input half-spectrum via the cascade.

    Mirrors NumPy by rejecting complex input (NumPy raises ``TypeError``).
    For real input the Hermitian half-spectrum is the full transform sliced
    to the non-redundant ``0 .. n//2`` bins (length ``n//2 + 1``).
    """
    a = np.asarray(arr)
    if np.iscomplexobj(a):
        raise TypeError(
            "rfft does not accept complex input (use fft); "
            "matches NumPy rfft which raises on complex dtype"
        )
    length = a.shape[axis] if a.ndim else 1
    effective = n if n is not None else length
    full = _transform_nd(a, n, axis, inverse=False)
    keep = range(effective // 2 + 1)
    return np.take(full, keep, axis=axis)


def fftfreq(n: int, d: float = 1.0) -> np.ndarray:
    """``NumPy fftfreq``-faithful DFT sample frequencies (pure carrier).

    Returns ``[0, 1, ..., n//2-1, -(n//2), ..., -1] / (n*d)`` — integer bin
    indices (Class I cyclic-group positions on the transformed axis) scaled
    by the carrier ``1/(n*d)``. No transcendentals; numpy is a carrier only.
    """
    val = 1.0 / (n * d)
    results = np.empty(n, dtype=int)
    half = (n - 1) // 2 + 1
    results[:half] = np.arange(0, half, dtype=int)
    results[half:] = np.arange(-(n // 2), 0, dtype=int)
    return results * val
