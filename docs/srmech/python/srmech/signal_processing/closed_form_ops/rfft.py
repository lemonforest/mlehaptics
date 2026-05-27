"""Path A real-input FFT — closed-form half-spectrum cyclic DFT.

Real-input specialisation of :func:`srmech.signal_processing.closed_form_ops.fft.op`.
For a real signal the full DFT is Hermitian-symmetric
(``X[N-k] = conj(X[k])``), so the second half carries no new
information; ``rfft`` returns only the non-redundant first ``N//2 + 1``
bins. Half the compute and half the memory of the full ``fft``;
**algebra-identical** on the retained bins — not a correctness change.

Identity per ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``
+ ``[[user_stance_rotation_is_class_k_pin_slot]]`` + Spike #176: the
cyclic-DFT IS a Class A (content-addressing on canonical sequence order)
∘ Class I (cyclic-group ℤ/N transform domain) ∘ Class K (rotation as
pin-slot on the unit circle) composition. ``rfft`` is that same
composition restricted to the **real-symmetric half-substrate**: the
Hermitian conjugate-symmetry is the reflection the Class K pin-slot
already encodes, so only the independent half is materialised.

Path B dual ships alongside in
``srmech.signal_processing.path_b_ops.rfft`` (UPSTREAM_NOTES §1.1 from
the RBS-LM research subtree: real bit-string FFT cascades — bipolar bits
in {-1, +1} — used full ``fft`` at 2× cost; ``rfft`` closes that gap).

Closed-form reference: numpy's ``numpy.fft.rfft`` (Cooley & Tukey 1965 +
FFTPACK / pocketfft backends).
"""

from __future__ import annotations

from typing import Optional

import numpy as np

OPERATION_NAME = "rfft"
CLASS_COMPOSITION = ("A", "I", "K")
PERFORMANCE_HINT = "small-D-one-shot-real-input"
SSOT_CITATION = (
    "Cooley & Tukey (1965), 'An algorithm for the machine calculation of "
    "complex Fourier series', Math. Comp. 19, 297-301. DOI 10.1090/"
    "S0025-5718-1965-0178586-1 (Crossref-verified). Real-input Hermitian "
    "half-spectrum per Oppenheim & Schafer (2010) DTSP (3rd ed.) §8.6."
)


def op(signal, *, n: Optional[int] = None, axis: int = -1, D: int = 8192):
    """Forward real-input discrete Fourier transform of ``signal``.

    Parameters
    ----------
    signal:
        Real array-like. (A complex input has its real part taken by
        ``numpy.fft.rfft``; pass complex data to ``fft`` instead.)
    n:
        Optional length of the transformed axis. ``None`` -> use signal
        length. Output length along ``axis`` is ``n // 2 + 1``.
    axis:
        Axis over which to compute the rFFT. Default last axis.
    D:
        Path B dimensionality (retained for cross-path API consistency;
        not used by the Path A closed-form numpy backend).

    Returns
    -------
    numpy.ndarray
        Complex DFT coefficients for the non-redundant bins
        ``0 .. N//2`` (length ``N//2 + 1``).
    """
    arr = np.asarray(signal)
    return np.fft.rfft(arr, n=n, axis=axis)
