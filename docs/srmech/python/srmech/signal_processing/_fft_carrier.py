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


def _maybe_numpy():
    """Return the numpy module if importable, else ``None`` (numpy-free path)."""
    try:
        import numpy as np

        return np
    except ImportError:  # pragma: no cover - numpy-absent path
        return None


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
    """Apply the 1-D cascade ``fft``/``ifft`` along ``axis`` with ``n`` semantics.

    1-D / default-axis runs numpy-free; n-D / non-default-axis uses numpy as a
    carrier (lazy import). With numpy present the 1-D path returns an
    ``ndarray`` for API parity; with numpy absent it returns the list."""
    cascade = _sc.ifft if inverse else _sc.fft
    if axis in (-1, 0):
        seq = _try_1d_sequence(arr)
        if seq is not None:
            result = _transform_1d(seq, n, cascade)
            np = _maybe_numpy()
            return np.asarray(result) if np is not None else result
    # n-D / non-default axis → numpy carrier (lazy)
    np = _maybe_numpy()
    if np is None:  # pragma: no cover - numpy-absent path
        raise ImportError(
            "n-D / non-default-axis FFT needs numpy (install 'srmech[scientific]'); "
            "the numpy-free path is a 1-D sequence with the default axis"
        )
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
    out = np.empty((flat.shape[0], n), dtype=np.complex128)
    for i in range(flat.shape[0]):
        out[i] = np.asarray(cascade(flat[i]))
    out = out.reshape(a.shape[:-1] + (n,))
    return np.moveaxis(out, -1, axis)


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
            half = full[: effective // 2 + 1]
            np = _maybe_numpy()
            return np.asarray(half) if np is not None else half
    np = _maybe_numpy()
    if np is None:  # pragma: no cover - numpy-absent path
        raise ImportError(
            "n-D / non-default-axis rfft needs numpy; the numpy-free path is 1-D"
        )
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


def fftfreq(n: int, d: float = 1.0):
    """``NumPy fftfreq``-faithful DFT sample frequencies (numpy-free carrier).

    Returns ``[0, 1, ..., n//2-1, -(n//2), ..., -1] / (n*d)`` — integer bin
    indices (Class I cyclic-group positions on the transformed axis) scaled
    by the carrier ``1/(n*d)``. No transcendentals; a plain list when numpy is
    absent, an ``ndarray`` for parity when present."""
    val = 1.0 / (n * d)
    half = (n - 1) // 2 + 1
    idx = list(range(0, half)) + list(range(-(n // 2), 0))
    result = [i * val for i in idx]
    np = _maybe_numpy()
    return np.asarray(result) if np is not None else result
