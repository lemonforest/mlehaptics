"""Path A multitaper — closed-form DPSS / Slepian multitaper spectral estimator.

Identity per the implementation plan §1: multitaper IS a Class L (band-limit
Laplacian eigendecomposition producing DPSS / discrete prolate spheroidal
sequences) ∘ Class M (bundle averaging across tapered eigenspectrum-windowed
periodograms) composition.

The closed-form reference uses scipy.signal.windows.dpss when available, else
falls back to a sinc-based Slepian approximation. The averaging is the
canonical multitaper estimator.

Path B dual in Phase 6 (DPSS bound-vector bank).

Carrier-free since v0.7.5rc91 (#564): plain Python ``list`` carriers. scipy is
an EXTERNAL accelerator (it needs numpy), so the ``dpss`` primary path stays a
LAZY import — numpy-absent it raises ImportError and the op falls through to the
fully numpy-free cosine-taper fallback. The fallback's cosine tapers use the
**Class-N π cascade** (``_PI``) fed to ``rational.sin`` via ``_csin``; the taper
ℓ²-normalisation is the inline ``rational.sqrt(Σvᵢ²)`` (the old `dense_norm`
helper is numpy-carrier INTERNALLY, so it cannot be called numpy-free). The
per-taper periodogram ``|F|²=real²+imag²`` (no ``abs()``) and the bundle average
are explicit elementwise list comprehensions; ``_sc.fft`` returns
``List[complex]`` numpy-absent.

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Slepian
(1978) + Thomson (1982) + Percival & Walden (1993).
"""

from __future__ import annotations

from typing import List

from srmech.amsc import rational as _srn
from srmech.amsc.cascade import spectral_cascades as _sc

OPERATION_NAME = "multitaper"
CLASS_COMPOSITION = ("L", "M")
PERFORMANCE_HINT = "shallow-cascade-bundle-amortise"
SSOT_CITATION = (
    "Slepian (1978), 'Prolate spheroidal wave functions, Fourier analysis, "
    "and uncertainty - V: The discrete case', Bell Sys. Tech. J. 57(5), "
    "1371-1430. Thomson (1982), 'Spectrum estimation and harmonic analysis', "
    "Proc. IEEE 70(9), 1055-1096. DOI 10.1109/PROC.1982.12433. Percival & "
    "Walden (1993), 'Spectral Analysis for Physical Applications', "
    "Cambridge."
)

# Class-N π geometric cascade (Archimedes hexagon-doubling; Spike #32), numpy-free.
_PI = float(_srn.pi_cascade_digits(30))


def _csin(a):
    """Elementwise substrate-native sine (Class-N rational cascade), numpy-free.

    Replaces ``np.sin`` on the cosine-taper angle array — routes each angle
    through ``srmech.amsc.rational.sin`` (pi-free range reduction); no ``np.sin``
    / ``math.sin`` in the call graph. ``rational.sin`` returns an exact ``Q``;
    the taper bank is a real FPU windowing array that multiplies the complex
    signal, so collapse to ``float`` here (the last-mile rotate — ``Q × complex``
    has no interop by design). Returns a plain ``list`` of ``float``.
    """
    return [float(_srn.sin(float(v))) for v in a]


def op(
    signal,
    *,
    n_tapers: int = 4,
    nw: float = 4.0,
    D: int = 8192,
) -> List[float]:
    """Multitaper power spectral density estimate of ``signal``.

    Parameters
    ----------
    signal:
        1-D real sequence.
    n_tapers:
        Number of DPSS tapers (must satisfy ``n_tapers <= 2*nw - 1``).
    nw:
        Time-bandwidth product (Slepian concentration parameter).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    list
        Real PSD estimate of length ``len(signal)`` as a ``list`` of ``float``.
    """
    seq = list(signal)
    if seq and hasattr(seq[0], "__len__") and not isinstance(seq[0], (str, bytes)):
        raise ValueError("multitaper expects 1-D signal")
    arr = [float(v) for v in seq]
    n = len(arr)
    try:
        from scipy.signal.windows import dpss  # type: ignore[import-untyped]

        tapers = [[float(x) for x in row] for row in dpss(n, NW=nw, Kmax=n_tapers)]
    except (ImportError, ValueError):
        # Fallback: cosine tapers (sinusoidal multitaper approximation; less
        # concentrated but identity-preserving for the dispatch surface).
        tapers = []
        for k in range(n_tapers):
            raw = _csin([_PI * (k + 1) * (i + 1) / (n + 1) for i in range(n)])
            # ℓ² norm via Class-N sqrt → exact Q; collapse to float so the taper
            # bank (which multiplies the complex signal below) stays real-FPU.
            norm = float(_srn.sqrt(sum(v * v for v in raw)))
            tapers.append([v / norm for v in raw])
    acc = [0.0] * n
    for k in range(n_tapers):
        tapered = [arr[i] * tapers[k][i] for i in range(n)]
        spec = list(_sc.fft(tapered))
        for i in range(n):
            acc[i] += spec[i].real * spec[i].real + spec[i].imag * spec[i].imag
    return [v / n_tapers for v in acc]
